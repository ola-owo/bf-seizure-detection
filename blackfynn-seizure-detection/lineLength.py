#!/usr/bin/env python2
'''
Line length seizure detector

Usage: python lineLength.py ptName [startTime [endTime]] [append]
'''
import sys
import numpy as np

from blackfynn import Blackfynn

from settings import (
    CHANNELS, LL_CLIP_LENGTH, LL_LAYER_NAME, THRESHOLDS, TS_IDs,
)

def lineLength(ts, ch, startTime=None, endTime=None, append=False, layerName=LL_LAYER_NAME):
    '''
    Runs the line length detector.

    ts: TimeSeries object to annotate
    ch: channels to annotate
    startTime: time (usec) to start from. Default value (None) starts from the beginning of the timeseries
    append: Whether to append or overwrite the line length annotation layer
    layerName: name of layer to write to
    '''

    ptName = ts.name
    threshold = THRESHOLDS[ptName]
    segments = ts.segments()

    # Make sure startTime and endTime are valid
    if startTime is not None:
        if startTime < ts.start:
            print 'Warning: startTime', startTime, 'is earlier than the beginning of the Timeseries. Ignoring startTime argument...'
            startTime = None
        elif startTime > ts.end:
            print 'Warning: startTime', startTime, 'is after the end of the Timeseries. No data will be analyzed.'
            return

    if endTime is not None:
        if endTime > ts.end:
            print 'Warning: endTime', endTime, 'is later than the end of the Timeseries. Ignoring endTime argument...'
            endTime = None
        elif endTime < ts.start:
            print 'Warning: endTime', endTime, 'is before the beginning the Timeseries. No data will be analyzed.'
            return

    # edit segments so that it starts at startTime
    if startTime is None:
        startTime = segments[0][0]
    else:
        try:
            i = next(i for i, (a,b) in enumerate(segments) if b > startTime)
            segments[:i] = []
        except StopIteration:
            pass
        startTime = max(segments[0][0], startTime)
        print 'start time:', startTime
        segments[0] = (startTime, segments[0][1])

    # Same thing with end time:
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
        print 'end time:', endTime
        segments[-1] = (segments[-1][0], endTime)

    try:
        # Get layer if it already exists
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

    pos = segments[0][0]
    for seg in segments:
        pos = max(pos, seg[0])
        while pos < seg[1]:
            try:
                clip = ts.get_data(start=pos, length=LL_CLIP_LENGTH, channels=ch, use_cache=False)
                # caching disabled to prevent database disk image errors
                # note: actual clip length may be shorter than LL_CLIP_LENGTH
            except Exception as e:
                print 'Pull failed:', e
                pos += LL_CLIP_LENGTH
                continue
            if clip.empty:
                pos += LL_CLIP_LENGTH
                continue

            startTime = clip.iloc[0].name.value / 1000 # convert to Unix epoch time, in usecs
            endTime = clip.iloc[-1].name.value / 1000
            clip.fillna(0, inplace=True) # replace NaNs with zeros

            clip = clip.transpose().values
            l = _length(clip)

            if l > threshold:
                print '+ %f (%d, %d)' % (l, startTime, endTime)
                sys.stdout.flush()
                layer.insert_annotation('Possible seizure', start=startTime, end=endTime)
            else:
                print '- %f (%d, %d)' % (l, startTime, endTime)
                sys.stdout.flush()

            pos += LL_CLIP_LENGTH

def _length(clip):
    'Measures the line length of clip'
    lengths = np.zeros(clip.shape[0]).astype('float64')
    for i in range(1, clip.shape[1]):
        lengths += np.abs(clip[:, i] - clip[:, i-1])

    # remove zero-length channels
    lengths = lengths[np.nonzero(lengths)] 
    if lengths.size == 0: return 0.0

    # take the median and normalize by clip length
    length = np.median(lengths) / clip.shape[1] 
    return length

if __name__ == '__main__':
    ptName = sys.argv[1]
    bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])
    ch = CHANNELS.get(ptName, None)

    try:
        startTime = int(sys.argv[2])
    except (IndexError, ValueError):
        startTime = None

    try:
        endTime = int(sys.argv[3])
    except (IndexError, ValueError):
        endTime = None

    append = ('append' in sys.argv[2:])

    lineLength(ts, ch, startTime, endTime=None, append=append)
