'''
Miscellaneous helper functions
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
    '''
    Suppress print output.
    Usage:
    with NoPrint():
        foo()
        bar()
    '''

    def __enter__(self):
        self._stdout = sys.stdout
        self._devnull = open(os.devnull, 'w')
        sys.stdout = self._devnull

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout
        self._devnull.close()

def timeString(epoch_usecs):
    'Returns (example): "Thu Sep 13 02:22:50 2012 UTC (1347517370)"'
    return DT.datetime.fromtimestamp(epoch_usecs).strftime('%c UTC ') + '(%d)' % epoch_usecs
