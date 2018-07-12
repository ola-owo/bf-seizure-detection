# blackfynn-seizure-detection
Before running anything, make sure all of the correct settings and patient-specific data are set in `settings.py`.

This pipeline provides automated seizure detection of EEG data that is hosted on Blackfynn. It is adapted from an [old pipeline](https://github.com/sbaldassano/blackfynnPipeline) that was made for a previous version of the Blackfynn API.

Two seizure detectors are included: a random forest classifier and a line length detector. `pipeline.py` and `lineLength.py` can be run to use either of these classifiers to predict seizures along an entire TimeSeries. In addition, `cron.py` can be used for real-time seizure detection.

## Random Forest Classifier
Usage: `pipeline.py ptName [annotate [startTime [endTime]]]`

`pipeline.py` automatically downloads clips from patient `ptName` and trains the classifier<sup>[1](#note-1)</sup> (stored in `liveAlgo/`). If `annotate` is specified, the script tests the TimeSeries for seizures between `startTime` and `endTime`.

Each step of the pipeline can also be run separately using modules `annots`, `pullClips`, `sliceClips`, and `testTimeSeries`.

## Line Length Detector
The line length detector can be run using `lineLength.py`. It is faster and more sensitive than the random forest, which may be preferred depending on the situation.

For each data segment \[t<sub>1</sub>, t<sub>2</sub>\], the line length of each channel is measured and normalized as follows:

<p align="center"><img src="https://latex.codecogs.com/gif.latex?LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2&space;-&space;\Delta&space;t}\left|&space;x_{i&plus;1}&space;-&space;x_i&space;\right|" title="LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i+1} - x_i \right|"></p>

The median line length across all channels is then compared to an absolute threshold which must be manually set for each patient. Clips with a median line length greater than the threshold are marked as possible seizures.

Alternatively, a more sophisticated line length detector is also available in `lineLengthNew.py` It is modeled after the line length detector specified by [Esteller et. al.](#ref-1) Instead of using absolute thresholds, it computes long-term line length averages and uses those to generate adaptive thresholds for seizure detection.

## Live Detection
Usage: `cron.py linelength|pipeline`

Real time seizure detection can be done using either the line length detector or the random forest.`cron.py` will, at a specified time interval, check for new EEG data and search it for possible seizures.

`cron.py` will also automatically maintain seizure diaries, displaying each patient's history of human-annotated and auto-detected seizures.

## Helper Scripts
The `helper-scripts` folder contains several small scripts for automating various tasks.

***TODO** - document each script*

## Notes
<b name="note-1">1.</b> The classifier was created by Michael Hills for a Kaggle contest and is hosted separately [here](https://github.com/MichaelHills/seizure-detection).

## References
<b name="ref-1">1.</b> R. Esteller, J. Echauz, T. Tcheng, B. Litt and B. Pless, "Line length: an efficient feature for seizure onset detection," 2001 Conference Proceedings of the 23rd Annual International Conference of the IEEE Engineering in Medicine and Biology Society, 2001, pp. 1707-1710 vol.2.
