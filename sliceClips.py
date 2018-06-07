#!/usr/bin/env python2
'''
Slice annotation clips into 1s segments and save to file.
This script can be called standalone using
'''

import os
import sys
import hickle
import numpy as np
import scipy.io as sio

def sliceClips(clipDir, clipType, fs, ptName):
    '''
    Slice a clip of type clipType and frequency fs from patient ptName,
    and save it inside ./seizure-data/
    
    Clips should be inside folder clipDir.
    clipType should be 'ictal' or 'interictal'.
    '''

    # Make seizure-data folder if it doesn't already exist
    try:
        os.makedirs('seizure-data')
    except:
        pass

    # Validate clip type
    if clipType == 'ictal': 
        clipFilePrefix = 'sz'
        ictal = True
    elif clipType == 'interictal':
        clipFilePrefix = 'nonsz'
        ictal = False
    else:
        print 'Unkown clip type "%s" (should be ictal or interictal).'
        return

    # Load and clip seizures
    numClips = 0 # total number of clips
    sampleCount = 0 # total number of 1s samples across all clips
    while True:
        try:
            clip = hickle.load('%s/%s%d.hkl' % (clipDir, clipFilePrefix, numClips+1))
            numClips = numClips + 1
        except:
            break

        numSamples = int(clip.shape[1] / fs) # total number of 1s samples per clip
        c = _clip(clip, fs, 4, ptName, numSamples, sampleCount, ictal)
        sampleCount = sampleCount + c
    print '%d clips converted to %d 1s samples.' % (numClips, sampleCount)

def _clip(clip, fs, channels, ptName, numSamples, sampleCount, ictal):
    'Helper function for sliceClips()'
    pos = 0
    skippedForNans = 0
    if sampleCount == 0: # debug
        print 'Clip shape:', clip.shape
    for i in range(numSamples):
        latency = i
        data = clip[:, pos:pos+fs]

        if np.any(data == None):
            print 'Skipped clip %d (Some/all data is NaN)' % pos
            skippedForNans = skippedForNans + 1
            continue

        if np.any(np.all((data == 0), axis=1)):
            print 'Skipped clip %d (Empty channel)' % pos
            skippedForNans = skippedForNans + 1
            continue

        pos = pos + fs
    
        # Mean normalize each channel signal (copied from the old pipeline)
        data = data - np.mean(data, axis=1, keepdims=True)

        if ictal:
            sio.savemat('seizure-data/{0}/{0}_ictal_segment_{1}.mat'.format(
                        ptName, (i+1 + sampleCount - skippedForNans)), {
                'data': data,
                'channels': channels,
                'freq': fs,
                'latency': latency
            })
        else:
            sio.savemat('seizure-data/{0}/{0}_interictal_segment_{1}.mat'.format(
                        ptName, (i+1 + sampleCount - skippedForNans)), {
                'data': data,
                'channels': channels,
                'freq': fs,
                'latency': latency
            })

    return numSamples - skippedForNans

if __name__ == '__main__':
    clipDir = sys.argv[1]
    clipType = sys.argv[2]
    fs = sys.argv[3]
    ptName = sys.argv[4]
    sliceClips(clipDir, clipType, fs, ptName)
