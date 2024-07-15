import os
import multiprocessing
from loihi_utils import *
from serial_comm import SerialDataPipeline

from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

"""CONSTANTS"""
USB_SERIAL_PORT = '/dev/ttyACM0'  #Device driver for the USB serial port to Arduino Coprocessor
BAUD_RATE = 1000000

INCLUDE_DIR = os.path.join(os.getcwd(), 'snips/')
ENCODER_FUNC_NAME = "run_encoding"
ENCODER_GUARD_NAME = "do_encoding"
DECODER_FUNC_NAME = "run_decoding"
DECODER_GUARD_NAME = "do_decoding"

CHANNEL_BUFFER_SIZE = 32
ENCODER_MSG_SIZE = 4
DECODER_MSG_SIZE = 4

NUM_STEP = 200
NUM_NEURONS = 2

def encoder_process(encoderChannel, stop_event, encoder_queue):
    while not stop_event.is_set():
        try:
            data = encoder_queue.get(timeout=1)  # Wait for data from the queue with a timeout
            encoderChannel.write(1, [data])
        except multiprocessing.queues.Empty:
            continue  # Timeout occurred, check stop_event and continue

def decoder_process(decoderChannel, stop_event, decoder_queue):
    while not stop_event.is_set():
        if decoderChannel.probe():
            data = decoderChannel.read(2)
            decoder_queue.put(data)



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
    stop_event = multiprocessing.Event()
    #Used for inter-process communication between the pipeline processes
    encoder_queue = multiprocessing.Queue()
    decoder_queue = multiprocessing.Queue()

    encoder_proc = multiprocessing.Process(target=encoder_process, args=(encoderChannel, stop_event, encoder_queue))
    decoder_proc = multiprocessing.Process(target=decoder_process, args=(decoderChannel, stop_event, decoder_queue))

    serial_pipeline = SerialDataPipeline(USB_SERIAL_PORT, BAUD_RATE, stop_event)
    serial_proc = multiprocessing.Process(target=serial_pipeline.run)


    # Run the board and the pipeline processes
    board.run(NUM_STEP, aSync=True)
    encoder_proc.start()
    decoder_proc.start()
    serial_proc.start()
    # Wait for the board to finish running
    board.finishRun()
    print("Run finished")
    # Stop the pipeline processes
    stop_event.set()
    encoder_proc.join()
    decoder_proc.join()
    serial_proc.join()

    board.disconnect()
    # Plot the probes
    plot_probes(u_probes, v_probes, s_probes)
