#!/usr/bin/env python2
'''
Compute metrics for a classifier on one or more patients and plot the ROC.

Usage:
python -m helper-scripts.metrics keyFile predFile ptName1 [ptName2 ... ptName(n)]
'''

import sys
from matplotlib import pyplot as plt
import numpy as np
import sklearn.metrics as skl_metrics

def printMetrics(keyFile, predFile, subjNames):
    
    ### Read answer key and predictions
    print 'Reading predictions and answer key...'
    keyAll = np.loadtxt(keyFile, delimiter=',', skiprows=1, usecols=1)
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
    pred = np.rint(predAll[predIdx, 0]).flatten()
    scores = predAll[predIdx, 1].flatten()

    ### Generate ROC and AUC
    print 'Generating ROC curves...'
    fp_sz, tp_sz, thresh_sz = skl_metrics.roc_curve(key, scores, drop_intermediate=False)

    auc_sz = skl_metrics.roc_auc_score(key, scores)
    print 'Area under ROC (seizure):', auc_sz

    plt.plot(fp_sz, tp_sz)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.ylim(ymin=0)
    plt.title('Seizure detection ROC for %s' % ', '.join(subjNames))
    plt.savefig('roc-%s.png' % '_'.join(subjNames))
    plt.show()

    ### Other stats (precision, recall, f1, support)
    szStats = skl_metrics.classification_report(key, pred, target_names = ('Interictal', 'Ictal'))
    print '\n============ SEIZURE DETECTION SUMMARY ============='
    print 'Patient:', ', '.join(subjNames)
    print szStats

    ### Contingency table
    tp_total = 0
    fp_total = 0
    tn_total = 0
    fn_total = 0

    for i in range(pred.size):
        if key[i] == 1:
            if pred[i] == 1:
                tp_total += 1
            elif pred[i] == 0:
                fn_total += 1
        elif key[i] == 0:
            if pred[i] == 1:
                fp_total += 1
            elif pred[i] == 0:
                tn_total += 1

    print 'True Positives:', tp_total
    print 'False Positives:', fp_total
    print 'True Negatives:', tn_total
    print 'False Negatives:', fn_total

    ### Sensitivity and specificity
    sens = float(tp_total) / (tp_total + fn_total)
    spec = float(tn_total) / (tn_total + fp_total)
    print 'Sensitivity:', sens
    print 'Specificity:', spec

if __name__ == '__main__':
    keyFile = sys.argv[1]
    predFile = sys.argv[2]
    subjNames = sys.argv[3:]
    printMetrics(keyFile, predFile, subjNames)
