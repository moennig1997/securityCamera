# -*- coding: utf-8 -*-

import cv2
import imagehash
from PIL import Image
import datetime
import time
import ConfigParser
import copy

# Read paramater from config file
config = ConfigParser.ConfigParser()
config.read('securityCamera.ini')
interval = float(config.get('settings','interval')) 
threshold = int(config.get('settings','threshold')) 

# image capture
c = cv2.VideoCapture(0)
c.read()


prev_hash = None

try:
	while True:	
		time.sleep(interval)
		r, img = c.read()
		if r == True:

			hash = imagehash.average_hash(Image.fromarray(img))
			print(hash)
			print(prev_hash)

			if prev_hash is None or prev_hash - hash > threshold:
				now = datetime.datetime.now()
				datestr = '{0:%Y%m%d%H%M%S}'.format(now)
				print('Detect somthing change!!....' + datestr)
				cv2.imwrite(datestr + 'detected.jpg', img)
			
			prev_hash = copy.deepcopy(hash)

		print('next')
		
		k = cv2.waitKey(1)
		if k == ord('q'):
			break

except KeyboardInterrupt:
	c.release()


