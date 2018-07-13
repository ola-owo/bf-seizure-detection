'''
Get a patient's annotations and rewrite their seizure diary

Usage: python rewriteDiary.py ptName layerID diaryFile
'''

import sys
import sqlite3
from blackfynn import Blackfynn

TS_IDs = { 
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

ptName = sys.argv[1]
layerID = int(sys.argv[2])
diaryFile = sys.argv[3]

bf = Blackfynn()
tsID = TS_IDs[ptName]
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
