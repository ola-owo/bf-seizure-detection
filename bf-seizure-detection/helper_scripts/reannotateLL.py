'''
Re-annotate basic line length detector using a custom threshold.

Usage: python -m helper_scripts.reannotateLL ptName logfile threshold
'''

import sys
from blackfynn import Blackfynn

from settings import TS_IDs, LL_LAYER_NAME

ptName = sys.argv[1]
logfile = sys.argv[2]
thresh = float(sys.argv[3])

tsID = TS_IDs[ptName]
bf = Blackfynn()
ts = bf.get(tsID)
layer = ts.get_layer(LL_LAYER_NAME)
for ann in layer.annotations():
    ann.delete()

with open(logfile, 'rU') as f:
    for line in f.readlines():
        spl = line.strip().split()
        if len(spl) != 4 or spl[0] not in '+-' : continue
        length = float(spl[1])
        startTime = int(spl[2].lstrip('(').rstrip(','))
        endTime = int(spl[3].rstrip(')'))
        if length > thresh:
            layer.insert_annotation('Possible seizure',
                                    start=startTime, end=endTime)
