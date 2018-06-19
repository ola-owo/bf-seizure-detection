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

import json
import sys

from blackfynn import Blackfynn

from annots import *
from pullClips import pullClips
from sliceClips import sliceClips
from testTimeSeries import testTimeSeries
from train import train
from tools import *


### NOTE: ALGO_DATA_ROOT must match the value of competition-data-dir
### in liveAlgo/SETTINGS.json
ANNOT_ROOT = 'annotations'
CLIP_ROOT = 'clips'
ALGO_DATA_ROOT = 'seizure-data'
PREDICTION_LAYER_NAME = 'UPenn_Seizure_Detections'

ptName = sys.argv[1]
bf = Blackfynn()


### Get TimeSeries
timeseries_ids = {
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R950': 'N:package:6af7dd3b-50f6-43cd-84ad-e0b3af5b636a',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}
ts = bf.get(timeseries_ids[ptName])
segments = ts.segments()


### Get annotation layer containing the seizures to train from
layer_ids = {
    'Old_Ripley': 16,
    'R950': 143,
    'Ripley': 10,
    'UCD2': 450,
}
layer = ts.get_layer(layer_ids[ptName])
layerName = layer.name

### Pull ictal and interictal annotation times
print "Pulling annotations from layer '%s'..." % layerName
makeDir(ANNOT_ROOT)
ictals = getIctalAnnots(layer)
makeAnnotFile(ictals, '%s/%s_annotations.txt' % (ANNOT_ROOT, ptName))

print 'Generating interictal annotations...'
interictals = getInterictalAnnots(ictals, segments)
makeAnnotFile(interictals, '%s/%s_interictal_annotations.txt' % \
                           (ANNOT_ROOT, ptName))
print ''


### Pull clips
clipDir = CLIP_ROOT + '/' + ptName
makeDir(clipDir)
print 'Pulling ictal clips...'
pullClips('%s/%s_annotations.txt' % (ANNOT_ROOT, ptName),
          'ictal', ts, clipDir)
print 'Pulling interictal clips...'
pullClips('%s/%s_interictal_annotations.txt' % (ANNOT_ROOT, ptName),
          'interictal', ts, clipDir)
print ''


### Slice and preprocess clips
algoDataDir = ALGO_DATA_ROOT + '/' + ptName
makeDir(algoDataDir)
print 'Preparing ictal data for classifier...'
sliceClips(clipDir, 'ictal', 250, ptName, trainingSz = 4)
print 'Preparing interictal data for classifier...'
sliceClips(clipDir, 'interictal', 250, ptName)
print ''


### Prepare classifier
with open('liveAlgo/targets.json', 'w') as f:
    json.dump([ptName], f)


### Train classifier
print 'Training classifier...'
train('train_model', target=ptName)
print ''


### Compute cross-Validation scores
print 'Computing cross-validation scores...'
train('cv', target=ptName)
print ''


### Make predictions on entire timeseries
print 'Testing on entire time series...'

### DEBUG: comment out this block when not uploading annotatins to blackfynn
try:
    # Delete layer if it already exists
    layer = ts.get_layer(PREDICTION_LAYER_NAME)
    layer.delete()
    layer = ts.add_layer(PREDICTION_LAYER_NAME)
except:
    layer = ts.add_layer(PREDICTION_LAYER_NAME)

testTimeSeries(ts, layer, ptName, ANNOT_ROOT, clipDir, annotating=True)
#testTimeSeries(ts, None, ptName, ANNOT_ROOT, clipDir, annotating=False) # DEBUG
