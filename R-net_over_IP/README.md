PGDT R-Net CAN library for power-wheelchairs with R-Net electronics
================================================

By Stephen Chavez & Specter

Demo Video
======================
- [OPEN-SOURCE PROJECT: Remote exploit of wheelchair R-Net protocol and so can you](https://youtu.be/wW4jzoRx98A)


Controls
======================
![Screenshot](demo.jpg)

Hardware required:
=====================

- Raspberry Pi 3 (Model B)

- PiCan2 w/ SMPS board made by SkPang (great board SkPang!)
	- http://copperhilltech.com/pican-2-can-interface-for-raspberry-pi/
	- http://skpang.co.uk/catalog/pican2-canbus-board-for-raspberry-pi-23-with-smps-p-1476.html

- R-Net cable
	- cable will need to be cut to reveal the four conductors inside
	- you only need enough cable to connect Pi3 to whichever R-net port you wish to use

- WiFi router - secured with WPA2 or better

- Linux box

- USB game controller "xbox 360 like"



Raspberry PI setup
=====================
1. Install latest Raspbian onto Pi (https://www.raspberrypi.org/downloads/)

2. Attach PiCan2 Board to Pi3.

3. Boot Pi, and after selecting the correct keyboard in raspi-config ;-)
	- Enable ssh.

4. To install PiCan2 on pi3, add to /boot/config.txt:
```
dtparam=spi=on 

dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25         
dtoverlay=spi-bcm2835
```


5. Add the following lines under file /etc/network/interfaces
```
allow-hotplug can0
iface can0 can static
        bitrate 125000
        up /sbin/ip link set $IFACE down
        up /sbin/ip link set $IFACE up
```
6. Add these kernel modules under /etc/modules
```
mcp251x
can_dev
```
Reboot the pi! 

Once your are back to the terminal: 
```
ifconfig
```
You should see a can0 interface listed.

If not, you won't be able to proceed.

Install CAN-UTILS
=================================
```
$ git clone https://github.com/linux-can/can-utils
or sudo apt-get install can-utils
```

Clone this github onto Pi and "remote" machine
=================================
```
$ git clone https://github.com/redragonx/can2RNET
```


Attach R-net cable to PiCan2 board
=================================
Split and strip the R-net cable to the length you want.
Tin the ends of the four wires inside the cable.
Note: the two power wires (BLK and RED) are a bit too large to fit into the tiny screw terminals on the PiCan2 board.  I used a grinding wheel to narrow them down by sanding the tinned wires to about half their original size.  There are many other ways to accomplish the same thing: filing, scraping, or eliminate copper strands prior to tinning.
Screw the R-net wires into the terminal strip on the PiCan2 board.
```
	RED -> +12V
	BLK -> GND
	BLU -> CAN_L
	WHT -> CAN_H
```

Configure Pi3 to connect to router
=================================
This router will be used to route traffic between the "remote" machine and the Pi3 residing on your chair.  By configuring your supplicant now, you will be able to access the Pi3 via ssh later.
After confirming that networking is working, sudo shutdown now.

Connect Pi3 to power wheelchair R-net port
=================================
It doesn't matter what port you connect it to.  R-net runs on CANbus.  The bus is shared by all devices on the network regardless of their position on the bus.
The Pi will draw it's power from the chair electrical system (24V).  After plugging the Pi into an R-net port, it should power on and boot as usual.


Connect "remote" machine to router
=================================
This machine will be used to ssh into Pi.  It will also host the USB game controller.

SSH into Pi
=================================
Find your Pi's IP address.  I use nmap.  You can check your routers DHCP leases page.  Alternatively, you can give the Pi a static IP address so you'll always know where its going to be on the network.
ssh into pi.

once you are in, go to the can2RNET/R-net_over_IP directory.
```
python3 JoyClient.py
```
Chair's JSM should play a little tune indicating the exploit was successful.

Plug in USB controller
=================================
check devices to ensure the controller appears to Linux in a way our code expects it to.
```
ls /dev/input/js*
```
controllers often follow a de-facto standard that Linux can easily process... except when they don't.

Open connection between JoyServer and JoyClient
=================================
on "remote" machine:
```
python3 JoyServerLeftStick.py xxx.xxx.xxx.xxx
```
where xxx.xxx.xxx.xxx is the IP address of your Pi3

PLEASE be careful!
=================================
If all is working correctly the "remote" machine should now be controlling various aspects of the wheelchair.  We've mapped X-Y to the left stick on the USB controller.  Additionally, buttons map to MAXSPEED, HORN, and HEADLIGHTS/FLASHERS.

Seriously... both of us were injured and humbled during the creation of this code.  We've tried to make it fail-safe.  You are a beta-tester.  BEWARE.  What can go wrong WILL go wrong.  So stay clear of cliffs, canals, china-shops, monster-trucks, puppies, or anything else that can injure you or that you might injure due to some kind of bug we did not anticipate.

We've waited over a year to release this code publicly.  If you have gotten this far in trying to get this to work then you must be prepared to assume the risk of something going wrong.

So, that was scary.    But the good news is we tested this code at defcon24, in the hallways of the con, with many people walking all around us, in a VERY hostile radio environment, and there was not a single incident after many hours of crazed and irresponsible use.  Your mileage may vary.  Nuff said.


