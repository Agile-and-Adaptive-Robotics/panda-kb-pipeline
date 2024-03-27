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

# Creating an execution time probe
def runBoard():
    board = N2Board(id=0, numChips=1, numCores=[1], initNumSynapses=[[1]])

    etProbe = board.probe(
        probeType=ProbeParameter.EXECUTION_TIME, 
        probeCondition=PerformanceProbeCondition(
            tStart=1, 
            tEnd=100000, 
            bufferSize=1024, 
            binSize=2)
    )

    # Creating an execution time probe
    board = N2Board(id=0, numChips=1, numCores=[1], initNumSynapses=[[1]])

    eProbe = board.probe(
        probeType=ProbeParameter.ENERGY, 
        probeCondition=PerformanceProbeCondition(
            tStart=1, 
            tEnd=100000, 
            bufferSize=1024, 
            binSize=2)
    )

    board.run(100000)
    board.disconnect()

    return etProbe

@timeit
def execute_network():
    return runBoard()



if __name__ == 'main':
   
   exec_times = execute_network()
   plt.figure(figsize=(20,5))
   exec_times.plotExecutionTime()
    