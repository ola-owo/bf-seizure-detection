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
> python pipeline.py ptName [annotate [startTime [endTime]]]
Use 'start' in place of startTime to go from the beginning until endTime
'''

import json
import sys

from blackfynn import Blackfynn

from annots import *
from pullClips import pullClips
from sliceClips import sliceClips
from settings import (
    ALGO_DATA_ROOT, ANNOT_ROOT, CHANNELS, CLIP_ROOT,
    FREQ, GOLD_STD_LAYERS, PL_LAYER_NAME, TRAINING_SZ_LIMIT, TS_IDs
)
from testTimeSeries import testTimeSeries
from train import train
from tools import *

def pipeline(ptName, annotating=True, startTime=None, endTime=None, bf=None):
    ### Get patient-specific settings
    if bf is None: # WORKAROUND: see crontest.py
        bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])
    segments = ts.segments()
    layer = ts.get_layer(GOLD_STD_LAYERS[ptName])
    layerName = layer.name
    ch = CHANNELS.get(ptName, None)

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
    sys.stdout.flush()


    ### Pull clips
    clipDir = CLIP_ROOT + '/' + ptName
    makeDir(clipDir)
    print 'Pulling ictal clips...'
    pullClips('%s/%s_annotations.txt' % (ANNOT_ROOT, ptName),
              'ictal', ts, clipDir, ch, limit=TRAINING_SZ_LIMIT)
    print 'Pulling interictal clips...'
    pullClips('%s/%s_interictal_annotations.txt' % (ANNOT_ROOT, ptName),
              'interictal', ts, clipDir, ch)
    print ''
    sys.stdout.flush()

    ### Slice and preprocess clips
    algoDataDir = ALGO_DATA_ROOT + '/' + ptName
    makeDir(algoDataDir)
    print 'Preparing ictal data for classifier...'
    sliceClips(clipDir, 'ictal', FREQ, ptName)
    print 'Preparing interictal data for classifier...'
    sliceClips(clipDir, 'interictal', FREQ, ptName)
    print ''
    sys.stdout.flush()


    ### Prepare classifier
    with open('liveAlgo/targets.json', 'w') as f:
        json.dump([ptName], f)


    ### Train classifier
    print 'Training classifier...'
    train('train_model', target=ptName)
    print ''
    sys.stdout.flush()


    ### Compute cross-Validation scores
    print 'Computing cross-validation scores...'
    train('cv', target=ptName)
    print ''
    sys.stdout.flush()

    if annotating:
        ### Make predictions on entire timeseries
        print 'Testing on entire time series...'

        try:
            # Delete layer if it already exists
            layer = ts.get_layer(PL_LAYER_NAME)
            layer.delete()
        finally:
            layer = ts.add_layer(PL_LAYER_NAME)

        testTimeSeries(ts, layer, ptName, ANNOT_ROOT, clipDir, startTime, endTime)

        ### Use "annotating=False" option if you're not writing annotations to Blackfynn
        # testTimeSeries(ts, None, ptName, ANNOT_ROOT, clipDir, startTime, endTIme, annotating=False)

if __name__ == '__main__':
    num_args = len(sys.argv) - 1

    ptName = sys.argv[1]

    if num_args >= 2:
        annotating = (sys.argv[2] == 'annotate')
    else:
        annotating = False

    if num_args >= 3:
        startTime = int(sys.argv[3])
    else:
        startTime = None

    if num_args >= 4:
        endTime = int(sys.argv[4])
    else:
        endTime = None

    pipeline(ptName, annotating, startTime, endTime)
