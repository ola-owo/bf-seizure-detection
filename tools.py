'''
Miscellaneous pipeline functions
'''

import csv
import os
import sys

def makeDir(dirName):
    'Make directory dirName. If directory already exists, do nothing.'
    try:
        os.makedirs(dirName)
    except:
        pass

def savecsv(data, outfile):
    'Save data (iterable) as a csv to outfile.'
    with open(outfile, 'wb') as f:
        w = csv.writer(f)
        w.writerows(data)

def clearDir(dirName):
    'Delete all files in dirName.'
    for filename in os.listdir(dirName):
        filepath = os.path.join(dirName, filename)
        if os.path.isfile(filepath):
            os.remove(filepath)

class NoPrint:
    'Suppress print outputs'

    def __enter__(self):
        self._orig_stdout = sys.stdout
        self._devnull = open(os.devnull, 'w')
        sys.stdout = self._devnull
        # sys.stdout = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._orig_stdout
        self._devnull.close()
