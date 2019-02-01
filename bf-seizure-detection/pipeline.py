#!/usr/bin/env python3
'''
Master file for downloading EEG clips and training the classifier.
Modeled after trainMaster.m from the old pipeline.

This script assumes that the Blackfynn profile has been already setup
using the command line tool.

The general pipeline flow is: Download annotation timestamps -> Pull
ictal and interictal clips -> preproccess clips for the classifier ->
Run classifier.

Usage:
> python pipeline.py ptName [startTime [endTime]] [annotate]
Use 'start' in place of startTime to go from the beginning until endTime
'''

import json
import sys
from time import sleep

from blackfynn import Blackfynn
from requests.exceptions import RequestException

from annots import *
from pullClips import pullClips
from sliceClips import sliceClips
from settings import (
    CHANNELS, DEFAULT_FREQ, FREQs, GOLD_STD_LAYERS, PL_LAYER_NAME, PL_ROOT,
    TRAINING_SZ_LIMIT, TS_IDs
)
from testTimeSeries import testTimeSeries
from train import train
from tools import *

def pipeline(ptName, annotating=True, startTime=None, endTime=None, bf=None):
    ch = CHANNELS.get(ptName, None)
    freq = FREQs.get(ptName, DEFAULT_FREQ)

    ### Get patient-specific settings
    if bf is None: # WORKAROUND: see cron.py
        bf = Blackfynn()
    ts = bf.get(TS_IDs[ptName])

    while True:
        try:
            segments = ts.segments()
            break
        except RequestException:
            sleep(2)
            continue
        
    layer = ts.get_layer(GOLD_STD_LAYERS[ptName])
    layerName = layer.name

    ### Pull ictal and interictal annotation times
    print("Reading annotations from layer '%s'..." % layerName)
    annotDir = PL_ROOT + '/annotations'
    makeDir(annotDir)
    ictals = getIctalAnnots(layer)
    makeAnnotFile(ictals, '%s/%s_annotations.txt' % (annotDir, ptName))

    print('Generating interictal annotations...')
    interictals = getInterictalAnnots(ictals, segments)
    makeAnnotFile(interictals, '%s/%s_interictal_annotations.txt' % \
                               (annotDir, ptName))
    print('')
    sys.stdout.flush()


    ### Pull clips
    clipDir = PL_ROOT + '/clips/' + ptName
    makeDir(clipDir)
    print('Pulling ictal clips...')
    pullClips('%s/%s_annotations.txt' % (annotDir, ptName),
              'ictal', ts, clipDir, ch, limit=TRAINING_SZ_LIMIT)
    print('Pulling interictal clips...')
    pullClips('%s/%s_interictal_annotations.txt' % (annotDir, ptName),
              'interictal', ts, clipDir, ch)
    print('')
    sys.stdout.flush()

    ### Slice and preprocess clips
    algoDataDir = PL_ROOT + '/seizure-data/' + ptName
    makeDir(algoDataDir)
    print('Preparing ictal data for classifier...')
    sliceClips(clipDir, 'ictal', freq, ptName)
    print('Preparing interictal data for classifier...')
    sliceClips(clipDir, 'interictal', freq, ptName)
    print('')
    sys.stdout.flush()


    ### Prepare classifier
    #with open('liveAlgo/targets.json', 'w') as f:
    #    json.dump([ptName], f)


    ### Train classifier
    print('Training classifier...')
    train('train_model', target=ptName)
    print('')
    sys.stdout.flush()


    ### Compute cross-Validation scores
    print('Computing cross-validation scores...')
    train('cv', target=ptName)
    print('')
    sys.stdout.flush()

    if annotating:
        ### Make predictions on entire timeseries
        print('Testing on entire time series...')

        try:
            # Delete layer if it already exists
            layer = ts.get_layer(PL_LAYER_NAME)
            layer.delete()
        except:
            pass
        finally:
            layer = ts.add_layer(PL_LAYER_NAME)

        testTimeSeries(ts, layer, ptName, startTime, endTime)

        ### Use "annotating=False" option if you're not writing annotations to Blackfynn
        # testTimeSeries(ts, None, ptName, startTime, endTIme, annotating=False)

if __name__ == '__main__':
    num_args = len(sys.argv) - 1

    ptName = sys.argv[1]

    try:
        startTime = int(sys.argv[2])
    except (IndexError, ValueError):
        startTime = None

    try:
        endTime = int(sys.argv[3])
    except (IndexError, ValueError):
        endTime = None

    annotating = ('annotate' in sys.argv[2:])
    pipeline(ptName, annotating, startTime, endTime)
