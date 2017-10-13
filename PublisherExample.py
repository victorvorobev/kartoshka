 #!/usr/bin/env python3
import time 
import pygame
import paho.mqtt.client as mqtt

running = True
q = 0
z = 0
c = 0 
speedRight = 0
speedLeft = 0
m = 600
n = 100 
pygame.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()
name = joystick.get_name()
clock = pygame.time.Clock()
print("Joystick initilised")
print(name)
print("open")
#ser = serial.Serial(port='/dev/ttyUSB0',baudrate=57600)

# This is the Publisher

client = mqtt.Client()
client.connect("localhost",1883,60)


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 
            break
        if (event.type == pygame.JOYAXISMOTION):
            clock.tick(10)
            #print("Axis 0: " + str(joystick.get_axis(0)))
            #print("Axis 1: " + str(joystick.get_axis(1)))
            speedRight=int(joystick.get_axis(1)*255)
            speedLeft=int(joystick.get_axis(3)*255)
            # if speedLeft < 0:
            #    speedLeft = speedLeft*(-1)
            client.publish("robot/speedLeft", payload=speedLeft)
            
            # if speedRight < 0:
            #    speedRight = speedRight*(-1)
            client.publish("robot/speedRight", payload=speedRight)
            print(speedRight, speedLeft)
           # print("speed")
        #if (event.type == pygame.JOYAXISMOTION):
        #    #print("Axis 2: " + str(joystick.get_axis(2)))
        #    #print("Axis 3: " + str(joystick.get_axis(3)))
        #    q=q+int(joystick.get_axis(2)*255)
        #    z=z+int(joystick.get_axis(3)*255)
        #    client.publish("robot/q", payload=q)
        #    client.publish("robot/z", payload=z)
        if (event.type == pygame.JOYBUTTONDOWN):
            if joystick.get_button(0) == 1:
                client.publish("robot/workMode", 1)
                print("work")
           
            if joystick.get_button(1) == 1:
                client.publish("robot/workMode", 0)
                print("no  work")
           
            if joystick.get_button(5) == 1:
                n=n+20
                client.publish("robot/n", payload=n)
           
            if joystick.get_button(7) == 1:
                n=n-20   
                client.publish("robot/n", payload=n)
           
            if joystick.get_button(4) == 1:
                m=m+20
                client.publish("robot/m", payload=m)
           
            if joystick.get_button(6) == 1:
                m=m-20   
                client.publish("robot/m", payload=m)


        
pygame.quit()
client.disconnect();

