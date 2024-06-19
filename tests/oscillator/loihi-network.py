"""
Author: Reece Wayt

Version: 1.0.0

Code adapted from "tutorial_24_control_loop_using_rospy.py" in the NxSDK tutorials package
k_interactive_spike_sender_receiver.ipynb in the NxSDK tutorials package

Notes: 
    This program uses the threading library which emulates a multi-threaded program,
    but a more appropriate library might be the multiprocessing library which is best for 
    CPU bound tasks because it sidesteps the Global Interpreter Lock (GIL) by using seperate
    memory spaces. In essance it allows for the creation of fully isolated processes. 

    threading library is very suitable for I/O bound tasks

"""
import time
import os
import threading
import queue
import matplotlib.pyplot as plt
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase
from pinpong.board import Board, Pin
from OscGenProcess import oscillator

'''import matplotlib.pyplot as plt
import matplotlib as mpl

haveDisply = "DISPLAY" in os.environ
if not haveDisply:
    mpl.use('Agg')

'''
NUM_PLOTS_PER_RECEIVER = 1
NUM_TIME_STEPS = 3000


"""Used for callback method of spike receiver"""
class Callable:
    def __init__(self, index):
        # data will hold the spike activity for the compartments associated with a spikereceiver
        # Each spikereceiver will have its own Callable instance as the callback. This is denoted by index
        self.data = [[] for i in range(NUM_PLOTS_PER_RECEIVER)]
        self.index = index

    def __call__(self, *args, **kwargs):
        # At every invocation of this method, new data since the last invocation will be passed along.
        # args[0] essentially is a list[list]. Length of the parent list is the number of compartments 
        # connecting to this spike receiver while each sublist is the timeseries data associated with that
        # compartment accrued since the last invocation. len(args) is 1.
        for compartmentId, tsData in enumerate(args[0]):
            self.data[compartmentId].extend(tsData)

# Plotter of the time-series spike receiver data
def plot_spike_data(callable1, callable2):
    fig, axes = plt.subplots(1, 2, figsize=(12,6))

    for i in range(NUM_PLOTS_PER_RECEIVER):
        times = callable1.data[i]
        values = [1] * len(times)
        axes[0].vlines(times, 0, values, color='blue')
        axes[0].set_title('Spike Receiver 1')
        axes[0].set_ylim(0,2)
        axes[0].set_xlim(0,3000)

    for i in range(NUM_PLOTS_PER_RECEIVER):
        times = callable2.data[i]
        values = [1] * len(times)
        axes[1].vlines(times, 0, values, color ='red')
        axes[1].set_title('Spike Receiver 2')
        axes[1].set_ylim(0,2)
        axes[1].set_xlim(0,3000)

def setupNetwork():

    # Create a network
    net = nx.NxNet()

    # Create a compartment prototype with the following parameters:
    # biasMant: Configure bias mantissa.  Actual numerical bias is
    #   biasMant*(2^biasExp) = 1*(2^6) = 64.
    # vThMant: Configuring voltage threshold value mantissa. Actual numerical
    #   threshold is vThMant*(2^6) = 10*2^6 = 640
    # functionalState: The setting to PHASE_IDLE = 2 allows the compartment to
    #   be driven by a bias current alone.  See user guide for all possible
    #   phases.
    # compartmentVoltageDecay: Set to 1/16 (2^12 factor for fixed point
    #   implementation) {1/16 * 2^12=256}
    # compartmentCurrentDecay: Set to 1/10 (2^12 factor for fixed point
    #   implementation) {1/10 * 2^12=409}
    prototype1 = nx.CompartmentPrototype(biasMant=1,
                                         biasExp=6,
                                         vThMant=10,
                                         functionalState=2,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)

    neuron1 = net.createCompartment(prototype1)
    neuron2 = net.createCompartment(prototype1)
    # will hold the spike activity for the 3 compartments
   #TODO: get compartment nodeId and Group.id 
   #nodeId is the compartment index
   # You can use kewords nxCompartment and nxCompartmentGroup in the C API
   #Compartment and compartment groups are indexed in the order they are created starting at 0
    print("Compartment 1 index is ", neuron1.nodeId)
    print("Compartment 2 index is ", neuron2.nodeId)

    """ Interactive Spike Generator and Receiver Processes"""
    #Connection prototype
    spikeConnProto = nx.ConnectionPrototype(weight = 128)

    #Spike generator process for neuron1
    interactiveSpikeGen1 = net.createInteractiveSpikeGenProcess(numPorts=1)
    interactiveSpikeGen1_connection = interactiveSpikeGen1.connect(neuron1, spikeConnProto)
    #Spike receiver process for neuron1
    spikeReceiver1 = nx.SpikeReceiver(net)
    neuron1.connect(spikeReceiver1)

    #Spike generator process for neuron2
    interactiveSpikeGen2 = net.createInteractiveSpikeGenProcess(numPorts=1)
    interactiveSpikeGen2_connection = interactiveSpikeGen2.connect(neuron2, spikeConnProto)
    #Spike receiver process for neuron2
    spikeReceiver2 = nx.SpikeReceiver(net)
    neuron2.connect(spikeReceiver2)


    callable1 = Callable(1)
    callable2 = Callable(2)

    # Register these callable objects as callbacks
    spikeReceiver1.callback(callable1)
    spikeReceiver2.callback(callable2)


    

    #Compile defined network
    compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    board = compiler.compile(net)


    # Return the configured probes
    return board, net, neuron1, neuron2, callable1, callable2, interactiveSpikeGen1, interactiveSpikeGen2

def create_SpikeGenProcess(net, num_spike_generators):
    runtime_spike_generators = []
    # Create a spike generator process
    for i in range(num_spike_generators):
        runtime_spike_generators[i] = net.createInteractive


if __name__ == '__main__':

    #Configure network
    board, net, neuron1, neuron2, callable1, callable2, interactiveSpikeGen1, interactiveSpikeGen2 = setupNetwork()

    # Define directory where SNIP C-code is located
    # includeDir = os.path.dirname(os.path.realpath(__file__))
    # cFilePath = os.path.join(includeDir, "spiking-snip.c")
    # funcName = "run_spiking"
    # guardName = "do_spiking"

    
    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    # Phase.EMBEDDED_MGMT - Execute SNIP on embedded management core. Enums are defined in nxsdk.graph.processes.phase
    # The API directory file for phase enums is nxsdk/graph/processes/phase_enums.py
    """
    pikeProcess = board.createSnip(phase = Phase.EMBEDDED_SPIKING,
                                     includeDir=includeDir,
                                     cFilePath = cFilePath,
                                     funcName = funcName,
                                     guardName = guardName)
    """


    #Create send channel SuperHost(computer) --> SnipProcess(Loihi LMT x86 Chip)
    """
        createChannel API creates a channel object that can be used to send and receive data between SuperHost (computer) and Host
        See NxNet API and Programming SNIPs section in the user guide for more information
        @Params: 
        - name: Name of the channel
        - messageSize: Size of the message in bytes, MUST BE A MULTIPLE OF 4
        - numElements: Number of elements the channel can hold
    

    sendSpikeChannel = board.createChannel(name = b'nxSendChannel', 
                                           messageSize = 4, 
                                           numElements = 1)
     #Create send channel SuperHost(computer) --> SnipProcess(Loihi LMT x86 Chip)
    sendSpikeChannel.connect(None, spikeProcess)
    
        #Create Receive channel
    recvSpikeChannel = board.createChannel(name = b'nxRecvChannel', 
                                           messageSize = 4, 
                                             numElements = 1)
    """


    """
        The next section is the spiking process to be send in realtime, 
        although realtime is not guaranteed as the superhost and the loihi
        are executing asynchronously without any common notion of timestep

        IMPORTANT: Lakemont checks every 10 ms (maxF = 100 Hz) for spikes from 
        the interactive spike generator. Is this frequence high enough? Probably not! 
    """
    spike_queue = queue.Queue()
    oscillator = oscillator(amplitude = 200, 
                            frequency = 1, 
                            phase_shift=0, 
                            spike_queue = spike_queue)
    
    oscillator.run() # Starts generating sinewave in a separate thread

    
    board.start()

    inputPortNodeIds = interactiveSpikeGen1.getSpikeInputToResourceMapping()
    print("Input port node ids for spikeGen1: ", inputPortNodeIds)
    inputPortNodeIds = interactiveSpikeGen2.getSpikeInputToResourceMapping()
    print("Input port node ids for spikeGen2: ", inputPortNodeIds)
    

    interactiveSpikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
    print("Spikes sent to neuron1")
    interactiveSpikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])
    print("Spikes sent to neuron2")

    board.run(NUM_TIME_STEPS, aSync = True)


    timeout_period = 2 #[s]
    start_timer = time.time()
    try: 
        #listen for spikes
        while True: 
            print("I'm here 1")
            if not spike_queue.empty(): 
                print("I'm here 2")
                start_timer = time.time()
                neuron_id = spike_queue.get()
                if neuron_id == 0:
                    print("I'm here 3")
                    interactiveSpikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
                elif neuron_id == 1:
                    print("I'm here 4")
                    interactiveSpikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])

            if time.perf_counter() - start_timer > timeout_period: 
                print("Timeout occured")
                break
            time.sleep(0.005)

    except KeyboardInterrupt:
        pass

    finally: 
        oscillator.stop()
        # board.finishRun()
        board.disconnect()
        print("Finished run successfully.")

    # -------------------------------------------------------------------------
    # Finished Run
    # -------------------------------------------------------------------------


    """
        The read() method is part of the channel API, see Communicating vis Channels section of NxSDK documentation

        IMPORTANT NOTE: the read method is blocking, therefore, it will block if now data is available
        
        Return value: The read method returns a list of elements, so in the below we are indexing the first and only value in 
        the return list. For example this code would return the same thing
        time_step = recvSpikeChannel.read(1)
        value = time_step[0]
    """

    """
    timeout = False
    timeout_period = 2 # 5 [s]

    start_timer= time.time()

    while not timeout:
        if recvSpikeChannel.probe(): 
            #Data is available to read
            time_step = recvSpikeChannel.read(1)[0]
            print(f"Data received: {time_step}")
            start_timer = time.time()
        else:
            #Check for timeout 
            current_time = time.time()
            if current_time - start_timer >= timeout_period:
                timeout = True
    """


    

