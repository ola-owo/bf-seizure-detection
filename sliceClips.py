#!/usr/bin/env python2
'''
Slice annotation clips into 1sec segments and save to file.

Standalone usage:
python sliceClips.py clipDir clipType fs ptName [trainingSz]
'''

import csv
import os
import sys

from tools import makeDir, savecsv

import hickle
import numpy as np
import scipy.io as sio

def sliceClips(clipDir, clipType, fs, ptName, trainingSz = None, skipNans = True):
    '''
    Slice a clip of type clipType and frequency fs from patient ptName,
    and save it inside ./seizure-data/

    trainingSz indicates the number of seizures to use as training data.
    The rest are used as test data.
    A value of None means that all clips will be used as training data.

    clipDir: folder containing clips
    clipType: either 'ictal', 'interictal', or 'timeseries'
    fs: frequency
    ptName: patient name
    trainingSz: number of seizures to use as training data, the rest are used
        as test data.
        The default value (-1) means all seizures become training data.
    '''

    # Check clip type
    if clipType == 'ictal': 
        clipFilePrefix = 'sz'
    elif clipType == 'interictal':
        clipFilePrefix = 'nonsz'
    elif clipType == 'timeseries':
        clipFilePrefix = 'ts'
    else:
        print 'Unkown clip type "%s" (should be ictal or interictal).'
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

        numSegments = int(clip.shape[1] / fs) # number of 1sec segments per clip
        c = _clip(clip, fs, 4, ptName, numSegments, segTotal, clipType, skipNans)
        segTotal += c
    print '%d clips converted to %d 1sec segments.' % (numClips, segTotal)

def _clip(clip, fs, channels, ptName, numSegments, segTotal, clipType, skipNans):
    '''
    Helper function for sliceClips()

    clip: the clip to be preprocessed
    clipType: either ictal, interictal, or test
    fs: recording frequency
    ptName: patient name
    numSegments: number of segments to save
    segTotal: current total number of segments
    skipNans: whether to skip segments with missing data
    '''
    pos = 0
    nanSkips = 0
    for i in range(numSegments):
        data = clip[:, pos:pos+fs]

        if skipNans:
            if np.any(data == None):
                print 'Skipped clip %d (Some/all data is NaN)' % pos
                nanSkips = nanSkips + 1
                continue

            if np.any(np.all((data == 0), axis=1)):
                print 'Skipped clip %d (Empty channel)' % pos
                nanSkips = nanSkips + 1
                continue

        pos += fs
    
        # Mean normalize each channel signal (copied from the old pipeline)
        data = data - np.mean(data, axis=1, keepdims=True)

        # Save segment
        matData = {
            'data': data,
            'channels': channels,
            'freq': fs,
            'latency': latency
        }
        if clipType == 'ictal':
            matData['latency'] = i

        sio.savemat('seizure-data/{0}/{0}_{1}_segment_{2}.mat'.format(
                    (ptName, clipType, i + 1 + segTotal - nanSkips)), matData)

    return numSegments - nanSkips

if __name__ == '__main__':
    clipDir = sys.argv[1]
    clipType = sys.argv[2]
    fs = int(sys.argv[3])
    ptName = sys.argv[4]

    try:
        trainingSz = int(sys.argv[5])
    except IndexError:
        trainingSz = -1

    makeDir('seizure-data/' + ptName)

    sliceClips(clipDir, clipType, fs, ptName, trainingSz)
