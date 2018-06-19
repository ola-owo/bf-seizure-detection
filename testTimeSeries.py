'''
Standalone usage:
python testTimeSeries.py tsID layerID ptName annotDir clipDir
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

CLIP_LENGTH = 15000000 # length (usec) of each clip to test

def testTimeSeries(ts, layer, ptName, annotDir, clipDir, logging=True, annotating=False):
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

    if logging:
        # Make sure log file exists and is empty
        logfile = ptName + '_seizures.txt'
        open(logfile, 'w').close()
    
    timePeriods = ts.segments()
    for timePd in timePeriods:
        szStarted = False
        szStart = 0
        szEnd = 0

        pos = timePd[0]
        while pos + CLIP_LENGTH <= timePd[1]:
            print 'Testing position (%d, %d)' % (pos, pos + CLIP_LENGTH)

            with NoPrint(): # suppress console output
                makeAnnotFile([(pos, pos + CLIP_LENGTH)],
                              '%s/%s_timeseries.txt' % (annotDir, ptName))
                pullClips('%s/%s_timeseries.txt' % (annotDir, ptName),
                          'timeseries', ts, clipDir)
                segs = sliceClips(clipDir, 'test', 250, ptName, skipNans=True)

                if segs: 
                    train('make_predictions', target=ptName)
                    submissions = filter(lambda f: ptName in f, os.listdir('submissions'))
                    submissions.sort()
                    predFile = os.path.join('submissions', submissions[-1])
                    preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)
                    if preds.shape == (): 
                        # if preds has only one element, convert it from 0-D to 1-D
                        preds = preds.reshape((1,))
                else:
                    # Predict negative if no segments were created
                    preds = [0.0]

            ###
            # If a majority of predictions are positive, then:
            # (if annotating) mark clip as a seizure and upload annonation to blackfynn, and
            # (if logging) write positive prediction to file
            if sum(np.round(preds)) > len(preds) / 2:
                msg = '+ (%d, %d) %f\n' % (pos, pos + CLIP_LENGTH, np.mean(preds))
                if not szStarted:
                    szStarted = True
                    szStart = pos

            else:
                msg = '- (%d, %d) %f\n' % (pos, pos + CLIP_LENGTH, np.mean(preds))
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
        logging = ('logging' in kwargs)
        annotating = ('annotating' in kwargs)
    except IndexError:
        logging = True
        annotating = False

    ts = bf.get(tsID)
    try:
        layer = ts.get_layer(int(layerID))
    except ValueError:
        layer = None

    testTimeSeries(ts, layer, ptName, annotDir, clipDir, logging, annotating)
