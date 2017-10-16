#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import signal
import threading
import serial

motorRight = 1
motorLeft = 0
port = 2000

cmdCount = 0

class myReceiver:
    def __init__(self, serial):
        print("Creating socket...")
        self.serialSocket = serial
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketOnline = False
        self.ConnectSocket()
        self.speedRight = 0
        self.speedLeft = 0
        self.speedRightOld = 0
        self.speedLeftOld = 0
        self.lampOld = 0
        self.recvMsgFormat = '=2i 3?'

    def ConnectSocket(self):
        print("Wait for connection...")
        self.sock.bind(('', port))  # listen to this port
        self.sock.listen(0)  # only one connection
        self.connection, addr = self.sock.accept()
        print("Connected: ", addr)

    def RecieveSocket(self):
        while self.socketOnline:
            try:
                data = self.connection.recv(struct.calcsize(self.recvMsgFormat)) # 10 byte blocks
                bytesRecvd = len(data)
                if not data:
                    print("ERROR: no data recieved by socket")
                else:
                    self.MsgHandler(data)
            except KeyboardInterrupt:
                self.CloseAll()


    def MsgHandler(self, msg):
        self.recvMsg = struct.unpack(self.recvMsgFormat,msg)
        self.SetMotors(self.recvMsg[0],self.recvMsg[1])
        self.SetLamp(self.recvMsg[2])
        self.SetR2D2(self.recvMsg[3])
        self.DebugMsg(self.recvMsg[4])
        # print("Data:",self.recvMsg)

    def DebugMsg(self, msg):
        global cmdCount
        if(msg):
            self.serialSocket.SendCommand('PRM', ((0, 2), (1, 2)))

    def SetMotors(self,leftSpeed,rightSpeed):
        # print('l:',leftSpeed,'r:',rightSpeed)
        if(rightSpeed != self.speedRightOld):
            self.speedRightOld = rightSpeed
            self.serialSocket.SendCommand('DRV', ((motorRight, 2), (rightSpeed, 4)))
        if(leftSpeed != self.speedLeftOld):
            self.speedLeftOld = leftSpeed
            self.serialSocket.SendCommand('DRV', ((motorLeft, 2), (leftSpeed, 4)))

    def SetLamp(self,lamp):
        if(lamp != self.lampOld):
            self.lampOld = lamp
            self.serialSocket.SendCommand('PWR', ((lamp, 2),))
    def SetR2D2(self,r2d2):
        global cmdCount
        if(r2d2):
            cmd = str('<%0.2X %s>' % (cmdCount, 'R2D2'))  # формируем cmd
            print('r2d2',self.serialSocket.serialPort.write(cmd.encode()))
            print(cmd)
            cmdCount += 1
            if cmdCount == 255:
                cmdCount = 0
            # self.serialPort.SendCommand('RD2D',())

        # self.motors.SetSpeed(motorRight, -rightSpeed)
        # self.motors.SetSpeed(motorLeft, leftSpeed)


    def StartRecv(self):
        print ("Starting recieve data from socket...")
        self.socketOnline = True
        t = threading.Thread(target=self.RecieveSocket())
        t.start()
        self.serialSocket.SendCommand('PRM', ((0, 2), (1, 2)))

    def StopRecv(self):
        print("Closing ports...")
        self.socketOnline = False
        self.sock.close()
        self.serialOnline = False
        self.serialSocket.Exit()
        print("Ports closed")

    def CloseAll(self,signal,frame):
        self.socketOnline = False
        self.sock.close()
        self.serialOnline = False
        self.serialSocket.Exit()
        # self.StopRecv()
        sys.exit(0)
        print("Goodbye")

class MySerial(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.serialPort = serial.Serial(port='/dev/ttyAMA0',
                                        baudrate=57600,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        write_timeout=0)
        self.serialOnline = False

    def run(self):
        self.serialOnline = True
        self.SendCommand('PRM', ((0, 2), (1, 2)))
        self.ReadSerial()

    def ReadSerial(self):
        print("Started read serial")
        tagCmd = False
        tmpCmd = ''
        while True:
            ch = self.serialPort.read()
            if ch == b'<':
                tagCmd = True
                tmpCmd = b''
            elif ch == b'>' and tagCmd == True:
                tagCmd = False
                k = tmpCmd.decode('utf-8')
                a = k.split(' ')
                print(k)
                self.ParseCmd(a)
            else:
                tmpCmd += ch

    def ParseCmd(self, tmpList):
        param = int(tmpList[1],16)
        if tmpList[0] == 'OL':
            self.SendCommand('AOL',((param,2),))
        elif tmpList[0] == 'BAT':
            print('bat')
            batary = tmpList[1]

    def toHex(self,val,nbytes):
        tmp = hex((val + (1 << 8 * int(nbytes / 2))) % (1 << 8 * int(nbytes / 2)))
        ret = tmp[2:]
        while (len(ret) < nbytes):
            ret = "0" + ret
        return ret

    def SendCommand(self,cmd, params):
        paramList = ''
        global cmdCount  # создаем
        for param in params:  # создаем цикл для формаирования paramList
            paramList = paramList + str(self.toHex(param[0], param[1])).upper()
        cmd = str('<%0.2X %s %s>' % (cmdCount, cmd, paramList))  # формируем cmd
        # self.serialPort.write(cmd.encode())  # отправляем сформированную команду
        self.serialPort.write(cmd.encode())
        print(cmd)
        cmdCount = cmdCount + 1  # увеличиваем счетчик для номерования команд
        if cmdCount == 255:
            cmdCount = 0

    def Exit(self):
        self.serialOnline = False
        self.serialPort.close()
        print("Serial closed")

print ("Creating serial...")
serialSocket = MySerial()
print ("Creating socket...")
recv = myReceiver(serialSocket)
signal.signal(signal.SIGINT, recv.CloseAll)
print ("Starting serial..")
serialSocket.start()
print ("Starting socket...")
recv.StartRecv()
