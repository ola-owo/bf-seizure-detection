#!/usr/bin/env python2

import os
import sys
from liveAlgo.seizure_detection import run_seizure_detection

def train(action):
    os.chdir('liveAlgo')
    run_seizure_detection(action)
    os.chdir('..')

if __name__ == '__main__':
    action = sys.argv[1]
    train(action)
