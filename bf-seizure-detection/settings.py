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
    'Gus': 'N:package:cb8231c7-5b8b-4baf-be00-5658133b4d16',
    'Joseph': 'N:package:3768b47c-5ded-4cf9-9bda-dc32f4520b40',
    'R_950': 'N:package:f950c9de-b775-4919-a867-02ae6a0c9370',
    'R_951': 'N:package:6ff9eb72-4d70-4122-83a1-704d87cfb6b2',
    'Ripley': 'N:package:401f556c-4747-4569-b1a8-9e6e50abf919',
    'T_488': 'N:package:7d49ad78-26a8-4726-b253-cf70a237ec42',
    'T_537': 'N:package:a48ffe55-be70-4fb6-af79-129bf8de2623',
    'T_571': 'N:package:666bcf72-ce45-46b2-9238-3ac1fa0403bd',
    'T_608': 'N:package:40da8a12-9f71-48a1-82f4-8c34ecbe0e14',
    'UCD1': 'N:package:3d9de38c-5ab2-4cfe-8f5b-3ed64d1a6b6e',
    'UCD2': 'N:package:86985e61-c940-4404-afa7-94d0add8333f',
}

CHANNELS = {
    # specify which channels to use if you're not using all of them
    'Gus': [
        'N:channel:2d3b9c01-2f00-482c-9c67-5ca044f19e89',
        'N:channel:7fea9bce-31aa-44bf-9bd8-398f51e7e00a',
        'N:channel:cdc30ba2-17ee-44a4-a9b4-81ca293dfab9'
    ],
    'Joseph': [
        'N:channel:6829575f-aae0-45d8-9701-73c59aed1236',
        'N:channel:1a59225e-ce86-4029-82b4-82f40204681d',
        'N:channel:5b56e802-abf2-4f63-91e2-fe641e94ecf1',
        'N:channel:36a7010f-2f5b-4f98-aa8b-89dccf2188f8'
    ],
    'Ripley': [ 
        'N:channel:95f4fdf5-17bf-492b-87ec-462d31154549',
        'N:channel:c126f441-cbfe-4006-a08c-dc36bd309c38',
        'N:channel:23d29190-37e4-48b0-885c-cfad77256efe',
        'N:channel:07f7bcae-0b6e-4910-a723-8eda7423a5d2'
    ],  
    'T_537': [
        'N:channel:545be622-ce99-4b2d-b2c2-7666449068d6',
        'N:channel:9bfa2889-b84b-461a-8519-ab0c323884b5',
        'N:channel:ab307889-5adf-4aae-8c2c-6de5e3742b2c',
        'N:channel:6ef52c33-3eb2-4161-a481-7496e2f38d3c'
    ],
    'T_571': [
        'N:channel:c5857227-64f1-48c7-b479-7cb111ee3e79',
        'N:channel:846e4ef3-ef77-4335-90b0-abc0f3ba11cf',
        'N:channel:84f2ac91-1d73-4592-bfd2-7db61430460f',
        'N:channel:e61879d1-fa15-4037-abc7-f1cfebb639b1'
    ],
    'T_608': [
        'N:channel:6561d10e-64d2-497e-bbd4-180c64ea29f0',
        'N:channel:84a960d5-e168-425a-8ff0-9b146e28a6e9',
        'N:channel:fdcc966e-f8cd-4ab8-989f-5ef82bd4a99d',
        'N:channel:e6852e07-a9be-4ed5-a932-94bfb485488c'
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

# Old LL Detector:
LL_CLIP_LENGTH = 60000000 # length (usec) of each clip to test
LL_THRESHOLDS = {
    'Gus': 19,
    'R_950': 20,
    'R_951': 15,
    'Ripley': 16,
    'UCD1': 10000,
    'UCD2': 10000,

    # TODO: change these values
    'Joseph': 1000000,
    'T_488':  1000000,
    'T_537':  1000000,
    'T_571':  1000000,
    'T_608':  1000000,
}

# Moving Average LL Detector:
LL_LONG_WINDOW_DEFAULT = 28800000000 # default value (usec)
LL_SHORT_WINDOW_DEFAULT = 60000000 # default value (usec)

LL_LONG_WINDOWS = {
    # Specify custom long-term window lengths
}
LL_SHORT_WINDOWS = {
    # Specify custom short-term window lengths
    'T_537': 30000000,
    'Gus': 30000000,
    'Joseph': 30000000,
}

LL_MA_THRESHOLDS = {
    # The new LL detector uses scaling factors relative to the mean,
    # instead of absolute thresholds
    'Gus': 1.5,
    'Joseph': 1.5,
    'R_950': 2.0,
    'R_951': 2.0,
    'Ripley': 2.0,
    'T_488': 3.0,
    'T_537': 3.0,
    'T_571': 2.2,
    'T_608': 3.0,
    'UCD1': 3.0,
    'UCD2': 3.0,
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
PL_LAYER_NAME = 'UPenn_Seizure_Detections'

# cron:
LIVE_UPDATE_TIMES = 'live/last_updated.json'

# liveDetect:
SZ_PLOT_ROOT = 'live' # folder to store seizure history plots
DIARY_DB_NAME = 'live/diaries.db'

# lineLength:
LL_LAYER_NAME = 'UPenn_Line_Length_Detector'

# lineLengthMA:
LL_MA_LAYER_NAME = 'UPenn_MA_LL_Detector'
