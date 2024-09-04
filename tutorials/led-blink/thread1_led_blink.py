"""
thread1-led-blink.py - this thread control the latte panda expansion header pin D13 which
is connected to an LED for testing

Author: Reece Wayt
Date: 4/25/2024
"""
import time
import threading
import queue
from pinpong.board import Board, Pin

def monitor_for_spike(panda_board, led, queue, stop_event): 
    #Pin initialization as digital output
    led = Pin(Pin.D13, Pin.OUT) 

    while not stop_event.is_set(): 
        spike_signal = queue.get(timeout=3) #Blocks for one second
        if spike_signal: 
            print(f"Spike received from thread id: {threading.get_ident()}")    # Debugging message
            led.write_digital(1) #turn on LED
            time.sleep(1)
            led.write_digital(0) #turn of LED