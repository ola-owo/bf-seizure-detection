'''
This file contains all of the tuning parameters and patient-specific information
needed for seizure detection.
File and folder names can also be customized here.
'''

#############################
### PATIENT-SPECIFIC INFO ###
#############################
DEFAULT_FREQ = 250 # frequency (Hz) of each timeseries
FREQs = {
    # Specify the frequency of each patient's timeseries if it's different
    # from the default:
    'T_488': 500,
}

TS_IDs = { 
    # ID of each patient's timeseries
    'My_Patient': 'N:package:XXX-XXX-XXX-XXX-XXX'
}

CHANNELS = {
    # specify which channels to use if you're not using all of them
    'My_Patient': [ 
        'N:channel:XXX-XXX-XXX-XXX-XXX',
        'N:channel:YYY-YYY-YYY-YYY-YYY',
        'N:channel:ZZZ-ZZZ-ZZZ-ZZZ-ZZZ'
    ]
}

#########################
### PIPELINE SETTINGS ###
#########################
TRAINING_SZ_LIMIT = 4 # number of seizures to use as training data

GOLD_STD_LAYERS = { 
    'My_Patient': 123
}

# annotations:
TIME_BUFFER = 14400000000 # time (usec) before and after each seizure to exclude from interictal training data
DATA_RATIO = 10 # ratio of interictal to ictal training data

# testing for seizures:
PL_CLIP_LENGTH = 30000000 # length (usec) of each clip to test

#####################################
### LINE LENGTH DETECTOR SETTINGS ###
#####################################

# Old LL Detector:
LL_CLIP_LENGTH = 60000000 # length (usec) of each clip to test
LL_THRESHOLDS = {
    'My_Patient': 1000
}

# Moving Average LL Detector:
LL_LONG_WINDOW_DEFAULT = 28800000000 # default value (usec)
LL_SHORT_WINDOW_DEFAULT = 60000000 # default value (usec)

LL_LONG_WINDOWS = {
    # (Optional) specify custom long-term window lengths
    'My_Patient': 14400000000
}
LL_SHORT_WINDOWS = {
    # (Optional) specify custom short-term window lengths
    'My_Patient': 10000000
}

LL_MA_THRESHOLDS = {
    # The new LL detector uses scaling factors relative to the mean,
    # instead of absolute thresholds
    'My_Patient': 2.5
}

#################################################
### LIVE DETECTION AND SEIZURE DIARY SETTINGS ###
#################################################
DETECTION_INTERVAL = 30 # minutes

###########################
### Misc variable names ###
###########################
# pipeline:
PL_ROOT = 'pipeline-data' # folder for temporary pipeline data
PL_LAYER_NAME = 'My Pipeline Detections'

# cron:
LIVE_UPDATE_TIMES = 'live/last_updated.json'

# liveDetect:
SZ_PLOT_ROOT = 'live' # folder to store seizure history plots
DIARY_DB_NAME = 'live/diaries.db'

# lineLength:
LL_LAYER_NAME = 'Basic Line Length Detections'

# lineLengthMA:
LL_MA_LAYER_NAME = 'MA Line Length Detections'
