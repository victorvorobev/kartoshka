#! /usr/bin/env python3

# coding: utf-8
import serial
import paho.mqtt.client as mqtt
import time
import threading
paramList=''
cmdCount = 0
batary = ''
voltageLevel = ''
voltage = ''
amperege = ''
i = ''
k = ''
b = ''
a = ''
workMode = 00
speedLeft = 0
speedRigh = 0
m = 600
n = 100
c = 0
running = True

print("open")
ser = serial.Serial(port='/dev/ttyUSB0',baudrate=57600)                     #подключаемся через USB(посмотреть полный адрес USB: ls /dev)

def on_connect(client, userdata, flags, rc):                                # что делаем при коннекте
    print("Connected with result code: " + str(rc))
    client.subscribe("robot/#", qos=0)                                      # подписываемся на топики
    #client.subscribe("robot/x")
    #client.subscribe("robot/y")
    client.message_callback_add("robot/speedLeft", speedLeft_callback)
    client.message_callback_add("robot/speedRight", speedRight_callback)
    client.message_callback_add("robot/workMode", workMode_callback)
    #client.message_callback_add("robot/n", n_callback)
    #client.message_callback_add("robot/m", m_callback)

def on_message(client, userdata, msg):  
    print("%s: %s" % (msg.topic, msg.payload))
    
def speedLeft_callback(client, userdata, message):
    time.sleep(0.1)
    speedLeft = int(message.payload)
    sendComand('DRV',((0,2),(speedLeft,4)))

    # print(speedLeft)

def speedRight_callback(client, userdata, message):
    time.sleep(0.1)
    speedRight = int(message.payload)
    sendComand('DRV',((1,2),(speedRight,4)))
    # print(speedRight)
    
def workMode_callback(client, userdata, message):
    workMode = int(message.payload)
    #print("workMode")
    sendComand('PRM',((0,2), (workMode,2)))
    print("workMode")
    
    
#def n_callback(client, userdata, message):
#    global n
#    n = int(message.payload)

#def m_callback(client, userdata, message):
#    global m
#    m = int(message.payload)



def A():
  while True:
    ser.write(b'<cmdCount GET_ID>') 
    time.sleep(0.5)

def ReadSerial():                                                     #поток для считывания сообщений и отправки ответных команд                                                
  print("started")
  tagCmd = False
  tmpCmd = ''
  while True:
    ch = ser.read()                                                   #считываем байт с порта                        
    if ch == b'<':                                                    #проверяем начало команды 
      tagCmd = True                                                   #признак команды True, тем саммым начали принимать команду
      tmpCmd = b''                                                    #обнуляем формумируемую команду
    elif ch == b'>' and tagCmd == True:                               #проверяем конец команды
      tagCmd = False                                                  #признак команды false, тем саммым закончили принимать команду
      k = tmpCmd.decode('utf-8')
      a = k.split(' ') 
      parseCmd(a);
      print(k)
    else :
      tmpCmd += ch                                                    #прибавляем счиьтваемый символ к команде
      
def parseCmd(tmpList):                                                #создаем функцию для отправки ответной команды(tmpList-то что нам присылает контроллер) 
  param  = int(tmpList[1], 16)
  if tmpList[0] == 'OL':                                              #проверяем что какое сообщение прислали  
    sendComand('AOL', ((param,2),))
  elif tmpList[0] == 'BAT':
    batary = tmpList[1]
    #print(batary)
    #voltage ='напряжение:  ' batary[4:7]
    #amperage ='сила тока:  ' batary[0:3]
    #voltageLevel ='норма напряжения:  ' batary[8:9]
    #print(voltage)
    #print(amperage)
    #print(voltageLevel)

def toHex(val,nbytes):
    tmp = hex((val + (1 << 8*int(nbytes/2))) % (1 << 8*int(nbytes/2)))
    ret = tmp[2:]
    while(len(ret) < nbytes):
        ret = "0"+ret
    return ret


#создаем функцию для отпрвки команд (cmd-команда для отправки, params-значение для команды) 
def sendComand(cmd, params):                                
    paramList=''
    global cmdCount                                                         #создаем 
    for param in params:                                                    #создаем цикл для формаирования paramList
        paramList = paramList + str(toHex(param[0],param[1])).upper()
    cmd = str( '<%0.2X %s %s>' % (cmdCount, cmd, paramList))                #формируем cmd
    ser.write(cmd.encode())                                                 #отправляем сформированную команду
    print(cmd)
    cmdCount = cmdCount+1                                               #увеличиваем счетчик для номерования команд
    if cmdCount == 255:
        cmdCount = 0                                                    #обнуляем считчик в случае, если номер команды достик 255

subscriber = mqtt.Client()                                              #Подключаемся к издателю 
subscriber.on_connect = on_connect
subscriber.on_message = on_message

subscriber.connect("localhost",1883,60)
        
subscriber.loop_start()
  


  

#if __name__ == '__main__':
    


#t1 = threading.Thread(target=A)
t2= threading.Thread(target=ReadSerial)
#t3= threading.Thread(target=parseCmd)
#t1.start()
t2.start()
#t3.start()
while running:
  time.sleep(10)
  print("while")
   # p1.join()
   # p2.join()

subscriber.loop_forever()
subscriberloop_stop(force=False)
  
