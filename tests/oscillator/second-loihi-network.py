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
import numpy as np
import os
from threading import Thread, Event
import queue
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase
from pinpong.board import Board, Pin
from OscGenProcess import oscillator
import matplotlib as mpl


mpl.use('Agg')

# -------------------------------------------------------------------------
NUM_PLOTS_PER_RECEIVER = 1
NUM_TIME_STEPS = 500


curr_timestep = 0
# -------------------------------------------------------------------------


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
        global curr_timestep
        print(f"Data for neuron{self.index}: {args[0]}")
        for compartmentId, tsData in enumerate(args[0]):
            self.data[compartmentId].extend(tsData)
            for spike in tsData:
                if spike == 1: 
                    print(f"Sending spike now to neuron{self.index}")
            #print(f"{compartmentId}: {self.data[compartmentId]}, Index: {self.index}, Timestamp {tsData}")

        #print(f"Done this time.... time-step: {len(self.data[compartmentId])}")
        
        curr_timestep = len(self.data[compartmentId])

    def plot_data(self):
        fig, axes = plt.subplots(NUM_PLOTS_PER_RECEIVER, 1, figsize=(10, 5))
        if NUM_PLOTS_PER_RECEIVER == 1:
            axes = [axes]

        for compartmentId, ax in enumerate(axes):
            spikes = np.array(self.data[compartmentId])
            spike_times = np.where(spikes > 0)[0]
            ax.eventplot(spike_times, colors='red', lineoffsets=0, linelengths=1.0)
            ax.set_title(f"SpikeReceiver{self.index} Compartment{compartmentId+1}")
            ax.set_xlim((0, NUM_TIME_STEPS))
            ax.set_ylim((-1, 1))

        plt.tight_layout()
        plt.savefig(f'SpikeReceiver{self.index}_plot.png')
        plt.close(fig)
        print("Data has been plotted")


def plot_probes(vProbes, sProbes):
    # IMPORTANT: probes will not be evaluated unless run is finished
    # Must use board.finishRun() to make this true
    # Retrieve data from probes

    fig = plt.figure(figsize=(25,15))

    plt.subplot(2, 2, 1)
    vProbes[0].plot()
    plt.title('Compartment 1 Voltage')

    plt.subplot(2, 2, 2)
    sProbes[0].plot()
    plt.title('Compartment 1 Spikes')

    plt.subplot(2, 2, 3)
    vProbes[1].plot()
    plt.title('Compartment 2 Voltage')

    plt.subplot(2, 2, 4)
    sProbes[1].plot()
    plt.title('Compartment 2 Spike')

    if haveDisplay:
        plt.show()
    else: 
        print("No display available, save figure to file")
        plt.savefig('SpikeData.png')
        plt.close(fig)

#-------------------------------------------------------------


#-------------------------------------------------------------



if __name__ == '__main__':

    """Configure Network"""

    net = nx.NxNet()

    # Create a networkplot_probes(probes)
    prototype = nx.CompartmentPrototype(biasMant=0,
                                         biasExp=6,                 # biasMant * 2^biasExp = 100 * 2^6 = 6400
                                         vThMant=1000,              # VThMant * 2^vThExp = 1000 * 2^6 = 64000
                                         functionalState=2,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)

    neuron1 = net.createCompartment(prototype)
    neuron2 = net.createCompartment(prototype)


    # Taken from a_compartment_setup.ipynb in the NxSDK tutorials package
    probeParameters = [nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                       nx.ProbeParameter.SPIKE]
    probeConditions = None


    #probes1 = neuron1.probe(probeParameters, probeConditions)

    #probes2 = neuron2.probe(probeParameters, probeConditions)

    #vProbes = [probes1[0], probes2[0]]
    #sProbes = [probes1[1], probes2[1]]


    print("Compartment 1 index is ", neuron1.nodeId)
    print("Compartment 2 index is ", neuron2.nodeId)

    """ Interactive Spike Generator and Receiver Processes"""
    #Connection prototype
    spikeConnProto = nx.ConnectionPrototype(weight = 64)

    #Spike generator process for neuron1
    spikeGen1 = net.createInteractiveSpikeGenProcess(numPorts=1)
    spikeGen1.connect(neuron1, prototype=spikeConnProto)
    #Spike receiver process for neuron1
    #spikeReceiver1 = nx.SpikeReceiver(net)
    #neuron1.connect(spikeReceiver1)

    #Spike generator process for neuron2
    spikeGen2 = net.createInteractiveSpikeGenProcess(numPorts=1)
    spikeGen2.connect(neuron2, prototype=spikeConnProto)
    #Spike receiver process for neuron2
    #spikeReceiver2 = nx.SpikeReceiver(net)
    #neuron2.connect(spikeReceiver2)

    spikeReceiver1 = nx.SpikeReceiver(net)
    print("I'm here 1")
    spikeReceiver1.connect(neuron1)
    #neuron1.connect(spikeReceiver1)
    spikeReceiver2 = nx.SpikeReceiver(net)
    spikeReceiver2.connect(neuron2)
    print("I'm here 2")
    callable1 = Callable(1)
    callable2 = Callable(2)

    spikeReceiver1.callback(callable1)
    spikeReceiver2.callback(callable2) 
    

    #Compile defined network
    #compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    #board = compiler.compile(net)

    # Define directory where SNIP C-code is located
    includeDir = os.path.dirname(os.path.realpath(__file__))
    cFilePath = os.path.join(includeDir, "runmgmt.c")
    funcName = "run_mgmt"
    guardName = "do_run_mgmt"

    
    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    # Phase.EMBEDDED_MGMT - Execute SNIP on embedded management core. Enums are defined in nxsdk.graph.processes.phase
    # The API directory file for phase enums is nxsdk/graph/processes/phase_enums.py
    """
    managementProcess = net.createSnip(phase = Phase.EMBEDDED_MGMT,
                                     includeDir=includeDir,
                                     cFilePath = cFilePath,
                                     funcName = funcName,
                                     guardName = guardName)
    

    #Create Receive channel
    recvMgmtChannel= net.createChannel(name = b'nxRecvChannel', 
                                         messageSize = 4, 
                                         numElements = 1)
    
    #Connect the receive channel to the management process: Loihi ---> SuperHost
    recvMgmtChannel.connect(managementProcess, None)
    """
    
    spike_queue = queue.Queue()
    oscillator = oscillator(amplitude = 200, 
                            frequency = 1, 
                            phase_shift=0, 
                            spike_queue = spike_queue)
    
    oscillator.run() # Starts generating sinewave in a separate thread

    
    #board.start()
    #board.run(NUM_TIME_STEPS, aSync = True)

    net.runAsync(numSteps=NUM_TIME_STEPS)
    # is_complete = False
    try: 
        #listen for spikes
        while curr_timestep < NUM_TIME_STEPS:
            if not spike_queue.empty(): 
                
                #print("I'm here 2")
                neuron_id = spike_queue.get()
                if neuron_id == 0:
                    # print("Spiking neuron 1")
                    spikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
                elif neuron_id == 1:
                    # print("Spiking neuron 2")
                    spikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])
            
            time.sleep(0.001)
            
            #grab any spikes received
            #TODO: use threading loops to run both notify and spike in parallel
            #spikeReceiver1.notify()
            #spikeReceiver2.notify()

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Stopping run.")
        pass
    

    finally: 
        oscillator.stop()
        #board.finishRun()
        #board.disconnect()
        net.disconnect()
        print("Finished run successfully.")

        callable1.plot_data()
        callable2.plot_data()
        

        #TODO: plot_spike_data(callable1, callable2, filename='SpikeData.png')

    #plot_probes(vProbes, sProbes)
    # -------------------------------------------------------------------------
    # Plot Probe Data
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Finished
    # -------------------------------------------------------------------------


    

