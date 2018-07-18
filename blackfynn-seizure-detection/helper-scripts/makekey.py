#!/usr/bin/env python2
'''
Takes in a pipeline output file (XXX_seizures.txt) plus a seizure annotation
file, and makes prediction and answer key CSVs which can be used by metrics.py

Usage: python -m helper-scripts.makekey ptName annotFile logFile
'''

import csv
from random import randint
import re
import sys

from blackfynn import Blackfynn

from settings import TS_IDs

ptName = sys.argv[1]
annotFile = sys.argv[2]
logFile = sys.argv[3]

bf = Blackfynn()
ts = bf.get(TS_IDs[ptName])
start = ts.start
end = ts.end

CLIP_LENGTH = 15000000
keyFile = ptName + '_key.csv'
predFile = ptName + '_preds.csv'
ptrn = re.compile(r'^([+-])\s+\((\d+),\s+(\d+)\)\s+((?:\d*\.)?\d+)$')

#def searchSegs(t):
#    'Finds start time t in segments and updates segs_idx to match'
#    global segs_idx
#    while segs_idx < num_segs:
#        curr_seg = segs[segs_idx]
#        if curr_seg[0] <= t and curr_seg[1] > t:
#            return True
#        elif curr_seg[0] > t:
#            return False
#        segs_idx += 1
#    return False

def isIctal(start, end):
    'Returns s: clip is a seizure, and e: clip is an early seizure'
    s = 0
    e = 0
    clipLength = end - start
    for ictal in ictals:
        #if min(end, ictal[1]) - max(start, ictal[0]) >= clipLength / 2:
        if min(end, ictal[1]) - max(start, ictal[0]) == clipLength:
            s = 1
            if start - ictal[0] < 15000000:
                e = 1
            break
    return s, e

# Read ictal annotations
ictals = []
with open(annotFile, 'rU') as f:
    for line in f.readlines():
        ictals.append(map(int, line.strip().split()))

# Create output key file
outfile_key = open(keyFile, 'wb')
key_writer = csv.writer(outfile_key, lineterminator='\n')
key_writer.writerow( ('clip', 'seizure', 'early') )

# Create csv of predictions
outfile_pred = open(predFile, 'wb')
pred_writer = csv.writer(outfile_pred, lineterminator='\n')
pred_writer.writerow( ('clip', 'seizure', 'early') )

with open(logFile, 'rU') as f:
    n = 1
    for line in f.readlines():
        match = re.match(ptrn, line)
        pred = int(match.group(1) == '+')
        startTime = int(match.group(2))
        endTime = int(match.group(3))
        score = float(match.group(4))

        # Check if valid time period
        #if not searchSegs(startTime): continue

        # Check if clip is in ictals
        s, _ = isIctal(startTime, endTime)

        # Write output files
        clipname = '%s_%d-%d' % (ptName, startTime, endTime)
        key_writer.writerow( (clipname, s) )
        pred_writer.writerow( (clipname, pred, score) )
        n += 1

outfile_key.close()
outfile_pred.close()
