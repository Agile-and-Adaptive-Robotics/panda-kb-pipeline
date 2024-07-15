import os
import time
import threading
import queue
from loihi_utils import *
from serial_comm import SerialDataPipeline

from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

"""CONSTANTS"""
USB_SERIAL_PORT = '/dev/ttyACM0'  # Device driver for the USB serial port to Arduino Coprocessor
BAUD_RATE = 256000

INCLUDE_DIR = os.path.join(os.getcwd(), 'snips/')
ENCODER_FUNC_NAME = "run_encoding"
ENCODER_GUARD_NAME = "do_encoding"
DECODER_FUNC_NAME = "run_decoding"
DECODER_GUARD_NAME = "do_decoding"

CHANNEL_BUFFER_SIZE = 32
ENCODER_MSG_SIZE = 4
DECODER_MSG_SIZE = 4

NUM_STEP = 500
NUM_NEURONS = 2

def encoder_thread(encoderChannel, stop_event, encoder_queue):
    while not stop_event.is_set():
        #print("Is encoder queue empty?", encoder_queue.empty())
        if not encoder_queue.empty():
            try:
                data = encoder_queue.get(timeout = 0.01)
                data_32bit = int.from_bytes(data, byteorder='little', signed=False)
                print("Data received from pipeline:", data_32bit)
                encoderChannel.write(1, [data_32bit])
            except queue.Empty:
                continue
        time.sleep(0.001)

def decoder_thread(decoderChannel, stop_event, decoder_queue):
    while not stop_event.is_set():
        if decoderChannel.probe():
            data = decoderChannel.read(1) 
            low_8_bits = data[0] & 0xFF
            print("Data received from Loihi, sending to pipeline:", data)
            decoder_queue.put(low_8_bits.to_bytes(1, byteorder='little', signed=False))
            print(f"Byte {low_8_bits} sent to teensy.")
        time.sleep(0.001)


if __name__ == "__main__":
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

    encoder_thr = threading.Thread(target=encoder_thread, args=(encoderChannel, stop_event, encoder_queue))
    decoder_thr = threading.Thread(target=decoder_thread, args=(decoderChannel, stop_event, decoder_queue))

    serial_pipeline = SerialDataPipeline(USB_SERIAL_PORT, BAUD_RATE, stop_event, encoder_queue, decoder_queue)
    serial_thr = threading.Thread(target=serial_pipeline.run)
    
    board.start()
    test_data = 1
    encoderChannel.write(1, [test_data])

    try:
        # Run the board and the pipeline threads
        board.run(NUM_STEP, aSync=True)
        encoder_thr.start()
        decoder_thr.start()
        serial_thr.start()

       
        # Wait for the board to finish running
        board.finishRun()
        print("Run finished")
    
    finally:
        #Stop the pipeline threads
        stop_event.set()
        encoder_thr.join()
        decoder_thr.join()
        serial_thr.join()

        board.disconnect()

        # Plot the probes
        plot_probes(u_probes, v_probes, s_probes)