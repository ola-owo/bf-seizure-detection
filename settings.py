### Patient-specific info ###
TS_IDs = { 
    # ID of each patient's timeseries
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
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
}

### Pipeline settings ###

# (pipeline)
ANNOT_ROOT = 'annotations'
ALGO_DATA_ROOT = 'seizure-data' # NOTE: this must match competition-data-dir in liveAlgo/SETTINGS.json
CLIP_ROOT = 'clips'
PL_LAYER_NAME = 'UPenn_Seizure_Detections'
FREQ = 250 # frequency (hz) of each timeseries
TRAINING_SZ_LIMIT = 4 # number of seizures to use as training data
GOLD_STD_LAYERS = { 
    # ID of the gold standard annotation layer to train from
    'Ripley': 1088,
    'UCD2': 450,
}

# (annots)
TIME_BUFFER = 14400000000 # time (usec) before and after each seizure to exclude from interictal training data
DATA_RATIO = 10 # ratio of interictal to ictal time

# (testTimeSeries)
PL_CLIP_LENGTH = 30000000 # length (usec) of each clip to test

### Line length detector settings ###
LL_CLIP_LENGTH = 60000000 #  length (usec) of each clip to test
LL_LAYER_NAME = 'UPenn_Line_Length_Detector'
THRESHOLDS = {
    'R_950': 15,
    'R_951': 15,
    'Ripley': 16,
    'UCD1': 5000,
    'UCD2': 10000,
}

### Live detection and seizure diary settings ###

# (cron)
DETECTION_INTERVAL = 30 # minutes

# (liveDetect)
LIVE_LAYER_NAME = 'UPenn_Live_Detect'
DIARY_DB_NAME = 'diaries.db'
SZ_PLOT_ROOT = 'diaries' # folder to store seizure history plots
