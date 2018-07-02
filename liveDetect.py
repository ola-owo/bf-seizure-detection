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
    LIVE_LAYER_NAME, DIARY_DB_NAME, SZ_PLOT_ROOT, TS_IDs, CHANNELS
)
from testTimeSeries import testTimeSeries
from tools import makeDir

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
        lastSz = c.execute('SELECT end FROM ' + ptName + ' ORDER BY start DESC LIMIT 1').fetchone() 
 
        # Add seizure times that aren't already in the diary
        if lastSz is None:
            startTime = 0
        else:
            startTime = lastSz[1]

        try:
            layer = ts.get_layer(LIVE_LAYER_NAME)
            anns = layer.annotations(start=startTime)
            print 'Adding', len(anns), 'new annotations to diary.'
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
        seizures = np.array(seizures) / 1000000 # convert from usecs to secs
        startTimes = [date2num(dt.datetime.utcfromtimestamp(s[0])) for s in seizures]
        endTimes = [date2num(dt.datetime.utcfromtimestamp(s[1])) for s in seizures]

        y = np.ones(seizures.shape[0])
        fig, ax = plt.subplots(1)
        ax.hlines(y, startTimes, endTimes)
        ax.vlines(startTimes, y-0.1, y+0.1)
        ax.vlines(endTimes, y-0.1, y+0.1)
        ax.xaxis.set_major_formatter(DateFormatter('%b %d %y %H:%M'))
        ax.yaxis.set_ticks(())
        fig.autofmt_xdate()
        plt.ylim(0.5, 1.5)
        plt.title('Seizure diary for ' + ptName)

        # Save plot
        szPlotDir = os.path.join(SZ_PLOT_ROOT, ptName)
        makeDir(szPlotDir)
        plt.savefig(os.path.join(szPlotDir, ptName + '.png'))
 
    conn.close()
