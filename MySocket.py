import time, datetime
import threading
import struct
import sys
import socket

class SocketSender():
    def __init__(self, ip, port):
        self.exit = False
        self.online = False

        self.queue = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketLock = threading.Lock()

        self.connected = False
        self.ip = ip
        self.port = port
        self.Connect()
        self.StartSendQueue()


    def Exit(self):
        self.exit = True

    def Connect(self):
        if not self.connected:
            try:
                self.socket.connect((self.ip, self.port))
                # self.SendOnline()
            except OSError as msg:
                print("Cannot connect to server: %s\n " % msg)
            else:
                print(self.ip + " connected")
                self.connected = True

    def Disconnect(self):
        self.online = False
        self.socket.close()
        self.connected = False
        self.exit()

    def SendMsg(self,data): #
        try:
            self.socket.send(data)
            now = datetime.datetime.now()
            time.sleep(0.05)
            self.sendSuccess = True
        except OSError:
            print("Socket error\n")
            time.sleep(0.1)

    def Send(self,msg):   #
        self.queue.append(msg)

    def SendQueue(self):    #
        while not self.exit:
            self.sendSuccess = False
            if len(self.queue) != 0: #
                self.SendMsg(self.queue[0]) #
                if self.sendSuccess:
                    self.queue.pop(0)
            else:
                time.sleep(0.1) #

    def StartSendQueue(self):   #
        t = threading.Thread(target = self.SendQueue)
        t.start()
        self.StartSendQueue = self.KillFunction #

    def KillFunction(self): #
        pass

    def RecvMsg(self):  #
        canMsg = struct.Struct('=I 12B')
        while not self.exit:
            try:
                InMsg = self.socket.recv(canMsg.size) #
                success = True
            except OSError as msg:
                print("Socket error: %s\n " % msg)
                success = False
            if success:
                self.MsgHandler(InMsg)
            time.sleep(0.01)

    def MsgHandler(self, InMsg):    # TODO:
        print("got message" + InMsg)

    def Listen(self):   #
        t = threading.Thread(target = self.RecvMsg)
        t.start()

if __name__ == "__main__":  #
    pass
