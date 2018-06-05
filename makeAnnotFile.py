'''
Generates annotation files from a given annotation layer.
This script can also be called standalone with:
> python makeAnnonationFile.py outFile timeseriesID layerName
'''

import os
import sys
from blackfynn import Blackfynn

def makeAnnotFile(layer, outFile):
    '''
    Write annotations from layer to outFile.
    layer is a TimeSeriesAnnotationLayer object,
    and outFile is the name of the file to write to.
    '''
    n = 0
    f = open(outFile, 'wt')
    try:
        annots = layer.annotations()
        if not annots:
            print 'makeAnnotFile(): no annotations to write'
            return
        for annot in annots:
            f.write('%d %d\n' % (annot.start, annot.end))
            n = n + 1
    finally:
        f.close()
        print '%d annotations written to file.' % n

if __name__ == '__main__':
    # ptName = sys.argv[1]
    # layerName = sys.argv[2]
    # outFile = sys.argv[3]
    outFile = sys.argv[1]
    tsID = sys.argv[2]
    layerName = sys.argv[3]

    bf = Blackfynn()
    ts = bf.get(tsID)
    layer = ts.get_layer(layerName)
    makeAnnotFile(layer, outFile)
