'''
Generates annotation files from a given annotation layer.
This script can also be called standalone with:
> python makeAnnonationFile.py ptName timeseriesID layerID
'''

import os
from random import shuffle
import sys

from blackfynn import Blackfynn

from settings import TIME_BUFFER, DATA_RATIO

def makeAnnotFile(annotations, filename):
    '''
    Write annotations to file filename.
    '''

    if not annotations:
        print 'makeAnnotFile(): no annotations to write'
        return

    with open(filename, 'wt') as f:
        n = 0
        for annot in annotations:
            f.write('%d %d\n' % (annot[0], annot[1]))
            n += 1

    print '%d annotations written to %s.' % (n, filename)

def getIctalAnnots(layer):
    '''
    Get ictal annotations from Layer object slayer
    '''

    'getIctalAnnots(layer) --> list of annotation tuples from layer'
    anns = map(lambda x: (x.start, x.end), layer.annotations())
    return anns

def getInterictalAnnots(ictals, segments):
    '''
    Takes a list of ictal annotations and generates interictal annotations.

    ictals: list of ictal annotations
    segments: list of all (non-empty) periods within the timeseries
    '''
    interictals = segments
    start = segments[0][0]
    end = segments[-1][1]

    ### First pass: Remove each ictal period from interictals
    for ictal in ictals:
        # Get the seizure start/end points
        trimStart = max(start, ictal[0] - TIME_BUFFER)
        trimEnd = min(end, ictal[1] + TIME_BUFFER)

        # Find all the interictal periods between trimStart and trimEnd
        for i in range(len(interictals)):
            if interictals[i][1] > trimStart: break

        for j in range(i+1, len(interictals)):
            if interictals[j][1] > trimEnd: break

        # Trim the interictals periods containing trimStart and trimEnd
        newAnnot = (interictals[i][0], trimStart)
        interictals[i] = newAnnot
        newAnnot = (trimEnd, interictals[j][1])
        interictals[j] = newAnnot

        # Remove interictal periods between trimStart and trimEnd
        interictals[i+1 : j] = []

    ### Second pass: Use only enough interictal clips to satisfy DATA_RATIO
    interictalsCopy = interictals
    shuffle(interictalsCopy)
    interictals = []
    totalIctalTime = reduce(lambda acc, (a,b): b - a + acc, ictals, 0)
    totalInterTime = 0

    for inter in interictalsCopy:
        interictals.append(inter)
        totalInterTime += (inter[1] - inter[0])
        if totalInterTime / totalIctalTime >= DATA_RATIO: break

    return interictals

if __name__ == '__main__':
    ptName = sys.argv[1]
    tsID = sys.argv[2]
    layerID = int(sys.argv[3])

    bf = Blackfynn()
    ts = bf.get(tsID)
    segs = ts.segments()
    layer = ts.get_layer(layerID)
    
    ictals = getIctalAnnots(layer)
    interictals = getInterictalAnnots(ictals, segs) 
    makeAnnotFile(ictals, 'annotations/%s_annotations.txt' % ptName)
    makeAnnotFile(interictals, 'annotations/%s_interictal_annotations.txt' % ptName)
