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

from makeAnnots import *
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
TS_CLIP_LENGTH = 15000000 # length (usec) of each clip when testing on the entire timeseries
PREDICTION_LAYER_NAME = 'UPenn_Seizure_Detections'

ptName = sys.argv[1]
#layerID = int(sys.argv[2])
bf = Blackfynn()


### Get TimeSeries
timeseries_ids = {
    'Old_Ripley': 'N:package:8d8ebbfd-56ac-463d-a717-d48f5d318c4c',
    'R950': 'N:package:6af7dd3b-50f6-43cd-84ad-e0b3af5b636a',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}
ts = bf.get(timeseries_ids[ptName])


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
interictals = getInterictalAnnots(ictals, int(ts.start), int(ts.end))
makeAnnotFile(interictals, '%s/%s_interictal_annotations.txt' % \
                           (ANNOT_ROOT, ptName))
print ''


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
algoDataDir = ALGO_DATA_ROOT + '/' + ptName
makeDir(algoDataDir)
print 'Preparing interictal data for classifier...'
sliceClips(clipDir, 'interictal', 250, ptName)
print 'Preparing ictal data for classifier...'
sliceClips(clipDir, 'ictal', 250, ptName, trainingSz = 4)
print ''


### Prepare classifier
with open('liveAlgo/targets.json', 'w') as f:
    json.dump([ptName], f)


### Train classifier
print 'Training classifier...'
train('train_model')
print ''


### Compute cross-Validation scores
print 'Computing cross-validation scores...'
train('cv')
print ''


### Make predictions on entire timeseries
print 'Testing on entire time series...'

try:
    # Delete layer if it already exists
    # DEBUG: don't create/delete any layers yet
    layer = ts.get_layer(PREDICTION_LAYER_NAME)
    #layer.delete()
except:
    layer = ts.add_layer(PREDICTION_LAYER_NAME)

testTimeSeries(ts, layer, TS_CLIP_LENGTH, ptName, ANNOT_ROOT, clipDir)
