#!/usr/bin/env python3

import os
import sys
from liveAlgo.seizure_detection import run_seizure_detection

def train(action, target=None):
    os.chdir('liveAlgo')
    run_seizure_detection(action, target)
    os.chdir('..')

if __name__ == '__main__':
    action = sys.argv[1]
    try:
        target = sys.argv[2]
    except IndexError:
        target = None
    train(action, target)
