"""
led-multithread.py - A test program to create a concurrent thread that communicates
with the panda board's expansion header Arduino pin D13 to control an LED based on spike data.
This program also tests the read speed of SNIP receive channels and prepares for future
explorations with embedded SNIPs and the NxCore API.

Author: Reece Wayt
Sources: Adapted from NxSDK tutorial "0_snip_for_reading_lakemont_spike_count.ipynb"
Date: 4/25/2024
"""

import os
import sys
import numpy as np
import threading
import queue
from thread1_led_blink import monitor_for_spike
from pinpong.board import Board, Pin
import matplotlib.pyplot as plt
import nxsdk.api.n2a as nx
from nxsdk.graph.monitor.probes import *
from benchmark_kit.perf_wrappers import timeit

def configure_paths():
    """Configure paths for the benchmark kit."""
    this_program_dir = os.path.dirname(os.path.abspath(__file__))
    benchmark_kit_path = os.path.normpath(os.path.join(this_program_dir, '../benchmark_kit'))
    sys.path.append(benchmark_kit_path)

@timeit
def read_spike_counter(spikeCntrChannel, spike_queue, num_reads=100):
    """
    Read spike counters from the channel and signal LED thread if spike occurs.
    
    Args:
    spikeCntrChannel: Channel to read spike counts from
    spike_queue: Queue to communicate with LED thread
    num_reads: Number of times to read from the channel

    Returns:
    results: List of spike counts
    """
    last_result = 0
    results = []
    for _ in range(num_reads):
        curr_result = spikeCntrChannel.read(1)[0]
        print(f"Read spike {curr_result}")
        if curr_result > last_result: 
            spike_queue.put(True)  # Signal LED thread to blink LED
        last_result = curr_result
        results.append(last_result)
    return results

def setup_nxsdk_network():
    """
    Set up the NxSDK network with a single compartment and spike generator.
    
    Returns:
    board: Compiled NxSDK board object
    """
    net = nx.NxNet()
    cxp = nx.CompartmentPrototype(biasMant=1000, biasExp=6, vThMant=10000,
                                  compartmentVoltageDecay=0, functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE)
    cx = net.createCompartment(cxp)

    # Create spike generator
    num_ports = 1
    spike_gen = net.createSpikeGenProcess(num_ports)
    spike_times = list(range(100))
    spike_gen.addSpikes([0], [spike_times])

    # Connect spike generator to compartment
    conn_proto = nx.ConnectionPrototype(weight=200, signMode=nx.SYNAPSE_SIGN_MODE.MIXED)
    spike_gen.connect(cx, prototype=conn_proto)

    # Set up spike probe
    custom_spike_probe_cond = nx.SpikeProbeCondition(tStart=10000000)
    cx.probe(nx.ProbeParameter.SPIKE, custom_spike_probe_cond)

    # Compile network
    compiler = nx.N2Compiler()
    return compiler.compile(net)

def init_led_thread():
    """
    Initialize LED thread components.
    
    Returns:
    board: PinPong board object
    led: LED pin object
    my_queue: Queue for communication between threads
    stop_event: Event to signal thread termination
    """
    board = Board("uno", "/dev/ttyACM0").begin()
    led = Pin(Pin.D13, Pin.OUT)  # Initialize pin as output
    my_queue = queue.Queue()
    stop_event = threading.Event()
    return board, led, my_queue, stop_event

def main():
    # Initialize panda board, LED, and queue
    lp_board, led, spk_queue, stop_event = init_led_thread()

    # Set up the LED thread
    monitor_thread = threading.Thread(target=monitor_for_spike, args=(lp_board, led, spk_queue, stop_event))
    monitor_thread.daemon = True  # Ensures the thread will exit when the main program does
    monitor_thread.start()

    configure_paths()
    board = setup_nxsdk_network()

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
    # Connect spikeCntr from runMgmtProcess to SuperHost which is receiving spike count in the channel
    spikeCntrChannel.connect(runMgmtProcess, None)
    
    # Run the board simulation
    board.run(100, aSync=True)

    # Read spike counter and measure execution time
    spike_counter, execution_time = read_spike_counter(spikeCntrChannel, spk_queue)

    print(spike_counter)
    print(f"Execution time of 100 reads: {execution_time:.8f} s")

    try:
        board.finishRun()
        board.disconnect()
    finally:
        # Ensure LED thread is properly terminated
        stop_event.set()
        monitor_thread.join()
        print("Thread joined successfully.")

    # Calculate and print average frequency of spike reads
    average_frequency = 1 / (execution_time / 100)
    print(f"Average Frequency: {average_frequency:.5f} Hz")

if __name__ == '__main__':
    main()
    
            