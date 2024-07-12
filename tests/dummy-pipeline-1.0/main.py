import os
import threading
# User-defined functions from utility files
from loihi_utils import *
from threading_utils import *
from serial_comm import * 

from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase



"""CONSTANTS"""
# SNIP params
INCLUDE_DIR = os.path.join(os.getcwd(), 'snips/')  #include directory used for compiling snips
ENCODER_FUNC_NAME = "run_encoding"
ENCODER_GUARD_NAME = "do_encoding"
DECODER_FUNC_NAME = "run_decoding"
DECODER_GUARD_NAME = "do_decoding"

# Channel params
CHANNEL_BUFFER_SIZE = 32   # Must be multiple of 4... 
ENCODER_MSG_SIZE = 4       # (32 * messageSize = 128 bytes)                 
DECODER_MSG_SIZE = 4

#Network params
NUM_STEP = 200

"""GLOBAL VARIABLES""" 
# Add as needed

if __name__ == "__main__":
    net = nx.NxNet()

    prototype = nx.CompartmentPrototype(biasMant=0,
                                        biasExp=6,  
                                        vThMant=1000, 
                                        functionalState=2,
                                        compartmentVoltageDecay=256,
                                        compartmentCurrentDecay=4096)
    
    neurons = []
    neurons.append(create_neuron(net, prototype))
    neurons.append(create_neuron(net, prototype))
    # Add more neurons as needed
    # neurons.append(create_neuron(net, prototype))

    # Create input layer
    input_conn_proto = nx.ConnectionPrototype(weight = 255)
    inputSynapseIds = create_input_layer(net, input_conn_proto, neurons)
    print("Logical Input Synapse IDs:", inputSynapseIds)

    # Create output layer
    outputSynapseIds = create_output_layer(net, neurons)
    print("Logical Output Synapse IDs:", outputSynapseIds)

    # Create probes
    probe_parameters = [nx.ProbeParameter.COMPARTMENT_CURRENT,
                        nx.ProbeParameter.COMPARTMENT_VOLTAGE,
                        nx.ProbeParameter.SPIKE]

    probes = create_probes(neurons, probe_parameters)
    u_probes = [probe[0] for probe in probes] # Current probes
    v_probes = [probe[1] for probe in probes] # Voltage probes
    s_probes = [probe[2] for probe in probes] # Spike probes


    compiler = nx.N2Compiler()
    board = compiler.compile(net)

   
    resource_maps = store_resource_maps(net, neurons, inputSynapseIds, outputSynapseIds)
    
    # Print the entire dictionary of resource maps, useful for understand NxSDK resource allocation
    print("Resource Maps:")
    print(resource_maps)


    # Create encoder SNIP, which runs spiking injection process. If spikes are detected on channel, SNIP will process them.
    encoderSnip = board.createSnip(phase = Phase.EMBEDDED_SPIKING,
                                    includeDir = INCLUDE_DIR,
                                    cFilePath = INCLUDE_DIR +"encoder.c",
                                    funcName = ENCODER_FUNC_NAME,
                                    guardName = ENCODER_GUARD_NAME)
    
    encoderChannel = board.createChannel(name = b'nxEncoder', 
                                         messageSize = ENCODER_MSG_SIZE,
                                         numElements = CHANNEL_BUFFER_SIZE)
    #Connect input channel to the encoding process: SuperHost --> Loihi
    encoderChannel.connect(None, encoderSnip)

    # Create decoder SNIP, which runs management process per time step. Process detects spikes from output layer
    decoderSnip = board.createSnip(phase = Phase.EMBEDDED_MGMT,
                                    includeDir = INCLUDE_DIR,
                                    cFilePath = INCLUDE_DIR + "decoder.c",
                                    funcName = DECODER_FUNC_NAME,
                                    guardName = DECODER_GUARD_NAME)
    
    decoderChannel = board.createChannel(name = b'nxDecoder',
                                         messageSize = DECODER_MSG_SIZE,
                                         numElements = CHANNEL_BUFFER_SIZE)
    
    #Connect output channel from the decoding process: SuperHost <-- Loihi
    decoderChannel.connect(decoderSnip, None)

    # Define stop event for threads
    stop_event = threading.Event()
    
    # Define encoding and decoding threads, see README.md for more information
    encoder_thread = threading.Thread(target=encoder_thread, args=(encoderChannel, NUM_STEP))
    decoder_thread = threading.Thread(target=decoder_thread, args=(decoderChannel, stop_event))

    
    # Run the network and insert spikes
    board.run(NUM_STEP, aSync=True)

    encoder_thread.start()
    decoder_thread.start()

    # Cleanup and plot the probes
    encoder_thread.join()
    board.finishRun()
    print("Run finished")
    stop_event.set() # Stop the decoder thread
    decoder_thread.join()
    board.disconnect()
    plot_probes(u_probes, v_probes, s_probes)

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