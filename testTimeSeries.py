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

CLIP_LENGTH = 15000000 # length (usec) of each clip when testing on the entire timeseries

def testTimeSeries(ts, layer, ptName, annotDir, clipDir):
    '''
    Test liveAlgo classifier on an entire timeseries.
    Detected seizures are written to the given annotation layer.

    ts: TimeSeries object to be tested
    layer: Annotation layer object to write to
    ptName: Subject name
    annotDir: Annotation folder
    clipDir: Location of the current subject's seizure/nonseizure clips
    '''

    # Make sure log file exists and is empty
    logfile = ptName + '_seizures.txt'
    open(logfile, 'w').close()
    
    pos = ts.start
    if ptName=='UCD2': pos = 1527560255414440 # DEBUG: skipping to 1st seizure to avoid deadspace
    while pos + CLIP_LENGTH <= ts.end:


        print 'Testing position (%d, %d)' % (pos, pos + CLIP_LENGTH)

        with NoPrint(): # suppress console output
            # Download and preprocess the current clip
            makeAnnotFile([(pos, pos + CLIP_LENGTH)],
                          '%s/%s_timeseries.txt' % (annotDir, ptName))
            pullClips('%s/%s_timeseries.txt' % (annotDir, ptName),
                      'timeseries', ts, clipDir)
            segs = sliceClips(clipDir, 'test', 250, ptName, skipNans=True)

            if segs: # don't run classifier if no segments were created
                train('make_predictions', target=ptName)

        if segs:
            # load the submission file
            submissions = filter(lambda f: ptName in f, os.listdir('submissions'))
            submissions.sort()
            predFile = os.path.join('submissions', submissions[-1])
            preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)
        else:
            # Predict negative if no segments were created
            preds = [0]

        # If a majority of predictions are positive,
        # mark clip as a seizure and upload annonation to blackfynn
        #
        #if sum(np.round(preds)) > len(preds) / 2:
        #    layer.insert_annotation('Seizure', start = pos, end = pos + CLIP_LENGTH)

        ### DEBUG: Output results to file
        if sum(np.round(preds)) > len(preds) / 2:
            msg = '[+] (%d, %d)\n' % (pos, pos + CLIP_LENGTH)
        else:
            msg = '[-] (%d, %d)\n' % (pos, pos + CLIP_LENGTH)
        with open(logfile, 'a') as f:
            f.write(msg)

        pos += CLIP_LENGTH

        # Delete temporary clip data
        os.remove('%s/%s_timeseries.txt' % (annotDir, ptName))
        try:
            os.remove(predFile)
        except:
            pass
        clearDir(clipDir)
        clearDir(os.path.join('seizure-data', ptName))

if __name__ == '__main__':
    bf = Blackfynn()

    tsID = sys.argv[1]
    layerID = sys.argv[2]
    ptName = sys.argv[3]
    annotDir = sys.argv[4].rstrip('/')
    clipDir = sys.argv[5].rstrip('/')

    ts = bf.get(tsID)
    try:
        layer = ts.get_layer(int(layerID))
    except ValueError:
        layer = None
    testTimeSeries(ts, layer, ptName, annotDir, clipDir)
