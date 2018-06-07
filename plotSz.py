#!/usr/bin/env python2
'''
Plot seizure clips
'''

import os
import sys
import hickle
from matplotlib import pyplot as plt

def plotSz(data, label, channels=4):
    plt.figure()
    for ch in range(channels):
        plt.subplot(channels, 1, ch+1)
        plt.plot(data[ch,:])
    plt.suptitle(label)
    plt.show()

if __name__ == '__main__':
    ptName = sys.argv[1]
    clipDir = 'clips/' + ptName
    if not os.path.isdir(clipDir):
        print "Clips not found for patient '%s'" % ptName
        sys.exit()

    i = 1
    while True:
        try:
            # data = hickle.load('%s/nonsz%d.hkl' % (clipDir, i)) # load non-seizures
            data = hickle.load('%s/sz%d.hkl' % (clipDir, i)) # load seizures
        except:
            break
        plotSz(data, 'Sz%d' % i, 4)
        i = i + 1
