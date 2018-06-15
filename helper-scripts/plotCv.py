#!/usr/bin/env python2

from matplotlib import pyplot as plt
import numpy as np
import hickle

score1 = hickle.load('score_Dog1.hkl')
score2 = hickle.load('score_UCD2_spliced.hkl')

scores = (score1, score2)

auc = [float(score['score']) for score in scores]
S_auc = [float(score['S_auc']) for score in scores]
E_auc = [float(score['E_auc']) for score in scores]

idx = np.arange(2)
w = 0.3 # width

p1 = plt.bar(idx, auc, w)
p2 = plt.bar(idx + w, S_auc, w)
p3 = plt.bar(idx + 2*w, E_auc, w)

plt.xticks(idx + w, ('Kaggle Dog 1', 'UCD2 (spliced with Dog 1 interictal clips)'))
plt.legend((p1, p2, p3),
           ('Overall score', 'Seizure detection only', 'Early seizure detection only'),
           loc=4)
plt.ylabel('Cross-Validation AUROC')
plt.xlabel('Test subject')
plt.title('CV Performance using Dog 1 interictal clips')
#plt.show()

filename = 'cv_comparison.png'
plt.savefig(filename)
print 'Saved chart as', filename
