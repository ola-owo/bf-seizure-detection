# blackfynnPipeline

This pipeline is used to automatically download EEG data hosted on blackfynn and train the classifier.

The pipeline is adapted from the repo of the same name at https://github.com/sbaldassano/blackfynnPipeline, but modified to work with the current Blackfynn API.

The classifier comes from the Kaggle contest-winning seizure detector algorithm, hosted here: https://github.com/MichaelHills/seizure-detection

To use this pipeline, use the command `python pipeline.py patientName`. However, you first need to add and/or uncomment the name of the patient in `target` in liveAlgo/seizure\_detection.py. You also must make sure that your ANNOT\_ROOT folder contains both ictal and interictal files for the patient. (makeAnnotFile might help with this).

Each step can be done individually by calling `pullClips.py`, `sliceClips.py`, and `train.py` from the command line.
