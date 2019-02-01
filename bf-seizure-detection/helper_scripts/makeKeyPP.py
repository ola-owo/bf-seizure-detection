#!/usr/bin/env python3
'''
Takes in a pipeline output file (XXX_seizures.txt) plus a seizure annotation
file, and makes prediction and answer key CSVs which can be used by metrics.py

Usage: python -m helper_scripts.makekey ptName logFile
'''

import csv
from random import randint
import re
import sys

from settings import PL_ROOT, TS_IDs

def isIctal(ictals, start, end):
    'Returns s: clip is a seizure, and o: clip overlaps with a seizure'
    s = 0
    o = 0
    clipLength = end - start
    for ictal in ictals:
        if min(end, ictal[1]) - max(start, ictal[0]) > 0:
            o = 1
            # Check if entire clip is contained within seizure annotation
            if start >= ictal[0] and end <= ictal[1]:
                s = 1
            break
    return s, o

def makeKey(ptName, logFile):
    annotFile = PL_ROOT + '/annotations/' + ptName + '_annotations.txt'
    keyFile = ptName + '_key.csv'
    predFile = ptName + '_preds.csv'
    ptrn = re.compile(r'^([+-])\s+\((\d+),\s+(\d+)\)\s+((?:\d*\.)?\d+)$')


    # Read ictal annotations
    ictals = []
    with open(annotFile, 'r') as f:
        for line in f.readlines():
            ictals.append(list(map(int, line.strip().split())))

    # Create key csv file
    outfile_key = open(keyFile, 'w')
    key_writer = csv.writer(outfile_key, lineterminator='\n')
    key_writer.writerow( ('clip', 'seizure', 'early') )

    # Create predictions csv file
    outfile_pred = open(predFile, 'w')
    pred_writer = csv.writer(outfile_pred, lineterminator='\n')
    pred_writer.writerow( ('clip', 'seizure', 'early') )

    with open(logFile, 'r') as f:
        n = 0
        for line in f.readlines():
            match = re.match(ptrn, line)
            pred = int(match.group(1) == '+')
            startTime = int(match.group(2))
            endTime = int(match.group(3))
            score = float(match.group(4))

            # Check if clip is ictal 
            s, o = isIctal(ictals, startTime, endTime)
            if o and not s: continue

            # Write to output files
            clipname = '%s_%d-%d' % (ptName, startTime, endTime)
            key_writer.writerow( (clipname, s) )
            pred_writer.writerow( (clipname, pred, score) )
            n += 1

    print(n, 'entries written.')
    outfile_key.close()
    outfile_pred.close()

if __name__ == '__main__':
    ptName = sys.argv[1]
    logFile = sys.argv[2]
    makeKey(ptName, logFile)
