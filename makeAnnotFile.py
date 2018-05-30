'''
Generates annotation files from a given annotation layer.
'''

import sys
from blackfynn import Blackfynn

bf = Blackfynn()
ts = bf.get("N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c") # 'old ripley' data
# ts = bf.get("N:package:401f556c-4747-4569-b1a8-9e6e50abf919") # 'ripley' data

def makeAnnotFile(layer, outfile):
    '''
    Write annotations from layer to outfile.
    layer is a TimeSeriesAnnotationLayer object,
    and outfile is the name of the file to write to.
    '''
    f = open(outfile, 'wt')
    n = 0
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
    layerName = sys.argv[1]
    outfile = sys.argv[2]
    layer = ts.get_layer(layerName)
    makeAnnotFile(layer, outfile)
