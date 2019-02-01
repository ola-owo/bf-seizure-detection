#!/usr/bin/env python3
'''
Automatically checks for new data and tests it for seizures
'''
from glob import glob
import re

import annots
from dashplot import updateDB
from helper_scripts import makeKeyPP, metrics
from lineLength import lineLength
from lineLengthMA import lineLength as maLineLength
from pipeline import pipeline
from settings import (
    GOLD_STD_LAYERS, LL_LAYER_NAME, LL_MA_LAYER_NAME, PL_LAYER_NAME, PL_ROOT, TS_IDs
)
from testTimeSeries import testTimeSeries

PTNAME_REGEX = re.compile(r'^[\w-]+$') # only allow letters, numbers, and "-" in patient name

annotDir = PL_ROOT + '/annotations'
clipDir = PL_ROOT + '/clips'

def detect(bf, ptName, startTime, endTime, algo):
    '''
    Run classifier on all patients, starting from startTime.

    algo should either be 'linelength' or 'pipeline'
    (other classifiers might be added in the future)
    '''

    # Make sure startTime is valid
    if startTime >= endTime:
        raise ValueError("startTime %d is in the future." % startTime)

    try:
        ts = bf.get(TS_IDs[ptName])
    except Exception as e: # TODO: should probably make this more specific
        print("Error getting timeseries for patient '" + ptName + "':")
        print(e)
        return startTime

    if algo == 'linelength':
        lineLength(ptName, startTime, endTime, append=True, layerName=LL_LAYER_NAME)
        return endTime
    elif algo == 'ma_linelength':
        t = maLineLength(ptName, startTime, endTime, append=True, layerName=LL_MA_LAYER_NAME)
        return t
    elif algo == 'pipeline':
        # Train liveAlgo if classifier doesn't already exist
        classifier_exists = bool(glob(PL_ROOT + '/data-cache/classifier_' + ptName + '_*'))
        if not classifier_exists:
            pipeline(ptName, annotating=False, bf=bf)

        layer = ts.add_layer(PL_LAYER_NAME)
        testTimeSeries(ts, layer, ptName, startTime=startTime, endTime=endTime, annotating=True)
        return endTime
    else:
        raise ValueError("Invalid classifier option '%s'" % algo)

def diary(bf, algo):
    '''
    Update all patients' seizure diaries.
    This should automatically run daily.
    '''
    if algo == 'linelength':
        liveLayerName = LL_LAYER_NAME
    elif algo == 'ma_linelength':
        liveLayerName = LL_MA_LAYER_NAME
    elif algo == 'pipeline':
        liveLayerName = PL_LAYER_NAME
    else:
        raise ValueError("Invalid classifier option '%s'" % algo)

    patients = sorted(TS_IDs)
    for pt in patients:
        print('Current patient:', pt)
        print('Updating seizure diary')
        updateDB(bf, pt, algo)

        if algo == 'pipeline': # TODO: implement this for the other classifiers
            print('Updating performance stats')
            ts = bf.get(TS_IDs[pt])

            # update ictal annotations file
            if pt not in GOLD_STD_LAYERS:
                print('Skipping patient', pt, '(no gold standard layer)')
                continue
            goldLayer = ts.get_layer(GOLD_STD_LAYERS[pt])
            anns = annots.getIctalAnnots(goldLayer)
            if not anns:
                print('Skipping patient', pt, '(no gold standard annotations)')
                continue
            annots.makeAnnotFile(anns, '%s/%s_annotations.txt' % (annotDir, pt))

            # run makeKey
            logFile = pt + '_seizures.txt'
            try:
                makeKeyPP.makeKey(pt, logFile)
            except IOError:
                print('Skipping patient', pt, '(log file not found)')
                continue

            # run metrics and save [patient]_roc.hkl
            keyFile = pt + '_key.csv'
            predFile = pt + '_preds.csv'
            metrics.printMetrics(keyFile, predFile, pt, printReport=False)
