#!/usr/bin/env python
# -*- coding: utf-8 -*-

import signal
import sys

import MySocket
import KartoshkaJoy
import time

# import GstCV
# import cv2
import threading
ip = '192.168.42.234'
port = 2000
LineRtpRecvPort = 5000
LineRtcpRecvPort = 5001
LineRtcpSendPort = 5005

MainRtpRecvPort = 6000
MainRtcpRecvPort = 6001
MainRtcpSendPort = 6005

class mySender:
    def __init__(self):
        print("Creating sender...")
        self.socket = MySocket.SocketSender(ip, port)
        print("Creating joystick...")
        self.joystick = KartoshkaJoy.RoverJoy(self.socket, ip)
        self.exit = False
        self.autonomous = False

    def start(self):
        print("Starting threads...")
        self.joystick.start()

        print("Threads started")

    def killer(self):
        print("IM WATCHING")
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print('KILLED!')
            Close(0,0)

    def startKiller(self):
        t = threading.Thread(target=self.killer)
        t.start()
        print("Killer started")


def Close(self, signal, frame):
    print("Caught SIGINT")
    print("Stopping programm..")
    sender.joystick.Exit()
    sender.socket.exit()
    # self.Line.stop()
    sender.exit = True
    print("Goodbye")
    sys.exit(0)

sender = mySender()
signal.signal(signal.SIGINT, Close)
sender.start()
