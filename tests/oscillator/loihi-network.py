"""
Author: Reece Wayt

Version: 1.0.0

Code Adopted From: 
tutorial_02_single_compartment_with_bias_connecting_to_two_others.py
All snip tutorial in the NxSDK

"""

from abs import ABC 
from threading  import Thread
import os
import atexit
from nxsdk.graph.channel import Channel
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase.enums import Phase

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

    # Define directory where SNIP C-code is located
    includeDir = os.getcwd()


    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    runMgmtProcess = board.createProcess("runMgmt",
                                     includeDir=includeDir,
                                     cFilePath = includeDir + "/runmgmt.c",
                                     funcName = "run_mgmt",
                                     guardName = "do_run_mgmt",
                                     phase = "mgmt")
    

    # Return the configured probes
    return board, uProbes, vProbes

if __name__ == '__main__':

    #Configure network
    board, uProbes, vProbes = setupNetwork()

    # Define directory where SNIP C-code is located
    includeDir = os.getcwd()


    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    spikeProcess = board.createProcess(name="spikingProcess",
                                     includeDir=includeDir,
                                     cFilePath = includeDir + "/spiking.c",
                                     funcName = "run_spiking",
                                     guardName = "do_spiking",
                                     phase = "spiking")
    


    #Create send channel SuperHost(computer) --> SnipProcess(Loihi LMT x86 Chip)
    sendSpikeChannel = board.createChannel(b'nxSendChannel', "int", 1)
    sendSpikeChannel.connect(None, spikeProcess)
    #Create read channel SnipProcess --> SuperHost
    recvSpikeChannel = board.createChannel(b'nxRecvChannel', "int", 1)
    recvSpikeChannel.connect(spikeProcess, None)

    
    net.run(30)
    net.disconnect()

    # -------------------------------------------------------------------------
    # Plot
    # -------------------------------------------------------------------------

    # The explanation of the behavior is in the tutorial introduction above.
    # The plot for compartment2 voltage appears to not always reach the
    # threshold of 640 when it spikes.  This is because when v crosses
    # the threshold during time step t, it gets reset immediately. Since the
    # monitor reads out the v value at the end of the time step, the
    # intermediate values are not visible from the plot.  Compartment1 voltage
    # is more consistent because it is only driven by a bias. Compartment2
    # receives time varying input and thus the last value below threshold is
    # always different and thus it appears to be spiking at different levels.
    fig = plt.figure(1002)
    k = 1
    for j in range(0, 3):
        plt.subplot(3, 2, k)
        uProbes[j].plot()
        plt.title('u'+str(j))
        k += 1
        plt.subplot(3, 2, k)
        vProbes[j].plot()
        plt.title('v'+str(j))
        k += 1
    if haveDisplay:
        plt.show()
    else:
        fileName = "tutorial_02_fig1002.png"
        print("No display available, saving to file " + fileName + ".")
        fig.savefig(fileName)



