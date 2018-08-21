'''
Get patients' annotations from Blackfynn and rewrite their seizure diary
database entries.

Usage: python -m helper_scripts.rewriteDiary algo
'''

import sys
import sqlite3
from blackfynn import Blackfynn

from settings import (
    DIARY_DB_NAME, LL_MA_LAYER_NAME, LL_LAYER_NAME, PL_LAYER_NAME, TS_IDs
)

algo = sys.argv[1]

if algo == 'linelength':
    layerName = LL_LAYER_NAME
elif algo == 'ma_linelength':
    layerName = LL_MA_LAYER_NAME
elif algo == 'pipeline':
    layerName = PL_LAYER_NAME
else:
    raise ValueError('Invalid classifier: ' + algo)

bf = Blackfynn()
conn = sqlite3.connect(DIARY_DB_NAME)
c = conn.cursor()

for ptName in TS_IDs:
    ts = bf.get(TS_IDs[ptName])
    layer = ts.get_layer(layerName)
    anns = [(a.start, a.end) for a in layer.annotations()]

    try:
        # Clear old entries
        c.execute('DELETE FROM ' + ptName)

        # Add new entries
        for ann in anns:
            c.execute('INSERT INTO ' + ptName + ' VALUES (?,?)', ann)
        conn.commit()
    except:
        c.close()
        conn.close()
        raise

c.close()
conn.close()
