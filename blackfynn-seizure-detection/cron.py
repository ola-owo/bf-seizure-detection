#!/usr/bin/env python2
'''
"Cron" job to automatically check for new data and annotate

Usage:
python cron.py algo

The "algo" option specifies which classifier to use:
"linelength" uses the line length detector,
"ma_linelength" uses the moving average line length detector,
and "pipeline" uses the random forest pipeline/classifier.
'''
import json
import sys
import time

# Workaround for occasional blackfynn server errors:
from requests.exceptions import RequestException

import schedule

from settings import DETECTION_INTERVAL, LIVE_UPDATE_TIMES
from tools import timeString
import liveDetect
import datetime as DT

# BUG WORKAROUND: Initialize blackfynn here and pass it to the liveDetect functions
from blackfynn import Blackfynn
bf = Blackfynn()

EPOCH = DT.datetime(1970,1,1)

algo = sys.argv[1]
if algo == 'pipeline':
    print '=== Using pipeline ==='
elif algo == 'linelength':
    print '=== Using line length detector ==='
elif algo == 'ma_linelength':
    print '=== Using MA line length detector ==='
else:
    raise ValueError("Invalid classifier option '%s'" % algo)

with open(LIVE_UPDATE_TIMES, 'r') as f:
    lastUpdated = json.load(f)

def detectJob():
    global lastUpdated
    startTime = lastUpdated[algo]
    print '=== Running %s classifier from %s ===' % (algo, timeString(startTime))
    try:
        endTime = liveDetect.detect(bf, startTime, algo)
        lastUpdated[algo] = endTime
        print '=== Up to date as of', timeString(endTime), '==='
    except RequestException as e:
        print '=== Error running classifier ==='
        print e
    sys.stdout.flush() # make sure all print statements are outputted by this point
    with open(LIVE_UPDATE_TIMES, 'w') as f:
        json.dump(lastUpdated, f)

def diaryJob():
    print '=== Updating seizure diaries ==='
    try:
        liveDetect.diary(bf, algo)
        print '=== Seizure diaries are up to date ==='
    except Exception as e:
        print '=== Error updating diary ==='
        print e
    sys.stdout.flush() # make sure all print statements are outputted by this point

schedule.every(DETECTION_INTERVAL).minutes.do(detectJob)
schedule.every().day.at('00:00').do(diaryJob)

while True:
    schedule.run_pending()
    time.sleep(1)
