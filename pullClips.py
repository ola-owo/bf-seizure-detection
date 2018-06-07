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
            if ts.name == 'Ripley': # workaround for Ripley having an empty 5th channel
                ch = [
                    'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
                    'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
                    'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
                    'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
                ]
                df = ts.get_data(start=annotStart, end=annotEnd, channels = ch)
            else:
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
