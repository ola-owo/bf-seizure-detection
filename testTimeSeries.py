import os

import numpy as np

from annots import makeAnnotFile
from pullClips import pullClips
from sliceClips import sliceClips
from train import train
from tools import clearDir, NoPrint

def testTimeSeries(ts, layer, clipLength, ptName, annotDir, clipDir):
    pos = ts.start
    while pos + clipLength <= ts.end:
        print 'Testing position (%d, %d)' % (pos, pos + clipLength)

        with NoPrint():
            # Download and preprocess clip
            makeAnnotFile([(pos, pos + clipLength)],
                          '%s/%s_timeseries.txt' % (annotDir, ptName))
            pullClips('%s/%s_timeseries.txt' % (annotDir, ptName),
                      'timeseries', ts, clipDir)
            sliceClips(clipDir, 'test', 250, ptName, skipNans=False)

            # Make predictions
            train('make_predictions')

        # load the most recent submission file
        predFile = 'submissions/' + sorted(os.listdir('submissions'))[-1]
        preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)

        # If a majority of predictions are positive,
        # annotate clip as a seizure and upload to blackfynn
        if sum(np.round(preds)) > len(preds) / 2:
            layer.insert_annotation('Seizure', start = pos, end = pos + clipLength)

        ### DEBUG: Output results to file
        # if sum(np.round(preds)) > len(preds) / 2:
        #     with open(ptName + '_seizures.txt', 'a') as f:
        #         msg = 'Seizure detected at time (%d, %d)\n' % (pos, pos + clipLength)
        #         f.write(msg)
        # else:
        #     with open(ptName + '_seizures.txt', 'a') as f:
        #         msg = 'No seizure at time (%d, %d)\n' % (pos, pos + clipLength)
        #         f.write(msg)

        pos += clipLength

        # Delete clip data
        clearDir(annotDir)
        clearDir(clipDir)
        clearDir('seizure-data')
        clearDir('submissions')
