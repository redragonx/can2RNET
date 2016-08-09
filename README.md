================================================
R-Net CAN library for power-wheelchairs with R-Net electronics
================================================

By Stephen Chavez & Specter


Raspberry PI setup
=====================

- Raspberry Pi 3 (Model B)
- PiCan2 Pi hat board
- R-Net cable
- Blank 2GB SD Card

To install PiCan2 on pi3, add to /boot/config.txt:
`dtparam=spi=on 
dtoverlay=mcp2515-can0-overlay,oscillator=16000000,interrupt=25 		
dtoverlay=spi-bcm2835-overlay`

SocketCAN setup and examples
================================== 

`
$ sudo ip link set can0 up type can bitrate 125000

$ git clone https://github.com/linux-can/can-utils
or sudo apt-get install can-utils

$ candump can0 -L   # -L puts in log format
(1469933235.191687) can0 00C#
(1469933235.212450) can0 00E#08901C8A00000000
(1469933235.212822) can0 7B3#
(1469933235.251708) can0 7B3#

$ cansend can0 181C0D00#0840085008440840  #play a tune

$ cangen can0 -e -g 10  -v -v     #fuzz buss with random extended frames+data

$ candump -n 1 can0,7b3:7ff     #wait for can id 7B3`
