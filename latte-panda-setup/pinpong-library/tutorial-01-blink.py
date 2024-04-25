'''
tutorial-01-blink.py - Tutorial blinks an LED and introduces the user how to use the pinpong library

Source code comes directly from the lattepand documentatio 

Date; 4/24/2024
'''

import time

from pinpong.board import Board,Pin

#Board("uno").begin() #Initialization, select board type (uno, microbit, RPi,) and port number. If the port number is not entered, it will be automatically recognized

# Board("leonardo","COM5").begin() #Specify the port initialization under Windows

Board("uno","/dev/ttyACM0").begin() #Specify the port initialization under Linux

#Board("uno","/dev/cu.usbmodem14101").begin() #Specify the port initialization under MacOS

led = Pin(Pin.D13, Pin.OUT) #Pin initialization as level output

while True:

    #led.value(1) #Output high level method 1

    led.write_digital(1) #Output high level method 2

    print("1") #Terminal printing information.

    time.sleep(1) #Wait for 1 second and keep the state

    #led.value(0) #Output Low Level Method 1

    led.write_digital(0) #Output Low Level Method 1

    print("0") #Terminal printing information.

    time.sleep(1) #Wait for 1 second and keep the state
