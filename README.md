# blackfynnPipeline

This pipeline is used to run real-time analysis of EEG data hosted on blackfynn.

First, masterTrain is used to train the kaggle-winning seizure detection algorithm (see instructions in detail below).
Once the algorithm is trained, liveDetect can be run to detect seizure events over a user-specified time interval (default 30 minutes).
