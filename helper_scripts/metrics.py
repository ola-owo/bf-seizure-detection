#!/usr/bin/env python2
'''
Compute metrics on the liveAlgo classifier and plot ROC graph.

Usage:
python metrics.py keyFile predFile subjName(s)

Key and prediction files should be CSVs formatted in order, like this:

clip,seizure,early
Dog_1_test_segment_1.mat,0,0
...
Dog_1_test_segment_n.mat,0,0
Dog_2_test_segment_1.mat,0,0
...
Dog_2_test_segment_n.mat,0,0
'''

import sys
from matplotlib import pyplot as plt
import numpy as np
import sklearn.metrics as skl_metrics

def printMetrics(keyFile, predFile, subjNames):
    
    ### Read answer key and predictions
    print 'Reading predictions and answer key...'
    keyAll = np.loadtxt(keyFile, delimiter=',', skiprows=1, usecols=(1,2))
    predAll = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=(1,2))
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
    fp_sz, tp_sz, thresh_sz = skl_metrics.roc_curve(key[:,0], pred[:,0])
    fp_early, tp_early, thresh_early = skl_metrics.roc_curve(key[:,1], pred[:,1])

    auc_sz = skl_metrics.roc_auc_score(key[:,0], pred[:,0])
    print 'Area under ROC (seizure):', auc_sz

    plt.plot(fp_sz, tp_sz)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC (Seizure detection)')
    plt.show()

    auc_early = skl_metrics.roc_auc_score(key[:,1], pred[:,1])
    print 'Area under ROC (early seizure):', auc_early

    plt.plot(fp_early, tp_early)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC (Early seizure detection)')
    plt.show()

    auc_avg = (auc_sz + auc_early) / 2.0
    print 'Average AUC:', auc_avg

    ### Other stats (precision, recall, f1, support)
    szStats = skl_metrics.classification_report(key[:,0], np.rint(pred[:,0]), target_names = ('Interictal', 'Ictal'))
    earlyszStats = skl_metrics.classification_report(key[:,1], np.rint(pred[:,1]), target_names = ('Non-early sz', 'Early sz'))
    print '\n============ SEIZURE DETECTION SUMMARY ============='
    print szStats
    print '========== EARLY SEIZURE DETECTION SUMMARY =========='
    print earlyszStats

if __name__ == '__main__':
    keyFile = sys.argv[1]
    predFile = sys.argv[2]
    subjNames = sys.argv[3:]
    printMetrics(keyFile, predFile, subjNames)
