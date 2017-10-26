from numpy.core.umath import right_shift

import RTCjoystic
import time
import threading
import struct

import GstCV
import cv2

import sys

import numpy as np


class RoverJoy(threading.Thread):
    def __init__(self,sender,ip):
        threading.Thread.__init__(self)
        self.Joy = RTCjoystic.Joystick()
        self.Joy.connect("/dev/input/js0")
        self.Joy.info()
        time.sleep(1)
        self.Joy.start()
        self.exit = False

        self.Line = GstCV.CVGstreamer(ip,5000,5001,5005)

        self.sender = sender
        self.leftSpeed = 0
        self.rightSpeed = 0
        self.speedRotate = 0
        self.speedForward = 0
        self.speedRT = 0
        self.speedLT = 0

        self.hatReleased  = True
        self.hatXold = 0
        self.hatYold = 0

        self.sendMsg = struct.Struct('=2i 3?')
        self.R2D2 = False
        self.R2D2WasReleased = True
        self.lamp = False
        self.lampWasReleased = True

        self.debug = False
        self.debugWasReleased = True

        self.imageWidth = 160
        self.imageHeight = 120
        self.frameCol = 5
        self.frameRow = 3
        self.frameWidth = self.imageWidth / self.frameCol
        self.frameHeight = self.imageHeight / self.frameRow

        self.autonom = False
        self.autonomWasReleased = True
        self.intensityList = []

        self.maxSpeed = 255
        self.speedUpReleased = True
        self.speedDownReleased = True
        self.speedGotFromHat = False

        self.lineColor = 'black'
    def convertSpeed(self):
        tempAxis = self.Joy.getAxis()
        tempButtons = self.Joy.getButtons()

        if(tempAxis != None and tempButtons != None):
            if(tempButtons.get('thumbl') == 1):
                if (self.autonomWasReleased):
                    self.autonomWasReleased = False
                    if (self.autonom == True):
                        self.autonom = False
                        self.speedForward = 0
                        print("no autonom")

                    elif (self.autonom == False):
                        self.autonom = True
                        print("autonom")

            if(tempButtons.get('thumbl') == 0):
                self.autonomWasReleased = True

            if(tempButtons.get('thumbr')  == 1):
                if(self.lampWasReleased):
                    self.lampWasReleased = False
                    if(self.lamp == True):
                        self.lamp = False
                        print("Lamp off")
                    elif(self.lamp == False):
                        self.lamp = True
                        print("Lamp on")

            if(tempButtons.get('thumbr') == 0):
                self.lampWasReleased = True

            if(tempButtons.get('mode') == 1):
                if(self.R2D2WasReleased):
                    self.R2D2WasReleased = False
                    self.R2D2 = True
            if(tempButtons.get('mode') == 0):
                self.R2D2 = False
                self.R2D2WasReleased = True

            if(tempButtons.get('y') == 1):
                if(self.debugWasReleased):
                    self.debugWasReleased = False
                    self.debug = True
            if(tempButtons.get('y') == 0):
                self.debug = False
                self.debugWasReleased = True

            if((tempButtons.get('start') == 1)):
                if(self.speedUpReleased):
                    self.speedUpReleased = False
                    print("speed up")
                    self.maxSpeed += 20
                    if(self.maxSpeed > 100):
                        self.maxSpeed = 100
            if((tempButtons.get('start') == 0)):
                self.speedUpReleased = True

            if((tempButtons.get('select') == 1)):
                if(self.speedDownReleased):
                    self.speedDownReleased = False
                    print ("speed down")
                    self.maxSpeed -= 20
                    if(self.maxSpeed < 20):
                        self.maxSpeed = 20
            if((tempButtons.get('select') == 0)):
                self.speedDownReleased = True

            if((tempAxis.get('hat0y')) == -1 and (tempAxis.get('hat0y') != self.hatYold)):
                print("hat up")
                self.speedGotFromHat = True
                self.speedForward = self.maxSpeed
                self.speedRotate = 0
                self.hatYold = -1
            elif((tempAxis.get('hat0y')) == 1 and (tempAxis.get('hat0y') != self.hatYold)):
                print("hat down")
                self.speedGotFromHat = True
                self.speedForward = -self.maxSpeed
                self.speedRotate = 0
                self.hatYold = 1
            if((tempAxis.get('hat0y')) == 0 and (tempAxis.get('hat0x')) == 0 and ((tempAxis.get('hat0y') != self.hatYold) or (tempAxis.get('hat0x') != self.hatXold))):
                print("haty released")
                self.speedGotFromHat = False
                self.speedForward = 0
                self.speedRotate = 0
                self.hatYold = 0
                self.hatXold = 0

            if ((tempAxis.get('hat0x')) == 1 and (tempAxis.get('hat0x') != self.hatXold)):
                self.speedGotFromHat = True
                self.speedRotate = -self.maxSpeed*2/3
                self.speedForward = 0
                self.hatXold = 1
                print("hat right")
            elif ((tempAxis.get('hat0x')) == -1 and (tempAxis.get('hat0x') != self.hatXold)):
                self.speedGotFromHat = True
                self.speedRotate = self.maxSpeed*2/3
                self.speedForward = 0
                self.hatXold = -1
                print("hat left")
            if(not self.speedGotFromHat):
                self.speedRT = tempAxis.get('rz')
                self.speedRT += 1
                self.speedRT *= 127
                self.speedLT = tempAxis.get('z')
                self.speedLT += 1
                self.speedLT *= 127
                self.speedForward = self.speedRT - self.speedLT
                self.speedRotate = tempAxis.get('x')
                self.speedRotate *= -255
            if((self.speedRotate < 60) and (self.speedRotate > -60)):
                self.speedRotate = 0

    def run(self):
        self.Line.start()
        self.VideoStart()
        while(not self.exit):
            try:
                tempForward = self.speedForward
                tempRotate = self.speedRotate
                tempLamp = self.lamp
                tempR2D2 = self.R2D2
                tempDebug = self.debug
                self.convertSpeed()
                if((tempForward != self.speedForward) or (tempRotate != self.speedRotate) or (tempLamp != self.lamp) or (tempR2D2 != self.R2D2) or (tempDebug != self.debug)):
                    if(self.autonom == False):
                        self.rightSpeed = self.speedForward + self.speedRotate
                        self.leftSpeed = self.speedForward - self.speedRotate
                        if(self.leftSpeed > 255): self.leftSpeed = 255
                        if(self.leftSpeed < -255): self.leftSpeed = -255
                        if(self.rightSpeed > 100): self.rightSpeed = 255
                        if(self.rightSpeed < -255): self.rightSpeed = -255
                        msg = self.sendMsg.pack(self.leftSpeed, self.rightSpeed, self.lamp, self.R2D2,self.debug)
                        self.sender.Send(msg)
                time.sleep(0.05)
            except KeyboardInterrupt:
                self.Exit()

    def LineVideoShow(self):
        # font = cv2.FONT_HERSHEY_SIMPLEX
        while not self.exit:
            if self.Line.cvImage is not None:
                # Crop the image
                showFrame = self.Line.cvImage[10:self.imageHeight/2-5, 0:self.imageWidth]
                # Convert to gray
                gray = cv2.cvtColor(showFrame, cv2.COLOR_BGR2GRAY)
                # Gaussian blur
                if self.autonom:
                    blur = cv2.GaussianBlur(gray, (5, 5), 0)
                    # Color thresholding
                    ret, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
                    # Find the contours of the frame
                    cont_img, contours, hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)
                    # Find the biggest contour (if detected)
                    if len(contours) > 0:
                        c = max(contours, key=cv2.contourArea)
                        M = cv2.moments(c)
                        if(M['m00'] != 0):
                            cx = int(M['m10'] / M['m00'])
                            cy = int(M['m01'] / M['m00'])

                        cv2.line(gray, (cx, 0), (cx, 720), (255, 0, 0), 1)
                        cv2.line(gray, (0, cy), (1280, cy), (255, 0, 0), 1)

                        cv2.drawContours(gray, contours, -1, (0, 255, 0), 1)
                        if(cx > 110 or cx < 60):
                            self.speedForward = 0
                            self.speedRotate = -(cx-self.imageWidth/2)+10
                        else:
                            self.speedForward = 40
                            cx = cx - self.imageWidth/2
                            self.speedRotate = -cx/2
                        self.rightSpeed = self.speedForward + self.speedRotate
                        self.leftSpeed = self.speedForward - self.speedRotate
                        if (self.leftSpeed > 100): self.leftSpeed = 100
                        if (self.leftSpeed < -100): self.leftSpeed = -100
                        if (self.rightSpeed > 100): self.rightSpeed = 100
                        if (self.rightSpeed < -100): self.rightSpeed = -100
                        self.lamp = False
                        self.R2D2 = False
                        self.debug = False
                        msg = self.sendMsg.pack(self.leftSpeed, self.rightSpeed, self.lamp, self.R2D2, self.debug)
                        self.sender.Send(msg)
                        print("cx:",cx,"l:",self.leftSpeed,"r:",self.rightSpeed)
                    # else:
                    #     self.lamp = False
                    #     self.R2D2 = False
                    #     self.debug = False
                    #     self.leftSpeed = 0
                    #     self.rightSpeed = 0
                    #     msg = self.sendMsg.pack(self.leftSpeed, self.rightSpeed, self.lamp, self.R2D2, self.debug)
                    #     self.sender.Send(msg)
                cv2.waitKey(1)
                cv2.imshow("Line", gray)

                # if self.autonom:
                #     self.speedForward = 20
                #     if (self.leftSpeed > 100): self.leftSpeed = 100
                #     if (self.leftSpeed < -100): self.leftSpeed = -100
                #     if (self.rightSpeed > 100): self.rightSpeed = 100
                #     if (self.rightSpeed < -100): self.rightSpeed = -100
                #     print("l", self.leftSpeed, "rs", self.rightSpeed)
                #     msg = self.sendMsg.pack(self.leftSpeed, self.rightSpeed, self.lamp, self.R2D2, self.debug)
                #     self.sender.Send(msg)
            time.sleep(0.1)

    def VideoStart(self):
        print("Starting videocapture..")
        t = threading.Thread(target=self.LineVideoShow)
        t.start()
        print("Video capturing started")

    def Exit(self):
        self.exit= True
        self.Line.stop()
        self.Joy.exit()
        sys.exit(0)
