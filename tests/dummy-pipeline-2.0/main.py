"""
@Brief: This is a dummy pipeline that demonstrates the communication between the Loihi board and the Teensy board.
        The Teensy board is running an oscillator process (/teensy/oscillator.cpp) that emulates a cpg type of biofeedback.
        Spikes from the oscillator are generated to create a spike train which are sent through the pipeline to the Loihi Network. 

@Notes: 
    - The pipeline consists of three threads: encoder, decoder, and serial.
    - The encoder thread reads data from the encoder queue and sends it to the Loihi board.
    - The decoder thread reads data from the Loihi board and sends it to the decoder queue.
    - The serial thread reads data from the onboard coprocessor (Arduino Leonardo) and sends it to the decoder queue.
        - The pipeline is managed and compiled by the arduino_manager module.
        - See documentation on Arduion CLI for more context - https://arduino.github.io/arduino-cli/0.34/installation/

@Options: When running the python script there are two options by default debugging and probes are disabled
          to enable both run `python main.py --debug --probe
          --debug [Enables debug logger]
          --probe [Enables probe collection on Loihi]

@Author: Reece Wayt        
"""
import os
import time
import threading
import queue
import argparse
import arduino_manager
from serial_comm import SerialDataPipeline
from snn_utils import NeuralNetworkHelper
import subprocess

from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
from nxsdk.graph.monitor.probes import *
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

"""CONSTANTS"""
USB_SERIAL_PORT = '/dev/ttyACM0'  # Device driver for the USB serial port to Arduino Coprocessor
BAUD_RATE = 1000000
ENDIANNESS = 'little'

INCLUDE_DIR = os.path.join(os.getcwd(), 'snips/')
ENCODER_FUNC_NAME = "run_encoding"
ENCODER_GUARD_NAME = "do_encoding"
DECODER_FUNC_NAME = "run_decoding"
DECODER_GUARD_NAME = "do_decoding"

CHANNEL_BUFFER_SIZE = 32
ENCODER_MSG_SIZE = 4
DECODER_MSG_SIZE = 4

NUM_STEP = 500
NUM_NEURONS = 4

def debug_logger(message, debug_enabled):
    if debug_enabled:
        print(f"[DEBUG] {message}")

# Logs non-fatal error
def error_logger(message):
    print(f"[ERROR] {message}")


def cli_parser():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Dummy pipeline for communication between Loihi and Teensy boards.")
    parser.add_argument("--debug", action="store_true", help="Enable debugging output")
    parser.add_argument("--probe", action="store_true", help="Enable probes")
    args = parser.parse_args()
    if not args.debug:
        print("[INFO] Running without debugging enabled...")
    if not args.probe: 
        print("[INFO] Running without probes enabled, this should make network faster...")
    debug_enabled = args.debug
    probe_enabled = args.probe

    return debug_enabled, probe_enabled


def build_shared_libary() -> str:
    """Build the host snip shared library"""
    lib = os.path.dirname(os.path.realpath(__file__)) + \
        "/build/libhost_snip.so" # FIXME: This is hardcoded for now 

    # Compile the Host Snip to create the library after linking with ros libs
    build_script = "{}/build.sh".format(
        os.path.dirname(os.path.realpath(__file__)))
    subprocess.run(
        [build_script],
        check=True,
        shell=True,
        executable="/bin/bash")

    return lib



if __name__ == "__main__":
    
    debug_enabled, probe_enabled = cli_parser()
    
    shared_library_path = build_shared_libary() # Build the host snip shared library and arduino sketch

    net = nx.NxNet()
    # get network class
    mySNN = NeuralNetworkHelper(net)

    prototype = nx.CompartmentPrototype(biasMant=0,
                                        biasExp=6,
                                        vThMant=500,
                                        functionalState=2,
                                        compartmentVoltageDecay=256,
                                        compartmentCurrentDecay=4096)

    neurons = [mySNN.create_neuron(prototype) for _ in range(NUM_NEURONS)]

    input_conn_proto = nx.ConnectionPrototype(weight=255)

    # Create input layer
    inputSynapseIds = mySNN.create_input_layer(input_conn_proto, neurons[:2])  # Use two neurons for input
    print("Logical Input Synapse IDs:", inputSynapseIds)

    # Create output layer
    outputSynapseIds = mySNN.create_output_layer(neurons[2:4])  # Use two neurons for output
    print("Logical Output Synapse IDs:", outputSynapseIds)


    neurons[0].connect(neurons[2], prototype=input_conn_proto)
    neurons[1].connect(neurons[3], prototype=input_conn_proto)

    #Track probes if command line argument is TRUE
    #[IMPORTANT] Spike probe of some sort much be enabled for use of Spike Count register in embedded SNIPs 
    if probe_enabled:
        probe_parameters = [nx.ProbeParameter.COMPARTMENT_CURRENT,
                            nx.ProbeParameter.COMPARTMENT_VOLTAGE,
                            nx.ProbeParameter.SPIKE]
        probes = mySNN.create_probes(neurons, probe_parameters)
        u_probes, v_probes, s_probes = zip(*probes)
    else:
        customSpikeProbeCond = SpikeProbeCondition(tStart=1000000000)
        for neuron in neurons:
            sProbe = neuron.probe(nx.ProbeParameter.SPIKE, customSpikeProbeCond)

    compiler = nx.N2Compiler()
    board = compiler.compile(net)

    mySNN.write_precomputed_axons_file(inputSynapseIds, outputSynapseIds)

    cppFile = os.path.dirname(os.path.realpath(__file__)) +"/host_snip.cpp"

    """SNIPs on Host"""
    spikeInjector = board.createSnip(
        phase=Phase.HOST_PRE_EXECUTION,
        library=shared_library_path)
    
    spikeReader = board.createSnip(
        phase=Phase.HOST_POST_EXECUTION,
        library=shared_library_path)
    
    """SNIPs on x86 Cores (embedded snips)"""
    encoderEmbeddedProcess = board.createSnip(phase=Phase.EMBEDDED_SPIKING,
                                   includeDir=INCLUDE_DIR,
                                   cFilePath=INCLUDE_DIR + "encoder.c",
                                   funcName=ENCODER_FUNC_NAME,
                                   guardName=ENCODER_GUARD_NAME)
    
    decoderEmbeddedProcess = board.createSnip(phase=Phase.EMBEDDED_MGMT,
                                   includeDir=INCLUDE_DIR,
                                   cFilePath=INCLUDE_DIR + "decoder.c",
                                   funcName=DECODER_FUNC_NAME,
                                   guardName=DECODER_GUARD_NAME)

    """Create Channels"""
    encoderChannel = board.createChannel(name=b'nxEncoder',
                                         messageSize=ENCODER_MSG_SIZE,
                                         numElements=CHANNEL_BUFFER_SIZE)
    #Create input channel: host_process ----> loihi
    encoderChannel.connect(spikeInjector, encoderEmbeddedProcess)

    

    decoderChannel = board.createChannel(name=b'nxDecoder',
                                         messageSize=DECODER_MSG_SIZE,
                                         numElements=CHANNEL_BUFFER_SIZE)
    #Create output channel: host_process <---- loihi
    decoderChannel.connect(decoderEmbeddedProcess, spikeReader)

    board.start()
    
    try:
        board.run(NUM_STEP, aSync=True)
        board.finishRun()
        print("Run finished")
    
    finally:
        board.disconnect()
        # Plot the probes
        if probe_enabled:
            mySNN.plot_probes(u_probes, v_probes, s_probes)