'''
Miscellaneous internal tools
'''

import csv
import os
import sys
import datetime as DT

EPOCH = DT.datetime(1970,1,1)

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
    Suppress print output. Example:
        with NoPrint():
            dontPrintThis()
        doPrintThis()
    '''

    def __enter__(self):
        self._stdout = sys.stdout
        self._devnull = open(os.devnull, 'w')
        sys.stdout = self._devnull

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._stdout
        self._devnull.close()

def timeString(epoch_usecs):
    '''
    Returns the current time, in UTC
    example: "Sep 13 2012 02:22:50 UTC (1347517370)"
    '''
    epoch_secs = epoch_usecs / 1000000.
    return DT.datetime.utcfromtimestamp(epoch_secs).strftime('%b %d %Y %X') + ' UTC (%d)' % epoch_usecs

def toUsecs(dt):
    'Convert datetime to epoch microseconds'
    return int((dt - EPOCH).total_seconds() * 1000000)

def getTime():
    'Get the current Unix time, in usecs'
    now = DT.datetime.utcnow()
    return toUsecs(now)

def toDateTime(t):
    'convert epoch time to datetime object'
    return DT.datetime.utcfromtimestamp(t//1000000)
    
def toDateTimeFromConcatStr(s):
    'convert string in form YYYYMMDDhhmmss to datetime'
    return DT.datetime.strptime(s,"%Y%m%d%H%M%S")
