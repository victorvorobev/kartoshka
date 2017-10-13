

import os, struct, array
import time
import termios
from fcntl import ioctl
import threading
import RTCevent_master

class JoyCrashError(Exception):
    pass
class JoyNotFoundError(Exception):
    pass
class InternalError(Exception):
    pass
class ButtonError(Exception):
    pass



JSIOCGAXES    = 0x80016a11
JSIOCGBUTTONS = 0x80016a12
JSIOCGNAME    = 0x81006a13
JSIOCGAXMAP   = 0x80406a32
JSIOCGBTNMAP  = 0x80406a34



axisNames = {
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

buttonNames = {
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


class Joystick(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.path=None
        self.axisMap = []
        self.buttonMap = []
        self.axisStates = {}
        self.buttonStates = {}
        self.jsdev=None
        self.jname=None
        self.axisNum = 0
        self.buttonsNum = 0
        self.EXIT = False
        self.buttonHandler = {}
        self.EV = RTCevent_master.EVENT_MASTER()
        self.EV.start()

    def info(self):
        print('Device name', self.jname) 
        print('Device path: %s' % self.path)
        print('%d axes found: %s' % (self.axisNum, ', '.join(self.axisMap)))
        print('%d buttons found: %s' % (self.buttonsNum, ', '.join(self.buttonMap)))

    def connect(self, path):
        self.path = path
        buf = b' '
        try:
            self.jsdev = open(path, 'rb')
        except:
            raise JoyNotFoundException("Joystick not found")
        else:
            buf = array.array('b', buf * 50)
            ioctl(self.jsdev, JSIOCGNAME, buf)
            self.jname = buf.tostring()

            buf = array.array('B', [0])
            ioctl(self.jsdev, JSIOCGBUTTONS, buf)
            self.buttonsNum = buf[0]

            buf = array.array('B', [0])
            ioctl(self.jsdev, JSIOCGAXES, buf)
            self.axisNum = buf[0]

            buf = array.array('B', [0] * 40)
            ioctl(self.jsdev, JSIOCGAXMAP, buf)

            for axis in buf[:self.axisNum]:
                axisName = axisNames.get(axis, 'unknown(0x%02x)' % axis)
                self.axisMap.append(axisName)
                self.axisStates[axisName] = 0.0

            buf = array.array('H', [0] * 200)
            ioctl(self.jsdev, JSIOCGBTNMAP, buf)

            for btn in buf[:self.buttonsNum]:
                btnName = buttonNames.get(btn, 'unknown(0x%03x)' % btn)
                self.buttonMap.append(btnName)
                self.buttonStates[btnName] = False
    
    def read(self):
        try:
            evbuf = self.jsdev.read(8)
        except OSError:                         
            raise JoyCrashException("Joystic crash")     
            time.sleep(2)
        except AttributeError:
            raise InternalError("Joystick not open")
            time.sleep(2)
        else:
            if evbuf:                
                time0, value, type, number = struct.unpack('IhBB', evbuf)
                if type & 0x80:
                    pass
                            
                if type & 0x01:
                    button = self.buttonMap[number]
                    if button:
                        if(self.buttonStates[button]!=value):
                            if(value==True):
                                #print("button pressed")
                                handler = self.buttonHandler.get(button)
                                if(handler):
                                    handler.push()
                            else:
                                pass
                                #print("button released")
                        self.buttonStates[button] = value

                if type & 0x02:
                    axis = self.axisMap[number]
                    if axis:                        
                        fvalue = value/32767.0
                        self.axisStates[axis] = fvalue
                
    def run(self):
        while(not self.EXIT):           
            self.read()
        self.jsdev.close()
        
    def exit(self):
        self.EXIT = True      
    
    def getAxis(self):
        return self.axisStates

    def getButtons(self):
        return self.buttonStates
    
    def connectButton(self, buttonName, handler):
        for but in self.buttonMap:
            if(but==buttonName):
                ev = RTCevent_master.Event_block()
                ev.setFun(handler)
                self.EV.append(ev)
                self.buttonHandler.update({but: ev})
                return
        raise ButtonError("no such button")
        
    Axis = property(getAxis)
    Buttons = property(getButtons)

