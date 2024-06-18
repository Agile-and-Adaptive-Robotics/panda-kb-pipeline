"""
Author: Reece Wayt

Version: 1.0.0

Code adapted from "tutorial_24_control_loop_using_rospy.py" in the NxSDK tutorials package

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

    compartment1 = net.createCompartment(prototype1)

    prototype2 = nx.CompartmentPrototype(vThMant=10,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)

    compartment2 = net.createCompartment(prototype2)
    compartment3 = net.createCompartment(prototype2)

    # Excitatory synapse (connection)
    connProto1 = nx.ConnectionPrototype(weight=4, compressionMode=3)
    net._createConnection(compartment1, compartment2, connProto1)

    # Inhibitatory synapse (connection)
    connProto2 = nx.ConnectionPrototype(weight=-4, compressionMode=3)
    net._createConnection(compartment1, compartment3, connProto2)

    probeParameters = [nx.ProbeParameter.COMPARTMENT_CURRENT,
                       nx.ProbeParameter.COMPARTMENT_VOLTAGE]
    # Use default probe conditions - i.e. probeConditions=None
    probeConditions = None
    # Create a compartment probe to probe the states of compartment1
    cx1Probes = compartment1.probe(probeParameters, probeConditions)
    # Create a compartment probe to probe the states of compartment2
    cx2Probes = compartment2.probe(probeParameters, probeConditions)
    # Create a compartment probe to probe the states of compartment3
    cx3Probes = compartment3.probe(probeParameters, probeConditions)

    # cx1Probes is a list of probe objects for compartment1.
    # cx1Probes[0] is the compartment voltage probe and cx1Probes[1] is the compartment current respectively

    # uProbes below is the list of all the compartment current probes
    uProbes = [cx1Probes[0], cx2Probes[0], cx3Probes[0]]
    # vProbes below is the list of all the compartment voltage probes
    vProbes = [cx1Probes[1], cx2Probes[1], cx3Probes[1]]

   

    #compile defined network
    compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    board = compiler.compile(net)


    # Return the configured probes
    return board, uProbes, vProbes

if __name__ == '__main__':

    #Configure network
    board, uProbes, vProbes = setupNetwork()

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
    

