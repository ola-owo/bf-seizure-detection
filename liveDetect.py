# -*- coding: utf-8 -*-
"""

@author: stevenbaldassano

This script is used for live detection of seizures on the streaming dataset
This will be called at 30 minute intervals to download data and make predictions.

"""
import numpy as np
from blackfynn import Blackfynn
import datetime
import scipy.io as sio
import sys,os
import glob
from subprocess import call

# module to split data if there are gaps
# If there is a gap of less than 0.1 seconds, the gap is ignored
# If there is a gap larger than 0.1 seconds, the dataset is split and analyzed in two chunks
# This module is the most time-intensive part of the pipeline, so you could make changes here if you would like
def split_data(df):
    dfs = []
    toContinue=True
    while toContinue:
        for i in range(1, df.shape[0]):
            toContinue=False
            #print(i)
            deltaT = (df.iloc[i].name-df.iloc[i-1].name).microseconds
            if  deltaT> 10000:
                dfs.append(df.iloc[:i])
                df = df.iloc[i:]
                toContinue=True
                break          
    dfs.append(df)
    return dfs

# Need to fill in personal Blackfynn login information here
bf = Blackfynn(email='you_email_here',password='your_passwd_here')
bf.set_context('Mayo')
ts = bf.datasets()[0].items[0] # again, this is set up for 951 now. Need to change this line for a different BF dataset
# Here we grab the last 30 minutes of data
tempEnd = datetime.datetime.now()
tempStart = tempEnd - datetime.timedelta(0,1800)

d = ts.get_data(start=tempStart,end=tempEnd)
d = d.drop_duplicates() # had some issues with duplicate data points. Remove them if they exist
if d.shape[0]==0:
    print('no data in time segment...quitting \n')
    exit()
print('starting split...')
dfs = split_data(d)
print('done')
for df in dfs:
    # for each chunk of data, organize it into one-second clips
    clipped = df.as_matrix()
    print clipped.shape
    fs = 250
    numClips = int(np.floor(clipped.shape[0]/fs))
    print numClips
    if numClips==0:
        continue
    temp1 = clipped[:numClips*fs,:]
    temp = temp1.reshape(numClips,fs,4)
    inputData= np.transpose(temp, (0,2,1))
    
    # here we send the clips into the kaggle algo for detection
    #output will be a series of seizure probabilities (one for each clip) called preds
    # For now I will just save the clips
    #I will later try to modify the algo to do it without saving to make it run faster
    
    for i in range(0,inputData.shape[0]):
        curData = inputData[i,:,:]
        filename = 'R951/R951_test_segment_' + str(i+1) + '.mat'
        sio.savemat(filename,{'data':curData, 'freq':fs})

    os.chdir('liveAlgo')
    # call the prediction function
    ret = call(['python', 'predict.py'])
    os.chdir('..')
    output = np.genfromtxt('liveAlgo/submissions/preds.csv',delimiter=',')
    # get the seizure probability of each clip
    preds = output[1:,1]
    #delete intermediate files (test, data-cache, preds)
    r = glob.glob('R951/*')
    for i in r:
        os.remove(i)
    r = glob.glob('liveAlgo/data-cache/data_test*')
    for i in r:
        os.remove(i)
    r = glob.glob('liveAlgo/data-cache/predictions*')
    for i in r:
        os.remove(i)
    r = glob.glob('liveAlgo/submissions/*')
    for i in r:
        os.remove(i)
    
    # here we convolve over a few seconds to make the actual seizure calls
    # we look at 3 consecutive seconds, and need the sum of the seizure probabilities to be over 2.5
    finalPreds = np.convolve(preds, [1,1,1])>=2.5
    # find the indices when a seizure is detected
    idx = np.where(finalPreds)[0]
    
    if idx.any():
        #right now we will just look at the first detected seizure. It is possible that 
        #there are multiple seizures in the 30 minute window
        # Use this code to get the time stamp of the seizure and write to an output file
        numSteps = idx[0]*fs 
        timeOfDetect = df.iloc[numSteps].name
        with open("szCalls.txt","a") as text_file:
            text_file.write('Seizure detected at ' + str(timeOfDetect) + '\n')
