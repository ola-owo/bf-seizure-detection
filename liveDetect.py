# -*- coding: utf-8 -*-
"""

@author: stevenbaldassano

This will be called at 30 minute intervals to download data and make predictions

"""
import numpy as np
from blackfynn import Blackfynn
import datetime
import scipy.io as sio
import sys,os
import glob
from subprocess import call

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
# get time-series object

#ts = bf.data.get_timeseries('N:fo:3ca99d71-63e5-4fe1-a7d6-ffe5cd5a54ed')
#ts = bf.data.get_timeseries('N:fo:856511ca-0d3d-4922-9ed2-991c8e699ec5') #loop recorder
bf.set_context('Mayo')
ts = bf.datasets()[0].items[0]
tempEnd = datetime.datetime.now()
tempStart = tempEnd - datetime.timedelta(0,1800)

#ts = bf.data.get_timeseries('N:fo:f6cd4d29-7916-417e-98b2-8d90586febd1')
#tempStart = datetime.datetime(2016,11,8,19,30,36)
#tempEnd = datetime.datetime(2016,11,8,19,30,51)


#d = bf.data.get_timeseries_data(ts, tempStart, tempEnd)
d = ts.get_data(start=tempStart,end=tempEnd)
d = d.drop_duplicates()
if d.shape[0]==0:
    print('no data in time segment...quitting \n')
    exit()
print('starting split...')
dfs = split_data(d)
print('done')
for df in dfs:
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
    #output will be a series of 0s and 1s (one for each clip) called preds
    #for now I will just save the clips and make sure this works. If it does
    #I will try to do it without saving to make it run faster
    
    for i in range(0,inputData.shape[0]):
        curData = inputData[i,:,:]
        filename = 'R951/R951_test_segment_' + str(i+1) + '.mat'
        sio.savemat(filename,{'data':curData, 'freq':fs})
    #subprocess.call('liveAlgo/seizure_detection.py')
    os.chdir('liveAlgo')
    #execfile('predict.py')
    ret = call(['python', 'predict.py'])
    os.chdir('..')
    output = np.genfromtxt('liveAlgo/submissions/preds.csv',delimiter=',')
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
    
    #end segment that should be replaced
    
    finalPreds = np.convolve(preds, [1,1,1])>=2.5
    idx = np.where(finalPreds)[0]
    #compute amount of time before detection to get the right timestamp
    
    if idx.any():
        #right now we will just look at the first detected seizure. It is possible that 
        #there are multiple seizures in the 30 second window
        numSteps = idx[0]*fs 
        timeOfDetect = df.iloc[numSteps].name
        with open("szCalls.txt","a") as text_file:
            text_file.write('Seizure detected at ' + str(timeOfDetect) + '\n')
