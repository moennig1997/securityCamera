import cv2
import sys
import imagehash
from PIL import Image
import datetime
import time

c = cv2.VideoCapture(0)
prev_hash = None

while True:
	time.sleep(1)

	r, img = c.read()

	if r == True:

		hash = imagehash.average_hash(Image.fromarray(img))
		print(hash)
		print(type(hash))

		if prev_hash is None or prev_hash != hash:
			now = datetime.datetime.now()
			datestr = '{0:%Y%m%d%H%M%S}'.format(now)
			print('Detect somthing change!!....' + datestr)

			cv2.imwrite(datestr + 'detected.jpg', img)
			prev_hash = hash

	print('next')





