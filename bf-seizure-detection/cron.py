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

from settings import DETECTION_INTERVAL, LIVE_UPDATE_TIMES, TS_IDs
from tools import getTime, timeString
import liveDetect
import datetime as DT

# BUG WORKAROUND: Initialize blackfynn here and pass it to the liveDetect functions
from blackfynn import Blackfynn
bf = Blackfynn()

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
    endTime = getTime()
    print '=== Running %s classifier until %s ===' % (algo, endTime)
    patients = sorted(TS_IDs.keys())
    for ptName in patients:
        startTime = lastUpdated[algo][ptName]
        print '=== Testing patient', ptName, 'from', timeString(startTime), '==='
        try:
            newStartTime = liveDetect.detect(bf, ptName, startTime, endTime, algo)
            lastUpdated[algo][ptName] = newStartTime
        except RequestException as e:
            print '=== Server error (will try again later) ==='
            print e
            continue
        except:
            with open(LIVE_UPDATE_TIMES, 'w') as f:
                json.dump(lastUpdated, f)
            raise
        print '=== Up to date as of', timeString(endTime), '==='
        sys.stdout.flush() # make sure all print statements are outputted by this point
    print '=== Done running classifier on all patients ==='
    sys.stdout.flush()
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
