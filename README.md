PGDT R-Net CAN library for power-wheelchairs with R-Net electronics
================================================

By Stephen Chavez & Specter

Discord server (2021 update)
===============
I don't know what happened, but can2RNET has gotten a lot of attention lately. It's a good thing. However, various people forked my project and done different things over the years. Nobody has really wanted to contribute publicly. So, to help with that. I started a Discord Server. Please join it.

https://discord.gg/mYqJSS5

Projects that use this
======================
- [Smart Wheels](https://github.com/ysshah/SmartWheels)
   - https://youtu.be/6C0-vXI56D4
   - https://www.youtube.com/watch?v=VejDcxrd6uk (Old video)
- Remote Control Demos
   - https://www.youtube.com/watch?v=wW4jzoRx98A
   - https://www.youtube.com/watch?v=jDMYnpxqKHw
- Kaspersky SAS 2017 Demo
   - https://www.youtube.com/watch?v=kJR1fNI8iNQ
   
Raspberry PI setup
=====================

- Raspberry Pi 3 (Model B)
- PiCan2 Pi hat board http://copperhilltech.com/pican-2-can-interface-for-raspberry-pi/
- R-Net cable
- Blank 2GB SD Card

To install PiCan2 on pi3, add to /boot/config.txt:
```
dtparam=spi=on 

dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25         
dtoverlay=spi-bcm2835
```

R-Net Wiring Pinout to CAN inferface
==================================
1. Strip a R-Net wire in half.
2. Connect the wire with this pinout:
```
white is can high
blue is can low
black is gnd
red is +vin
```
SocketCAN setup
================================== 

Add the following lines under file /etc/network/interfaces
```
allow-hotplug can0
iface can0 can static
        bitrate 125000
        up /sbin/ip link set $IFACE down
        up /sbin/ip link set $IFACE up
```
Add these kernel modules under /etc/modules
```
mcp251x
can_dev
```
Reboot the pi! Then you should see an can0 interface listed under the command `ifconfig`

Install CAN-UTILS
=================================
```
$ git clone https://github.com/linux-can/can-utils
or sudo apt-get install can-utils
```
R-Net command examples from the terminal
=========================================
```
$ candump can0 -L   # -L puts in log format
(1469933235.191687) can0 00C#
(1469933235.212450) can0 00E#08901C8A00000000
(1469933235.212822) can0 7B3#
(1469933235.251708) can0 7B3#

$ cansend can0 181C0D00#0840085008440840  #play a tune

$ cangen can0 -e -g 10  -v -v     #fuzz buss with random extended frames+data

$ candump -n 1 can0,7b3:7ff     #wait for can id 7B3
```

Or run `python3 JoyLocal.py` to control a R-Net based PWC using any usb gamepad connected to the pi3.

Python 3 is required.

Using different hardware
=========================================
CAN is a widely used communication protocol, so there are many different controllers available you could use instead of the Raspberry Pi setup described above. However, there are a few important points to consider:
- R-Net apparently uses low-speed fault-tolerant CAN as defined in ISO 11898-3, which means that it is able to continue normal operation even if one of the two data lines is disconnected. However, this is incompatible with high-speed CAN as defined in ISO 11898-2, so make sure to use a CAN transceiver that supports the fault-tolerant physical layer, otherwise no communication will be possible. Typical fault-tolerant CAN transceivers are the MCP2551 (which is used on the PiCAN2) and the TJA1055. A NXP A1050/C also works.
- Make sure that there is no termination resistor active on the board you are using (you can usually disconnect these using a jumper).
- The wheelchair is powered by its own batteries, which are a large, floating power supply. It is usually not earth-grounded. Keep this in mind when somehow connecting the wheelchair to the power grid (for example via a USB cable to a desktop computer), as there may be large voltage differences resulting in short current spikes the moment you make the connection. Use proper isolation for all connections (including power and ground) to avoid damaging your hardware.
