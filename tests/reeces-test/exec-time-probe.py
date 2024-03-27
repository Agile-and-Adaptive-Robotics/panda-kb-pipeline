'''
Basic execution time test taken from tutorials/ipython/i_performance_profiling.ipynb

Author: Reece Wayt
Data: 3/27/2024
'''

import os, math
import matplotlib.pyplot as plt
import numpy as np

from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.api.enums.api_enums import ProbeParameter
from nxsdk.graph.monitor.probes import PerformanceProbeCondition
from benchmark_kit.perf_wrappers import timeit

#Basic execution time test taken from tutorials/ipython/i_performance_profiling.ipynb

def runNetwork(numCoresPerChip=1, numCompartmentsPerCore=1, 
               numAxonsPerCompartment=1, numSynPerAxon=1, 
               interSpikeInterval=1, runtime=1,
               bufferSize=1024, binSize=1,
               tEpoch=0,
               createDebugProbe=False):
    """Creates a scalable sample network, executes the network and returns energy, voltaga and spike probes."""
    
    assert numCompartmentsPerCore*numAxonsPerCompartment <= 4096
    
    board = N2Board(id=0,
                    numChips=1,
                    numCores=[numCoresPerChip],
                    initNumSynapses=[[numCompartmentsPerCore*numSynPerAxon]*numCoresPerChip])
    
    vth = 1000
    bias = int(vth//interSpikeInterval)
    
    # Configure compartments on cores
    for core in board.n2Chips[0].n2CoresAsList:
        core.numUpdates.configure(numUpdates=math.ceil(numCompartmentsPerCore/4))
        core.cxProfileCfg[0].configure(
            decayV=0,
            bapAction=0,
            refractDelay=1)
        core.vthProfileCfg[0].staticCfg.configure(vth=vth)
        core.dendriteAccumCfg[0].configure(delayBits=3)
        for i in range(numCompartmentsPerCore):
            core.cxCfg[i].configure(
                bias=bias,
                biasExp=6)
            core.cxMetaState[i//4].configure(phase0=2, phase1=2, phase2=2, phase3=2)
        
    # Connect compartments on cores
    for core in board.n2Chips[0].n2CoresAsList:
        ptr = 0
        for i in range(numCompartmentsPerCore):
            # Create output axon
            core.createDiscreteAxon(
                srcCxId=i,
                dstChipId=0,
                dstCoreId=core.id,
                dstSynMapId=i*2**(tEpoch>0))
            
            # Create input axon
            synMapId = i*2**(tEpoch>0)
            core.synapseMap[synMapId].synapsePtr=ptr
            core.synapseMap[synMapId].synapseLen=numSynPerAxon
            core.synapseMap[synMapId].discreteMapEntry.configure()
            ptr+=numSynPerAxon
            
            # Create synapses
            for k, j in enumerate(range(i*numSynPerAxon, (i+1)*numSynPerAxon)):
                core.synapses[j].configure(CIdx=k, Wgt=0, LrnEn=1, synFmtId=1)
    
        # Create synapse formats
        core.synapseFmt[1].configure(numSynapses=63, idxBits=5, wgtBits=1, compression=3, fanoutType=2, learningCfg=3)
        
        # Enable learning
        if tEpoch>0:
            core.stdpPreProfileCfg[0].configure(updateAlways=1)
            core.stdpCfg[0].configure(firstLearningIndex = 0)
            core.numUpdates[0].configure(numStdp=numAxonsPerCompartment)
            core.timeState[0].configure(tepoch=tEpoch)
        
    vProbe = sProbe = None
    if createDebugProbe:
        vProbe = board.monitor.probe(board.n2Chips[0].n2Cores[0].cxState, [0], 'v')[0]
        sProbe = board.monitor.probe(board.n2Chips[0].n2Cores[0].cxState, [0], 'spike')[0]
        
    # Create energy probe
    pc = PerformanceProbeCondition(tStart=1, tEnd=runtime, bufferSize=bufferSize, binSize=binSize)
    eProbe = board.probe(ProbeParameter.ENERGY, pc)
    
    # Run network
    board.run(runtime)
    board.disconnect()
    
    powerStats = board.energyTimeMonitor.powerProfileStats
    
    return eProbe, vProbe, sProbe, powerStats


def run_timed_network():
    return runNetwork(
        numCoresPerChip=1, 
        numCompartmentsPerCore=1024, 
        numAxonsPerCompartment=1, 
        numSynPerAxon=256, 
        interSpikeInterval=1000, 
        runtime=1000,
        bufferSize=1024,
        tEpoch=16,
        createDebugProbe=False
    )

if __name__ == '__main__':
    
    #Run network and collection execution time probes and times total execution time of network
    @timeit
    def execute_network():
        eProbeWithProbes, _, _, _ = run_timed_network()
        return eProbeWithProbes

    eProbeWithProbes = execute_network()
    print(eProbeWithProbes)

    #plt.figure(figsize=(20, 5))
    #eProbeWithProbes.plotExecutionTime()
    
