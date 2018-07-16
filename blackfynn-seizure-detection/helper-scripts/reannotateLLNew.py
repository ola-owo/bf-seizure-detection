
'''
Annotate new line length detector from an output log

Usage: python reannotateLL.py ptName logfile layerID
'''

import sys
from blackfynn import Blackfynn
from settings import LL_NEW_LAYER_NAME

TS_IDs = { 
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
    'Gus': 'N:package:cb8231c7-5b8b-4baf-be00-5658133b4d16',
}

ptName = sys.argv[1]
logfile = sys.argv[2]
scalar = float(sys.argv[3])

tsID = TS_IDs[ptName]
bf = Blackfynn()
ts = bf.get(tsID)
ts.get_layer(LL_NEW_LAYER_NAME).delete()
layer = ts.add_layer(LL_NEW_LAYER_NAME)

trend = None

with open(logfile, 'rU') as f:
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
