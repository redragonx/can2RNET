#!/python3

#Requires: socketCan, can0 interface

# This file is part of can2RNET.
#
# can2RNET is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# can2RNET is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import socket, sys, os, array, threading
from time import *
from fcntl import ioctl
from can2RNET import *

#JoyLocal_V2.py - Translate USB joystick x/y axis to Rnet and inject onto canbus
#Version 2: Extended to include more features, but also simplified joystick
#handling since it is not that interesting. Makes the code much shorter and
#simpler, but also means that button layout may vary on different controllers.

xthreshold = 8 * 0x10000 / 128
ythreshold = 8 * 0x10000 / 128
numModes = 4
numProfiles = 5

speed_range = 0
mode = 0
profile = 0

joystick_x = 0
joystick_y = 0
rnet_threads_running = True

def usb_joystick_read_thread(jsdev):
	global joystick_x
	global joystick_y
	global rnet_threads_running
	was_centered = False
	print('waiting for joystick to be centered')
	while rnet_threads_running:
		try:
			evbuf = jsdev.read(8)
			jtime, jvalue, jtype, jnumber = struct.unpack('IhBB', evbuf)
			if not was_centered and (joystick_x != 0 or joystick_y != 0):
				print('joystick not centered')
			else:
				was_centered = True
				if jtype & 0x02:
					handleAxis(jnumber, jvalue)
				elif jtype & 0x01:
					if jvalue == 1:
						handleButtonPress(jnumber)
					else:
						handleButtonRelease(jnumber)
		except:
			print("Error reading USB joystick")
			joystick_x = 0
			joystick_y = 0
			rnet_threads_running = False

def handleAxis(axisNum, value):
	global joystick_x
	global joystick_y
	if (axisNum == 0):
		if abs(value) > xthreshold:
			joystick_x = 0x100 + int(value * 100 / 128) >> 8 &0xFF
		else:
			joystick_x = 0
	elif (axisNum == 1):
		if abs(value) > ythreshold:
			joystick_y = 0x100 - int(value * 100 / 128) >> 8 &0xFF
		else:
			joystick_y = 0

def handleButtonPress(buttonNum):
	global speed_range
	global mode
	global profile
	if buttonNum == 0:
		if speed_range>0:
			speed_range -= 25
			print("SpeedRange: " + str(speed_range))
			RNETsetSpeedRange(speed_range)
	elif buttonNum == 1:
		RNETtoggleLights()
	elif buttonNum == 2:
		RNETsetHorn(True)
	elif buttonNum == 3:
		if speed_range<100:
			speed_range += 25
			print("SpeedRange: " + str(speed_range))
			RNETsetSpeedRange(speed_range)
	elif buttonNum == 4:
		RNETtoggleLeftIndicator()
	elif buttonNum == 5:
		RNETtoggleHazardsIndicator()
	elif buttonNum == 6:
		RNETtoggleRightIndicator()
	#button 7 unused
	elif buttonNum == 8:
		prev_mode = mode
		mode=(mode+1)%numModes
		print('Mode ' + str(prev_mode) + ' -> ' + str(mode))
		RNETsetMode(prev_mode, mode)
	elif buttonNum == 9:
		profile=(profile+1)%numProfiles
		print('Profile ' + str(profile))
		RNETsetProfile(profile)
	#buttons 10 and 11 unused

def handleButtonRelease(buttonNum):
	if buttonNum == 2:
		RNETsetHorn(False)

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
	if speed_range>=0 and speed_range<=0x64:
		cansend(can_socket,'0A040100#'+dec2hex(speed_range,2))
	else:
		print('Invalid RNET SpeedRange: ' + str(speed_range))

def RNETsetHorn(horn_on):
	cansend(can_socket,"0C040100#" if horn_on else "0C040101#")

def RNETtoggleLights():
	cansend(can_socket, "0C000404#")

def RNETtoggleLeftIndicator():
	cansend(can_socket, "0C000401#")

def RNETtoggleRightIndicator():
	cansend(can_socket, "0C000402#")

def RNETtoggleHazardsIndicator():
	cansend(can_socket, "0C000403#")

def RNETsetMode(prev_mode_num, new_mode_num):
	cansend(can_socket,"061#400"+dec2hex(prev_mode_num,1)+"0000") #suspend previous mode
	sleep(0.1) #some delay required
	cansend(can_socket,"061#000"+dec2hex(new_mode_num,1)+"0000")

def RNETsetProfile(profile_num):
	cansend(can_socket,"051#000"+dec2hex(profile_num,1)+"0000")

def RNET_JSMerror_exploit():
	print("Waiting for JSM heartbeat")
	canwait(can_socket,"03C30F0F:1FFFFFFF")
	t=time()+0.20
	print("Waiting for joy frame")
	joy_id = wait_rnet_joystick_frame(t)
	print("Using joy frame: "+joy_id)
	for i in range(0,3): #induce JSM error
		cansend(can_socket,'0c000000#')
	print("3 x 0c000000# sent")
	return(joy_id)

#THREAD: sends RnetJoyFrame every mintime seconds
def send_joystick_canframe(joy_id, mintime):
	nexttime = time() + mintime
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
	rnet_joystick_frame_raw = build_frame(rnet_joystick_id + "#0000") #prebuild the frame we are waiting on
	while rnet_threads_running:
		cf, addr = can_socket.recvfrom(16)
		if cf == rnet_joystick_frame_raw:
			cansend(can_socket, rnet_joystick_id + '#' + dec2hex(joystick_x, 2) + dec2hex(joystick_y, 2))

#Waits for any frame containing a Joystick position
#Returns: JoyFrame extendedID as text
def wait_rnet_joystick_frame(start_time):
	frameid = ''
	while frameid[0:3] != '020':  #just look for joystick frame ID (no extended frame)
		cf, addr = can_socket.recvfrom(16) #this is a blocking read, so if there is no canbus traffic it will sit forever (to fix!)
		candump_frame = dissect_frame(cf)
		frameid = candump_frame.split('#')[0]
		if time() > start_time:
			 print("JoyFrame wait timed out ")
			 return('Err!')
	return(frameid)

if __name__ == "__main__":
	#init usb joystick
	joystick_path = '/dev/input/js0'
	print('Opening %s...' % joystick_path)
	try:
		usb_joystick_dev = open(joystick_path, 'rb') # Open the joystick device.
	except IOError:
		print ('No joystick at ' + joystick_path + ', exiting.')
		sys.exit()
	print('Using USB joystick @ ' + str(usb_joystick_dev).split("'")[1])
	
	can_socket = opencansocket(0)
	if (can_socket == ''):
		print ('Cannot open CAN interface, exiting.')
		sys.exit()
	
	usb_joystick_read_thread = threading.Thread(
		target=usb_joystick_read_thread,
		args=(usb_joystick_dev,),
		daemon=True)
	usb_joystick_read_thread.start()
	
	#select control exploit
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
			args=(rnet_joystick_id,0.01,),
			daemon=True)
		sendjoyframethread.start()
	elif (user_selection == 2):
		inject_rnet_joystick_frame_thread = threading.Thread(
			target=inject_rnet_joystick_frame,
			args=(rnet_joystick_id,),
			daemon=True)
		inject_rnet_joystick_frame_thread.start()
	
	#watch and wait
	started_time = time()
	while threading.active_count() > 0 and rnet_threads_running: #output something as sign-of-life
		sleep(0.5)
		print(str(round(time()-started_time,2))+'\tX: '+dec2hex(joystick_x,2)+'\tY: '+dec2hex(joystick_y,2)+ '\tThreads: '+str(threading.active_count()))
	
	rnet_threads_running = False
	print("Exiting")
