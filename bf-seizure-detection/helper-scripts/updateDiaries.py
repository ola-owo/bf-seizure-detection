'''
Manually rebuild seizure diary database.

Usage: python -m helper-scripts.updateDiaries algo
'''

import sys
import sqlite3

from blackfynn import Blackfynn

import liveDetect
from settings import TS_IDs

algo = sys.argv[1]
if algo not in ('pipeline', 'linelength', 'ma_linelength'):
    raise ValueError("Invalid classifier option '" + algo + "'")

bf = Blackfynn()
conn = sqlite3.connect('live/diaries.db')
c = conn.cursor()

### Delete old entries
try:
    for pt in TS_IDs:
        print 'Deleting entries from:', pt
        c.execute("DELETE FROM " + pt + " WHERE type = '" + algo + "'")
    conn.commit()
finally:
    c.close()
    conn.close()

### Add new entries
print 'Adding new entries...'
liveDetect.diary(bf, algo)
