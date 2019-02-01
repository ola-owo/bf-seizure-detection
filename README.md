# blackfynn-seizure-detection
This collection of scripts provides automated seizure detection of EEG data that is hosted on Blackfynn. It is adapted from an [old pipeline](https://github.com/sbaldassano/blackfynnPipeline) that was made for a previous Blackfynn API version.

Three seizure detectors are included: a random forest classifier, basic line length detector, and moving average (MA) line length detector. Real-time seizure detection is also possible using any of these classifiers.

## Setup
### Installing dependencies
It is recommended to set up a virtual environment for these scripts in order to avoid conflicts with globally installed packages<sup>[1](#note-1)</sup>. This can be done using `pip`<sup>[2](#note-2)</sup> and `virtualenv`:
```bash
virtualenv -p python3 env
source env/bin/activate # to enter the virtual environment running python 3
pip install -r requirements.txt
deactivate # to exit the virtual environment
```

### Configuring the Blackfynn client
For the Blackfynn API to work correctly, the user profile must be set up (see [this guide](http://help.blackfynn.com/getting-started) for help).

### Settings
Before running anything, make sure all of the correct settings and patient-specific info are set in `settings.py`. This file contains:
- Blackfynn timeseries information for each patient being tested.
- Tuning parameters for the line length detector and random forest pipeline. 
- Custom names for various files and folders.

## Using the Random Forest Classifier
Command: `pipeline.py ptName [annotate [startTime [endTime]]]`

Example: `pipeline.py My_Patient annotate 1000000000000 2000000000000`

`pipeline.py` automatically downloads clips from patient `ptName` and trains the classifier<sup>[3](#note-3)</sup> (stored in `liveAlgo/`). If `annotate` is specified, the script tests the TimeSeries for seizures between `startTime` and `endTime` (measured in microseconds since Unix epoch) and annotates the results on Blackfynn.

Each step of the pipeline can also be run separately using modules `annots`, `pullClips`, `sliceClips`, and `testTimeSeries`.

## Using the Basic Line Length Detector
Command: `lineLength.py ptName [startTime [endTime]] [append]`

Example: `lineLength.py My_Patient 1000000000000 2000000000000 append`

The basic line length detector can be run using `lineLength.py`. It is faster and more sensitive than the random forest, which may be preferred depending on the situation. Optional arguments `startTime` and `endTime` (both microseconds) specify which portion of the timeseries to annotate. If `append` is included, the classifier will append to the MA line length annotation layer on Blackfynn. Otherwise, the layer is overwritten.

For each data segment \[t<sub>1</sub>, t<sub>2</sub>\], the line length of each channel is measured and normalized as follows:

<p align="center"><img src="https://latex.codecogs.com/svg.latex?LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2&space;-&space;\Delta&space;t}\left|&space;x_{i&plus;1}&space;-&space;x_i&space;\right|" alt="LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i+1} - x_i \right| title=LL(t1,t2)=\frac{1}{t_2-t_1}\sum_{i=t_1}^{t_2 - \Delta t}\left| x_{i 1} - x_i \right|"></p>

The median line length across all channels is then compared to an absolute threshold which must be manually set for each patient. Clips with a median line length greater than the threshold are marked as possible seizures.

## Using the Moving Average Line Length Detector
Command: `lineLengthMA.py ptName [startTime [endTime]] [append]`

Example: `lineLengthMA.py My_Patient 1000000000000 2000000000000 append`

A moving average (MA) line length detector<sup>[4](#note-4)</sup> is available, located in `lineLengthMA.py` Its command line arguments are identical to those of `lineLength.py`.

The MA line length detector requires each patient to have a long-term window length *L*, a short-term window length *S*, and a scalar *k* which is multiplied by the average line length to get the detection threshold for a long-term window. For a long-term window starting at time *t*, the threshold value *T* is calculated as:

<p align="center"><img src="https://latex.codecogs.com/svg.latex?T(t)%3D\frac{k}{N}\sum_{n%3D0}^{N-1}LL(t&plus;nS%2C\%3At&plus;(n&plus;1)S)" alt="T(t)=\frac{k}{N}\sum_{n=0}^{N-1}LL(t+nS,\:t+(n+1)S)"></p>

Here, *N* is the number short-term windows in each long term window and is equal to floor\[*L/S*\].

The MA line length detector splits the timeseries into long-term windows and checks them, one at a time, for seizures. First, it splits the long-term window into short-term windows and measures the line length of each. Next, it calculates the long-term threshold as explained above. Then, it looks back at the individual line lengths and marks any clip with a line length greater than the threshold as a potential seizure.

## Real-Time Seizure Detection
Command: `cron.py algo > output_file`

Example: `cron.py ma_linelength`

Live seizure detection can be done using any of the available classifiers, depending the `algo` argument. `pipeline` uses the random forest pipeline/classifier, `linelength` uses the basic line length detector, and `ma_linelength` uses the MA line length detector. `cron.py` will, at a specified time interval, check for new EEG data and search it for possible seizures. The output is written to the file `output_file`. NOTE: change the live/last_updated_example.json file to live/last_updated.json with patient names and upload start times. 

`cron.py` also automatically maintains daily seizure diaries, displaying each patient's history of human-annotated and auto-detected seizures.

## Logging
All of the above scripts will print a lot of information, so it is strongly recommended to save the output to a separate file. This is required if you plan to compute metrics on a classifier because the output file is needed by `metrics.py`.  For example, `nohup lineLength.py My_Patient > cron.txt` will run the line length detector on My_Patient and write the output to `cron.txt`.

## Helper Scripts
`helper-scripts/` contains several small scripts for automating various tasks:

### lineLengthTest
Command: `python -m helper-scripts.lineLengthTest ptName [startTime]`

Example: `python -m helper-scripts.lineLengthTest My_Patient 1000000000000`

`lineLengthTest` is used to measure line lengths of sequential clips in a timeseries, starting from `startTime`. This can help with determining threshold values for the basic LL detector; line lengths of known interical periods can be compared to those of known ictal periods. The clip length is equal to `LL_CLIP_LENGTH` (see `settings.py`).

### makeKey
Command: `python -m helper-scripts.makeKey-XX ptName logFile`

Example: `python -m helper-scripts.makeKey-ll My_Patient My_Patient_log.txt`

The `makeKey` scripts each take in a classifier's output log and a patient's list of known seizures, and uses them to create a prediction file and a key file. These 2 files can then be used by `metrics`. `makeKey-pp` takes in the auto-generated `[Patient]_seizures.txt` file, while `makeKey-ll` and `makeKey-ma` take in the output of their respective `lineLength` scripts.

### metrics
Command: `python -m helper-scripts.metrics keyFile predFile ptName`

Example: `python -m helper-scripts.metrics My_Patient_key.csv My_Patient_preds.csv My_Patient`

`metrics.py` takes in key and prediction files, and generates an ROC curve along with precision and recall stats. This script can be used to compare the performance of different classifiers on a patient, or to compare the one classifier's performance across different patients.

### reannotate
Command: `python -m helper-scripts.reannotateXX ptName logFile threshold`

Example: `python -m helper-scripts.reannotateLL My_Patient My_Patient_log.txt 1000`

`reannotate` is used to redo line length seizure detection for a patient, using a custom threshold. `reannotateLL` is used for the basic line length detector, while `reannotateMA` corresponds to the MA line length detector.

### rewriteDiary
Command: `python -m helper-scripts.rewriteDiary algo`

Example: `python -m helper-scripts.rewriteDiary pipeline`

`rewriteDiary` gets all patients' auto-detected seizure annotations from Blackfynn and overwrties the seizure diary database. This is useful if switching the real-time seizure detector to a different classifier. Note that seizure plots won't be updated until `cron.py` does its daily seizure diary update.

## Notes
<b name="note-1">1.</b> Note that if this installation method is used, **all scripts** must also be run from inside the virtual environment.

<b name="note-2">2.</b> I recommend using wheels to install the dependencies so that pip installs an optimized, pre-compiled version of numpy instead of building it from source. Newer versions of pip (9.0.1 and above) do this by default. Otherwise, this can be done by adding the `--use-wheel` option.

<b name="note-3">3.</b> The classifier was created by Michael Hills for a [Kaggle contest](https://www.kaggle.com/c/seizure-detection) and is hosted separately [here](https://github.com/MichaelHills/seizure-detection).

<b name="note-4">4.</b> The moving average line length detector is based on a paper by [Esteller et. al.](#ref-1)

## References
<b name="ref-1">1.</b> R. Esteller, J. Echauz, T. Tcheng, B. Litt and B. Pless, "Line length: an efficient feature for seizure onset detection," 2001 Conference Proceedings of the 23rd Annual International Conference of the IEEE Engineering in Medicine and Biology Society, 2001, pp. 1707-1710 vol.2.
