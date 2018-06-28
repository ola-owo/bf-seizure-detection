#!/usr/bin/env python2
'''
Automatically checks for new data and tests it for seizures
'''
import datetime as DT
import re
import sqlite3

from blackfynn import Blackfynn
from matplotlib.dates import DateFormatter, date2num
import numpy as np

from lineLength import lineLength
from pipeline import pipeline
from testTimeSeries import testTimeSeries

EPOCH = DT.datetime(1970,1,1)
LIVE_LAYER_NAME = 'UPenn_Live_Detect'
DIARY_DB_NAME = 'diaries.db'
PTNAME_REGEX = re.compile(r'^[A-Za-z0-9_-]*$')

patients = [
    # Patients are tested in the order listed below.
    # Note: each patient must also be listed in TS_IDs
    'R950',
    'R951',
    'Ripley',
    'UCD2',
]

TS_IDs = {
    'R950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

channels_lists = { 
    'Ripley': [ 
        'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
        'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
        'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
        'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
    ],
}

bf = Blackfynn()

def detect(startTime, algo):
    '''
    Run classifier on all patients, starting from startTime.

    algo should either be 'linelength' or 'pipeline'
    (other classifiers might be added in the future)
    '''

    # Make sure startTime is valid
    now = DT.datetime.utcnow()
    endTime = int((now - EPOCH).total_seconds() * 1000000) # convert to epoch usecs
    if startTime >= endTime:
        raise ValueError("Time %d hasn't happened yet" % startTime)

    # Loop through each patient
    for ptName in patients:
        print 'Testing patient', ptName
        ts = bf.get(TS_IDs[ptName])
        ch = channels_lists.get(ptName, None)

        if algo == 'linelength':
            lineLength(ts, ch, startTime, endTime, append=True, layer=LIVE_LAYER_NAME)
        elif algo == 'pipeline':
            # Train liveAlgo if classifier doesn't already exist
            classifier_exists = bool(glob.glob('data-cache/classifier_' + ptName + '_*'))
            if not classifier_exists:
                pipeline.pipeline(ptName, annotating=False)

            layer = ts.add_layer(LIVE_LAYER_NAME)
            testTimeSeries(ts, layer, ptName, 'annotations', 'clips', startTime=startTime, endTime=endTime, logging=False, annotating=True)
        else:
            raise ValueError("Invalid classifier option '%s'" % algo)

    return endTime

def diary():
    '''
    Updates the patient's seizure diary.
    This should automatically run daily.
    '''
    conn = sqlite3.connect(DIARY_DB_NAME)
    c = conn.cursor()

    for ptName in patients:
        print 'Updating seizure diary for', ptName
        ts = bf.get(TS_IDs[ptName])

        # Make sure patient name is valid
        if re.match(PTNAME_REGEX, ptName):
            raise Exception('Invalid patient name - must only contain letters, numbers, underscores, and/or dashes') 

        # Get most recent seizure in diary
        c.execute('CREATE TABLE IF NOT EXISTS ' + ptName + ' (start INT, end INT)')
        lastSz = c.execute('SELECT end FROM ' + ptName + ' ORDER BY start DESC LIMIT 1').fetchone() 
 
        # Add blackfynn annotations that aren't already in the diary
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
        except:
            print 'No new annotations to add.'

        # Plot all seizures
        seizures = c.execute('SELECT start, end FROM ' + ptName).fetchall()
        if seizures is None: seizures = []
        startTimes = [date2num(DT.datetime.utcfromtimestamp(s[0])) for s in seizures]
        endTimes = [date2num(DT.datetime.utcfromtimestamp(s[1])) for s in seizures]

        y = np.ones(len(seizures))
        plt.hlines(y, startTimes, endTimes)
        plt.vlines(startTimes, y-0.1, y+0.1)
        plt.vlines(endTimes, y-0.1, y+0.1)
        ax = plt.gca()
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(DateFormatter('%b %d %y %H:%M:%S')) # Formatted as: Jan 01 98 12:34:56
        ax.xaxis.set_major_locator(DayLocator(interval=1))
        plt.ylim(0,2)
        plt.xlim(startTimes[0] - 30, endTimes[-1] + 30)
        plt.xlabel('Time')
        plt.ylabel('Seizures')
        plt.show()
 
    conn.close()
