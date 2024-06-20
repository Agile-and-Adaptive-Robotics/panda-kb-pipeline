"""
Author: Reece Wayt

Version: 1.0.1

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
import matplotlib as mpl


haveDisplay = "DISPLAY" in os.environ
if not haveDisplay:
    mpl.use('Agg')

# -------------------------------------------------------------------------
NUM_PLOTS_PER_RECEIVER = 1
NUM_TIME_STEPS = 500
# -------------------------------------------------------------------------

def setupNetwork(net):

    # Create a network

    prototype1 = nx.CompartmentPrototype(biasMant=1,
                                         biasExp=6,               # biasMant * 2^biasExp = 1 * 2^6 = 64
                                         vThMant=10,              # VThMant * 2^vThExp = 10 * 2^6 = 
                                         functionalState=2,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)
    

    neuron1 = net.createCompartment(prototype1)

    prototype2 = nx.CompartmentPrototype(vThMant=100,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)
    

    neuron2 = net.createCompartment(prototype2)

    #Excitatory Synapse Connection
    connProto1 = nx.ConnectionPrototype(weight=40, compressionMode=3)

    net._createConnection(neuron1, neuron2, connProto1)

    # Taken from a_compartment_setup.ipynb in the NxSDK tutorials package
    probeParameters = [nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                       nx.ProbeParameter.SPIKE]
    probeConditions = None


    n1Probes = neuron1.probe(probeParameters, probeConditions)

    n2Probes = neuron2.probe(probeParameters, probeConditions)

    vProbes = [n1Probes[0], n2Probes[0]]
    sProbes = [n1Probes[1], n2Probes[1]]

    return vProbes, sProbes

if __name__ == '__main__':
    net = nx.NxNet()

    #Configure network
    vProbes, sProbes = setupNetwork(net)
     #Compile defined network
    compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    board = compiler.compile(net)

    #Note: This code only works if ran aSync = False
    board.run(100, aSync = False)


    board.disconnect

    
    
    fig = plt.figure(1002)
    plt.subplot(3, 2, 1)
    vProbes[0].plot()
    plt.title('Compartment 1 Voltage')

    plt.subplot(3, 2, 2)
    vProbes[1].plot()
    plt.title('Compartment 2 Voltage')

    plt.subplot(3, 2, 3)
    sProbes[0].plot()
    plt.title('Compartment 1 Spikes')

    plt.subplot(3, 2, 4)
    sProbes[1].plot()
    plt.title('Compartment 2 Spikes')

    if haveDisplay:
        plt.show()
    else: 
        print("No display")
        fig.savefig("plot-test.png")
    

    # -------------------------------------------------------------------------
    # Plot Probe Data
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Finished
    # ------------------------------------------------------------------------
