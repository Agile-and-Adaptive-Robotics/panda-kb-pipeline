#
# Author: Reece Wayt
# Sources: Adapted from NxSDK tutorial "0_snip_for_reading_lakemont_spike_count.ipynb"
# Date: 4/11/2024
#
# Test Purpose: This is a preliminary test program to determine speed of snip send/recv channels from superhost to
# x86 chips on the KB (host). 

import sys
import os

# Gets the directory where this program is located
this_program_dir = os.path.dirname(os.path.abspath(__file__))

# Constructs and normalizes the path to the benchmark_kit directory
benchmark_kit_path = os.path.normpath(os.path.join(this_program_dir, '../benchmark_kit'))

# Add the benchmark kit directory to sys.path
sys.path.append(benchmark_kit_path)

import nxsdk.api.n2a as nx
import numpy as np
import matplotlib.pyplot as plt
from nxsdk.graph.monitor.probes import *
from benchmark_kit.perf_wrappers import timeit

@timeit
#bulk read timer
def read_spike_counter(spikeCntrChannel, num_reads = 100):
    results = [spikeCntrChannel.read(1) for _ in range(num_reads)]
    return results
'''one shot read timer
def read_spike_counter(spikeCntrChannel):
    return spikeCntrChannel.read(1)
'''
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
    
    # Defining a process which will run during spiking phase
    # This snip will run on chip 1 lmt 0
    '''
    spikingProcess = board.createProcess(
                                     name="spikingProcess",
                                     cFilePath= includeDir + "/spiking.c",
                                     includeDir=includeDir,
                                     funcName="run_spiking",
                                     guardName="do_spiking",
                                     phase="spiking",
                                     chipId=1,
                                     lmtId=0
                                    )
    '''
    
                          
    # Create a channel named spikeCntr to get the spikes count information from Lakemont
    spikeCntrChannel = board.createChannel(b'nxspkcntr', "int", 1)

    ## TODO: implement later sendSpikeChannel = board.createChannel(b'nxsendspk', "int", 1)

    # Connecting spikeCntr from runMgmtProcess to SuperHost which is receiving spike count in the channel
    spikeCntrChannel.connect(runMgmtProcess, None)

    ##sendSpikeChannel.connect(None, spikingProcess)

    board.run(100, aSync=True)
    # print(spikeCntrChannel.read(100)) doesn't work in real time, must read whole buffer otherwise stalls???
    steps = 0
    #execution_times = []
    execution_time = 0
    spikeCntr = []

    spikeCntr, execution_time = read_spike_counter(spikeCntrChannel)
    '''
    for spike in spikeTimes0:
        # Call the function and capture both return values
        curr_count, elapsed_time = read_spike_counter(spikeCntrChannel)

        # Append the elapsed time to the execution_times list
        execution_times.append(elapsed_time)
    
        print(curr_count)  # Print the current count
        prev_count = curr_count  # Update the previous count
        steps += 1  # Increment the step count
    '''

    #curr_count = spikeCntrChannel.read(1)    
    print(spikeCntr)
    print("Execution time of 100 reads: {:.8f} s" .format(execution_time))
    #spikeCntr = []
    #spikeCntr.append(spikeCntrChannel.read(100))
    #print(spikeCntr)

    board.finishRun()
    board.disconnect()


    # Convert execution times to frequencies (in Hz)
    # frequencies = [1 / time for time in execution_times if time > 0]  # Avoid division by zero

    # Compute the average frequency
    # average_frequency = sum(frequencies) / len(frequencies) if frequencies else 0
    average_frequency = 1 / (execution_time / 100)
    # print("Frequencies: ", frequencies)
    print("Average Frequency: {:.5f} Hz".format(average_frequency))
