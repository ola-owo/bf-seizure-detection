'''
Annotate MA line length detector from an output log,
using a custom threshold multiplier

Usage: python -m helper-scripts.reannotateLLNew ptName logfile threshold
'''

import sys
from blackfynn import Blackfynn
from settings import LL_MA_LAYER_NAME, TS_IDs

ptName = sys.argv[1]
logfile = sys.argv[2]
scalar = float(sys.argv[3])

tsID = TS_IDs[ptName]
bf = Blackfynn()
ts = bf.get(tsID)
ts.get_layer(LL_MA_LAYER_NAME).delete()
layer = ts.add_layer(LL_MA_LAYER_NAME)

with open(logfile, 'rU') as f:
    trend = None
    for line in f.readlines():
        spl = line.strip().split()
        if spl[0] == 'TREND:':
            trend = float(spl[1])
            continue
        elif len(spl) != 4 or spl[0] not in '+-':
            continue
        positive = (float(spl[1]) >= trend * scalar)
        startTime = int(spl[2].lstrip('(').rstrip(','))
        endTime = int(spl[3].rstrip(')'))

        if positive: layer.insert_annotation('Possible seizure', start=startTime, end=endTime)
