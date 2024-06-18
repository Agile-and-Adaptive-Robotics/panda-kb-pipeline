"""
Author: Reece Wayt

Version: 1.0.0

Code adapted from "tutorial_24_control_loop_using_rospy.py" in the NxSDK tutorials package
k_interactive_spike_sender_receiver.ipynb in the NxSDK tutorials package

"""
import time
import os
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase
'''import matplotlib.pyplot as plt
import matplotlib as mpl

haveDisply = "DISPLAY" in os.environ
if not haveDisply:
    mpl.use('Agg')

'''
NUM_PLOTS_PER_RECEIVER = 1
class Callable:
    def __init__(self, index):
        # data will hold the spike activity for the 3 compartments associated with a spikereceiver
        # Each spikereceiver will have its own Callable instance as the callback. This is denoted by index
        self.data = [[] for i in range(NUM_PLOTS_PER_RECEIVER)]
        self.index = index

    def __call__(self, *args, **kwargs):
        # At every invocation of this method, new data since the last invocation will be passed along.
        # args[0] essentially is a list[list]. Length of the parent list is the number of compartments 
        # connecting to this spike receiver while each sublist is the timeseries data assciated with that
        # compartment accrued since the last invocation. len(args) is 1.
        for compartmentId, tsData in enumerate(args[0]):
            self.data[compartmentId].extend(tsData)
        
callable1 = Callable(1)
callable2 = Callable(2)

# Register these callable objects as callbacks
spikeReceiver1.callback(callable1)
spikeReceiver2.callback(callable2)

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

   #TODO: get compartment nodeId and Group.id 
   #nodeId is the compartment index
   # You can use kewords nxCompartment and nxCompartmentGroup in the C API
   #Compartment and compartment groups are indexed in the order they are created starting at 0

    print("Compartment 1 index is ", neuron1.nodeId)
    print("Compartment 2 index is ", neuron2.nodeId)

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
    return board, net

def create_SpikeGenProcess(net, num_spike_generators):
    runtime_spike_generators = []
    # Create a spike generator process
    for i in range(num_spike_generators):
        runtime_spike_generators[i] = net.createInteractive


if __name__ == '__main__':

    #Configure network
    board, net = setupNetwork()

    # Define directory where SNIP C-code is located
    includeDir = os.path.dirname(os.path.realpath(__file__))
    cFilePath = os.path.join(includeDir, "spiking-snip.c")
    funcName = "run_spiking"
    guardName = "do_spiking"

    
    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    # Phase.EMBEDDED_MGMT - Execute SNIP on embedded management core. Enums are defined in nxsdk.graph.processes.phase
    # The API directory file for phase enums is nxsdk/graph/processes/phase_enums.py
    spikeProcess = board.createSnip(phase = Phase.EMBEDDED_SPIKING,
                                     includeDir=includeDir,
                                     cFilePath = cFilePath,
                                     funcName = funcName,
                                     guardName = guardName)
    


    #Create send channel SuperHost(computer) --> SnipProcess(Loihi LMT x86 Chip)
    """
        createChannel API creates a channel object that can be used to send and receive data between SuperHost (computer) and Host
        See NxNet API and Programming SNIPs section in the user guide for more information
        @Params: 
        - name: Name of the channel
        - messageSize: Size of the message in bytes, MUST BE A MULTIPLE OF 4
        - numElements: Number of elements the channel can hold
    """
    sendSpikeChannel = board.createChannel(name = b'nxSendChannel', 
                                           messageSize = 4, 
                                           numElements = 1)
     #Create send channel SuperHost(computer) --> SnipProcess(Loihi LMT x86 Chip)
    sendSpikeChannel.connect(None, spikeProcess)
    
    """ Create Receive channel"""
    recvSpikeChannel = board.createChannel(name = b'nxRecvChannel', 
                                           messageSize = 4, 
                                           numElements = 1000)
    recvSpikeChannel.connect(spikeProcess, None)


    board.start()

    board.run(100, aSync = True)

    """
        The read() method is part of the channel API, see Communicating vis Channels section of NxSDK documentation

        IMPORTANT NOTE: the read method is blocking, therefore, it will block if now data is available
        
        Return value: The read method returns a list of elements, so in the below we are indexing the first and only value in 
        the return list. For example this code would return the same thing
        time_step = recvSpikeChannel.read(1)
        value = time_step[0]
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

    
    board.finishRun()
    board.disconnect()


    # -------------------------------------------------------------------------
    # TODO: Plot probe data to implement later
    # -------------------------------------------------------------------------
    

