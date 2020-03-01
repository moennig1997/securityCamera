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

# import library for slack
from slackclient import SlackClient

import logging


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

def slack_send_message(client, channel_id, message):
    client.api_call(
        "chat.postMessage",
        channel=channel_id,
        text=message
	)

#main routin

#create logger
logger = logging.getLogger('seccamera_application')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('securityCamera.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


# Read paramater from config file
config = ConfigParser.ConfigParser()
config.read('securityCamera.ini')
interval = float(config.get('settings','interval')) 
threshold = int(config.get('settings','threshold')) 
camera_num =  int(config.get('settings','cameraNum'))
retention_time =  int(config.get('settings','retentionTime'))
tailcut_time =  int(config.get('settings','tailcutTime'))
slack_token = config.get('settings','slackToken')

# Read mail paramater from mail config file
config.read('mail.ini')
from_addr = config.get('mail', 'from_addr')
to_addr = config.get('mail', 'to_addr')
smtp_host = config.get('mail', 'smtp_host')
smtp_port = int(config.get('mail', 'smtp_port'))
smtp_user = config.get('mail', 'smtp_user')
smtp_pass = config.get('mail', 'smtp_pass')

logger.info(from_addr) 
logger.info(to_addr)
logger.info(smtp_host)
logger.info(smtp_port)
logger.info(smtp_user)
logger.info(smtp_pass)


# create video capture object
c = cv2.VideoCapture(camera_num)
time.sleep(5)

# Initialize variable
prev_hash = None
change_detected = 0
detect_images = []

# create slack client

slack_client = SlackClient(slack_token)


while True:	
	try:
		time.sleep(interval)

		# read image from camera
		r, img = c.read()
		if r == True:

			# get hash value 
			hash = imagehash.average_hash(Image.fromarray(img))

			# compare hash from 
			if prev_hash is None or prev_hash - hash > threshold:
				change_detected = retention_time
				now = datetime.datetime.now(timezone('Asia/Tokyo'))
				datestr = '{0:%Y%m%d%H%M%S}'.format(now)
				logger.info('Detect something change!!....' + datestr)
				cv2.imwrite(datestr + 'detected.jpg', img)
				detect_images.append(datestr + 'detected.jpg')

			elif change_detected > 0:

				#now = datetime.datetime.now(timezone('Asia/Tokyo'))
				#datestr = '{0:%Y%m%d%H%M%S}'.format(now)
				#logger.info('Detect something change!!....' + datestr)
				#cv2.imwrite(datestr + 'detected.jpg', img)
				#detect_images.append(datestr + 'detected.jpg')

				change_detected -= 1
				logger.info('counter:'+str(change_detected))

				if change_detected == 0:
					if len(detect_images) > 1:
						if tailcut_time != 0 :
							del(detect_images[-tailcut_time:])
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

						msg = create_message(from_addr, to_addr, 'Detect something change!!....' + datestr,'Detect something change!!....' + datestr, 'attache_' + datestr + '.jpeg')
						send(from_addr, to_addr, smtp_host, smtp_port, smtp_user, smtp_pass, msg )
						slack_send_message(slack_client,"home","Detect something change!!....")
						change_detected = 0

						logger.info('send message')
			prev_hash = copy.deepcopy(hash)
		else :
			c.release()
			c = cv2.VideoCapture(camera_num)

		#logger.info('next')

		if cv2.waitKey(1) & 0xFF == ord('q'):
			break

	except Exception as e:
		logger.info(e)
		pass;



