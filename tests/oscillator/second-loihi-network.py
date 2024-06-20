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
from nxsdk.utils.plotutils import plotRaster
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

def plot_probes(vProbes, sProbes):
    # IMPORTANT: probes will not be evaluated unless run is finished
    # Must use board.finishRun() to make this true
    # Retrieve data from probes

    fig = plt.figure(1001)

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
        plt.savefig('Compartment1Voltage.png')
        plt.close(fig)



def setupNetwork():

    net = nx.NxNet()

    # Create a networkplot_probes(probes)
    prototype = nx.CompartmentPrototype(biasMant=100,
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


    probes1 = neuron1.probe(probeParameters, probeConditions)

    probes2 = neuron2.probe(probeParameters, probeConditions)

    vProbes = [probes1[0], probes2[0]]
    sProbes = [probes1[1], probes2[1]]


    print("Compartment 1 index is ", neuron1.nodeId)
    print("Compartment 2 index is ", neuron2.nodeId)

    """ Interactive Spike Generator and Receiver Processes"""
    #Connection prototype
    spikeConnProto = nx.ConnectionPrototype(weight = 128)

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

    """
    callable1 = Callable(1)
    callable2 = Callable(2)

    # Register these callable objects as callbacks
    spikeReceiver1.callback(callable1)
    spikeReceiver2.callback(callable2)
    """

    

    #Compile defined network
    compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    board = compiler.compile(net)


    # Return the configured probes
    return board, net, neuron1, neuron2, spikeGen1, spikeGen2, vProbes, sProbes



if __name__ == '__main__':

    #Configure network
    board, net, neuron1, neuron2, spikeGen1, spikeGen2, vProbes, sProbes = setupNetwork()

    # Define directory where SNIP C-code is located
    includeDir = os.path.dirname(os.path.realpath(__file__))
    cFilePath = os.path.join(includeDir, "runmgmt.c")
    funcName = "run_mgmt"
    guardName = "do_run_mgmt"

    
    # Create SNIP, define which code to execute and in which phase of the NxRuntime execution cycle
    # Phase.EMBEDDED_MGMT - Execute SNIP on embedded management core. Enums are defined in nxsdk.graph.processes.phase
    # The API directory file for phase enums is nxsdk/graph/processes/phase_enums.py
    
    managementProcess = board.createSnip(phase = Phase.EMBEDDED_MGMT,
                                     includeDir=includeDir,
                                     cFilePath = cFilePath,
                                     funcName = funcName,
                                     guardName = guardName)
    

    #Create Receive channel
    recvMgmtChannel= board.createChannel(name = b'nxRecvChannel', 
                                         messageSize = 4, 
                                         numElements = 1)
    
    #Connect the receive channel to the management process: Loihi ---> SuperHost
    recvMgmtChannel.connect(managementProcess, None)

    
    spike_queue = queue.Queue()
    oscillator = oscillator(amplitude = 200, 
                            frequency = 1, 
                            phase_shift=0, 
                            spike_queue = spike_queue)
    
    oscillator.run() # Starts generating sinewave in a separate thread

    
    board.start()
    board.run(NUM_TIME_STEPS, aSync = True)

    # is_complete = False
    try: 
        #listen for spikes
        while True:
            if not spike_queue.empty(): 
                if(recvMgmtChannel.probe()):
                    timeStep = recvMgmtChannel.read(1)[0]
                    if(timeStep == NUM_TIME_STEPS):
                        is_complete = True
                        print("Execution complete")
                        break

                #print("I'm here 2")
                neuron_id = spike_queue.get()
                if neuron_id == 0:
                    # print("Spiking neuron 1")
                    spikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
                elif neuron_id == 1:
                    # print("Spiking neuron 2")
                    spikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])
            
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Stopping run.")
        pass
    

    finally: 
        oscillator.stop()
        board.finishRun()

        board.disconnect()
        print("Finished run successfully.")

        #TODO: plot_spike_data(callable1, callable2, filename='SpikeData.png')

    plot_probes(vProbes, sProbes)
    # -------------------------------------------------------------------------
    # Plot Probe Data
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Finished
    # -------------------------------------------------------------------------


    

