#
# Author: Reece Wayt
# Sources: Adapted from NxSDK tutorial "0_snip_for_reading_lakemont_spike_count.ipynb"
# Date: 4/11/2024
#
# Test Purpose: This is a preliminary test program to determine speed of snip send/recv channels from superhost to
# x86 chips on the KB (host). 


import os
import nxsdk.api.n2a as nx
import numpy as np
import matplotlib.pyplot as plt
from nxsdk.graph.monitor.probes import *

if __name__ == '__main__':

    #get net object
    net = nx.NxNet()

    # create a compartment prototype
    cxp = nx.CompartmentPrototype(biasMant=1000,
                              biasExp=6,
                              vThMant=10000,                              
                              compartmentVoltageDecay=0,
                              functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE)
    # Create a compartment from prototype cxp
    cx = net.createCompartment(cxp)

    # create a spike generator spikeGen that sends spike at each time step
    numPorts = 1
    spikeGen = net.createSpikeGenProcess(numPorts)
    spikeTimes0 = list(range(100))
    spikeGen.addSpikes([0], [spikeTimes0])

    # connect spikeGen with compartment cx
    connProto = nx.ConnectionPrototype(weight=200, signMode=nx.SYNAPSE_SIGN_MODE.MIXED)
    spikeGen.connect(cx, prototype=connProto)

    # functionally disables spike probes from NxNET API, should help performance
    customSpikeProbeCond = SpikeProbeCondition(tStart=10000000)
    sProbe = cx.probe(nx.ProbeParameter.SPIKE, customSpikeProbeCond)

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
                          
    # Create a channel named spikeCntr to get the spikes count information from Lakemont
    spikeCntrChannel = board.createChannel(b'nxspkcntr', "int", 100)

    # Connecting spikeCntr from runMgmtProcess to SuperHost which is receiving spike count in the channel
    spikeCntrChannel.connect(runMgmtProcess, None)


    board.run(100, aSync=True)
    # print(spikeCntrChannel.read(100)) doesn't work in real time, must read whole buffer otherwise stalls???
    spikeCntr = []
    spikeCntr.append(spikeCntrChannel.read(100))
    print(spikeCntr)

    board.finishRun()
    board.disconnect()
