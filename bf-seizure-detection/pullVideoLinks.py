
import sys
import re

from blackfynn import Blackfynn
from settings import VIDEO_DIR_IDs, PL_ROOT

def makeVideoLinkFile(vidList, url_root, filename):
	'Write list of video URLs and timestamps to file filename'
	#get timestamp-get url

	with open(filename, 'w') as f:
		for video in vidList:
			#Retrieve timestamp string in video name
			timestamp=re.search('\d{14}', video.name)
			if timestamp != None:
				f.write('%s : %s\n' % (str(timestamp.group(0)), url_root+video.id))

		print(('video urls written to %s.' % (filename)))

if __name__ == '__main__':
    ptName = sys.argv[1]
    vidCollectionID = VIDEO_DIR_IDs[ptName]

    bf = Blackfynn()
    vids = bf.get(vidCollectionID)
    url_root='https://app.blackfynn.io/'+bf.context.id+'/datasets/'+vids.dataset+'/viewer/'
    makeVideoLinkFile(vids, url_root, PL_ROOT + '/videoLinks/%s_vidMap.txt' % ptName)