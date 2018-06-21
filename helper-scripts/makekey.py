#!/usr/bin/env python2

import csv
from random import randint
import re
import sys
from blackfynn import Blackfynn

ptName = sys.argv[1]
annotFile = sys.argv[2]
logFile = sys.argv[3]

bf = Blackfynn()
ts = bf.get('N:package:86985e61-c940-4404-afa7-94d0add8333f')
segs = ts.segments()
start = ts.start
end = ts.end

segs_idx = 0
num_segs = len(segs)
CLIP_LENGTH = 15000000
keyFile = ptName + '_key.csv'
predFile = ptName + '_preds.csv'
ptrn = re.compile(r'^([+-])\s+\((\d+),\s+(\d+)\)\s+((?:\d*\.)?\d+)$')

def searchSegs(t):
    'Finds start time t in segments and updates segs_idx to match'
    global segs_idx
    while segs_idx < num_segs:
        curr_seg = segs[segs_idx]
        if curr_seg[0] <= t and curr_seg[1] > t:
            return True
        elif curr_seg[0] > t:
            return False
        segs_idx += 1
    return False

def isSeizure(start, end):
    'Returns s: clip is a seizure, and e: clip is an early seizure'
    result = (False,False)
    s = 0
    e = 0
    for ictal in ictals:
        if min(end, ictal[1]) - max(start, ictal[0]) >= 7500000:
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
        pred = match.group(1)
        startTime = int(match.group(2))
        endTime = int(match.group(3))
        score = float(match.group(4))

        # Check if valid time period
        if not searchSegs(startTime): continue

        # Check if clip is in ictals
        s, e = isSeizure(startTime, endTime)

        # Write output files
        clipname = '%s_segment_%d' % (ptName, n)
        key_writer.writerow( (clipname, s, e) )
        pred_writer.writerow( (clipname, score, randint(0,1)) )
        n += 1

outfile_key.close()
outfile_pred.close()
