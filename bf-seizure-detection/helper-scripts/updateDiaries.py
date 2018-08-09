'''
Manually rebuild seizure diary database.

Usage: python -m helper-scripts.updateDiaries ptName
'''

import sqlite3

from blackfynn import Blackfynn

import liveDetect
from settings import TS_IDs, LL_LAYER_NAME, LL_MA_LAYER_NAME, PL_LAYER_NAME

algo = sys.argv[1]
if algo == 'pipeline':
    layerName = PL_LAYER_NAME
elif algo == 'linelength':
    layerName = LL_LAYER_NAME
elif algo == 'ma_linelength':
    layerName = LL_MA_LAYER_NAME
else:
    raise ValueError("Invalid classifier option '" + algo + "'")

bf = Blackfynn()
conn = sqlite3.connect('live/diaries.db')
c = conn.cursor()

### Delete old entries and add new ones
try:
    for ptName in TS_IDs:
        print 'current patient:', ptName
        c.execute('DELETE FROM ' + ptName)
        ts = bf.get(TS_IDs[ptName])
        layer = ts.get_layer(layerName)
        anns = layer.annotations()
        while anns:
            for ann in anns:
                c.execute('INSERT INTO ' + ptName + ' VALUES (?,?)', (ann.start, ann.end))
            t = anns[-1].end + 1
            anns = layer.annotations(start=t)
    conn.commit()
finally:
    c.close()
    conn.close()

### Update diaries
liveDetect.diary(bf, 'ma_linelength')
