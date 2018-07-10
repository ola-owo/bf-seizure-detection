'''
Re-annotate line length detector using a different threshold

Usage: python reannotateLL.py ptName logfile layerID threshold
'''

import sys
from blackfynn import Blackfynn

TS_IDs = { 
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

ptName = sys.argv[1]
logfile = sys.argv[2]
layerID = int(sys.argv[3])
thresh = float(sys.argv[4])

tsID = TS_IDs[ptName]
bf = Blackfynn()
ts = bf.get(tsID)
layer = ts.get_layer(layerID)
layerName = layer.name
layer.delete()
layer = ts.add_layer(layerName)

with open(logfile, 'rU') as f:
    for line in f.readlines():
        spl = line.strip().split()
        if len(spl) != 4 or spl[0] not in '+-' : continue
        length = float(spl[1])
        startTime = int(spl[2].lstrip('(').rstrip(','))
        endTime = int(spl[3].rstrip(')'))

        if length > thresh: layer.insert_annotation('Possible seizure', start=startTime, end=endTime)
