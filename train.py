#!/usr/bin/env python2

import os
import sys
from liveAlgo.seizure_detection import run_seizure_detection

tgt = sys.argv[1]
os.chdir('liveAlgo')
if tgt == 'train':
    run_seizure_detection('train_model')
elif tgt == 'cv':
    run_seizure_detection('cv')
elif tgt == 'predict':
    run_seizure_detection('make_predictions')
else:
    print "Invalid action '%s'" % tgt
