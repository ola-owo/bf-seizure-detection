'''
Miscellaneous pipeline functions
'''

import csv
import os

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
