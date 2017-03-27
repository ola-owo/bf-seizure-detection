# blackfynnPipeline

This pipeline is used to run real-time analysis of EEG data hosted on blackfynn.

First, masterTrain is used to train the kaggle-winning seizure detection algorithm (see instructions in detail below).
Once the algorithm is trained, liveDetect can be run to detect seizure events over a user-specified time interval (default 30 minutes).

Setup:
If using Blackfynn datasets, you must install the Blackfynn API client first (python)
Go to the github documentation for the Kaggle-winning algorithm at https://github.com/MichaelHills/seizure-detection 
and make sure you have all dependencies met. Note the package version numbers.

Make sure that the "target" of the algorithm in seizure_detection.py is the correct subject name (currently set to R951).
If you are retraining a classifier, make sure that the corresponding old classifier and seizure/nonseizure data files are removed from the data cache.

File structure:
Seizure and interictal annotation files should be text files. They should be organized as follows:

startTime1
stopTime1
startTime2
stopTime2
startTime3
stopTime3
...

where all times are in uUTC.

For debugging, it probably makes sense to run each component of the training pipeline individually:
pullSzClips.py
pullInterictalClips.py
clipForAlgoPipeline.py
liveAlgo/train.py

Note that this pipeline is built to pull data from Blackfynn, but could be amended to pull from MEF if needed.
