'''
This file contains all of the hyperparameters and patient-specific information
needed for seizure detection.
File and folder names can also be customized here.
'''

#############################
### PATIENT-SPECIFIC INFO ###
#############################
FREQ = 250 # frequency (hz) of each timeseries

TS_IDs = { 
    # ID of each patient's timeseries
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'UCD1': 'N:package:3d9de38c-5ab2-4cfe-8f5b-3ed64d1a6b6e',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

CHANNELS = {
    # specify which channels to use if you're not using all of them
    'Ripley': [ 
        'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
        'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
        'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
        'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
    ],  
    'UCD1': [
        'N:channel:f481e0e3-358f-41e7-b59c-6b0f80de58f4',
        'N:channel:64fd2f7b-2ee8-481c-9c4a-cbcd724934df',
        'N:channel:c6fb6bbe-f2d1-4a87-9092-97ea676cd6ce',
        'N:channel:4eb5905d-c191-4c32-b63c-1e2b37de7586'
    ],
}

#########################
### PIPELINE SETTINGS ###
#########################
TRAINING_SZ_LIMIT = 4 # number of seizures to use as training data

GOLD_STD_LAYERS = { 
    # ID of the gold standard annotation layer to train from
    'Ripley': 1088,
    'UCD1': 452,
    'UCD2': 450,
}

# annotations:
TIME_BUFFER = 14400000000 # time (usec) before and after each seizure to exclude from interictal training data
DATA_RATIO = 10 # ratio of interictal to ictal training data

# testing for seizures:
PL_CLIP_LENGTH = 30000000 # length (usec) of each clip to test

#####################################
### LINE LENGTH DETECTOR SETTINGS ###
#####################################
LL_CLIP_LENGTH = 60000000 #  length (usec) of each clip to test
THRESHOLDS = {
    'R_950': 15,
    'R_951': 15,
    'Ripley': 16,
    'UCD1': 10000,
    'UCD2': 10000,
}

#################################################
### LIVE DETECTION AND SEIZURE DIARY SETTINGS ###
#################################################
DETECTION_INTERVAL = 30 # minutes

###########################
### Misc variable names ###
###########################
# pipeline:
PL_ROOT = 'pipeline-data' # folder to store temporary pipeline data
PL_LAYER_NAME = 'UPenn_Seizure_Detections'

# cron:
LIVE_UPDATE_TIMES = 'live/last_updated.json'

# liveDetect:
SZ_PLOT_ROOT = 'live' # folder to store seizure history plots
DIARY_DB_NAME = 'live/diaries.db'

# lineLength:
LL_LAYER_NAME = 'UPenn_Line_Length_Detector'
