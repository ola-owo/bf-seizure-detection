# -*- coding: utf-8 -*-
"""
Use this to pull data from Blackfynn. Will first be used to pull sz, then we will grab interictal segs.
Goal for now is to pull, put in numpy array, and save.



This version will be used as a standalone function for the training pipeline 
"""

from blackfynn import Blackfynn
from datetime import datetime, timedelta
import scipy.io as sio
import sys

username = sys.argv[1]
passwd = sys.argv[2]
tsid = sys.argv[3]
ptname = sys.argv[4]
szfile = sys.argv[5]
#def pullSzClips(username, passwd, tsid, ptname, szfile):

bf = Blackfynn(email=username,password=passwd)
bf.set_context('Mayo')

ts = bf.datasets()[0].items[0]
# get time-series object
#ts = bf.data.get_timeseries(tsid)
#ts = bf.data.get_timeseries('N:fo:f6cd4d29-7916-417e-98b2-8d90586febd1') # jordan's 951 i think
#ts = bf.data.get_timeseries('N:fo:3ca99d71-63e5-4fe1-a7d6-ffe5cd5a54ed') # 951 routine 
#ts = bf.data.get_timeseries('N:fo:856511ca-0d3d-4922-9ed2-991c8e699ec5') # 951 loop
#ts = bf.data.get_timeseries('N:fo:bad19c96-7193-4fbe-a3cc-45798aa6bb38') #R950 routine recording
#ts = bf.data.get_timeseries('N:fo:8cb28586-1439-4a30-9233-c138df54b652') #R950 loop
#ts = bf.data.get_timeseries('N:fo:adfa464f-2ad0-414f-ba90-5541933f6af5') #Ripley routine
#allStart = datetime.datetime(2016,11,1,1,1,)
#for i in range (1,100):
    #tempStart = allStart + datetime.timedelta(0,14400)
    #tempEnd = tempStart +datetime.timedelta(0,60)
#tempStart = datetime.datetime(2016,11,8,19,30,36)
#tempEnd = datetime.datetime(2016,11,8,19,30,51)

    # retrieve specific data (within timespan >= start < end)

with open(szfile) as f:
 	times = f.read().splitlines()
for i in range(0,len(times),2):
    	tempStart = datetime.utcfromtimestamp(float(times[i])/1e6)# - timedelta(seconds=30)
    #tempEnd = tempStart + timedelta(seconds=30)
    	tempEnd = datetime.utcfromtimestamp(float(times[i+1])/1e6)
    
    	print(str(tempStart) + "until" + str(tempEnd))

    	try:
        	print('about to pull')
        #	df = bf.data.get_timeseries_data(ts, tempStart, tempEnd)
    		df = ts.get_data(start=tempStart,end=tempEnd)
	except:
        	print('Pull failed at ' + str(tempStart) + '\n')
        	continue

    	print(df)     
    	ar = df.as_matrix()
        
    	filename = 'sz'+str(i/2+1)+'.mat'
    	sio.savemat(filename,{'clip':ar})
    	print('.')

#if __name__ == "__main__":
#	pullSzClips()
