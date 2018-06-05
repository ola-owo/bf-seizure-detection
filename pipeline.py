#!/usr/bin/env python2
'''
Master file for downloading EEG clips and training the classifier.
Modeled after trainMaster.m from the old pipeline.

This script assumes that the Blackfynn profile has been already setup
using the command line tool.

The general pipeline flow is: Download annotation timestamps -> Pull
ictal and interictal clips -> preproccess clips for the classifier ->
Run classifier.

Usage:
> python pipeline.py ptName [layerID]
'''

import os
import sys

from blackfynn import Blackfynn

from makeAnnotFile import makeAnnotFile
from pullClips import pullClips
from sliceClips import sliceClips
from liveAlgo.seizure_detection import run_seizure_detection

ptName = sys.argv[1]
#layerID = int(sys.argv[2])

# NOTE: training_data_dir must match "competition-data-dir" in liveAlgo/SETTINGS.json
annotation_dir = 'annotations'
clip_dir = 'clips'
training_data_dir = 'seizure-data'

bf = Blackfynn()

def makeDir(dirName):
    try:
        os.makedirs(dirName)
    except:
        pass

# Get TimeSeries
timeseries_ids = {
    'R950': 'N:package:6af7dd3b-50f6-43cd-84ad-e0b3af5b636a',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}
ts = bf.get(timeseries_ids[ptName])

### Pull seizure annotation times
# makeDir(annotation_dir)
# layerName = ts.get_layer(layerID).name
# print "Pulling annotations from layer '%s'..." % layerName
# layer = ts.get_layer(layerName)
# makeAnnotFile(layer, '%s/%s_annotations.txt' % (annotation_dir, ptName))
# print 'Done.'

# TODO: Generate interictal_annotations file

### Pull clips
makeDir(clip_dir)
print 'Pulling interictal clips...'
pullClips('%s/%s_interictal_annotations.txt' % (annotation_dir, ptName),
          'interictal', ts, clip_dir)
print 'Pulling ictal clips...'
pullClips('%s/%s_annotations.txt' % (annotation_dir, ptName),
          'ictal', ts, clip_dir)
print 'Done.'

### Slice and preprocess clips
print 'Preparing data for classifier...'
sliceClips('clips', 'interictal', 250, ptName)
sliceClips('clips', 'ictal', 250, ptName)
print 'Done.'

### Train classifier
print 'Training liveAlgo classifier...'
os.chdir('liveAlgo')
run_seizure_detection('train_model')
os.chdir('..')
print 'Done. Classifier is trained ready to use.'
