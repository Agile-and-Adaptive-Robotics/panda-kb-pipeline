"""
Author: Reece Wayt

Version: 1.0.1

Sources: 
    - "tutorial_24_control_loop_using_rospy.py" in the NxSDK tutorials package
    - spike_sender_receiver_example.py found in this folder & the NxSDK tutorials package

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
import psutil


mpl.use('Agg')

# -------------------------------------------------------------------------
NUM_PLOTS_PER_RECEIVER = 1
NUM_TIME_STEPS = 500
CURR_TIMESTEP = 0
# -------------------------------------------------------------------------
"""Used for callback method of spike receiver"""
class Callable:
    def __init__(self, index):
        # data will hold the spike activity for the compartments associated with a spikereceiver
        # Each spikereceiver will have its own Callable instance as the callback. This is denoted by index
        self.data = [[] for i in range(NUM_PLOTS_PER_RECEIVER)]
        self.index = index
        """Performance Measures"""
        self.total_latency = 0.0
        self.request_count = 0

    def __call__(self, *args, **kwargs):
        # At every invocation of this method, new data since the last invocation will be passed along.
        # args[0] essentially is a list[list]. Length of the parent list is the number of compartments 
        # connecting to this spike receiver while each sublist is the timeseries data associated with that
        # compartment accrued since the last invocation. len(args) is 1.
        global CURR_TIMESTEP, led2_output, led3_output
        #print(f"Data for neuron{self.index}: {args[0]}")
        start_time = time.perf_counter()
        for compartmentId, tsData in enumerate(args[0]):
            self.data[compartmentId].extend(tsData)
            for spike in tsData:
                if spike == 1:
                    if self.index == 1:
                        #print(f"Data to blink led2, {self.index}")
                        led2_output.send_spike('blink')
                    elif self.index == 2:  
                        #print(f"Data to blink led3, {self.index}")
                        led3_output.send_spike('blink')
                    #Increment per request of spike received
                    self.request_count+= 1  
            #print(f"{compartmentId}: {self.data[compartmentId]}, Index: {self.index}, Timestamp {tsData}")

        #print(f"Done this time.... time-step: {len(self.data[compartmentId])}")
        CURR_TIMESTEP = len(self.data[compartmentId])

        end_time = time.perf_counter()
        self.total_latency = self.total_latency + (end_time - start_time)

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

    def get_average_latency(self):
        return self.total_latency / self.request_count if self.request_count > 0 else 0


class ledPinOutput:
    def __init__(self, pin_number):
        #self.board = Board("uno", "/dev/ttyACM0").begin()
        self.pin_number = pin_number
        self.led = Pin(pin_number, Pin.OUT)
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        while not self.stop_event.is_set():
            try:
                # Wait for a spike with a timeout to periodically check for stop event
                spike = self.queue.get(timeout=0.001)
                if spike == 'blink':
                    self._blink_led()
            except queue.Empty:
                continue

    def _blink_led(self):
        #print(f"Blinking Pin: {self.pin_number}")
        self.led.write_digital(1)
        time.sleep(0.005)     # Keep it on for 0.2 seconds
        self.led.write_digital(0)
        time.sleep(0.005)     # Keep it off for 0.2 seconds

    def send_spike(self, spike):
        self.queue.put(spike)

    def cleanup(self):
        self.stop_event.set()
        self.thread.join()
        
#--------------------------------------------------------------------------
# Main
#--------------------------------------------------------------------------
"""Header Pin Outputs"""
pandaBoard = Board("uno", "/dev/ttyACM0").begin()

led2_output = ledPinOutput(pin_number=Pin.D2)
led3_output = ledPinOutput(pin_number=Pin.D3)

if __name__ == '__main__':

    """Configure Network"""

    net = nx.NxNet()

    prototype = nx.CompartmentPrototype(biasMant=0,
                                         biasExp=6,  
                                         vThMant=1000, 
                                         functionalState=2,
                                         compartmentVoltageDecay=256,
                                         compartmentCurrentDecay=410)
    neuron1 = net.createCompartment(prototype)
    neuron2 = net.createCompartment(prototype)

    print("Compartment 1 index is ", neuron1.nodeId)
    print("Compartment 2 index is ", neuron2.nodeId)

    """ Interactive Spike Generator and Receiver Processes"""
    #Connection prototype
    spikeConnProto = nx.ConnectionPrototype(weight = 64)

    #Spike generator process for neuron1
    spikeGen1 = net.createInteractiveSpikeGenProcess(numPorts=1)
    spikeGen1.connect(neuron1, prototype=spikeConnProto)

    #Spike generator process for neuron2
    spikeGen2 = net.createInteractiveSpikeGenProcess(numPorts=1)
    spikeGen2.connect(neuron2, prototype=spikeConnProto)
    
    #Spike receiver processes
    spikeReceiver1 = nx.SpikeReceiver(net)
    spikeReceiver1.connect(neuron1)
    spikeReceiver2 = nx.SpikeReceiver(net)
    spikeReceiver2.connect(neuron2)
    #Register callback functions for spike receivers
    callable1 = Callable(1)
    callable2 = Callable(2)
    spikeReceiver1.callback(callable1)
    spikeReceiver2.callback(callable2) 
    

    #Compile defined network
    #if using the N2Board class, uncomment the following lines
    #compiler = nx.N2Compiler()
    #receive board object required by SNIPs
    #board = compiler.compile(net)
    
    """Oscillator Process, see OscGenProcess.py for more details"""
    spike_queue = queue.Queue()
    oscillator = oscillator(amplitude = 200, 
                            frequency = 1, 
                            phase_shift=0, 
                            spike_queue = spike_queue)
    
    oscillator.run() # Starts generating sinewave in a separate thread

    #if using the N2Board class, uncomment the following lines
    #board.start()
    #board.run(NUM_TIME_STEPS, aSync = True)

    """Setup performance measures"""
    total_spikes_sent = 0
    total_spikes_received = 0
    p = psutil.Process()
    net_counters_start = psutil.net_io_counters()
    p_start_time = time.perf_counter()

    """Run Network"""
    net.runAsync(numSteps=NUM_TIME_STEPS)
    

    try: 
        #listen for spikes
        while CURR_TIMESTEP < NUM_TIME_STEPS:
            if not spike_queue.empty(): 
                
                #print("I'm here 2")
                neuron_id = spike_queue.get()
                if neuron_id == 0:
                    # print("Spiking neuron 1")
                    spikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
                elif neuron_id == 1:
                    # print("Spiking neuron 2")
                    spikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])
            
            total_spikes_sent += 1
            

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Stopping run.")
        pass
    

    finally: 
        p_stop_time = time.perf_counter()
        net_counters_stop = psutil.net_io_counters()
        oscillator.stop()
        #board.finishRun()
        #board.disconnect()
        net.disconnect()
        print("Finished run successfully.")

        #cleanup LED objects
        led2_output.cleanup()
        led3_output.cleanup()

        #Plot spike receiver data from runtime
        callable1.plot_data()
        callable2.plot_data()


    """Performance Evaluation"""
    total_spikes_received = callable1.request_count + callable2.request_count
    total_elapsed_time = p_stop_time - p_start_time

    #I/O Counters Data
    print(p.io_counters())
    print(f"Net counters start: {net_counters_start}")
    print(f"Net counters stop: {net_counters_stop}")
    print(f"Total Bytes Sent: {net_counters_stop.bytes_sent - net_counters_start.bytes_sent}")
    print(f"Total Bytes Received: {net_counters_stop.bytes_recv - net_counters_start.bytes_recv}")

    average_latency = (callable1.get_average_latency() + callable2.get_average_latency()) / 2
    throughput = ((total_spikes_received + total_spikes_sent)/ total_elapsed_time)

    print(f"Total Spikes Sent: {total_spikes_sent}")
    print(f"Total Spikes Received: {total_spikes_received}")
    print(f"Total Elapsed Time: {total_elapsed_time} [seconds]")
    print(f"Average Spike Receiver Latency: {average_latency} [seconds]") 
    print(f"Throughput: {throughput} spikes/second")   

    # -------------------------------------------------------------------------
    # Finished
    # -------------------------------------------------------------------------


    

