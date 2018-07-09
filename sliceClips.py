#!/usr/bin/env python2
'''
Slice annotation clips into 1sec segments and save to file.

Standalone usage:
python sliceClips.py clipRoot ptName segType fs
'''

import csv
import os
import sys

from tools import makeDir, savecsv

import hickle
import numpy as np
import scipy.io as sio

def sliceClips(clipDir, segType, fs, ptName):
    '''
    Slice a clip from patient ptName into 1sec segments and save them.
    Returns: The number of segments successfully saved

    clipDir: folder containing clips
    segType: type of segment to save; either 'ictal', 'interictal', or 'test'
    fs: frequency
    ptName: patient name
    '''

    # Check clip type
    if segType == 'ictal': 
        clipFilePrefix = 'sz'
    elif segType == 'interictal':
        clipFilePrefix = 'nonsz'
    elif segType == 'test':
        clipFilePrefix = 'ts'
    else:
        print "Unkown clip type '%s' (should be ictal or interictal)."
        return

    numClips = 0 # total number of clips
    segTotal = 0 # total number of 1sec segments across all clips

    # Load and slice clips
    while True:
        try:
            clipName = '%s/%s%d.hkl' % (clipDir, clipFilePrefix, numClips+1)
            clip = hickle.load(clipName)
            numClips += 1
        except:
            break

        clipSegs = int(clip.shape[1] / fs) # number of segments in the current clip

        c = _clip(clip, fs, 4, ptName, clipSegs, segTotal, segType)
        if c < clipSegs:
            print (clipSegs - c), 'segments skipped in', clipName
        segTotal += c

    print '%d clips converted to %d segments.' % (numClips, segTotal)
    return segTotal

def _clip(clip, fs, channels, ptName, clipSegs, segTotal, segType):
    '''
    Helper function for sliceClips()

    clip: the clip to be preprocessed
    segType: either ictal, interictal, or test
    fs: recording frequency
    ptName: patient name
    clipSegs: number of segments to save
    segTotal: current total number of segments
    '''
    pos = 0
    nanSkips = 0
    for i in range(clipSegs):
        data = clip[:, pos:pos+fs]

        if np.any(np.isnan(data)):
            print 'Skipped segment %d/%d of clip at position %d (some/all data is NaN)' % (i+1, clipSegs, pos)
            nanSkips += 1
            pos += fs
            continue

        if np.any(np.all((data == 0), axis=1)):
            print 'Skipped segment %d/%d at position %d (empty channel)' % (i+1, clipSegs, pos)
            nanSkips += 1
            pos += fs
            continue
    
        # Mean normalize each channel signal (copied from the old pipeline)
        data -= np.mean(data, axis=1, keepdims=True)

        # Save segment
        matData = {
            'data': data,
            'channels': channels,
            'freq': fs,
        }
        if segType == 'ictal': matData['latency'] = i

        sio.savemat('pipeline-data/seizure-data/{0}/{0}_{1}_segment_{2}.mat'.format(
                    ptName, segType, i+1 + segTotal - nanSkips), matData)

        # Go to the next segment
        pos += fs

    return clipSegs - nanSkips

if __name__ == '__main__':
    clipRoot = sys.argv[1].rstrip('/')
    ptName = sys.argv[2]
    segType = sys.argv[3]
    fs = int(sys.argv[4])

    clipDir = os.path.join(clipRoot, ptName)
    makeDir(clipDir)
    makeDir('pipeline-data/seizure-data/' + ptName)

    sliceClips(clipDir, segType, fs, ptName)
