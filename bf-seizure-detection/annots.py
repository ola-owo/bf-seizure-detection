'''
Generates annotation files from a given annotation layer.
This script can also be called standalone with:
> python annots.py ptName [layerID]
'''

from random import shuffle
import sys

from blackfynn import Blackfynn

from settings import DATA_RATIO, GOLD_STD_LAYERS, PL_ROOT, TIME_BUFFER, TS_IDs
from functools import reduce

def makeAnnotFile(annotations, filename):
    'Write a list of annotations to file filename.'

    if not annotations:
        print('makeAnnotFile(): no annotations to write')
        return

    with open(filename, 'w') as f:
        n = 0
        for annot in annotations:
            f.write('%d %d\n' % (annot[0], annot[1]))
            n += 1

    print('%d annotations written to %s.' % (n, filename))

def getIctalAnnots(layer):
    'getIctalAnnots(layer) --> list of annotation (start,end) tuples'

    anns = [(a.start, a.end) for a in layer.annotations()]
    return anns

def getInterictalAnnots(ictals, segments):
    '''
    Takes a list of ictal annotations and generates interictal annotations.

    ictals: list of ictal annotations
    segments: list of all (non-empty) periods within the timeseries
    Returns: list of annotation (start, end) tuples
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
    totalIctalTime = reduce(lambda acc, ab: ab[1] - ab[0] + acc, ictals, 0)
    totalInterTime = 0

    for inter in interictalsCopy:
        interictals.append(inter)
        totalInterTime += (inter[1] - inter[0])
        if totalInterTime // totalIctalTime >= DATA_RATIO:
            diff = totalInterTime % totalIctalTime
            interictals[-1] = (inter[0], inter[1] - diff)
            totalInterTime -= diff
            break

    print('total ictal time:', totalIctalTime)
    print('total interictal:', totalInterTime)
    return interictals

if __name__ == '__main__':
    ptName = sys.argv[1]
    tsID = TS_IDs[ptName]

    if len(sys.argv) >= 3:
        layerID = int(sys.argv[2])
    else:
        layerID = GOLD_STD_LAYERS[ptName]

    bf = Blackfynn()
    ts = bf.get(tsID)
    segs = ts.segments()
    layer = ts.get_layer(layerID)
    
    ictals = getIctalAnnots(layer)
    interictals = getInterictalAnnots(ictals, segs) 
    makeAnnotFile(ictals, PL_ROOT + '/annotations/%s_annotations.txt' % ptName)
    makeAnnotFile(interictals, PL_ROOT + '/annotations/%s_interictal_annotations.txt' % ptName)
