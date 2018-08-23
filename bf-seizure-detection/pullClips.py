#!/usr/bin/env python2
"""
Use this to pull seizure data from Blackfynn for the pipeline.
Can be called standalone as:
> python pullClips.py annotFile clipType tsID outDir [limit]
"""

import sys
from time import sleep

from blackfynn import Blackfynn
import hickle
from requests.exceptions import RequestException
import scipy.io as sio

def pullClips(annotFile, clipType, ts, outDir, channels=None, limit=0):
    '''
    Using annotFile, download clips of type clipType from TimeSeries ts into folder outDir.

    annotFile: file containing annotation times
    clipType: either 'ictal', 'interictal', or 'ts'
    ts: TimeSeries object to pull from
    outDir: folder to save clips into
    channels: list of eeg channels to use
        default (None) uses all channels
    limit: maximum number of annotations to use
        default (0) uses all annotations

    Returns: list of (start,end) times for each clip (excluding gaps)
    '''
    # TODO: return (start,end) times of each clip

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
        if limit > 0 and limit < len(annots):
            annots = annots[:limit]
            print 'Using only the first %d annotations' % limit
        annots = [map(int, annot.split()) for annot in annots]

    # pull and save each annotated clip
    clipTimes = []
    num_saved = 0
    for annot in annots:
        if not annot: # ignore empty lines in file
            continue
        annotStart = annot[0]
        annotEnd = annot[1]

        # pull data for current clip 
        try:
            df = ts.get_data(start=annotStart, end=annotEnd, channels=channels, use_cache=False)
            # cache disabled to prevent malformed cache db errors
        except RequestException as e:
            # catch Blackfynn server errors
            print 'Server error (will retry):', e
            sleep(2)
            continue
        except:
            print 'Pull failed at (%d, %d)' % (annotStart, annotEnd)
            raise

        # skip clip if 1 or more channels are missing data 
        if df.empty or df.isnull().all().any():
            continue
        dfs = []

        # (WORKAROUND) scale ucd1 data after 7/31/18 22:11:28 by 1000
        if ts.name == 'UCD1' and annotStart >= 1533075088572912:
            df *= 1000

        # Handle gaps in data, if present
        # (Taken from Steve Baldassano's pipeline)
        i = 0
        for j in range(1, df.shape[0]):
            dT = (df.iloc[j].name - df.iloc[j-1].name).total_seconds()
            if dT > 0.01: # if gap is too big, split into 2 clips
                dfs.append(df.iloc[i:j])
                i = j
                if i+1 == df.shape[0]: break
        dfs.append(df.iloc[i:])

        # save clip(s)
        for df in dfs:
            time = (df.iloc[0].name.value / 1000,
                    df.iloc[-1].name.value / 1000)
            clipTimes.append(time)
            array = df.transpose().values
            outfile = '%s/%s%d.hkl' % (outDir, outfile_prefix, num_saved+1)
            hickle.dump(array, outfile)
            num_saved += 1

    print('%d clips saved.' % num_saved)
    return clipTimes

if __name__ == '__main__':
    annotFile = sys.argv[1]
    clipType = sys.argv[2]
    tsID = sys.argv[3]
    outDir = sys.argv[4].rstrip('/')

    try:
        limit = int(sys.argv[5])
    except IndexError:
        limit = None

    bf = Blackfynn()
    ts = bf.get(tsID)
    pullClips(annotFile, clipType, ts, outDir, limit=limit)
