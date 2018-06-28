#!/usr/bin/env python2
'''
"Cron" job to automatically check for new data and annotate

Usage:
python cron.py linelength|pipeline

The "linelength" option uses the line length detector,
while the "pipeline" option uses the pipeline and liveAlgo classifier.
'''
import time

import schedule

from tools import timeString
import liveDetect
import datetime as DT


EPOCH = DT.datetime(1970,1,1)
DETECTION_INTERVAL = 30 # minutes

algo = sys.argv[1]
if algo == 'pipeline':
    print '=== Using pipeline ==='
elif algo == 'linelength'
    print '=== Using line length detector ==='
else:
    raise ValueError("Invalid algo option '%s'" % algo)

startTime = DT.datetime.utcnow() - DT.timedelta(minutes=DETECTION_INTERVAL)
startTime = (startTime - EPOCH).total_seconds() * 1000000

def detectJob():
    print '=== Running %s classifier from time %s ===' % (algo, timeString(startTime))
    startTime = liveDetect.detect(startTime, algo)
    print '=== Up to date as of', timeString(startTime), '==='
    time.sleep(DETECTION_INTERVAL * 60)

def diaryJob():
    print '=== Updating seizure diaries ==='
    liveDetect.diary()

schedule.every(DETECTION_INTERVAL).minutes.do(detectJob)
schedule.every().day.at('00:00').do(diaryJob)

while True:
    schedule.run_pending()
    time.sleep(1)
