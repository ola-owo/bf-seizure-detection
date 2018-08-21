#!/usr/bin/env python2
'''
Find line lengths at certain times, in order to figure out threshold values
for the basic line length detector.

Usage: python -m helper_scripts.lineLengthTest ptName [startTime]
'''
import os
import sys
import numpy as np
from blackfynn import Blackfynn

from settings import CHANNELS, LL_CLIP_LENGTH, TS_IDs

ptName = sys.argv[1]
bf = Blackfynn()
ts = bf.get(TS_IDs[ptName])
ch = CHANNELS.get(ptName, None)

try:
    startTime = int(sys.argv[2])
    segments = ts.segments(start=startTime)
except:
    segments = ts.segments()
finally:
    startTime = segments[0][0]
    print 'start time:', startTime

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
