import os

import numpy as np

from makeAnnots import makeAnnotFile
from pullClips import pullClips
from sliceClips import sliceClips
from train import train

def testTimeSeries(ts, layer, clipLength):
    pos = ts.start
    while pos + clipLength <= ts.end:
        makeAnnotFile([(pos, pos + clipLength)],
                      '%s/%s_timeseries.txt' % (ANNOT_ROOT, ptName))
        pullClips('%s/%s_timeseries.txt' % (ANNOT_ROOT, ptName),
                  'timeseries', ts, clipDir)
        sliceClips(clipDir, 'timeseries', 250, ptName, skipNans=False)

        # Make predictions
        os.chdir('liveAlgo')
        train('make_predictions')
        os.chdir('..')

        # load the most recent submission file
        predFile = 'submissions/' + sorted(os.listdir('submissions'))[-1]
        preds = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)

        # If a majority of predictions are positive,
        # annotate clip as a seizure and upload to blackfynn
        if sum(np.round(preds)) > len(preds) / 2:
        ### DEBUG: print annotations instead of uploading
        #     layer.insert_annotation('Seizure', start = pos, end = pos + clipLength)
            print 'Seizure detected at time (%d, %d)' % pos, pos + clipLength

        pos += clipLength
