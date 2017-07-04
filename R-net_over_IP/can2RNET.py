#!/Python3.4
#Python canbus functions for R-net exploration by Specter and RedDragonX

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


import socket
import struct
import sys
from time import *
import binascii #used in build_frame
import threading

#all functions take CAN messages as a string in "CANSEND" (from can-utils) format
"""
FORMAT FOR CANSEND (matches candump -l)
    <can_id>#{R|data}          for CAN 2.0 frames
    <can_id>##<flags>{data}    for CAN FD frames

<can_id> can have 3 (SFF) or 8 (EFF) hex chars
{data} has 0..8 (0..64 CAN FD) ASCII hex-values (optionally separated by '.')
<flags> a single ASCII Hex value (0 .. F) which defines canfd_frame.flags

e.g. 5A1#11.2233.44556677.88 / 123#DEADBEEF / 5AA# / 123##1 / 213##311
     1F334455#1122334455667788 / 123#R for remote transmission request.
"""

def build_frame(canstr):
    if not '#' in canstr:
        print('build_frame: missing #')
        return 'Err!'

    cansplit=canstr.split('#')
    lcanid=len(cansplit[0])
    RTR='#R' in canstr
    if lcanid == 3:
        canid=struct.pack('I',int(cansplit[0],16)+0x40000000*RTR)        
    elif lcanid == 8:
        canid=struct.pack('I',int(cansplit[0],16)+0x80000000+0x40000000*RTR)
    else:
        print ('build_frame: cansend frame id format error: ' + canstr)
        return 'Err!'
    can_dlc = 0
    len_datstr = len(cansplit[1])
    if not RTR and len_datstr<=16 and not len_datstr & 1:
        candat = binascii.unhexlify(cansplit[1]) 
        can_dlc = len(candat)
        candat = candat.ljust(8,b'\x00')
    elif not len_datstr or RTR:
        candat = b'\x00\x00\x00\x00\x00\x00\x00\x00'
    else:
        print ('build_frame: cansend data format error: ' + canstr)
        return 'Err!'
    return canid+struct.pack("B",can_dlc&0xF)+b'\x00\x00\x00'+candat


def dissect_frame(frame):
    # CAN frame packing/unpacking (see `struct can_frame` in <linux/can.h>)
    can_frame_fmt = "<IB3x8s"
    can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
    if can_id & 0x80000000:
        idl = 16
    else:
        idl = 6
    if can_id & 0x40000000:
        rtr = True
    else:
        rtr = False
    can_idtxt = '{:08x}'.format(can_id & 0x1FFFFFFF)[-idl:]
    return (can_idtxt + '#'+''.join(["%02X" % x for x in data[:can_dlc]]) + 'R'*rtr)

def cansend(s,cansendtxt):
    try:
        out=build_frame(cansendtxt)
        if out != 'Err!':
            s.send(out)
    except socket.error:
        print('Error sending CAN frame ' + cansendtxt)

def canrepeat_stop(thread):
    thread._stop = True

def canrepeatThread(s,cansendtxt,interval):
    interval /= 1000
    nexttime = time() + interval
    socketcanframe = build_frame(cansendtxt)
    while not threading.currentThread()._stop:
        s.send(socketcanframe)
        nexttime += interval
        if (nexttime > time()):
            sleep(nexttime - time())
    print(str(threading.currentThread())+' stopped')

def canrepeat(s,cansendtxt,interval): #interval in ms
    t = threading.Thread(target=canrepeatThread,args=(s,cansendtxt,interval),daemon=True)
    t._stop = False #threading.Event()
    t.start()
    print('Starting thread: ' + cansendtxt + ' ' +str(interval))
    return (t)

def canwait(s,canfiltertxt):
    can_idf_split = canfiltertxt.split(':')
    canidint = int(can_idf_split[0],16)
    mask = int(can_idf_split[1],16)
    cancheckint = 0
    while cancheckint != canidint:
        cf, addr = s.recvfrom(16)
        cancheckint = struct.unpack("I", cf[:4])[0] & mask
    return cf

def canwaitRTR(s,canfiltertxt):
    can_idf_split = canfiltertxt.split(':')
    canidint = int(can_idf_split[0],16)+0x40000000
    mask = int(can_idf_split[1],16)+0x40000000
    cancheckint = 0
    while cancheckint != canidint:
        cf, addr = s.recvfrom(16)
        cancheckint = struct.unpack("I", cf[:4])[0] & mask
    return cf

def opencansocket(busnum):
    busnum=str(busnum)
    #open socketcan connection
    try:
        cansocket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        cansocket.bind(('can'+busnum,))
        print('socket connected to can'+busnum)
    except socket.error:
        print ('Failed to open can'+busnum+' socket')
        print ('Attempting to open vcan'+busnum+' socket')
        try:
            cansocket.bind(('vcan'+busnum,))
            print('socket connected to vcan'+busnum)
        except:
            print ('Failed to open vcan'+busnum+' socket')
            cansocket = ''
    return cansocket
