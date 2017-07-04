#!/python3
# joystick based on: https://www.kernel.org/doc/Documentation/input/joystick-api.txt


import socket, sys, os, struct, array, threading
from time import *
from fcntl import ioctl
from can2RNET import *

debug = False


#host = '192.168.43.47' # FOR COOLPAD hotspot
#host = '192.168.43.83' # FOR LG hotspot
#host = '192.168.43.46' # FOR ALCATEL hotspot
host = '192.168.100.2' #
#host = 'localhost'
port = 13337
deadrange = 16
maxjoyposition = 100


if len(sys.argv) != 2:
       print('Using hardcoded IP address!')

       #sys.exit(0)

elif len(sys.argv) == 2:
	host = sys.argv[1]


class X360:

    axis_map = []
    button_map = []
    xthreshold = deadrange * 0x10000 / 128
    ythreshold = deadrange * 0x10000 / 128

    joyx = 0
    joyy = 0
    exbuf = ""
    outstr = "0000"


    # We'll store the states here.
    axis_states = {}
    button_states = {}

    # These constants were borrowed from linux/input.h
    axis_names = {
        0x00 : 'x',
        0x01 : 'y',
        0x02 : 'z',
        0x03 : 'rx',
        0x04 : 'ry',
        0x05 : 'rz',
        0x06 : 'trottle',
        0x07 : 'rudder',
        0x08 : 'wheel',
        0x09 : 'gas',
        0x0a : 'brake',
        0x10 : 'hat0x',
        0x11 : 'hat0y',
        0x12 : 'hat1x',
        0x13 : 'hat1y',
        0x14 : 'hat2x',
        0x15 : 'hat2y',
        0x16 : 'hat3x',
        0x17 : 'hat3y',
        0x18 : 'pressure',
        0x19 : 'distance',
        0x1a : 'tilt_x',
        0x1b : 'tilt_y',
        0x1c : 'tool_width',
        0x20 : 'volume',
        0x28 : 'misc',
    }

    button_names = {
        0x120 : 'trigger',
        0x121 : 'thumb',
        0x122 : 'thumb2',
        0x123 : 'top',
        0x124 : 'top2',
        0x125 : 'pinkie',
        0x126 : 'base',
        0x127 : 'base2',
        0x128 : 'base3',
        0x129 : 'base4',
        0x12a : 'base5',
        0x12b : 'base6',
        0x12f : 'dead',
        0x130 : 'a',
        0x131 : 'b',
        0x132 : 'c',
        0x133 : 'x',
        0x134 : 'y',
        0x135 : 'z',
        0x136 : 'tl',
        0x137 : 'tr',
        0x138 : 'tl2',
        0x139 : 'tr2',
        0x13a : 'select',
        0x13b : 'start',
        0x13c : 'mode',
        0x13d : 'thumbl',
        0x13e : 'thumbr',

        0x220 : 'dpad_up',
        0x221 : 'dpad_down',
        0x222 : 'dpad_left',
        0x223 : 'dpad_right',

        # XBox 360 controller uses these codes.
        0x2c0 : 'dpad_left',
        0x2c1 : 'dpad_right',
        0x2c2 : 'dpad_up',
        0x2c3 : 'dpad_down',
    }

    def init_joystick(self):

        if debug:
            # Iterate over the joystick devices.
            print('Available devices:')

            for fn in os.listdir('/dev/input'):
                if fn.startswith('js'):
                    print('  /dev/input/%s' % (fn))

        # Open the joystick device.
        try:
            fn = '/dev/input/js0'
            if debug:
                print('Opening %s...' % fn)
            jsdev = open(fn, 'rb', buffering=0)
        except IOError:
            print ('No joystick at ' + fn)
            return ('')

       
        #jsdev = os.open(fn, 'rb', os.O_RDONLY|os.O_NONBLOCK)

        # Get the device name.
        #buf = bytearray(63)
        buf = bytearray([0] * 64)
        ioctl(jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        js_name = buf

        if debug:
            print('Device name: %s' % js_name)

        # Get number of axes and buttons.
        buf = array.array('B', [0] )
        ioctl(jsdev, 0x80016a11, buf) # JSIOCGAXES
        num_axes = buf[0]

        buf = array.array('B', [0] )
        ioctl(jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        num_buttons = buf[0]

        # Get the axis map.
        buf = array.array('B', [0] * 0x40)
        ioctl(jsdev, 0x80406a32, buf) # JSIOCGAXMAP

        for axis in buf[:num_axes]:
            axis_name = self.axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(axis_name)
            self.axis_states[axis_name] = 0.0

        # Get the button map.
        buf = array.array('H', [0] * 200)
        ioctl(jsdev, 0x80406a34, buf) # JSIOCGBTNMAP

        for btn in buf[:num_buttons]:
            btn_name = self.button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(btn_name)
            self.button_states[btn_name] = 0

        if debug:
            print ('%d axes found: %s' % (num_axes, ', '.join(self.axis_map)))
            print ('%d buttons found: %s' % (num_buttons, ', '.join(self.button_map)))
        return (jsdev)


    def dec2hex(self, dec,hexlen):  #convert dec to hex with leading 0s and no '0x' 
        h=hex(int(dec))[2:]
        l=len(h)
        if h[l-1]=="L":
            l-=1  #strip the 'L' that python int sticks on
        if h[l-2]=="x":
            h= '0'+hex(int(dec))[1:]
        return ('0'*hexlen+h)[l:l+hexlen]


    def joyread_thread(self, jsdev):
        global joyx
        global joyy
        
        while True:
            evbuf = jsdev.read(8)
            jtime, jvalue, jtype, jnumber = struct.unpack('IhBB', evbuf)
            if jtype & 0x02:
                axis = self.axis_map[jnumber]
                if (axis == 'x'):
                        if abs(jvalue) > self.xthreshold:
                                joyx = 0x100 + int(jvalue * maxjoyposition / 128) >> 8 &0xFF
                        else:
                                joyx = 0
                elif (axis == 'y'):
                        if abs(jvalue) > self.ythreshold:
                                joyy = 0x100 - int(jvalue * maxjoyposition / 128) >> 8 &0xFF
                        else:
                                joyy = 0


                                                   
                
    
    def socketjoyclientthread(self,conn):
        global joyx
        global joyy
        conn.send('This code is not correct\n'.encode())


    def socketjoyserverthread(self,ipsocket,jsdev):
            global joyx
            global joyy
            speed_range = 0
            global joyevent
            joypacketinterval = .01
            joyipsocketthread = threading.Thread(target=x360.joyipsocketthread,args=(ipsocket,joypacketinterval,),daemon = True)
            joyipsocketthread.start()
            running = True
            while running and joyipsocketthread.isAlive():
                try:
                        ev =  jsdev.read(8)
                        if len(ev) != 8:
                            break;
                        jtime, jvalue, jtype, jnumber = struct.unpack('IhBB', ev)
                        if jtype & 0x02:
                            axis = self.axis_map[jnumber]
                            if (axis == 'x'):
                                    if abs(jvalue) > self.xthreshold:
                                            #joyx = 0x100 + int(jvalue * 100 / 128) >> 8 &0xFF
                                            joyx = jvalue
                                    else:
                                            joyx = 0
                            elif (axis == 'y'):
                                    if abs(jvalue) > self.ythreshold:
                                            #joyy = 0x100 - int(jvalue * 100 / 128) >> 8 &0xFF
                                            joyy = jvalue
                                    else:
                                            joyy = 0
                            else:
                                print (axis)
                        elif jtype & 0x01:
                            if jvalue == 1 and jnumber == 0:
                                if speed_range>0:
                                    speed_range -= 25
                                    joyevent = 's:'+dec2hex(speed_range,2)
                                    print("SpeedRange: " + str(speed_range))
                            elif jvalue == 1 and jnumber == 1:
                                if speed_range<100:
                                    speed_range += 25
                                    joyevent = 's:'+dec2hex(speed_range,2)
                                    print("SpeedRange: " + str(speed_range))
                            elif jvalue == 0 and jnumber == 2:
                                joyevent = 'b:h0'
                            elif jvalue == 1 and jnumber == 2:
                                joyevent = 'b:h1'
                            else:
                                print("VAL:"+str(jvalue)+"NUM:"+str(jnumber))
                        
                except IOError or OSError:
                    print("Joystick read error")
                    joyx = 0
                    joyy = 0
                    running = False
                       

    def joyipsocketthread(self,ipsocket,interval,):
        #now joyevent global speed_range
        global joyevent
        joyevent = ' :00'
        nexttime = time()+interval
        filtercutoff = 2
        filtered_joyx=joyx
        filtered_joyy=joyy
        running = True
        while running:
            nexttime += interval
            try:
                filtered_joyx += joyx/filtercutoff - filtered_joyx/filtercutoff
                filtered_joyy += joyy/filtercutoff - filtered_joyy/filtercutoff
                joyxout = 0x100 + int(filtered_joyx * maxjoyposition / 128) >> 8 &0xFF
                joyyout = 0x100 - int(filtered_joyy * maxjoyposition / 128) >> 8 &0xFF
                if joyxout == 1:
                    joyxout = 0
                if joyyout == 1:
                    joyyout = 0
                ipsocket.send(('x:'+dec2hex(joyxout,2)+'y:'+dec2hex(joyyout,2)+joyevent+'\r').encode())
                joyevent = ' :00' #one time only
            except IOError as e:
                    if '[Errno 32]' in str(e):  #Errno 32 = Broken pipe  ie. client dropped
                        print('Client dropped connection')
                        running = False
                        
                    if '[Errno 104]' in str(e): #Errno 104 = connection reset
                        print('Destination port reset by client.')
                        running = False
                    return(e)
            if nexttime > time():
                sleep(nexttime - time())
            else:
                nexttime = time()+interval

                
def dec2hex(dec,hexlen):  #convert dec to hex with leading 0s and no '0x' 
    #this function is ugly and could be improved
    h=hex(int(dec))[2:]
    l=len(h)
    if h[l-1]=="L":
        l-=1  #strip the 'L' that python int sticks on
    if h[l-2]=="x":
        h= '0'+hex(int(dec))[1:]
    return ('0'*hexlen+h)[l:l+hexlen]
                            


if __name__ == "__main__":

    main_running = True 
    while main_running:

        #open client ip port listener
        if host=='':
            try:
                ipsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            except socket.error:
                print ("Failed to create ipsocket")
                sys.exit()
            print ("ip client socket created")
            ipsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                ipsocket.bind((host, port))
            except socket.gaierror:
                print ("Hostname could not be resolved.")
                sys.exit()
            print ("Socket bound to port " + str(port))

        #or open server ip port
        else:
            try:
                ipsocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            except socket.error:
                print ("Failed to create ipsocket")
                sys.exit()
            print ("Joystick over IP server socket created")
            ipsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print ("Attempting connection to "+host+':'+str(port))
            reconnect = True
            while reconnect:
                try:
                    ipsocket.connect((host, port))
                    reconnect = False
                except socket.gaierror:
                    print ("Hostname could not be resolved.")
                    sys.exit()
                except IOError as e:
                    if e == '[Errno 111] Connection refused':
                        print("Connection refused... trying again")
                    reconnect = True
                    
            print ("Socket connected to:" + host + ':' + str(port))
           
        #init /dev joystick
        x360 = X360()

        jsdev = x360.init_joystick()
        global joyx
        global joyy
        global joyevent
        joyx = 0
        joyy = 0
        
        
        if host=='':
            ipsocket.listen(10)
            print ('IPsocket now listening')
            while threading.active_count() > 0:
                conn, addr = ipsocket.accept()
                print ('Connected to ' + addr[0] +':' +str(addr[1]))
                socket_to_joy_thread = threading.Thread(target=x360.socketjoyclientthread,args=(conn,),daemon = True)
                socket_to_joy_thread.start()
        else:
            if jsdev != '':
                joy_to_socket_thread = threading.Thread(target=x360.socketjoyserverthread,args=(ipsocket,jsdev,),daemon = True)
                joy_to_socket_thread.start()
            
        while threading.active_count() > 0 and joy_to_socket_thread.isAlive():
            sleep(0.2)
        ipsocket.close()
        print("Close ipsocket")
        
        
                
