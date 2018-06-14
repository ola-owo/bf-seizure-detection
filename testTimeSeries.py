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

TS_CLIP_LENGTH = 15000000 # length (usec) of each clip when testing on the entire timeseries

def testTimeSeries(ts, layer, clipLength, ptName, annotDir, clipDir):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    annotDir: Annotation folder
    clipDir: Location of the current subject's seizure/nonseizure clips
    '''
    
    pos = ts.start
    if ptName=='UCD2': pos = 1527560255414440 # DEBUG: skipping to 1st seizure to avoid deadspace
    while pos + clipLength <= ts.end:

        # Delete temporary clip data
        clearDir(annotDir)
        clearDir(clipDir)
        clearDir('seizure-data')
        clearDir('submissions')
        print 'Testing position (%d, %d)' % (pos, pos + clipLength)

        with NoPrint(): # suppress console output
            # Download and preprocess the current clip
            makeAnnotFile([(pos, pos + clipLength)],
                          '%s/%s_timeseries.txt' % (annotDir, ptName))
            pullClips('%s/%s_timeseries.txt' % (annotDir, ptName),
                      'timeseries', ts, clipDir)
            segs = sliceClips(clipDir, 'test', 250, ptName, skipNans=True)

            if segs: # don't run classifier if no segments were created
                train('make_predictions')

        if segs:
            # load the most recent submission file
            predFile = 'submissions/' + sorted(os.listdir('submissions'))[-1]
            preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)
        else:
            # Predict negative if no segments were created
            preds = [0]

        # If a majority of predictions are positive,
        # mark clip as a seizure and upload annonation to blackfynn
        #
        #if sum(np.round(preds)) > len(preds) / 2:
        #    layer.insert_annotation('Seizure', start = pos, end = pos + clipLength)

        ### DEBUG: Output results to file
        if sum(np.round(preds)) > len(preds) / 2:
            msg = 'Seizure at time (%d, %d)\n' % (pos, pos + clipLength)
        else:
            msg = 'No seizure at time (%d, %d)\n' % (pos, pos + clipLength)
        with open(ptName + '_seizures.txt', 'a') as f:
            f.write(msg)

        pos += clipLength

if __name__ == '__main__':
    bf = Blackfynn()

    tsID = sys.argv[1]
    layerID = int(sys.argv[2])
    ptName = sys.argv[3]
    annotDir = sys.argv[4]
    clipDir = sys.argv[5]

    ts = bf.get(tsID)
    layer = ts.get_layer(layerID)
    testTimeSeries(ts, layer, clipLength, ptName, annotDir, clipDir)

def testTimeSeries(ts, layer, TS_CLIP_LENGTH, ptName, annotDir, clipDir):
