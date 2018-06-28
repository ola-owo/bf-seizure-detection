#!/usr/bin/env python2
'''
Standalone usage:
python testTimeSeries.py tsID layerID ptName annotDir clipDir [[log] [annotate]]
'''
import os
import sys

from blackfynn import Blackfynn
import numpy as np

from annots import makeAnnotFile
from pullClips import pullClips
from sliceClips import sliceClips
from train import train
from tools import clearDir, NoPrint

CLIP_LENGTH = 30000000 # length (usec) of each clip to test

def testTimeSeries(ts, layer, ptName, annotDir, clipDir, startTime=None, endTime=None, logging=True, annotating=True):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    annotDir: Annotation folder
    clipDir: Location of the current subject's seizure/nonseizure clips
    logging: Whether to log results to file
    annotating: Whether to upload annotations to Blackfynn
    '''

    if logging: logfile = ptName + '_seizures.txt'
    timeSegments = ts.segments()

    # TODO: train liveALgo if classifier doesn't already exist

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
            print 'Testing position (%d, %d)' % (pos, pos + CLIP_LENGTH)

            with NoPrint(): # suppress console output
                annotFile = '%s/%s_timeseries.txt' % (annotDir, ptName)
                makeAnnotFile([(pos, pos + CLIP_LENGTH)], annotFile)
                pullClips(annotFile, 'timeseries', ts, clipDir)
                segs = sliceClips(clipDir, 'test', 250, ptName)

                if segs: 
                    train('make_predictions', target=ptName)
                    submissions = [f for f in os.listdir('submissions') if ptName in f]
                    submissions.sort()
                    predFile = os.path.join('submissions', submissions[-1])
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
                msg = '+ (%d, %d) %f\n' % (pos, pos + CLIP_LENGTH, meanScore)
                if not szStarted:
                    szStarted = True
                    szStart = pos

            else:
                msg = '- (%d, %d) %f\n' % (pos, pos + CLIP_LENGTH, meanScore)
                if szStarted:
                    szStarted = False
                    szEnd = pos
                    if annotating:
                        layer.insert_annotation('Seizure',
                                                start = szStart, end = szEnd)

            if logging:
                with open(logfile, 'a') as f: f.write(msg)

            pos += CLIP_LENGTH

            ### Delete temporary clip data
            # Annotation:
            os.remove(os.path.join(annotDir, ptName + '_timeseries.txt'))
            # Submission file:
            try:
                os.remove(predFile)
            except:
                pass
            # Timeseries clip:
            clearDir(clipDir)
            # Test segments:
            clearDir(os.path.join('seizure-data', ptName))
            # Cached classifier data
            for fname in os.listdir('data-cache'):
                if (fname.startswith('data_test_' + ptName) or
                    fname.startswith('predictions_' + ptName)):
                    os.remove(os.path.join('data-cache', fname))

if __name__ == '__main__':
    bf = Blackfynn()

    tsID = sys.argv[1]
    layerID = sys.argv[2]
    ptName = sys.argv[3]
    annotDir = sys.argv[4].rstrip('/')
    clipDir = sys.argv[5].rstrip('/')

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

    testTimeSeries(ts, layer, ptName, annotDir, clipDir, logging, annotating)
