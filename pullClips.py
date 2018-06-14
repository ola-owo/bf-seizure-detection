#!/usr/bin/env python2
"""
Use this to pull seizure data from Blackfynn for the pipeline.
Can be called standalone as:
> python pullClips.py annotFile clipType tsID outDir
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
    elif clipType == 'timeseries':
        outfile_prefix = 'ts'
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
    for annotStr in annots:
        # get clip start/end times
        annot = map(int, annotStr.split())
        if not annot:
            # ignore empty lines in file
            continue
        annotStart = annot[0]
        annotEnd = annot[1]

        # pull data for current clip 
        try:
            if ts.name == 'Ripley': # workaround for Ripley having 5 channels
                ch = [
                    'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
                    'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
                    'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
                    'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
                ]
                df = ts.get_data(start=annotStart, end=annotEnd, channels=ch)
            else:
                df = ts.get_data(start=annotStart, end=annotEnd)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print 'Pull failed at', annotStart
            print e
            continue

        array = df.transpose().values
        outfile = '%s/%s%d.hkl' % (outDir, outfile_prefix, num_saved+1)
        hickle.dump(array, outfile)
        num_saved += 1

    print('%d clips saved.' % num_saved)

if __name__ == '__main__':
    annotFile = sys.argv[1]
    clipType = sys.argv[2]
    tsID = sys.argv[3]
    outDir = sys.argv[4].rstrip('/')

    bf = Blackfynn()
    ts = bf.get(tsID)
    pullClips(annotFile, clipType, ts, outDir)
