'''
Get a patient's annotations from Blackfynn and rewrite their seizure diary.
Seizure diary graphs can be updated using updateDiary.py

Usage: python -m helper-scripts.rewriteDiary ptName layerID diaryFile
'''

import sys
import sqlite3
from blackfynn import Blackfynn

from settings import TS_IDs

ptName = sys.argv[1]
layerID = int(sys.argv[2])
diaryFile = sys.argv[3]

tsID = TS_IDs[ptName]
bf = Blackfynn()
ts = bf.get(tsID)
layer = ts.get_layer(layerID)
conn = sqlite3.connect(diaryFile)
c = conn.cursor()
anns = [(a.start, a.end) for a in layer.annotations()]

# Clear old entries
c.execute('DELETE FROM ' + ptName)

# Add new entries
for ann in anns:
    c.execute('INSERT INTO ' + ptName + ' VALUES (?,?)', ann)

# Close connection
conn.commit()
c.close()
conn.close()
