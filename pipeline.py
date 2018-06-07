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
NOTE: The patient name must be uncommented in list "targets" in liveAlgo/seizure_detection.py
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

# NOTE: ALGO_DATA_ROOT must match "competition-data-dir" in liveAlgo/SETTINGS.json
ANNOT_ROOT = 'annotations'
CLIP_ROOT = 'clips'
ALGO_DATA_ROOT = 'seizure-data'

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
# makeDir(ANNOT_ROOT)
# layerName = ts.get_layer(layerID).name
# print "Pulling annotations from layer '%s'..." % layerName
# layer = ts.get_layer(layerName)
# makeAnnotFile(layer, '%s/%s_annotations.txt' % (ANNOT_ROOT, ptName))
# print 'Done.'

# TODO: Generate interictal_annotations file

### Pull clips
clipDir = CLIP_ROOT + '/' + ptName
makeDir(clipDir)
print 'Pulling interictal clips...'
pullClips('%s/%s_interictal_annotations.txt' % (ANNOT_ROOT, ptName),
          'interictal', ts, clipDir)
print 'Pulling ictal clips...'
pullClips('%s/%s_annotations.txt' % (ANNOT_ROOT, ptName),
          'ictal', ts, clipDir)
print ''

### Slice and preprocess clips
makeDir(ALGO_DATA_ROOT + '/' + ptName)
print 'Preparing interictal data for classifier...'
sliceClips(clipDir, 'interictal', 250, ptName)
print 'Preparing ictal data for classifier...'
sliceClips(clipDir, 'ictal', 250, ptName)
print ''

### Train classifier
print 'Training liveAlgo classifier...'
os.chdir('liveAlgo')
run_seizure_detection('train_model')
print 'Done. Classifier is trained and ready to use.'

### Cross-Validate the classifier
print 'Running cross validation test...'
run_seizure_detection('cv')
os.chdir('..')
print 'Pipeline finished.'
