#!/usr/bin/env python2
'''
Compute metrics on the liveAlgo classifier and plot ROC graph.

Usage:
python metrics.py keyFile predFile subjName(s)
'''

import sys
from matplotlib import pyplot as plt
import numpy as np
import sklearn.metrics as skl_metrics

def printMetrics(keyFile, predFile, subjNames):
    
    ### Read answer key and predictions
    print 'Reading predictions and answer key...'
    keyAll = np.loadtxt(keyFile, delimiter=',', skiprows=1, usecols=1)
    predAll = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=1)

    with open(keyFile, 'rU') as f:
        f.readline()
        keyClipNamesAll = [line.split(',')[0] for line in f.readlines()]
    with open(predFile, 'rU') as f:
        f.readline()
        predClipNamesAll = [line.split(',')[0] for line in f.readlines()]

    ### Filter only the patients in subjNames
    keyIdx = []
    predIdx = []
    for name in subjNames:
        l = [i for i in range(len(predClipNamesAll)) if predClipNamesAll[i].startswith(name)]
        predIdx.append(l)
        l = [i for i in range(len(keyClipNamesAll)) if keyClipNamesAll[i].startswith(name)]
        keyIdx.append(l)

    key = keyAll[keyIdx]
    pred = predAll[predIdx]

    ### Generate ROC and AUC
    print 'Generating ROC curves...'
    fp_sz, tp_sz, thresh_sz = skl_metrics.roc_curve(key, pred)

    auc_sz = skl_metrics.roc_auc_score(key, pred)
    print 'Area under ROC (seizure):', auc_sz

    plt.plot(fp_sz, tp_sz)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC (Seizure detection)')
    plt.savefig('roc-%s-sz.png' % '_'.join(subjNames))
    plt.show()

    ### Other stats (precision, recall, f1, support)
    szStats = skl_metrics.classification_report(key, np.rint(pred), target_names = ('Interictal', 'Ictal'))
    print '\n============ SEIZURE DETECTION SUMMARY ============='
    print szStats

if __name__ == '__main__':
    keyFile = sys.argv[1]
    predFile = sys.argv[2]
    subjNames = sys.argv[3:]
    printMetrics(keyFile, predFile, subjNames)
