#!/usr/bin/env python2
'''
Plot and label test segments

Usage:
python labelSeg.py segRoot ptName [keyFile]
'''

import os
import sys
import csv

import scipy.io as sio
from matplotlib import pyplot as plt

def labelSeg(data, label, channels=4):
    plt.figure()
    for ch in range(channels):
        plt.subplot(channels, 1, ch+1)
        plt.plot(data[ch,:])
    plt.suptitle(label)
    plt.show()
    
    # Get input
    while True:
        userLabel = raw_input('Seizure [1], or Non-seizure[0]?')
        if userLabel == '0' or userLabel == '1':
            return int(userLabel)

if __name__ == '__main__':
    # Parse command-line inputs
    segRoot = sys.argv[1].rstrip('/')
    ptName = sys.argv[2]

    try:
        keyFile = sys.argv[3]
    except IndexError:
        keyFile = None

    segDir = os.path.join(segRoot, ptName)
    if not os.path.isdir(segDir):
        print "Folder '%s' not found" % segDir
        sys.exit()

    # Use keyFile to find the starting point
    numSz = 0
    if keyFile:
        with open(keyFile, 'rt') as f:
            for _ in f.readlines(): numSz += 1
            numSz -= 1 # ignore 1st line (header) of keyFile

    # Get user labels
    seizures = []
    while True:
        try:
            data = sio.loadmat('%s/%s_test_segment_%d.mat' % (segDir, ptName, numSz+1))['data']
        except Exception as e:
            print e
            break

        try:
            label = labelSeg(data, '%s test segment %d' % (ptName, numSz+1), 16)
        except KeyboardInterrupt:
            # Save progress and exit if user presses ctrl-c
            break
        seizures.append(label)
        numSz += 1
    print numSz, 'seizures labeled.'

    # construct key array
    if keyFile:
        outfile = keyFile
    else:
        outfile = ptName + '_key.csv'
    clipnames = ['%s_test_segment_%d.mat' % (ptName, i+1) for i in range(numSz)]
    early = [0] * numSz

    # save csv key
    with open(outfile, 'ab') as f:
        f.write('clip,seizure,early\n')
        writer = csv.writer(f)
        for i in range(numSz):
            writer.writerow( (clipnames[i], seizures[i], early[i]) )
    print outfile, 'saved.'
