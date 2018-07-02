#!/usr/bin/env python2
'''
"Cron" job to automatically check for new data and annotate

Usage:
python cron.py linelength|pipeline

The "linelength" option uses the line length detector,
while the "pipeline" option uses the pipeline and liveAlgo classifier.
'''
import time
import sys

import schedule

from settings import DETECTION_INTERVAL
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
else:
    raise ValueError("Invalid algo option '%s'" % algo)

def getTime():
    'Get the current time, in usecs'
    t = DT.datetime.utcnow() - DT.timedelta(minutes=DETECTION_INTERVAL)
    t = (t - EPOCH).total_seconds() * 1000000
    return t
    
def detectJob():
    print '=== Running %s classifier at time %s ===' % (algo, timeString(detectJob.startTime))
    detectJob.startTime = liveDetect.detect(bf, detectJob.startTime, algo)
    sys.stdout.flush() # make sure all print statements are outputted by this point
    print '=== Up to date as of', timeString(detectJob.startTime), '==='

detectJob.startTime = getTime() - DETECTION_INTERVAL * 60000000

def diaryJob():
    print '=== Updating seizure diaries ==='
    liveDetect.diary(bf)
    sys.stdout.flush() # make sure all print statements are outputted by this point

schedule.every(DETECTION_INTERVAL).minutes.do(detectJob)
schedule.every().day.at('00:00').do(diaryJob)

while True:
    schedule.run_pending()
    time.sleep(1)
