
import nxsdk.api.n2a as nx
import numpy as np
from time import sleep

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from threading import Thread, Event

#Number of timesteps to run
NUM_TIMESTEPS=10

# Number of plots for each spike receiver (corresponds to how many compartments are connected with the spike receiver)
NUM_PLOTS_PER_RECEIVER=GROUP_SIZE=3

class Callable:
    def __init__(self, index):
        # data will hold the spike activity for the 3 compartments associated with a spikereceiver
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
            print(f"Data {compartmentId}: {self.data[compartmentId]}, Index: {self.index}, Timestamp {tsData}")
        print("Done")


class AsyncPlotter:
    """Async Plotter plots the callableObjects in a backend thread by repeatedly polling for new data"""
    def __init__(self, numPlotsPerReceiver, callableObjects, timesteps):
        self.thread = Thread(target=AsyncPlotter.plot, args=(numPlotsPerReceiver, callableObjects, timesteps), daemon=True)
        self.thread.start()
        
    @staticmethod
    def plot(numPlotsPerObject, callableObjects, timesteps):
        try:
            fig = plt.figure(figsize=(8, 6))
            eventColors = ['blue', 'red']
            
            # Axes is a 2D list of axes. Each sublist consists of axes for a plot
            axes = [[] for c in callableObjects]
            figIndexIter = iter(range(1, numPlotsPerObject*len(callableObjects)+1))
            for i in range(numPlotsPerObject):
                for index, obj in enumerate(callableObjects):
                    figIndex = next(figIndexIter)
                    ax = plt.subplot(numPlotsPerObject, len(callableObjects), figIndex)
                    
                    ax.set_xlim((0, NUM_TIMESTEPS))
                    plt.title("SpikeReceiver{} Compartment{}".format(index+1, i+1))
                    axes[index].append(ax)
            
            plt.tight_layout()

            # Loop till all timesteps are complete
            while len(callableObjects[0].data[0]) != timesteps:
                sleep(0.5)
                for objIndex, subplot in enumerate(axes):
                    for index, ax in enumerate(subplot):
                        ax.eventplot(np.where(callableObjects[objIndex].data[index]), colors=eventColors[objIndex])
                fig.canvas.draw()

            # Save the plot to a file
            fig.savefig('spike_plot.png')
                   
                        
        except Exception as e:
            print(str(e))
        print("Plotting Complete")

def setupNetwork(net):
    compartmentPrototype = nx.CompartmentPrototype(functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE)
    compartmentPrototype.compartmentThreshold = 64

    cg1 = net.createCompartmentGroup(prototype=compartmentPrototype, size=GROUP_SIZE)
    
    compartmentPrototype.compartmentThreshold = 6400

    cg2 = net.createCompartmentGroup(prototype=compartmentPrototype, size=GROUP_SIZE)

    connectionPrototype = nx.ConnectionPrototype(weight=32)

    #Create one to one connection between the 2 compartment groups
    conngrp = cg1.connect(cg2, prototype=connectionPrototype, connectionMask=np.eye(GROUP_SIZE))

    return cg1, cg2

def createBasicSpikeGen(net, cg1):
    basicSpikeGen = net.createSpikeGenProcess(numPorts=1)

    connectionPrototype = nx.ConnectionPrototype(weight=128)

    basicSpikeGenConnGrp = basicSpikeGen.connect(cg1, prototype=connectionPrototype)

    # Inject spikes at these pre-determined timesteps
    basicSpikeGen.addSpikes(0, [1,2,4,8])
    return connectionPrototype



if __name__ == '__main__':


    net = nx.NxNet()

    cg1, cg2 = setupNetwork(net)

    connectionPrototype = createBasicSpikeGen(net, cg1)

    interactiveSpikeGen = net.createInteractiveSpikeGenProcess(numPorts=1)

    interactiveSpikeGenConnGrp = interactiveSpikeGen.connect(cg1, prototype=connectionPrototype)

    spikeReceiver1 = nx.SpikeReceiver(net)
    cg1.connect(spikeReceiver1)

    spikeReceiver2 = nx.SpikeReceiver(net)
    cg2.connect(spikeReceiver2)

    callable1 = Callable(1)
    callable2 = Callable(2)

    # Register these callable objects as callbacks
    spikeReceiver1.callback(callable1)
    spikeReceiver2.callback(callable2)
    connectionPrototype.weight = 128
    #Instantiate AsyncPlotter and start the non-blocking plotter before running the network
    #ap = AsyncPlotter(NUM_PLOTS_PER_RECEIVER, [callable1, callable2], NUM_TIMESTEPS)

    # Run Asynchronously (Non-Blocking)
    net.runAsync(numSteps=NUM_TIMESTEPS)

    # Send Spikes
    """
    for i in range(2):
        sleep(0.5)
        """
    
    interactiveSpikeGen.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[3])
    
    # net.stop()
    net.disconnect()