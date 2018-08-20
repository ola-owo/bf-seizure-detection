#!/usr/bin/env python2
'''
Takes in a pipeline output file (XXX_seizures.txt) plus a seizure annotation
file, and makes prediction and answer key CSVs which can be used by metrics.py

Usage: python -m helper-scripts.makekey ptName logFile
'''

import csv
from random import randint
import re
import sys

from blackfynn import Blackfynn

from settings import PL_ROOT, TS_IDs

ptName = sys.argv[1]
logFile = sys.argv[2]

ICTAL_BUFFER = 30000000 # usec
annotFile = PL_ROOT + '/annotations/' + ptName + '_annotations.txt'
bf = Blackfynn()
ts = bf.get(TS_IDs[ptName])
start = ts.start
end = ts.end

keyFile = ptName + '_key.csv'
predFile = ptName + '_preds.csv'
ptrn = re.compile(r'^([+-])\s+\((\d+),\s+(\d+)\)\s+((?:\d*\.)?\d+)$')

def isIctal(start, end):
    'Returns s: clip is a seizure, and w: clip is within ICTAL_BUFFER margin of a seizure'
    s = 0
    w = 0
    clipLength = end - start
    for ictal in ictals:
        # Check if most of clip overlaps with seizure
        if (start >= ictal[0] - ICTAL_BUFFER) and \
             (end <= ictal[1] + ICTAL_BUFFER):
            w = 1
            if (min(end, ictal[1]) - max(start, ictal[0])) >= clipLength / 2:
                s = 1
            break
    return s, w

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
    n = 0
    for line in f.readlines():
        match = re.match(ptrn, line)
        pred = int(match.group(1) == '+')
        startTime = int(match.group(2))
        endTime = int(match.group(3))
        score = float(match.group(4))

        # Check if valid time period
        #if not searchSegs(startTime): continue

        # Check if clip is in ictals
        s, w = isIctal(startTime, endTime)
        #if not s and w: continue # exclude clips within 5min of seizure start/end

        # Write output files
        clipname = '%s_%d-%d' % (ptName, startTime, endTime)
        key_writer.writerow( (clipname, w) )
        #key_writer.writerow( (clipname, s) )
        pred_writer.writerow( (clipname, pred, score) )
        n += 1

print n, 'entries written.'
outfile_key.close()
outfile_pred.close()
