#!/usr/bin/env python2
'''
Compute metrics for a classifier on one or more patients and plot the ROC.

Usage:
python -m helper-scripts.metrics keyFile predFile ptName
'''

import sys
from matplotlib import pyplot as plt
import numpy as np
import sklearn.metrics as skl_metrics

def printMetrics(keyFile, predFile, ptName):
    
    ### Read answer key and predictions
    print 'Reading predictions and answer key...'
    key = np.loadtxt(keyFile, delimiter=',', skiprows=1, usecols=1)
    predArray = np.loadtxt(predFile, delimiter=',', skiprows=1, usecols=(1,2))

    preds = np.rint(predArray[:,0]).flatten()
    scores = predArray[:,1].flatten()

    ### Generate ROC and AUC
    print 'Generating ROC curves...'
    fp_sz, tp_sz, thresh_sz = skl_metrics.roc_curve(key, scores, drop_intermediate=False)

    auc_sz = skl_metrics.roc_auc_score(key, scores)
    print 'Area under ROC (seizure):', auc_sz

    plt.plot(fp_sz, tp_sz)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.ylim(ymin=0)
    plt.title('Seizure detection ROC for ' + ptName)
    plt.savefig('roc-%s.png' % ptName)
    plt.show()

    ### Other stats (precision, recall, f1, support)
    szStats = skl_metrics.classification_report(key, preds, target_names = ('Interictal', 'Ictal'))
    print '\n============ SEIZURE DETECTION SUMMARY ============='
    print 'Patient:', ptName
    print szStats

    ### Contingency table
    tp_total = 0
    fp_total = 0
    tn_total = 0
    fn_total = 0

    for i in range(preds.size):
        if key[i] == 1:
            if preds[i] == 1:
                tp_total += 1
            elif preds[i] == 0:
                fn_total += 1
        elif key[i] == 0:
            if preds[i] == 1:
                fp_total += 1
            elif preds[i] == 0:
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
    ptName = sys.argv[3]
    printMetrics(keyFile, predFile, ptName)
