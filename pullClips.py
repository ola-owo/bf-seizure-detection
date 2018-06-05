#!/usr/bin/env python2
"""
Use this to pull seizure data from Blackfynn for the pipeline.
Can be called standalone as:
> python pullClips.py annotFile clipType tsID outDir

NOTE: When training the classifier, the patient name should be listed
in "targets" inside liveAlgo/seizure_detection.py
"""

import sys
from blackfynn import Blackfynn
import hickle
import scipy.io as sio

def pullClips(annotFile, clipType, ts, outDir):
    '''
    Using annotFile, download clips of type clipType from TimeSeries ts into folder outDir.
    '''

    # Validate clip type
    if clipType == 'ictal':
        outfile_prefix = 'sz'
    elif clipType == 'interictal':
        outfile_prefix = 'nonsz'
    else:
        raise ValueError("Invalid clip type '%s' (should be ictal or interictal)" % clipType)

    # get the annotation times from file
    with open(annotFile, 'r') as f:
        """
        each line of the annotation file is formatted as: startTime endTime
        with times given in microseconds
        """
        annots = f.read().splitlines()

    # save each clip to file
    num_saved = 0
    for i in range(len(annots)):
        # get clip start/end times
        annot = map(int, annots[i].split())
        if not annot:
            # ignore empty lines in file
            continue
        annotStart = annot[0]
        annotEnd = annot[1]

        # pull data for current clip 
        try:
            df = ts.get_data(start=annotStart, end=annotEnd)
        except:
            print 'Pull failed at', annotStart
            continue

        array = df.transpose().values
        outfile = '%s/%s%d.hkl' % (outDir, outfile_prefix, i+1)
        hickle.dump(array, outfile)
        num_saved = num_saved + 1

    print('%d clips saved.' % num_saved)

if __name__ == '__main__':
    annotFile = sys.argv[1]
    clipType = sys.argv[2] # either ictal or interictal
    tsID = sys.argv[3]
    outDir = sys.argv[4].rstrip('/')

    bf = Blackfynn()
    ts = bf.get(tsID)
    pullClips(annotFile, clipType, ts, outDir)
