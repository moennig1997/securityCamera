# -*- coding: utf-8 -*-

import cv2
import imagehash
from PIL import Image
import datetime
import time
from pytz import timezone
import ConfigParser
import copy

# import library for mail
import smtplib
from email import Encoders
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.utils import formatdate
from retry import retry

def create_message(from_addr, to_addr,  subject, body, attach):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Date'] = formatdate()

    body = MIMEText(body)
    msg.attach(body)

    # 添付ファイルのMIMEタイプを指定する
    attachment = MIMEBase('image','jpeg')
    # 添付ファイルのデータをセットする
    file = open(attach)
    attachment.set_payload(file.read())
    file.close()
    Encoders.encode_base64(attachment)
    msg.attach(attachment)
    attachment.add_header("Content-Disposition","attachment", filename=attach)

    return msg

@retry(tries=3)
def send(from_addr, to_addr, smtp_host, smtp_port, smtp_user, smtp_pass, msg):
    smtpobj = smtplib.SMTP(smtp_host, smtp_port)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(smtp_user, smtp_pass)
    smtpobj.sendmail(from_addr, to_addr, msg.as_string())
    smtpobj.close()


# Read paramater from config file
config = ConfigParser.ConfigParser()
config.read('securityCamera.ini')
interval = float(config.get('settings','interval')) 
threshold = int(config.get('settings','threshold')) 


config.read('mail.ini')
from_addr = config.get('mail', 'from_addr')
to_addr = config.get('mail', 'to_addr')
smtp_host = config.get('mail', 'smtp_host')
smtp_port = int(config.get('mail', 'smtp_port'))
smtp_user = config.get('mail', 'smtp_user')
smtp_pass = config.get('mail', 'smtp_pass')

print(from_addr) 
print(to_addr)
print(smtp_host)
print(smtp_port)
print(smtp_user)
print(smtp_pass)


# image capture
c = cv2.VideoCapture(0)
time.sleep(5)
c.read()

prev_hash = None

change_detected = 0
detect_images = []


try:
	while True:	
		time.sleep(interval)
		r, img = c.read()
		if r == True:

			hash = imagehash.average_hash(Image.fromarray(img))
			print(hash)
			print(prev_hash)

			if prev_hash is None or prev_hash - hash > threshold:
				change_detected = 1
				now = datetime.datetime.now(timezone('Asia/Tokyo'))
				datestr = '{0:%Y%m%d%H%M%S}'.format(now)
				print('Detect somthing change!!....' + datestr)
				cv2.imwrite(datestr + 'detected.jpg', img)
				detect_images.append(datestr + 'detected.jpg')
			elif change_detected == 1:
				attache_image = Image.new('RGB', (640, 480 * len(detect_images)))
				for i, image in enumerate(detect_images):
					im = Image.open(image)
					attache_image.paste(im, (0, 480*i))
					im.close()

				now = datetime.datetime.now(timezone('Asia/Tokyo'))
				datestr = '{0:%Y%m%d%H%M%S}'.format(now)
				attache_image.save('attache_' + datestr + '.jpeg')
				attache_image.close()
				detect_images = []

				msg = create_message(from_addr, to_addr, 'Detect somthing change!!....' + datestr,'Detect somthing change!!....' + datestr, 'attache_' + datestr + '.jpeg')
				send(from_addr, to_addr, smtp_host, smtp_port, smtp_user, smtp_pass, msg )
				change_detected = 0
			else:
				change_detected = 0

			
			prev_hash = copy.deepcopy(hash)

		print('next')

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

except KeyboardInterrupt:
	c.release()

