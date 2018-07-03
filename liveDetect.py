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

from lineLength import lineLength
from pipeline import pipeline
from settings import (
    CHANNELS, LIVE_LAYER_NAME, DIARY_DB_NAME, GOLD_STD_LAYERS, SZ_PLOT_ROOT, TS_IDs
)
from testTimeSeries import testTimeSeries
from tools import makeDir

# Allows pyplot to work without a display:
plt.switch_backend('agg')

EPOCH = dt.datetime(1970,1,1)
PTNAME_REGEX = re.compile(r'^[\w-]+$') # only allow letters, numbers, and "-" in patient name

patients = sorted(TS_IDs.keys())

def detect(bf, startTime, algo):
    '''
    Run classifier on all patients, starting from startTime.

    algo should either be 'linelength' or 'pipeline'
    (other classifiers might be added in the future)
    '''

    # Make sure startTime is valid
    now = dt.datetime.utcnow()
    endTime = int((now - EPOCH).total_seconds() * 1000000) # convert to epoch usecs
    if startTime >= endTime:
        raise ValueError("Time %d hasn't happened yet" % startTime)

    # Loop through each patient
    for ptName in patients:
        print 'Testing patient', ptName
        try:
            ts = bf.get(TS_IDs[ptName])
        except Exception as e: # should probably make this more specific
            print 'Error getting timeseries from Blackfynn:', e
            continue
        ch = CHANNELS.get(ptName, None)

        if algo == 'linelength':
            lineLength(ts, ch, startTime, endTime, append=True, layerName=LIVE_LAYER_NAME)
        elif algo == 'pipeline':
            # Train liveAlgo if classifier doesn't already exist
            classifier_exists = bool(glob.glob('data-cache/classifier_' + ptName + '_*'))
            if not classifier_exists:
                pipeline(ptName, annotating=False, bf=bf)

            layer = ts.add_layer(LIVE_LAYER_NAME)
            testTimeSeries(ts, layer, ptName, 'annotations', 'clips', startTime=startTime, endTime=endTime, logging=False, annotating=True)
        else:
            raise ValueError("Invalid classifier option '%s'" % algo)

    return endTime

def diary(bf):
    '''
    Updates the patient's seizure diary.
    This should automatically run daily.
    '''
    #today = dt.date.today().isoformat()
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
            layer = ts.get_layer(LIVE_LAYER_NAME)
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

        fig, ax = plt.subplots(1)

        ## auto-detected seizures:
        seizures = np.array(seizures)
        _plot(ax, seizures, 'Auto-detected seizures', 'b')

        ## gold standard seizures (if any):
        layerID = GOLD_STD_LAYERS.get(ptName, None)
        if layerID is not None:
            layer = ts.get_layer(layerID)
            goldSeizures = np.array([(a.start, a.end) for a in layer.annotations()])
            _plot(ax, goldSeizures, 'Gold standard seizures', 'g')

        ax.xaxis.set_major_formatter(DateFormatter('%b %d %y %H:%M'))
        ax.yaxis.set_ticks(())
        ax.grid()
        ax.legend()
        fig.autofmt_xdate()
        plt.ylim(0.5, 1.5)
        plt.title('Seizure diary for ' + ptName)

        # Save plot
        szPlotDir = os.path.join(SZ_PLOT_ROOT, ptName)
        imgName = ptName + '.png'
        makeDir(szPlotDir)
        plt.savefig(os.path.join(szPlotDir, imgName))
        print imgName, 'saved in', szPlotDir
 
    conn.close()

def _plot(ax, seizures, label, color):
    'Helper function for diary()'
    convertTime = lambda x: date2num(dt.datetime.utcfromtimestamp(x / 1000000))
    startTimes = map(convertTime, seizures[:,0]) # convert to matplotlib time format:
    endTimes = map(convertTime, seizures[:,1])
    y = np.ones(seizures.shape[0])

    ax.vlines(startTimes, y-0.1, y+0.1, colors=color)
    ax.vlines(endTimes, y-0.1, y+0.1, colors=color)
    ax.hlines(y, startTimes, endTimes, label=label, colors=color)
