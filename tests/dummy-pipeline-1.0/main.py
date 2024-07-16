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
from loihi_utils import *
import arduino_manager
from serial_comm import SerialDataPipeline

from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
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

NUM_STEP = 1000
NUM_NEURONS = 2

def debug_logger(message, debug_enabled):
    if debug_enabled:
        print(f"[DEBUG] {message}")

# Logs non-fatal error
def error_logger(message):
    print(f"[ERROR] {message}")

def encoder_thread(encoderChannel, stop_event, encoder_queue, debug_enabled):
    while not stop_event.is_set():
        if not encoder_queue.empty():
            try:
                data = encoder_queue.get(timeout = 0.01)
                data_32bit = int.from_bytes(data, byteorder=ENDIANNESS, signed=False)
                debug_logger(f"Data received from pipeline: {data_32bit}", debug_enabled)
                if encoderChannel.probe():
                    encoderChannel.write(1, [data_32bit])

                else:
                    if not stop_event.is_set():  
                        error_logger(f"encoderChannel not ready for data....data missed!!!!")
            except queue.Empty:
                continue
        time.sleep(0.001)

def decoder_thread(decoderChannel, stop_event, decoder_queue, debug_enabled):
    while not stop_event.is_set():
        if decoderChannel.probe():
            data = decoderChannel.read(1) 
            low_8_bits = data[0] & 0xFF
            debug_logger(f"Data received from Loihi: {low_8_bits}", debug_enabled)
            decoder_queue.put(low_8_bits.to_bytes(1, byteorder=ENDIANNESS, signed=False))
            debug_logger(f"Data send to peripheral...", debug_enabled)
        time.sleep(0.001)

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


if __name__ == "__main__":
    
    debug_enabled, probe_enabled = cli_parser()

    # Compiles arduino.ino code and uploads it to the board
    print("Starting Coprocessor...")
    try: 
        arduino_manager.run()
    except Exception as e:
        print(f"An error occurred during Arduino compilation or upload: {e}")
        exit(1)

    # Start network
    net = nx.NxNet()

    prototype = nx.CompartmentPrototype(biasMant=0,
                                        biasExp=6,
                                        vThMant=1000,
                                        functionalState=2,
                                        compartmentVoltageDecay=256,
                                        compartmentCurrentDecay=4096)

    neurons = [create_neuron(net, prototype) for _ in range(NUM_NEURONS)]

    input_conn_proto = nx.ConnectionPrototype(weight=255)
    inputSynapseIds = create_input_layer(net, input_conn_proto, neurons)
    print("Logical Input Synapse IDs:", inputSynapseIds)

    outputSynapseIds = create_output_layer(net, neurons)
    print("Logical Output Synapse IDs:", outputSynapseIds)

    #Track probes if command line argument is TRUE
    if probe_enabled:
        probe_parameters = [nx.ProbeParameter.COMPARTMENT_CURRENT,
                            nx.ProbeParameter.COMPARTMENT_VOLTAGE,
                            nx.ProbeParameter.SPIKE]
        probes = create_probes(neurons, probe_parameters)
        u_probes, v_probes, s_probes = zip(*probes)


    compiler = nx.N2Compiler()
    board = compiler.compile(net)

    resource_maps = store_resource_maps(net, neurons, inputSynapseIds, outputSynapseIds)
    print("Resource Maps:")
    print(resource_maps)

    encoderSnip = board.createSnip(phase=Phase.EMBEDDED_SPIKING,
                                   includeDir=INCLUDE_DIR,
                                   cFilePath=INCLUDE_DIR + "encoder.c",
                                   funcName=ENCODER_FUNC_NAME,
                                   guardName=ENCODER_GUARD_NAME)

    encoderChannel = board.createChannel(name=b'nxEncoder',
                                         messageSize=ENCODER_MSG_SIZE,
                                         numElements=CHANNEL_BUFFER_SIZE)
    encoderChannel.connect(None, encoderSnip)

    decoderSnip = board.createSnip(phase=Phase.EMBEDDED_MGMT,
                                   includeDir=INCLUDE_DIR,
                                   cFilePath=INCLUDE_DIR + "decoder.c",
                                   funcName=DECODER_FUNC_NAME,
                                   guardName=DECODER_GUARD_NAME)

    decoderChannel = board.createChannel(name=b'nxDecoder',
                                         messageSize=DECODER_MSG_SIZE,
                                         numElements=CHANNEL_BUFFER_SIZE)
    decoderChannel.connect(decoderSnip, None)


    # Used to halt the pipeline processes
    stop_event = threading.Event()
    # Used for inter-thread communication between the pipeline processes
    encoder_queue = queue.Queue()
    decoder_queue = queue.Queue()

    encoder_thr = threading.Thread(target=encoder_thread, 
                                   args=(encoderChannel, stop_event, encoder_queue, debug_enabled))
    
    decoder_thr = threading.Thread(target=decoder_thread, 
                                   args=(decoderChannel, stop_event, decoder_queue, debug_enabled))

    serial_pipeline = SerialDataPipeline(USB_SERIAL_PORT, BAUD_RATE, stop_event, encoder_queue, decoder_queue, debug_enabled)
    serial_thr = threading.Thread(target=serial_pipeline.run)

    
    board.start()
    encoder_thr.start()
    decoder_thr.start()
    serial_thr.start()
    try:
        # Run the board and the pipeline threads
        board.run(NUM_STEP, aSync=True)
        #encoder_thr.start()
        #decoder_thr.start()
        #serial_thr.start()

       
        # Wait for the board to finish running
        board.finishRun()
        stop_event.set()
        print("Run finished")
    
    finally:
        #Stop the pipeline threads
        encoder_thr.join()
        decoder_thr.join()
        serial_thr.join()

        board.disconnect()

        # Plot the probes
        if probe_enabled:
            plot_probes(u_probes, v_probes, s_probes)