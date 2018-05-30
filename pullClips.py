# -*- coding: utf-8 -*-
"""
Use this to pull seizure data from Blackfynn for the pipeline
"""

from blackfynn import Blackfynn
from datetime import datetime, timedelta
import scipy.io as sio
import sys

clipType = sys.argv[1] # either ictal or interictal
filename = sys.argv[2]

if clipType == 'ictal':
    outfile_prefix = 'sz'
elif clipType == 'interictal':
    outfile_prefix = 'nonsz'
else:
    print 'Invalid clip type "%s" (should be ictal or interictal)' % clipType
    exit()

# Establish Blackfynn connection
bf = Blackfynn()
ts = bf.get("N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c") # 'old ripley' data
# ts = bf.get("N:package:401f556c-4747-4569-b1a8-9e6e50abf919") # 'ripley' data

# get the annotation times in usec from file
with open(filename, 'r') as f:
    """
    each line of the annotation file is formatted as: startTime endTime
    with times given in microseconds
    """
    annots = f.read().splitlines()

# save each clip to file
for i in range(len(annots)):
    # get clip start/end times
    annot = map(int, annots[i].split())
    if not annot:
        # ignore empty lines
        continue
    annotStart = annot[0]
    annotEnd = annot[1]

    # pull the data for each clip 
    try:
        # print('about to pull...')
        df = ts.get_data(start=annotStart, end=annotEnd)
    except:
        print('Pull failed at ' + str(annotStart) + '\n')
        continue

    # print(df)
    ar = df.as_matrix()
    filename = '%s%d.mat' % (outfile_prefix, i+1)
    sio.savemat(filename,{'clip':ar})
print('%d clips saved.' % i+1)
