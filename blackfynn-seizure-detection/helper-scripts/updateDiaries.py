'''
Update seizure diaries
'''
#!/usr/bin/env python2

import sqlite3
from blackfynn import Blackfynn
import liveDetect
from settings import TS_IDs, LL_LAYER_NAME, LL_MA_LAYER_NAME

bf = Blackfynn()
layerName = LL_MA_LAYER_NAME # change to whichever classifier is running

### Re-add annotations to database
conn = sqlite3.connect('live/diaries.db')
c = conn.cursor()

for ptName in TS_IDs:
    print 'current patient:', ptName
    ts = bf.get(TS_IDs[ptName])
    layer = ts.get_layer(layerName)
    for ann in layer.annotations():
        c.execute('INSERT INTO ' + ptName + ' VALUES (?,?)', (ann.start, ann.end))

c.close()
conn.commit()
conn.close()

### Update diaries
liveDetect.diary(bf, 'linelength')
