import time
import numpy as np
import os
import threading
import queue
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase
from pinpong.board import Board, Pin
from OscGenProcess import oscillator
import matplotlib as mpl
import psutil


mpl.use('Agg')

def create_neuron(net, prototype):
    neuron = net.createCompartment(prototype)
    return neuron

def store_resource_map(neurons, net):
    resource_map = {}
    for neuron in neurons: 
        resource_map[neuron.nodeId] = net.resourceMap.compartment(neuron.nodeId)

    return resource_map

# -------------------------------------------------------------------------
if __name__ == "__main__":
    net = nx.NxNet()

    prototype = nx.CompartmentPrototype(biasMant=0,
                                         biasExp=6,  
                                         vThMant=1000, 
                                         functionalState=2,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)
    neurons = []
    neurons.append(create_neuron(net, prototype))
    neurons.append(create_neuron(net, prototype))
    
    compiler = nx.N2Compiler()
    board = compiler.compile(net)

    resource_map = store_resource_map(neurons, net)

    # Print the entire dictionary of resource maps
    print("Resource Maps:")
    for neuron_id, resource_map in resource_map.items():
        print(f"Neuron ID {neuron_id}: {resource_map}")


""" Data pipeline in this code works
import serial
import time

# Define serial ports
USB_SERIAL_PORT = '/dev/ttyACM0'  #Device driver for the USB serial port to Arduino Coprocessor

# Define baud rate
BAUD_RATE = 1000000

# Define the kill command
KILL_COMMAND = 0xFF

def main():
    # Open the USB serial port
    with serial.Serial(USB_SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        print(f"Connected to {USB_SERIAL_PORT} at {BAUD_RATE} baud.")
        # start Teensy oscillator process
        ser.write(bytes([0x00]))
        start_time = time.time()

        while True:
            # Check if 60 seconds have passed
            if time.time() - start_time > 15:
                send_kill_command(ser)
                break

            # Read data from Teensy via Arduino
            if ser.in_waiting > 0:
                received_data = ser.read()
                print(f"Received from Teensy: {received_data}")

                # Echo the data back to Teensy via Arduino
                ser.write(received_data)
                print(f"Sent back to Teensy: {received_data}")

            # Sleep to avoid busy waiting
            time.sleep(0.01)

def send_kill_command(ser):
    print("Sending kill command.")
    ser.write(bytes([KILL_COMMAND]))

if __name__ == "__main__":
    main()
"""