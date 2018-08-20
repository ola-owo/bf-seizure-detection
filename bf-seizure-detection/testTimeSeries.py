#!/usr/bin/env python2
'''
Standalone usage:
python testTimeSeries.py ptName startTime [endTime] [annotate]
'''
import os
import sys

from blackfynn import Blackfynn
import numpy as np

from annots import makeAnnotFile
from pullClips import pullClips
from settings import (
    CHANNELS, DEFAULT_FREQ, FREQs, PL_CLIP_LENGTH, PL_LAYER_NAME, PL_ROOT,
    TS_IDs)
from sliceClips import sliceClips
from train import train
from tools import clearDir, NoPrint

def testTimeSeries(ts, layer, ptName, startTime=None, endTime=None, annotating=True):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    annotating: Whether to upload annotations to Blackfynn
    '''

    annotDir = PL_ROOT + '/annotations'
    clipDir = PL_ROOT + '/clips/' + ptName
    logfile = ptName + '_seizures.txt'
    ch = CHANNELS.get(ptName, None)
    freq = FREQs.get(ptName, DEFAULT_FREQ)

    # Make sure startTime and endTime are valid
    tsStart = ts.start
    tsEnd = ts.end
    if startTime is None:
        startTime = tsStart
    else:
        if startTime < tsStart:
            print 'Warning: startTime', startTime, 'is before the beginning of the Timeseries. Starting from the beginning...'
            startTime = tsStart
        elif startTime > tsEnd:
            print 'Warning: startTime', startTime, 'is after the end of the Timeseries. No data will be analyzed.'
            return

    if endTime is None:
        endTime = tsEnd
    else:
        if endTime > tsEnd:
            print 'Warning: endTime', endTime, 'is after the end of the Timeseries. Stopping at the end...'
            endTime = tsEnd
        elif endTime < tsStart:
            print 'Warning: endTime', endTime, 'is before the beginning the Timeseries. No data will be analyzed.'
            return

    segments = ts.segments(startTime, endTime)
    if startTime:
        startTime = max(startTime, segments[0][0])
        segments[0] = (startTime, segments[0][1])
    else:
        startTime = segments[0][0]

    if endTime:
        endTime = min(endTime, segments[-1][1])
        segments[-1] = (segments[-1][0], endTime)
    else:
        endTime = segments[-1][1]

    pos = startTime
    szStarted = False
    for seg in segments:
        pos = max(pos, seg[0])
        while pos < seg[1]:
            print 'Testing position (%d, %d)' % (pos, pos + PL_CLIP_LENGTH)

            with NoPrint(): # suppress console output
                annotFile = '%s/%s_timeseries.txt' % (annotDir, ptName)
                makeAnnotFile([(pos, pos + PL_CLIP_LENGTH)], annotFile)
                times = pullClips(annotFile, 'timeseries', ts, clipDir, ch)
                segs = sliceClips(clipDir, 'test', freq, ptName)

                if segs: 
                    clipStart = times[0][0]
                    clipEnd = times[-1][1]
                    train('make_predictions', target=ptName)
                    submissions = [f for f in os.listdir(PL_ROOT + '/submissions') if ptName in f]
                    submissions.sort()
                    predFile = PL_ROOT + '/submissions/' + submissions[-1]
                    preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1).astype(float)
                    if preds.shape == (): 
                        # if preds has only one element, convert it from 0-D to 1-D
                        preds = preds.reshape((1,))
                    meanScore = np.mean(preds)
                else:
                    # Predict negative if no segments were created
                    meanScore = 0.0
                    clipStart = pos
                    clipEnd = pos + PL_CLIP_LENGTH

            ###
            # If the mean prediction score is greater than 0.5, then
            # write positive prediction to file, and (if annotating)
            # mark on Blackfynn as a seizure.
            if meanScore > 0.5:
                msg = '+ (%d, %d) %f\n' % (clipStart, clipEnd, meanScore)
                if not szStarted:
                    szStarted = True
                    szStart = clipStart
                szEnd = clipEnd

            else:
                msg = '- (%d, %d) %f\n' % (clipStart, clipEnd, meanScore)
                if szStarted:
                    szStarted = False
                    if annotating:
                        layer.insert_annotation('Seizure',
                                                start = szStart, end = szEnd)

            with open(logfile, 'a') as f: f.write(msg)
            pos += PL_CLIP_LENGTH

            ### Delete temporary clip data
            # Annotation:
            os.remove(annotFile)
            # Submission file:
            try:
                os.remove(predFile)
            except:
                pass
            # Timeseries clip:
            clearDir(clipDir)
            # Test segments:
            clearDir(PL_ROOT + '/seizure-data/' + ptName)
            # Cached classifier data
            for fname in os.listdir(PL_ROOT + '/data-cache'):
                if (
                    fname.startswith('data_test_' + ptName) or
                    fname.startswith('predictions_' + ptName)
                ):
                    os.remove(PL_ROOT + '/data-cache/' + fname)

if __name__ == '__main__':
    ptName = sys.argv[1]
    startTime = int(sys.argv[2])
    kwargs = sys.argv[3:]
    annotating = ('annotate' in kwargs)

    try:
        endTime = int(sys.argv[3])
    except (ValueError, IndexError):
        endTime = None

    bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])
    layer = ts.add_layer(PL_LAYER_NAME)

    print 'Testing on patient:', ptName
    if annotating:
        print 'Annotating enabled'
    else:
        print 'Annotating disabled'
    testTimeSeries(ts, layer, ptName, startTime, endTime, annotating)
