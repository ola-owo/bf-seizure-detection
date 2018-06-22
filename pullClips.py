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

def pullClips(annotFile, clipType, ts, outDir, channels=None):
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
        annots = [map(int, annot.split()) for annot in annots]

    # pull and save each annotated clip
    num_saved = 0
    for annot in annots:
        if not annot:
            # ignore empty lines in file
            continue
        annotStart = annot[0]
        annotEnd = annot[1]

        # pull data for current clip 
        try:
            df = ts.get_data(start=annotStart, end=annotEnd, channels=channels, use_cache=False)
            # cache disabled to prevent malformed cache db errors
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print 'Pull failed at', annotStart
            print e
            continue

        # Handle gaps in data, if present
        # (Taken from Steve Baldassano's pipeline)
        if df.empty: continue
        dfs = []
        i = 0
        for j in range(1, df.shape[0]):
            if i+1 == df.shape[0]: break
            dT = (df.iloc[j].name - df.iloc[j-1].name).total_seconds()
            if dT > 0.01: # if gap is too big, split into 2 clips
                dfs.append(df.iloc[i:j])
                i = j
        dfs.append(df.iloc[i:])
        num_splits = len(dfs) - 1

        # save clip(s)
        for df in dfs:
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
