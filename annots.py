'''
Generates annotation files from a given annotation layer.
This script can also be called standalone with:
> python makeAnnonationFile.py ptName timeseriesID layerID
'''

import os
import sys
from blackfynn import Blackfynn

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

def getInterictalAnnots(ictals, start, end):
    '''
    Takes a tuple list ictals and a start and end time and generates
    interictal annotations (may contain spaces of empty data)
    '''

    total_span = (start, end)
    interictals = [total_span]
    TIME_BUFFER = 14400000000 # 4h converted to microseconds

    ### First pass: Remove each ictal period from interictals
    for ictal in ictals:
        if ictal[0] >= ictal[1]:
            print 'Malformed annotation (%d,%d). Skipping...' % \
                  (ictal[0], ictal[1])
            continue

        inter = () # interictal annotation to be clipped
        for i in range(len(interictals)):
            if interictals[i][0] < ictal[0] and \
            interictals[i][1] > ictal[1]:
                # inter should entirely contain ictal annot
                inter = interictals.pop(i)
                break
        if not inter:
            # Indicates malformed annotation (start >= end)
            # or overlap with a previous seizure annotation
            raise ValueError('Invalid ictal annotation (%d, %d)' % \
                                     (ictal[0], ictal[1]))

        # Remove seizure period from interictal
        newAnn1 = (inter[0], ictal[0])
        newAnn2 = (ictal[1], inter[1])
        interictals.insert(i, newAnn1)
        interictals.insert(i+1, newAnn2)

    ### Second pass: Enforce TIME_BUFFER constraint
    interictalsCopy = interictals
    interictals = []
    for inter in interictalsCopy:
        newStart = inter[0] + TIME_BUFFER
        newEnd = inter[1] - TIME_BUFFER

        # Only include valid interictal clips (where start < end)
        if newStart < newEnd:
            interictals.append((newStart, newEnd))

    ### Third pass: Convert long annotations into shorter ones
    interictalsUncut = interictals
    interictals = []
    totalIctalTime = reduce(lambda acc, x: acc + (x[1] - x[0]), ictals, 0)
    totalInterTime = 0
    clipLength = 60000000 # length (usec) of each clip to annotate
    clipInterval = 10800000000L # interval (usec) to grab clips

    for inter in interictalsUncut:
        numClips = (inter[1] - inter[0]) / clipInterval
        pos = inter[0]
        while pos + clipInterval < inter[1]:
            interictals.append( (pos, pos + clipLength) )
            pos += clipInterval

    return interictals


if __name__ == '__main__':
    ptName = sys.argv[1]
    tsID = sys.argv[2]
    layerID = int(sys.argv[3])

    bf = Blackfynn()
    ts = bf.get(tsID)
    start = int(ts.start)
    end = int(ts.end)
    layer = ts.get_layer(layerID)
    
    ictals = getIctalAnnots(layer)
    interictals = getInterictalAnnots(ictals, start, end)
    makeAnnotFile(ictals, 'annotations/%s_annotations.txt' % ptName)
    makeAnnotFile(interictals, 'annotations/%s_interictal_annotations.txt' % ptName)
