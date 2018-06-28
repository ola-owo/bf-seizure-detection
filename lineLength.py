#!/usr/bin/env python2
'''
Line length seizure detector

Usage: python lineLength.py ptName [startTime [append]]
'''
import sys
import numpy as np
from blackfynn import Blackfynn

CLIP_LENGTH = 60000000 # 1 minute in usec
PREDICTION_LAYER_NAME = 'UPenn_Line_Length_Detector'

THRESHOLDS = {
    'UCD1': 5000,
    'UCD2': 10000,
    'R_950': 15, # rough estimation
    'R_951': 15, # rough estimation
    'Ripley': 16, # changed from 10 after analyzing ROC
}

timeseries_ids = { 
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

channels_lists = {
    'Ripley': [ # Workaround since Ripley has 5 channels
        'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
        'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
        'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
        'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
    ]
}

def lineLength(ts, ch, startTime=None, endTime=None, append=False, layerName=PREDICTION_LAYER_NAME):
    '''
    Runs the line length detector.

    ts: TimeSeries object to annotate
    ch: channels to annotate
    startTime: time (usec) to start from. Default value (None) starts from the beginning of the timeseries
    append: Whether to append or overwrite the line length annotation layer
    layerName: name of layer to write to
    '''

    segments = ts.segments()
    pos = segments[0][0]

    # edit segments so that it starts at startTime
    if startTime is None:
        startTime = segments[0][0]
    else:
        i = next(i for i, (a,b) in enumerate(segments) if b > startTime)
        segments[:i] = []
        startTime = max(segments[0][0], startTime)
        print 'start time:', startTime
        segments[0] = (startTime, segments[0][1])

    # Same thing with end time:
    if endTime is None:
        endTime = segments[-1][1]
    else:
        l = len(segments)
        i = next(l-1 - i for i, (a,b) in enumerate(reversed(segments)) if a < endTime)
        segments[i+1:] = []
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

    for seg in segments:
        pos = max(pos, seg[0])
        while pos < seg[1]:
            try:
                clip = ts.get_data(start=pos, length=CLIP_LENGTH, channels=ch, use_cache=False)
                # caching disabled to prevent database disk image errors
                # note: actual clip length may be shorter than CLIP_LENGTH
            except Exception as e:
                print 'Pull failed:', e
                pos += CLIP_LENGTH
                continue
            if clip.empty:
                pos += CLIP_LENGTH
                continue

            startTime = clip.iloc[0].name.value / 1000 # convert to Unix epoch time, in usecs
            endTime = clip.iloc[-1].name.value / 1000
            clip.fillna(0, inplace=True) # replace NaNs with zeros

            clip = clip.transpose().values
            l = _length(clip)

            if l > threshold:
                print '+', l, (startTime, endTime)
                layer.insert_annotation('Possible seizure', start=startTime, end=endTime)
            else:
                print '-', l, (startTime, endTime)
            pos += CLIP_LENGTH

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
    threshold = THRESHOLDS[ptName]
    bf = Blackfynn()
    ts = bf.get(timeseries_ids[ptName])
    ch = channels_lists.get(ptName, None)

    try:
        startTime = sys.argv[2]
    except IndexError:
        startTime = None

    try:
        append = (sys.argv[3] == 'append')
    except IndexError:
        append = False

    lineLength(ts, ch, startTime, append)
