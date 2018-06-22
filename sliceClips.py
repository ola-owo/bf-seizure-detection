#!/usr/bin/env python2
'''
Slice annotation clips into 1sec segments and save to file.

Standalone usage:
python sliceClips.py clipDir segType fs ptName [trainingSz]
'''

import csv
import os
import sys

from tools import makeDir, savecsv

import hickle
import numpy as np
import scipy.io as sio

def sliceClips(clipDir, segType, fs, ptName, trainingSz = -1, skipNans = True):
    '''
    Slice a clip from patient ptName and save it inside ./seizure-data/
    Returns: The number of segments successfully saved

    clipDir: folder containing clips
    segType: type of segment to save; either 'ictal', 'interictal', or 'test'
    fs: frequency
    ptName: patient name
    trainingSz: number of seizures to use as training data.
        The default value (-1) means all seizures are used.
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
        if trainingSz >= 0 and numClips >= trainingSz:
            break

        try:
            clip = hickle.load('%s/%s%d.hkl' % (clipDir, clipFilePrefix, numClips+1))
            numClips += 1
        except:
            break

        clipSegs = int(clip.shape[1] / fs) # number of segments in the current clip

        c = _clip(clip, fs, 4, ptName, clipSegs, segTotal, segType, skipNans)
        segTotal += c

    print '%d clips converted to %d segments.' % (numClips, segTotal)
    return segTotal

def _clip(clip, fs, channels, ptName, clipSegs, segTotal, segType, skipNans):
    '''
    Helper function for sliceClips()

    clip: the clip to be preprocessed
    segType: either ictal, interictal, or test
    fs: recording frequency
    ptName: patient name
    clipSegs: number of segments to save
    segTotal: current total number of segments
    skipNans: whether to skip segments with missing data
    '''
    pos = 0
    nanSkips = 0
    for i in range(clipSegs):
        data = clip[:, pos:pos+fs]

        if skipNans:
            if np.any(np.isnan(data)):
                print 'Skipped segment %d/%d of clip at position %d (some/all data is NaN)' % (i+1, clipSegs, pos)
                nanSkips += 1
                continue

            if np.any(np.all((data == 0), axis=1)):
                print 'Skipped segment %d/%d at position %d (empty channel)' % (i+1, clipSegs, pos)
                nanSkips += 1
                continue
    
        # Mean normalize each channel signal (copied from the old pipeline)
        data = data - np.mean(data, axis=1, keepdims=True)

        # Save segment
        matData = {
            'data': data,
            'channels': channels,
            'freq': fs,
        }
        if segType == 'ictal':
            matData['latency'] = i

        sio.savemat('seizure-data/{0}/{0}_{1}_segment_{2}.mat'.format(
                    ptName, segType, i+1 + segTotal - nanSkips), matData)

        # Go to the next segment
        pos += fs

    return clipSegs - nanSkips

if __name__ == '__main__':
    clipRoot = sys.argv[1]
    ptName = sys.argv[2]
    segType = sys.argv[3]
    fs = int(sys.argv[4])

    try:
        trainingSz = int(sys.argv[5])
    except IndexError:
        trainingSz = -1

    clipDir = os.path.join(clipRoot, ptName)
    makeDir(clipDir)
    makeDir('seizure-data/' + ptName)

    sliceClips(clipDir, segType, fs, ptName, trainingSz)
