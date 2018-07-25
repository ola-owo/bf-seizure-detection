#!/usr/bin/env python2
'''
New and improved line length seizure detector,
using adaptive thresholds

Usage: python lineLength.py ptName [startTime [endTime]] [append]
'''
import sys
from time import sleep

from blackfynn import Blackfynn
import numpy as np
from requests.exceptions import RequestException

from settings import (
    CHANNELS, DEFAULT_FREQ, FREQs, LL_LONG_WINDOW_DEFAULT,
    LL_SHORT_WINDOW_DEFAULT, LL_LONG_WINDOWS, LL_SHORT_WINDOWS, LL_MA_LAYER_NAME,
    LL_MA_THRESHOLDS, TS_IDs
)

shortWindow = None
longWindow = None
freq = None
ch = None

def lineLength(ptName, startTime=None, endTime=None, append=False, layerName=LL_MA_LAYER_NAME):
    '''
    Runs the line length detector.

    ch: channels to annotate
    startTime: time (usec) to start from. Default value (None) starts from the beginning
    append: Whether to append to (or otherwise overwrite) the line length annotation layer
    layerName: name of layer to write to

    Returns: endTime (the end of the last full long-term window)
    '''
    global shortWindow, longWindow, freq, ch
    longWindow = LL_LONG_WINDOWS.get(ptName, LL_LONG_WINDOW_DEFAULT)
    shortWindow = LL_SHORT_WINDOWS.get(ptName, LL_SHORT_WINDOW_DEFAULT)
    freq = FREQs.get(ptName, DEFAULT_FREQ)
    ch = CHANNELS.get(ptName, None)

    bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])

    # Make sure startTime and endTime are valid
    if startTime is not None:
        if startTime < ts.start:
            print 'Warning: startTime', startTime, 'is before the beginning of the Timeseries. Starting from the beginning...'
            startTime = None
        elif startTime > ts.end:
            print 'Warning: startTime', startTime, 'is after the end of the Timeseries. Exiting...'
            if endTime is None:
                return ts.end
            else:
                return endTime

    if endTime is not None:
        if endTime > ts.end:
            print 'Warning: endTime', endTime, 'is after the end of the Timeseries. Stopping at the end...'
            endTime = None
        elif endTime < ts.start:
            print 'Warning: endTime', endTime, 'is before the beginning the Timeseries. Exiting...'
            return ts.start

    # Get/create annotation layer
    try:
        layer = ts.get_layer(layerName)
        if append:
            print "Appending to layer '%s'" % layerName
        else:
            print "Overwriting layer '%s'" % layerName
            layer.delete()
            layer = ts.add_layer(layerName)
    except:
        print "Creating layer '%s'" % layerName
        layer = ts.add_layer(layerName)

    # Find the long-term windows to start and end from
    windowStart = ts.start
    windowEnd = windowStart + longWindow
    if startTime:
        while windowEnd < startTime:
            windowStart = windowEnd
            windowEnd += longWindow
    else:
        startTime = ts.start
    if not endTime:
        endTime = ts.end

    # Make sure segments list starts at startTime and ends at endTime
    segments = ts.segments(startTime, endTime)
    if not segments:
        print 'No data found between %d and %d.' % (startTime, endTime), \
              ' Exiting...'
        return endTime
    startTime = max(segments[0][0], startTime)
    print 'start time:', startTime
    segments[0] = (startTime, segments[0][1])

    endTime = min(segments[-1][1], endTime)
    print 'end time:', endTime
    segments[-1] = (segments[-1][0], endTime)

    # Go through each long-term window
    while windowStart < endTime and windowEnd <= ts.end:
        # Calculate trend and threshold
        try:
            trend, shortClips = _trend(ts, windowStart, windowEnd)
        except RequestException:
            # Workaround in case of server errors
            sleep(2)
            continue
        if trend is None:
            print 'skipping long window (no clips)...'
            sys.stdout.flush()
            windowStart = windowEnd
            windowEnd += longWindow
            continue

        # If using a custom start time, trim shortClips
        # (This should only ever happen with the 1st long-term window)
        if windowStart < startTime:
            try:
                i = next(i for i,c in enumerate(shortClips) if
                    c['end'] > startTime)
                shortClips[:i] = []
            except StopIteration:
                pass
            shortClips[0]['start'] = max(shortClips[0]['start'], startTime)
            # Delete 1st clip if it's too short (less than half of shortWindow):
            if shortClips[0]['end'] - shortClips[0]['start'] < shortWindow / 2:
                shortClips.pop(0)

        # Do the same thing with endTime
        # (Should only ever happen to the last long-term window)
        if windowEnd > endTime:
            l = len(shortClips)
            try:
                i = next(l-1 - i for i,c in enumerate(reversed(shortClips)) if
                    c['start'] < endTime)
                shortClips[i+1:] = []
            except StopIteration:
                pass
            # Delete last clip if it's not long enough
            lastClip = shortClips.pop(-1)
            if lastClip['end'] - lastClip['start'] >= shortWindow / 2:
                lastClip['end'] = min(lastClip['end'], endTime)
                shortClips.append(lastClip)
            else:
                pass

        # Annotate and/or print predictions
        threshold = LL_MA_THRESHOLDS[ptName] * trend
        for clip in shortClips:
            l = clip['length']
            if l > threshold:
                print '+ %f (%d, %d)' % (l, clip['start'], clip['end'])
                layer.insert_annotation('Possible seizure',
                                        start=clip['start'], end=clip['end'])
            else:
                print '- %f (%d, %d)' % (l, clip['start'], clip['end'])
            sys.stdout.flush()

        # Go to next long term window
        windowStart = windowEnd
        windowEnd += longWindow
    return endTime

def _trend(ts, windowStart, windowEnd):
    'Returns: trend value, list of clips with their line lengths'
    print 'LONG-TERM WINDOW:', windowStart, windowEnd
    shortClips = [] # short term windows

    # Get time segments within the long-term window
    windowSegs = ts.segments(windowStart, windowEnd)
    if not windowSegs:
        print 'No data within the window.'
        return None, []
    _trimStart(windowStart, windowSegs)
    _trimEnd(windowEnd, windowSegs)

    # Measure line length of each short window
    pos = windowSegs[0][0]
    for seg in windowSegs:
        pos = max(pos, seg[0])
        while pos < seg[1]:
            try:
                clip = ts.get_data(start=pos, length=shortWindow, channels=ch, use_cache=False)
                # caching disabled to prevent database disk image errors
                # note: actual clip length may be shorter than the short window length
            except RequestException as e:
                # catch Blackfynn server errors
                print 'Server error (will retry):', e
                sleep(2)
                continue
            except Exception as e:
                print 'Pull failed:', e
                pos += shortWindow
                continue
            if clip.empty or clip.isnull().all().any():
                # skip clip if a channel is empty 
                pos += shortWindow
                continue
            if clip.shape[0] / freq * 1000000 < shortWindow / 2:
                # skip clip if it's less than half of max clip length
                pos += shortWindow
                continue

            clipStart = clip.iloc[0].name.value / 1000 # convert to Unix epoch time, in usecs
            clipEnd = clip.iloc[-1].name.value / 1000
            clip.fillna(0, inplace=True) # replace NaNs with zeros

            clip = clip.transpose().values
            l = _length(clip)
            shortClips.append({
                'start': clipStart,
                'end': clipEnd,
                'length': l
            })
            pos += shortWindow

    # Calculate trend and threshold; annotate
    if not shortClips:
        print 'No clips could be created within the window.'
        return None, []
    trend = np.mean([clip['length'] for clip in shortClips])
    print 'TREND:', trend
    return trend, shortClips

def _length(clip):
    'Measures the line length of a clip'
    lengths = np.zeros(clip.shape[0]).astype('float64')
    for i in range(1, clip.shape[1]):
        lengths += np.abs(clip[:, i] - clip[:, i-1])

    # remove zero-length channels
    lengths = lengths[np.nonzero(lengths)] 
    if lengths.size == 0: return 0.0

    # take the median and normalize by clip length
    length = np.median(lengths) / clip.shape[1] 
    return length

def _trimStart(startTime, segments):
    'trim segments list so it starts at or after startTime'
    if startTime is None:
        startTime = segments[0][0]
    else:
        try:
            i = next(i for i, (a,b) in enumerate(segments) if b > startTime)
            segments[:i] = []
        except StopIteration:
            pass
        startTime = max(segments[0][0], startTime)
        segments[0] = (startTime, segments[0][1])
    return startTime

def _trimEnd(endTime, segments):
    'trim segments list so it ends at or before endTime'
    if endTime is None:
        endTime = segments[-1][1]
    else:
        l = len(segments)
        try:
            i = next(l-1 - i for i, (a,b) in enumerate(reversed(segments)) if a < endTime)
            segments[i+1:] = []
        except StopIteration:
            pass
        endTime = min(segments[-1][1], endTime)
        segments[-1] = (segments[-1][0], endTime)
    return endTime

if __name__ == '__main__':
    ptName = sys.argv[1]

    try:
        startTime = int(sys.argv[2])
    except (IndexError, ValueError):
        startTime = None

    try:
        endTime = int(sys.argv[3])
    except (IndexError, ValueError):
        endTime = None

    append = ('append' in sys.argv[2:])

    lineLength(ptName, startTime, endTime=None, append=append)
