# -*- coding: utf-8 -*-
"""
Use this to pull seizure data from Blackfynn for the pipeline
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

# open up the BF dataset (again, this works for R951 but does not generalize)
# If you were to use a MEF file, you could point to it here
bf = Blackfynn(email=username,password=passwd)
bf.set_context('Mayo')
ts = bf.datasets()[0].items[0]

# get the annotation times in uUTC from file
with open(szfile) as f:
 	times = f.read().splitlines()
for i in range(0,len(times),2):
    	tempStart = datetime.utcfromtimestamp(float(times[i])/1e6)
    	tempEnd = datetime.utcfromtimestamp(float(times[i+1])/1e6)
    
    	print(str(tempStart) + "until" + str(tempEnd))
	# pull the data for each seizure
    	try:
        	print('about to pull')
    		df = ts.get_data(start=tempStart,end=tempEnd)
	except:
        	print('Pull failed at ' + str(tempStart) + '\n')
        	continue

    	print(df)     
    	ar = df.as_matrix()
        # save in mat file
    	filename = 'sz'+str(i/2+1)+'.mat'
    	sio.savemat(filename,{'clip':ar})
    	print('.')
