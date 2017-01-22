import time
import datetime
import RPi.GPIO as GPIO
import subprocess
from Adafruit_CharLCD import Adafruit_CharLCD
import smtplib
import operator
import itertools

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
	
GPIO.setmode(GPIO.BCM)
chk_coffee = 20
TRIG = 23
ECHO = 24
LED=17
GPIO.setup(LED,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)
GPIO.setup(25, GPIO.IN)

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)
GPIO.output(TRIG, False)
rate = 60
cost_per_ml = 0.125
lcd = Adafruit_CharLCD(rs=26, en=19,
                       d4=13, d5=6, d6=5, d7=11,
                       cols=16, lines=2)
lcd.clear()
def main():
	chk_coffee_540=1
	while True:
		print "Checking the amount of coffee left in container"
		f= open('coffee.txt', 'r+')
		tot_coffee=int(f.readline())
		print "Coffee left: " + str(tot_coffee)
		if GPIO.input(25):
			tot_coffee=1000
			print "Coffee refilled"
			with open('coffee.txt', 'w') as f:
			  		f.write('%d' % tot_coffee)
			chk_coffee_540=1
			lcd.clear()
                        lcd.message('Coffee\nrefilled...')
			time.sleep(2)
			print "Coffee refilled"

		if tot_coffee<540 and chk_coffee_540==1:
			lcd.clear()
                	lcd.message('Place your glass\n& Scan ur id')
                
			send_alert_mail()
			chk_coffee_540=0

		if tot_coffee <180 :
			print "Please refill the container!"
			lcd.clear()
			lcd.message('Dispenser out\n  of order')
			#time.sleep(10)
			#time.sleep(10)
			#set GPIO PIN HIGH signifies coffee dispenser out-of use
			#use a switch which can act as a reset button after the container has been filled
			while not GPIO.input(25):		#Check GPIO pin input of a pin corresponding to reset button 
				tot_coffee=1000
				
			  	chk_coffee_540=1
				GPIO.output(LED, True)
			with open('coffee.txt', 'w') as f:
			  		f.write('%d' % tot_coffee)
			GPIO.output(LED,False)
			lcd.clear()
			lcd.message('Coffee\nrefilled...')
			time.sleep(2)
			print "Coffee refilled"
			continue
		
		
		#time.sleep(1)
		subprocess.Popen(["python","lcd.py"],stdout=subprocess.PIPE).communicate()
		lcd.clear()
		lcd.message('Place your glass\n& Scan ur id')
		time.sleep(2)
		check_glass_flag=read_from_ultrasonic_sensor()
		
		if check_glass_flag!=-1:
			print "Glass detected! scan your id"
			time.sleep(1)
			#lcd.message('place ur id')
			#lcd.clear()
			
			user_id=barcode_scan_check_user()

			if user_id != -1 : #suppose the barcode_scan_chk_user returns -1 for invalid users
				#lcd.message('id: '+str(user_id)+'\ndont rm glass')
				print "User with id "+str(user_id)
				lcd.clear()
				lcd.message('Coffee\n  dispensing...')
				start = time.time()
				# This part is protected :P
				#********************************************************************************************
				while True:
					chk_glass_now = read_from_ultrasonic_sensor()
					if chk_glass_now == -1:
						GPIO.output(21,False)
						time_dispense=time.time()-start
						break

					time_dispense=time.time()-start
					if time_dispense > 4:
						GPIO.output(21,False)
						break
					if check_glass_flag!=-1:
						check_glass_flag=-1
						GPIO.output(21,True)
					time.sleep(0.01)
					#print time_dispense
					# print "Coffee dispening" + str(time_dispense)
					
				#*********************************************************************************************
				
				#lcd.message('Coffee filled!')
				#GPIO.output(21,False)
				#time.sleep(0.5)
				print "Coffee filled! \n take your glass"
				amt_coffee=(rate)*time_dispense

				# print str(amt_coffee)
				time_stamp=datetime.datetime.now()
				tot_coffee=tot_coffee-amt_coffee
				price = amt_coffee*cost_per_ml

				#lcd.clear()
				price=round(price,2)
				cmd=["python","lcd.py"]
				output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
				lcd.clear()
				#time.sleep(3)
				lcd.message(' User:'+str(user_id)+'\n   Price:'+str(price))
				if GPIO.input(25):
					tot_coffee=1000
					print "Coffee refilled"
					with open('coffee.txt', 'w') as f:
					  		f.write('%d' % tot_coffee)
					chk_coffee_540=1
					lcd.clear()
		                        lcd.message('Coffee\nrefilled...')
					time.sleep(2)
					print "Coffee refilled"
				time.sleep(3)
				with open('user_trans.txt', 'a+') as f:
			  		f.write('%s %d %f %d %d\n' %(str(user_id),amt_coffee,price,time_stamp.year,time_stamp.month))
			
			
				deleteContent('coffee.txt')
				lcd.clear()
	                        lcd.message('   Thank \n    you :)')
				with open('coffee.txt', 'w') as f:
			  		f.write('%d' % tot_coffee)
			  	#lcd.clear()
			

							
			send_mail_per_month()
			#send_mail_now(user_id, amt_coffee, price)
			time.sleep(3)
			# print 'end'
		if GPIO.input(25):
			tot_coffee=1000
			print "Coffee refilled"
			with open('coffee.txt', 'w') as f:
			  		f.write('%d' % tot_coffee)
			chk_coffee_540=1
			lcd.clear()
                        lcd.message('Coffee\nrefilled...')
			time.sleep(2)
			print "Coffee refilled"
		#lcd.clear()
		

def barcode_scan_check_user():
	output = subprocess.Popen(["zbarcam","--raw","--nodisplay","/dev/video0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	y= output.stdout.readline()
	print "Barcode reader reads " + str(y)
	output.kill()
	return y.split("\n")[0]

def read_from_ultrasonic_sensor():
	#time.sleep(0.6)
	GPIO.output(TRIG, True)
	time.sleep(0.00001)
	GPIO.output(TRIG, False)
	while GPIO.input(ECHO)==0:
		pulse_start = time.time()

	while GPIO.input(ECHO)==1:
		pulse_end = time.time()    

	pulse_duration = pulse_end - pulse_start
	distance = pulse_duration * 17150
	#print "Distance: ",distance,"cm"
	if distance<7:
		distance =1
	else:
		distance = -1
	return distance


def deleteContent(fName):
    	with open(fName, "w"):
        	pass

def send_mail_per_month():
	today=datetime.datetime.now()
	list_user=[]
	if True:
		if True:
	# if(today.day==20): #It should be a particular day of the month
	# 	if(today.hour == 04 and today.minute >= 20 and today.minute<=40 ):
	# 		#send mail
			print 'sending monthly mail'
			f= open('user_trans.txt', 'r+')
			for data in f:
				data=data.rstrip('\n') #Removes \n
				d=data.split(' ')
				print d
				list_user.append((int(d[0]),d[1],d[2],d[3],d[4]))
			f.close()
		
			#print(list_user)
			sort_user=[list(g) for k,g in itertools.groupby(sorted(list_user,key=operator.itemgetter(0)),operator.itemgetter(0))]
				
			#print(sort_user)
			s = smtplib.SMTP_SSL('smtp.gmail.com',465)
			s.login("abhisandhyasp.ap@gmail.com", "**********")
			for user in sort_user:
				user_id=user[0][0]
				total=0.0
				tot_coffee_drnk=0
				sub='Bill for user: '
				sub=sub+(str(user_id)+'\n')
				print(user_id)

				for user_tran in user:
					if int(user_tran[4])== today.month and int(user_tran[3])==today.year:
						# sub=sub+('Month: '+str(user_tran[4])+' '+'Year: '+str(user_tran[3])+'  Amt of coffee: '+' '+str(user_tran[1])+'ml'+' '+'Price: '+'Rs.'+str(user_tran[2])+'<br>')
						total=total+float(user_tran[2])
						tot_coffee_drnk = tot_coffee_drnk+int(user_tran[1])
				sub=sub+('<br>'+'Total Bill: '+'Rs.'+str(total)+'<br> Total coffee consumed '+str(tot_coffee_drnk)+'ml<br>')
				html = """<html><body>"""+sub+	"""<body><html>"""
				me = "abhisandhyasp.ap@gmail.com"
				you = ""+str(user_id)+""+"@daiict.ac.in"

				# Create message container - the correct MIME type is multipart/alternative.
				msg = MIMEMultipart('alternative')
				part2 = MIMEText(html, 'html')
				msg['Subject'] = "Coffee bill for Month" +str(user_tran[4])+"," +str(user_tran[3])+"."
				msg['From'] = me
				msg['To'] = you
				msg.attach(part2)
				s.sendmail(me, you, msg.as_string())
			s.quit()
			#time.sleep(180)


def send_mail_now(user_id, amt_coffee, price):
	# me == my email address
	# you == recipient's email address
	me = "abhisandhyasp.ap@gmail.com"
	you = ""+user_id+""+"@daiict.ac.in"

	# Create message container - the correct MIME type is multipart/alternative.
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Coffee bill for last purchase"
	msg['From'] = me
	msg['To'] = you
	x=int(amt_coffee)
	# Create the body of the message (a plain-text and an HTML version).

	html = """\
	<html>
	  <head></head>
	  <body>
	    <p>Hi,<br>
	       Amount of coffee purchased """+str(x)+"""
	       <br>
	       Price is """+str(price)+"""<br>Note: This is just testing<br>
	    </p>
	  </body>
	</html>
	"""

	# Record the MIME types of both parts - text/plain and text/html.

	part2 = MIMEText(html, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.

	msg.attach(part2)

	# Send the message via local SMTP server.
	s = smtplib.SMTP_SSL('smtp.gmail.com',465)
	s.login("abhisandhyasp.ap@gmail.com", "**********")    
	# sendmail function takes 3 arguments: sender's address, recipient's address
	# and message to send - here it is sent as one string.
	s.sendmail(me, you, msg.as_string())
	s.quit()		

def send_alert_mail():
	me = 'abhisandhyasp.ap@gmail.com'
	owner = ['biren25.prajapati@gmail.com','akash18modi@gmail.com', 'aalishadalal1996@gmail.com', 'malvikasingh2k@gmail.com']
	msg = MIMEMultipart('alternative')
	msg['Subject'] = "Dispenser alert"
	msg['From'] = me
	
	# Create the body of the message (a plain-text and an HTML version).

	html = """\
	<html>
	  <head></head>
	  <body>
	    <p>Coffee is less than 540ml, refill it immediately<br>
	    </p>
	  </body>
	</html>
	"""
	# Send the message via local SMTP server.
        s = smtplib.SMTP_SSL('smtp.gmail.com',465)
        s.login("abhisandhyasp.ap@gmail.com", "**********")
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
                

	
	for u in owner:
		# Record the MIME types of both parts - text/plain and text/html.
		msg['To'] = u
	
		part2 = MIMEText(html, 'html')

		# Attach parts into message container.
		# According to RFC 2046, the last part of a multipart message, in this case
		# the HTML message, is best and preferred.

		msg.attach(part2)

		s.sendmail(me, u, msg.as_string())
	s.quit()		


if __name__ == '__main__':
	main()
