#!/usr/bin/env python2
'''
Automatically checks for new data and tests it for seizures
'''
import datetime as dt
import glob
import os.path
import re

from blackfynn import Blackfynn
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, date2num
import numpy as np

# Workaround for blackfynn server errors:
from requests.exceptions import RequestException

from dashplot import updateDB
from lineLength import lineLength
from lineLengthMA import lineLength as maLineLength
from pipeline import pipeline
from settings import (
    CHANNELS, DIARY_DB_NAME, GOLD_STD_LAYERS, LIVE_UPDATE_TIMES, LL_LAYER_NAME,
    LL_MA_LAYER_NAME, PL_LAYER_NAME, PL_ROOT, SZ_PLOT_ROOT, TS_IDs
)
from testTimeSeries import testTimeSeries
from tools import makeDir

# Allows pyplot to work without a display:
plt.switch_backend('agg')

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
        print "Error getting timeseries for patient '" + ptName + "':"
        print e
        return startTime
    ch = CHANNELS.get(ptName, None)

    if algo == 'linelength':
        lineLength(ptName, startTime, endTime, append=True, layerName=LL_LAYER_NAME)
        return endTime
    elif algo == 'ma_linelength':
        t = maLineLength(ptName, startTime, endTime, append=True, layerName=LL_MA_LAYER_NAME)
        return t
    elif algo == 'pipeline':
        # Train liveAlgo if classifier doesn't already exist
        classifier_exists = bool(glob.glob(PL_ROOT + '/data-cache/classifier_' + ptName + '_*'))
        if not classifier_exists:
            pipeline(ptName, annotating=False, bf=bf)

        layer = ts.add_layer(PL_LAYER_NAME)
        testTimeSeries(ts, layer, ptName, startTime=startTime, endTime=endTime, logging=False, annotating=True)
        return endTime
    else:
        raise ValueError("Invalid classifier option '%s'" % algo)

def diary(bf, algo):
    '''
    Updates the patient's seizure diary.
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

    patients = sorted(TS_IDs.keys())
    for pt in patients:
        print 'Updating seizure diary for', pt
        updatePatient(bf, algo, pt)
