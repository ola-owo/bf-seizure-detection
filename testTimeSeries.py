#!/usr/bin/env python2
'''
Standalone usage:
python testTimeSeries.py tsID layerID ptName [[log] [annotate]]
'''
import os
import sys

from blackfynn import Blackfynn
import numpy as np

from annots import makeAnnotFile
from pullClips import pullClips
from settings import FREQ, PL_CLIP_LENGTH, PL_ROOT
from sliceClips import sliceClips
from train import train
from tools import clearDir, NoPrint

annotDir = PL_ROOT + '/annotations'
clipDir = PL_ROOT + '/clips'

def testTimeSeries(ts, layer, ptName, startTime=None, endTime=None, logging=True, annotating=True):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    logging: Whether to log results to file
    annotating: Whether to upload annotations to Blackfynn
    '''

    if logging: logfile = ptName + '_seizures.txt'
    timeSegments = ts.segments()

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
                pullClips(annotFile, 'timeseries', ts, clipDir)
                segs = sliceClips(clipDir, 'test', FREQ, ptName)

                if segs: 
                    train('make_predictions', target=ptName)
                    submissions = [f for f in os.listdir(PL_ROOT + 'submissions') if ptName in f]
                    submissions.sort()
                    predFile = PL_ROOT + 'submissions' + submissions[-1]
                    preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1).astype(float)
                    if preds.shape == (): 
                        # if preds has only one element, convert it from 0-D to 1-D
                        preds = preds.reshape((1,))
                    meanScore = np.mean(preds)
                else:
                    # Predict negative if no segments were created
                    meanScore = 0.0

            ###
            # If the mean prediction score is greater than 0.5, then:
            # (if annotating) mark clip as a seizure and upload annonation to blackfynn, and
            # (if logging) write positive prediction to file
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

            if logging:
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
                    os.remove(PL_ROOT + '/data-cache' + fname)

if __name__ == '__main__':
    bf = Blackfynn()

    tsID = sys.argv[1]
    layerID = sys.argv[2]
    ptName = sys.argv[3]

    try:
        kwargs = sys.argv[6:]
        logging = ('log' in kwargs)
        annotating = ('annotate' in kwargs)
    except IndexError:
        logging = True
        annotating = False

    ts = bf.get(tsID)
    try:
        layer = ts.get_layer(int(layerID))
    except ValueError:
        layer = None

    testTimeSeries(ts, layer, ptName, logging, annotating)
