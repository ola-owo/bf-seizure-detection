# blackfynn-seizure-detection
This pipeline provides automated seizure detection of EEG data that is hosted on Blackfynn. It is adapted from an [old pipeline](https://github.com/sbaldassano/blackfynnPipeline) that was made for a previous version of the Blackfynn API.

Two seizure detectors are included: a random forest classifier and a line length detector. `pipeline.py` and `lineLength.py` can be run to use either of these classifiers to predict seizures along an entire TimeSeries. Additionally, `cron.py` can be used for real-time seizure detection.

## Setup Instructions
### Installing dependencies
It is optional (but strongly recommended) to install the dependencies inside a virtual environment, in order to avoid conflicts with globally installed packages. This can be done using `pip`<sup>[1](#note-1)</sup> and `virtualenv`:
```bash
virtualenv env
source env/bin/activate # to enter the virtual environment
pip install -r requirements.txt
deactivate # to exit the virtual environment
```
Note that if this installation method is used, *all scripts* in this pipeline must also be run from inside the virtual environment.

### Configuring the Blackfynn client
For the Blackfynn API to work correctly, the user profile must be set up (see [this guide](http://docs.blackfynn.io/platform/clients/getting_started.html) for help).

### Settings
Before running anything, make sure all of the correct settings and patient-specific info are set in `settings.py`. This file specifies:
- Blackfynn timeseries information for each patient being tested
- Tuning parameters for the line length detector and random forest pipeline. 
- Custom names for various files/folders

## Using the Random Forest Classifier
Usage: `pipeline.py ptName [annotate [startTime [endTime]]]`

`pipeline.py` automatically downloads clips from patient `ptName` and trains the classifier<sup>[2](#note-2)</sup> (stored in `liveAlgo/`). If `annotate` is specified, the script tests the TimeSeries for seizures between `startTime` and `endTime`.

Each step of the pipeline can also be run separately using modules `annots`, `pullClips`, `sliceClips`, and `testTimeSeries`.

## Using the Line Length Detector
The line length detector can be run using `lineLength.py`. It is faster and more sensitive than the random forest, which may be preferred depending on the situation.

For each data segment \[t<sub>1</sub>, t<sub>2</sub>\], the line length of each channel is measured and normalized as follows:

<p align="center"><img src="https://latex.codecogs.com/svg.latex?LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2&space;-&space;\Delta&space;t}\left|&space;x_{i&plus;1}&space;-&space;x_i&space;\right|" title="LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i+1} - x_i \right|" alt="LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i+1} - x_i \right| title=LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i 1} - x_i \right|"></p>

The median line length across all channels is then compared to an absolute threshold which must be manually set for each patient. Clips with a median line length greater than the threshold are marked as possible seizures.

Alternatively, a more sophisticated line length detector is also available in `lineLengthNew.py` It is modeled after the line length detector specified by [Esteller et. al.](#ref-1) Instead of using absolute thresholds, it computes long-term line length averages and uses those to generate adaptive thresholds for seizure detection.

## Live Detection
Usage: `cron.py linelength|pipeline`

Real time seizure detection can be done using either the line length detector or the random forest pipeline, depending on which argument is passed to `cron.py`. This script will, at a specified time interval, check for new EEG data and search it for possible seizures.

`cron.py` will also automatically maintain daily seizure diaries, displaying each patient's history of human-annotated and auto-detected seizures.

## Helper Scripts
`helper-scripts/` contains several small scripts for automating various tasks.

***TODO** - document each script*
`makekey.py`

## Notes
<b name="note-1">1.</b> I recommend using wheels to install the required packages, so that pip installs an optimized, pre-compiled version of numpy instead of building it from source. Newer versions of pip do this by default.

<b name="note-2">2.</b> The classifier was created by Michael Hills for a Kaggle contest and is hosted separately [here](https://github.com/MichaelHills/seizure-detection).

## References
<b name="ref-1">1.</b> R. Esteller, J. Echauz, T. Tcheng, B. Litt and B. Pless, "Line length: an efficient feature for seizure onset detection," 2001 Conference Proceedings of the 23rd Annual International Conference of the IEEE Engineering in Medicine and Biology Society, 2001, pp. 1707-1710 vol.2.
