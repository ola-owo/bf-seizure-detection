# -*- coding: utf-8 -*-
"""
Use this to pull data from Blackfynn. Will first be used to pull sz, then we will grab interictal segs.
Goal for now is to pull, put in numpy array, and save.

Will also use for 
"""

from blackfynn import Blackfynn
from datetime import datetime, timedelta
import scipy.io as sio
import sys

username = sys.argv[1]
passwd = sys.argv[2]
tsid = sys.argv[3]
ptname = sys.argv[4]
interictalfile = sys.argv[5]

#bf = Blackfynn(username,passwd)

bf = Blackfynn(email=username,password=passwd)
bf.set_context('Mayo')

ts = bf.datasets()[0].items[0]

# get time-series object
#ts = bf.data.get_timeseries('N:fo:f6cd4d29-7916-417e-98b2-8d90586febd1') # jordan's 951 i think
#ts = bf.data.get_timeseries('N:fo:bad19c96-7193-4fbe-a3cc-45798aa6bb38') #R950 routine recording
#ts = bf.data.get_timeseries('N:fo:8cb28586-1439-4a30-9233-c138df54b652') #R950 loop
#ts = bf.data.get_timeseries(tsid)

# retrieve specific data (within timespan >= start < end)

# has interictal start and stop times in format: Jan 1 2017 1:30PM
with open(interictalfile) as f:
    times = f.read().splitlines()
for i in range(0,len(times),2):
    #tempStart = datetime.strptime(times[i],'%b %d %Y %I:%M%p')
    #tempEnd = datetime.strptime(times[i+1],'%b %d %Y %I:%M%p')
    tempStart = datetime.utcfromtimestamp(float(times[i])/1e6)
    tempStart = datetime.utcfromtimestamp(float(times[i+1])/1e6)    


    print(str(tempStart) + "until" + str(tempEnd))

    try:
        print('about to pull')
   #     df = bf.data.get_timeseries_data(ts, tempStart, tempEnd)
    	df = ts.get_data(start=tempStart,end=tempEnd)
    except:
        print('Pull failed at ' + str(tempStart) + '\n')
        continue

     
    ar = df.as_matrix()
        
    filename = 'intericatl'+str(i/2+1)+'.mat'
    sio.savemat(filename,{'clip':ar})
    print('.')
