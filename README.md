# blackfynn-seizure-detection
Before running anything, make sure all of the correct settings and patient-specific data are set in `settings.py`.

This pipeline provides automated seizure detection of EEG data that is hosted on Blackfynn. It is adapted from an [old pipeline](https://github.com/sbaldassano/blackfynnPipeline) that was made for Blackfynn's Matlab API.

Two seizure detecctors are included: a random forest classifier and a line length detector. `pipeline.py` and `lineLength.py` can be run to use either of these classifiers to predict seizures along an entire EEG TimeSeries. In addition, `cron.py` can be used for real-time seizure detection.

## Random Forest Classifier
`pipeline.py` automatically downloads EEG clips, trains the random forest (stored in `liveAlgo/`), and runs the classifier. The script calls `annots`, `pullClips`, `sliceClips`, and `testTimeSeries`, each of which can also be run separately.

The random forest was created for a Kaggle contest and is hosted separately [here:](https://github.com/MichaelHills/seizure-detection)

## Line Length Detector
A line length detector is also provided and can be run using `lineLength.py`. It is faster and more sensitive than the random forest, which may be preferred depending on the situation.

## Live Detection
`cron.py` will, at a specified time interval, check for new EEG data and search it for possible seizures. Either the line length detector or the random forest classifier can be used.
