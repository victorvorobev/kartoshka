#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import signal
import threading
import serial

motorRight = 0
motorLeft = 1
port = 2000


def RecvParam(prmNumber, prm):
    print('prmNumber: %d param: %d' % (prmNumber, prm))

class myReceiver:
    def __init__(self):
        print("Creating socket...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketOnline = False
        self.ConnectSocket()
        self.speedRight = 0
        self.speedLeft = 0
        self.recvMsg=[]

    def ConnectSocket(self):
        print("Wait for connection...")
        self.sock.bind(('', port))  # listen to this port
        self.sock.listen(0)  # only one connection
        self.connection, addr = self.sock.accept()
        print("Connected: ", addr)

    def RecieveSocket(self):
        while self.socketOnline:
            try:
                data = self.connection.recv(8) # 16 byte blocks
                bytesRecvd = len(data)
                if not data:
                    print("ERROR: no data recieved by socket")
                else:
                    # print("new msg!")
                    self.MsgHandler(data)
            except KeyboardInterrupt:
                self.CloseAll()

    def MsgHandler(self, msg):
        # data = msg.decode("utf-8")
        self.recvMsg = struct.unpack('=2i',msg)
        print("l:",self.recvMsg[0],"r:",self.recvMsg[1])
        self.SetMotors(self.recvMsg[0],self.recvMsg[1])
        # print("Data:",self.recvMsg)

    def SetMotors(self,leftSpeed,rightSpeed):
        self.motors.SetSpeed(motorRight, -rightSpeed)
        self.motors.SetSpeed(motorLeft, leftSpeed)

    def SetPusher(self,up,down):
        if up:
            print("up pusher")
        if down:
            print("down pusher")

    def StartRecv(self):
        self.socketOnline = True
        t = threading.Thread(target=self.RecieveSocket())
        t.start()

    def StopRecv(self):
        self.socketOnline = False
        self.sock.close()
        print

    def CloseAll(self,signal,frame):
        self.Marvin.online = False
        self.Marvin.StopRecv()
        self.socketOnline = False
        self.sock.close()
        # self.StopRecv()
        sys.exit(0)
        print("Goodbye")


recv = myReceiver()
signal.signal(signal.SIGINT, recv.CloseAll)
recv.StartRecv()
