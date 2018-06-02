#!/usr/bin/env python2
import numpy as np

def sliceClips(clipType, fs, ptName):
    'Slice a clip of frequency fs from patient ptName'
    if clipType == 'ictal': 
        clipFileType = 'sz'
    elif clipType == 'interictal':
        clipFileType = 'nonsz'
    else:
        print 'Unkown clip type "%s". (should be ictal or interictal)')
        return

    # Load and clip seizures
    numClips = 0
    while True:
        try:
            clip = sio.loadmat(clipFileType + str(numClips+1) + '.mat')['clip']
            numClips = numClips + 1
        except:
            print '%d total seizures loaded.' % numClips
            break

        netClips = _clip(clip, fs, channels, ptName, numClips, szClipNum, ictal)

    def _clip(clip, fs, channels, ptName, numClips, tempClipNum, ictal):
        pos = 0
        skippedForNans = 0
        for i in range(1, numClips+1):
            data = clip[:,pos:pos+fs]
            pos = pos + fs

            if np.any(data == None):
                print 'Skipped clip %d (Some/all data in NaN' % i
                skippedForNans = skippedForNans + 1
                continue
            
            if np.any(np.all((data == 0), axis=1)):
                print 'Skipped clip %d (Dead channel)' % i
                skippedForNans = skippedForNans + 1
                continue
        
            data = data - np.tile(np.mean(data, 2), (1, np.shape(data)[1]))
                # Mean normalize each channel signal
                # (copied from the old pipeline)
            latency = i - 1


            if ictal:
                hkl.dump({
                    'data': data,
                    'channels': channels,
                    'freq': freq,
                    'latency': latency
                }, 'seizure_data/{0}/{0}_ictal_segment_{1}.mat'.format(ptName, (i - skippedForNans + tempClipNum)))
            else:
                hkl.dump({
                    'data': data,
                    'channels': channels,
                    'freq': freq,
                }, 'seizure_data/{0}/{0}_interictal_segment_{1}.mat'.format(ptName, (i - skippedForNans + tempClipNum)))

        return numClips - skippedForNans
