# -*- coding: utf-8 -*-
"""
Use this to pull non-seizure (interictal) data from Blackfynn
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



bf = Blackfynn(email=username,password=passwd)
bf.set_context('Mayo')
ts = bf.datasets()[0].items[0]


# has interictal start and stop times in uUTC format
with open(interictalfile) as f:
    times = f.read().splitlines()
for i in range(0,len(times),2):
    tempStart = datetime.utcfromtimestamp(float(times[i])/1e6)
    tempStart = datetime.utcfromtimestamp(float(times[i+1])/1e6)    


    print(str(tempStart) + "until" + str(tempEnd))

    try:
        print('about to pull')
    	df = ts.get_data(start=tempStart,end=tempEnd)
    except:
        print('Pull failed at ' + str(tempStart) + '\n')
        continue

     
    ar = df.as_matrix()
        
    filename = 'intericatl'+str(i/2+1)+'.mat'
    sio.savemat(filename,{'clip':ar})
    print('.')
