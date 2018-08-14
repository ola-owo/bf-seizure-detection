#!/usr/bin/env python2
'''
Automatically checks for new data and tests it for seizures
'''
import datetime as dt
import glob
import os.path
import re
import sqlite3

from blackfynn import Blackfynn
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, date2num
import numpy as np

# Workaround for blackfynn server errors:
from requests.exceptions import RequestException

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
        testTimeSeries(ts, layer, ptName, startTime=startTime, endTime=endTime, annotating=True)
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
    conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()

    for ptName in patients:
        print 'Updating seizure diary for', ptName
        ts = bf.get(TS_IDs[ptName])

        # Make sure patient name is valid
        if not re.match(PTNAME_REGEX, ptName):
            raise Exception('Invalid patient name - must only contain letters, numbers, underscores, and/or dashes') 

        # Get most recent seizure in diary
        c.execute('CREATE TABLE IF NOT EXISTS ' + ptName + ' (start INT, end INT)')
        lastSz = c.execute('SELECT start, end FROM ' + ptName + ' ORDER BY end DESC LIMIT 1').fetchone() 
 
        # Add seizure times that aren't already in the diary
        if lastSz is None:
            startTime = 0
        else:
            startTime = lastSz[1]

        try:
            layer = ts.get_layer(liveLayerName)
            anns = layer.annotations(start=startTime)
            if anns:
                print 'Adding', len(anns), 'new annotations to diary.'
            else:
                print 'No new annotations to add.'
            for ann in anns:
                c.execute('INSERT INTO ' + ptName + ' VALUES (?,?)', (ann.start, ann.end))
            conn.commit()
        except: # if layer doesn't exist:
            print 'No new annotations to add.'

        # Plot all seizures
        seizures = c.execute('SELECT start, end FROM ' + ptName).fetchall()
        if not seizures:
            print 'No seizures to plot.'
            continue

        ## auto-detected seizures:
        fig, ax = plt.subplots(1)
        seizures = np.array(seizures)
        _plot(ax, seizures, 0.7, 'Auto-detected seizures', 'b')

        ## gold standard seizures (if any):
        layerID = GOLD_STD_LAYERS.get(ptName, None)
        if layerID is not None:
            layer = ts.get_layer(layerID)
            goldSeizures = np.array([(a.start, a.end) for a in layer.annotations()])
            _plot(ax, goldSeizures, 0.3, 'Gold standard seizures', 'g')

        ax.xaxis.set_major_formatter(DateFormatter('%b %d %y %H:%M'))
        ax.yaxis.set_ticks(())
        ax.grid()
        ax.legend()
        fig.autofmt_xdate()
        plt.ylim(0.0, 1.0)
        plt.title('Seizure diary for ' + ptName)

        # Save plot
        imgName = ptName + '.png'
        plt.savefig(SZ_PLOT_ROOT + '/' + imgName)
        print imgName, 'saved in', SZ_PLOT_ROOT + '/'
        plt.close()
 
    conn.close()

def _plot(ax, seizures, height, label, color):
    'Helper function for diary()'
    convertTime = lambda x: date2num(dt.datetime.utcfromtimestamp(x / 1000000))
    startTimes = map(convertTime, seizures[:,0]) # convert to matplotlib time format:
    endTimes = map(convertTime, seizures[:,1])
    y = np.full_like(seizures.shape[0], height, dtype='float64')

    ax.vlines(startTimes, y-0.1, y+0.1, colors=color)
    ax.vlines(endTimes, y-0.1, y+0.1, colors=color)
    ax.hlines(y, startTimes, endTimes, label=label, colors=color)
