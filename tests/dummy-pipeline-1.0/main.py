import numpy as np
from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import threading

haveDisplay = "DISPLAY" in os.environ
if not haveDisplay:
    mpl.use('Agg')

NUM_STEP = 200
running = True

def create_neuron(net, prototype):
    neuron = net.createCompartment(prototype)
    return neuron

def create_input_layer(net, prototype, neurons):
    inputSynapseIds = []
    for neuron in neurons: 
        spikeInputPort = net.createSpikeInputPort()
        spikeInputPort.connect(neuron, prototype = prototype)
        inputSynapseIds.append(spikeInputPort.nodeId)
    return inputSynapseIds

def create_output_layer(net, neurons):
    outputSynapseIds = []
    for neuron in neurons: 
        spikeOutputPort = net.createSpikeOutputPort()
        neuron.connect(spikeOutputPort)
        outputSynapseIds.append(spikeOutputPort.nodeId)
    return outputSynapseIds


def get_resource_map(net, neuron, inputSynapseId, outputSynapseId):
    boardId, chipId, coreId, compartmentId, cxProfileCfgId, vthProfileCfgId = net.resourceMap.compartment(neuron.nodeId)
    inputSynapseData = net.resourceMap.inputAxon(inputSynapseId)
    inputSynapseId = inputSynapseData[0][3]  # Unpack the inputAxonId from the inputAxonData
    outputSynapseData = net.resourceMap.synapse(outputSynapseId)
    return {
        "boardId": boardId,
        "chipId": chipId,
        "coreId": coreId,
        "compartmentId": compartmentId,
        "cxProfileCfgId": cxProfileCfgId,
        "vthProfileCfgId": vthProfileCfgId,
        "inputSynapseId": inputSynapseId,
        "outputSynapseId": outputSynapseId
    }

"""
Maps logical neuron IDs to physical IDs and stores the resource mappings.

This function takes a neural network, a list of neurons, and their corresponding
input and output synapse IDs, and maps the logical IDs to physical hardware IDs. 
The mappings are then stored in a dictionary with neuron names as keys.

Parameters:
    net (nx.NxNet): The neural network object containing the neurons and synapses.
    neurons (list of nx.NxCompartment): A list of neuron objects to be mapped.
    inputSynapseIds (list of int): A list of input synapse logical IDs corresponding to the neurons.
    outputSynapseIds (list of int): A list of output synapse logical IDs corresponding to the neurons.

Returns:
    dict: A dictionary containing the resource mappings for each neuron. The keys are 
          neuron names (e.g., "Neuron0", "Neuron1"), and the values are the results 
          of the `get_resource_map` function, which maps the logical IDs to physical IDs.
"""
def store_resource_maps(net, neurons, inputSynapseIds, outputSynapseIds):
    resource_maps = {}
    for idx, (neuron, inputSynapseId, outputSynapseId) in enumerate(zip(neurons, inputSynapseIds, outputSynapseIds)):
        neuron_name = f"Neuron{idx}"
        resource_maps[neuron_name] = get_resource_map(net, neuron, inputSynapseId, outputSynapseId)
    return resource_maps

def create_probes(neurons, probe_parameters, probe_conditions=None):
    probes = []
    for neuron in neurons:
        probes.append(neuron.probe(probe_parameters, probe_conditions))
    return probes

def plot_probes(u_probes, v_probes, s_probes):
    fig = plt.figure(2002, figsize = (35, 25))
    k = 1
    for i in range(len(u_probes)):
        plt.subplot(len(u_probes), 3, k)
        u_probes[i].plot()
        plt.title(f'Neuron {i} Current')
        k += 1

        plt.subplot(len(v_probes), 3, k)
        v_probes[i].plot()
        plt.title(f'Neuron {i} Voltage')
        k += 1

        plt.subplot(len(s_probes), 3, k)
        s_probes[i].plot()
        plt.title(f'Neuron {i} Spikes')
        k += 1

    plt.tight_layout(pad=3.0, w_pad=3.0, h_pad=3.0)
    if haveDisplay:
        plt.show()
    else: 
        fileName = "probes_plot.png"
        print(f"No display available. Saving plot to {fileName}")
        fig.savefig(fileName)

def encoder_thread(encoderChannel, num_steps):
    curr_neuron = 0
    for step in range(num_steps): 
        encoderChannel.write(1, [curr_neuron]) 
        curr_neuron = 1 - curr_neuron #toggle between neuron 0 and neuron 1

def decoder_thread(decoderChannel):
    global running
    while running: 
        if(decoderChannel.probe()):
            data = decoderChannel.read(2)
            print(f"Received from decoder, [synapse Id, time of spike]: {data}")

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

    # create input layer
    input_conn_proto = nx.ConnectionPrototype(weight = 255)
    inputSynapseIds = create_input_layer(net, input_conn_proto, neurons)
    print("Logical Input Synapse IDs:", inputSynapseIds)
    outputSynapseIds = create_output_layer(net, neurons)
    print("Logical Output Synapse IDs:", outputSynapseIds)

    # create probes to track network

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

    # Store resource maps for each neuron including input and output synapse IDs
    try:
        resource_maps = store_resource_maps(net, neurons, inputSynapseIds, outputSynapseIds)
    except ValueError as e:
        print(f"Error while storing resource maps: {e}")
        exit(1)

    # Print the entire dictionary of resource maps
    print("Resource Maps:")
    print(resource_maps)

    # Setup SNIPs
    includeDir = os.path.join(os.getcwd(), 'snips/')
    funcName = "run_encoding"
    guardName = "do_encoding"
    

    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    # Phase.EMBEDDED_MGMT - Execute SNIP on embedded management core. Enums are defined in nxsdk.graph.processes.phase
    # The API directory file for phase enums is nxsdk/graph/processes/phase_enums.py
    encoderSnip = board.createSnip(phase = Phase.EMBEDDED_SPIKING,
                                    includeDir = includeDir,
                                    cFilePath = includeDir +"encoder.c",
                                    funcName = funcName,
                                    guardName = guardName)
    
    # Message size is 4 bytes, number of elements is 1. Therefore, only one integer can be sent at a time(int = 4 bytes).
    # Messase size must be multple of four.
    encoderChannel = board.createChannel(name = b'nxEncoder', 
                                         messageSize = 4,
                                         numElements = 2)
    
    #Create input channel to the encoding process: SuperHost --> Loihi
    encoderChannel.connect(None, encoderSnip)

    funcName = "run_decoding"
    guardName = "do_decoding"

    decoderSnip = board.createSnip(phase = Phase.EMBEDDED_MGMT,
                                    includeDir = includeDir,
                                    cFilePath = includeDir + "decoder.c",
                                    funcName = funcName,
                                    guardName = guardName)
    
    decoderChannel = board.createChannel(name = b'nxDecoder',
                                         messageSize = 4,
                                         numElements = 32)
    
    #Create output channel from the decoding process: SuperHost <-- Loihi
    decoderChannel.connect(decoderSnip, None)
    
    encoder_thread = threading.Thread(target=encoder_thread, args=(encoderChannel, NUM_STEP))
    decoder_thread = threading.Thread(target=decoder_thread, args=(decoderChannel,))

    
    # Run the network and insert spikes
    running = True
    board.run(NUM_STEP, aSync=True)

    encoder_thread.start()
    decoder_thread.start()

    encoder_thread.join()
    board.finishRun()
    print("Run finished")
    running = False
    decoder_thread.join()
    board.disconnect()

    #plot the probes
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