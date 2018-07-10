#!/usr/bin/env python2
'''
Find line lengths at certain times,
in order to figure out threshold values

Usage: python lineLengthTest.py ptName [startTime]
'''
import os
import sys
import numpy as np
from blackfynn import Blackfynn

#sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#print os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print os.path.abspath('.')
sys.path.append('..')
from settings import CHANNELS, LL_CLIP_LENGTH, TS_IDs

ptName = sys.argv[1]
bf = Blackfynn()
ts = bf.get(TS_IDs[ptName])
ch = CHANNELS.get(ptName, None)
segments = ts.segments()

try:
    startTime = int(sys.argv[2])
    i = next(i for i, (a,b) in enumerate(segments) if b > startTime)
    segments[:i] = []
    startTime = max(segments[0][0], startTime)
    segments[0] = (startTime, segments[0][1])
    print 'start time:', startTime
except:
    startTime = segments[0][0]

def lineLength(clip):
    lengths = np.zeros(clip.shape[0]).astype('float64')
    for i in range(1, clip.shape[1]):
        lengths += np.abs(clip[:, i] - clip[:, i-1])

    # remove zero-length channels
    lengths = lengths[np.nonzero(lengths)] 
    if lengths.size == 0: return 0.0

    # take the median and normalize by clip length
    length = np.median(lengths) / clip.shape[1] 
    return length

for seg in segments:
    pos = seg[0]
    while pos < seg[1]:
        try:
            clip = ts.get_data(start=pos, length=LL_CLIP_LENGTH, channels=ch, use_cache=False)
            # note: actual clip length may be shorter than LL_CLIP_LENGTH
        except Exception as e:
            print 'Pull failed at time %d:' % pos, e
            pos += LL_CLIP_LENGTH
            continue
        if clip.empty:
            pos += LL_CLIP_LENGTH
            continue

        startTime = clip.iloc[0].name.value / 1000 # convert to Unix epoch time, in usecs
        endTime = clip.iloc[-1].name.value / 1000
        clip.fillna(0, inplace=True) # replace NaNs with zeros

        clip = clip.transpose().values
        length = lineLength(clip)
        print 't', (startTime, endTime), '\tlength:', length
        raw_input()

        pos += LL_CLIP_LENGTH
