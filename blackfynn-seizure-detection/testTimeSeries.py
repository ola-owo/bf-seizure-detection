#!/usr/bin/env python2
'''
Standalone usage:
python testTimeSeries.py ptName layerID startTime [endTime] [annotate]
'''
import os
import sys

from blackfynn import Blackfynn
import numpy as np

from annots import makeAnnotFile
from pullClips import pullClips
from settings import CHANNELS, DEFAULT_FREQ, FREQs, PL_CLIP_LENGTH, PL_ROOT, TS_IDs
from sliceClips import sliceClips
from train import train
from tools import clearDir, NoPrint

annotDir = PL_ROOT + '/annotations'
clipDir = PL_ROOT + '/clips'

def testTimeSeries(ts, layer, ptName, startTime=None, endTime=None, annotating=True):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    annotating: Whether to upload annotations to Blackfynn
    '''

    logfile = ptName + '_seizures.txt'
    ch = CHANNELS.get(ptName, None)
    freq = FREQs.get(ptName, DEFAULT_FREQ)
    timeSegments = ts.segments()

    # Make sure startTime and endTime are valid
    if startTime is not None:
        if startTime < ts.start:
            print 'Warning: startTime', startTime, 'is before the beginning of the Timeseries. Starting from the beginning of the timeseries...'
            startTime = None
        elif startTime > ts.end:
            print 'Warning: startTime', startTime, 'is after the end of the Timeseries. No data will be analyzed.'
            return

    if endTime is not None:
        if endTime > ts.end:
            print 'Warning: endTime', endTime, 'is after the end of the Timeseries. Stopping at the end of the timeseries...'
            endTime = None
        elif endTime < ts.start:
            print 'Warning: endTime', endTime, 'is before the beginning the Timeseries. No data will be analyzed.'
            return

    if startTime:
        # Get the idx of the time segment to start at, and exclude all time before it
        i = next(i for i, (a,b) in enumerate(timeSegments) if b > startTime)
        timeSegments[:i] = []
        startTime = max(startTime, timeSegments[0][0])
        timeSegments[0] = (startTime, timeSegments[0][1])
    else:
        startTime = timeSegments[0][0]

    if endTime:
        # Same thing as with startTime
        l = len(timeSegments)
        i = next(l-1 - i for i, (a,b) in enumerate(reversed(timeSegments)) if a < endTime)
        timeSegments[i+1:] = []
        endTime = min(endTime, timeSegments[-1][1])
        timeSegments[-1] = (timeSegments[-1][0], endTime)
    else:
        endTime = timeSegments[-1][1]

    pos = startTime
    szStarted = False
    for timeSeg in timeSegments:
        pos = max(pos, timeSeg[0])
        while pos < timeSeg[1]:
            print 'Testing position (%d, %d)' % (pos, pos + PL_CLIP_LENGTH)

            with NoPrint(): # suppress console output
                annotFile = '%s/%s_timeseries.txt' % (annotDir, ptName)
                makeAnnotFile([(pos, pos + PL_CLIP_LENGTH)], annotFile)
                pullClips(annotFile, 'timeseries', ts, clipDir, ch)
                segs = sliceClips(clipDir, 'test', freq, ptName)

                if segs: 
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

            ###
            # If the mean prediction score is greater than 0.5, then
            # write positive prediction to file, and (if annotating) mark clip
            # as a seizure and upload annonation to blackfynn.
            if meanScore > 0.5:
                msg = '+ (%d, %d) %f\n' % (pos, pos + PL_CLIP_LENGTH, meanScore)
                if not szStarted:
                    szStarted = True
                    szStart = pos

            else:
                msg = '- (%d, %d) %f\n' % (pos, pos + PL_CLIP_LENGTH, meanScore)
                if szStarted:
                    szStarted = False
                    szEnd = pos
                    if annotating:
                        layer.insert_annotation('Seizure',
                                                start = szStart, end = szEnd)

            with open(logfile, 'a') as f: f.write(msg)
            pos += PL_CLIP_LENGTH

            ### Delete temporary clip data
            # Annotation:
            os.remove(annotDir + '/' + ptName + '_timeseries.txt')
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
    layerID = int(sys.argv[2])
    startTime = int(sys.argv[3])

    kwargs = sys.argv[4:]
    try:
        endTime = int(sys.argv[4])
    except ValueError:
        endTime = None
    annotating = ('annotate' in kwargs)

    bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])
    try:
        layer = ts.get_layer(layerID)
    except:
        print 'Layer', layerID, 'not found. Not annotating...'
        layer = None
        annotating = None

    testTimeSeries(ts, layer, ptName, startTime, endTime, annotating)
