# blackfynn-seizure-detection
This collection of scripts provides automated seizure detection of EEG data that is hosted on Blackfynn. It is adapted from an [old pipeline](https://github.com/sbaldassano/blackfynnPipeline) that was made for a previous Blackfynn API version.

Three seizure detectors are included: a random forest classifier, basic line length detector, and moving average (MA) line length detector. Real-time seizure detection is also possible using any of these classifiers.

## Setup
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
Before running anything, make sure all of the correct settings and patient-specific info are set in `settings.py`. This file contains:
- Blackfynn timeseries information for each patient being tested.
- Tuning parameters for the line length detector and random forest pipeline. 
- Custom names for various files and folders.

## Using the Random Forest Classifier
Usage: `pipeline.py ptName [annotate [startTime [endTime]]]`

`pipeline.py` automatically downloads clips from patient `ptName` and trains the classifier<sup>[2](#note-2)</sup> (stored in `liveAlgo/`). If `annotate` is specified, the script tests the TimeSeries for seizures between `startTime` and `endTime` (measured in microseconds since Unix epoch) and annotates the results on Blackfynn.

Each step of the pipeline can also be run separately using modules `annots`, `pullClips`, `sliceClips`, and `testTimeSeries`.

## Using the Basic Line Length Detector
Usage: `lineLengthNew.py ptName [startTime [endTime]] [append]`

The basic line length detector can be run using `lineLength.py`. It is faster and more sensitive than the random forest, which may be preferred depending on the situation. Optional arguments `startTime` and `endTime` (both microseconds) specify which portion of the timeseries to annotate. If `append` is included, the classifier will append to the MA line length annotation layer on Blackfynn. Otherwise, the layer is overwritten.

For each data segment \[t<sub>1</sub>, t<sub>2</sub>\], the line length of each channel is measured and normalized as follows:

<p align="center"><img src="https://latex.codecogs.com/svg.latex?LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2&space;-&space;\Delta&space;t}\left|&space;x_{i&plus;1}&space;-&space;x_i&space;\right|" alt="LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i+1} - x_i \right| title=LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i 1} - x_i \right|"></p>

The median line length across all channels is then compared to an absolute threshold which must be manually set for each patient. Clips with a median line length greater than the threshold are marked as possible seizures.

## Using the Moving Average Line Length Detector
Usage: `lineLengthNew.py ptName [startTime [endTime]] [append]`

A moving average (MA) line length detector<sup>[3](#note-3)</sup> is available, located in `lineLengthNew.py` Its command line arguments are identical to those of `lineLength.py`.

The MA line length detector requires each patient to have a long-term window length *L*, a short-term window length *S*, and a scalar *k* which is multiplied by the average line length to get the detection threshold for a long-term window. For a long-term window starting at time *t*, the threshold value *T* is calculated as:

<p align="center"><img src="https://latex.codecogs.com/svg.latex?T(t)%3D\frac{k}{N}\sum_{n%3D0}^{N-1}LL(t&plus;nS%2C\%3At&plus;(n&plus;1)S)" alt="T(t)=\frac{k}{N}\sum_{n=0}^{N-1}LL(t+nS,\:t+(n+1)S)"></p>

Here, *N* is the number short-term windows in each long term window and is equal to floor\[*L/S*\].

The MA line length detector looks for seizures, one long-term window at a time. First, it splits the long-term window into short-term windows and measures the line length of each. Next, it calculates the long-term threshold as explained above. Then, it looks back at the individual line lengths and marks any clip with a line length greater than the threshold as a potential seizure.

## Real-Time Seizure Detection
Usage: `cron.py algo`

Live seizure detection can be done using any of the available classifiers, depending the `algo` argument. `pipeline` uses the random forest pipeline/classifier, `linelength` uses the basic line length detector, and `ma_linelength` uses the MA line length detector. `cron.py` will, at a specified time interval, check for new EEG data and search it for possible seizures.

`cron.py` also automatically maintains daily seizure diaries, displaying each patient's history of human-annotated and auto-detected seizures.

## Helper Scripts
`helper-scripts/` contains several small scripts for automating various tasks.

***TODO** - document each script*
`makekey.py`

## Notes
<b name="note-1">1.</b> I recommend using wheels to install the required packages, so that pip installs an optimized, pre-compiled version of numpy instead of building it from source. Newer versions of pip do this by default.

<b name="note-2">2.</b> The classifier was created by Michael Hills for a Kaggle contest and is hosted separately [here](https://github.com/MichaelHills/seizure-detection).


<b name="note-3">3.</b> The moving average line length detector is based on a paper by [Esteller et. al.](#ref-1)

## References
<b name="ref-1">1.</b> R. Esteller, J. Echauz, T. Tcheng, B. Litt and B. Pless, "Line length: an efficient feature for seizure onset detection," 2001 Conference Proceedings of the 23rd Annual International Conference of the IEEE Engineering in Medicine and Biology Society, 2001, pp. 1707-1710 vol.2.
