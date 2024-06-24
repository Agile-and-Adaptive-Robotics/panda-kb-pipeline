# Oscillator Test Program

**Purpose**: This test program is building up to being able to test the real-time capabilities of the KB Board. Ultimately, I am using a simulated oscillator to send spikes in real-time to the Loihi Network. In a similar vein, spikes are read out in "real-time" to blink two LEDs to signify the activation of neurons(_Note_: I realized early on that the NxNet API does not guarantee real-time performance, most operations are batch and schedule at various times depending on when the network can get to it). Future implementations should us embedded and host snips for real-time performance. The aforementioned statements of course are up for debate depending on performance benchmarking uncovered (to be continued).

### The following pipeline is created in this test program:

<span style="color: red;">oscillatorProcess</span> --------> <span style="color: orange;">InteractiveSpikeGen</span> -----> <span style="color: yellow;">[Spike Train Input]</span> ----> <span style="color: green;">KB / Loihi Network</span> ----> <span style="color: blue;">Target Neuron Activation</span> ----> <span style="color: purple;">[Spike Receiver]</span> ----> <span style="color: violet;">blinkLED(1 or 2?)</span>


-------
<br>  

# Design Log: Discoveries & General Findings

The following section is dedicated to general steps I took to achieve the goal of this test program, along with discoveries that could prove useful for future iterations and designs. 


## Compartments and Parameter Formulas: 
```python 
prototype1 = nx.CompartmentPrototype(biasMant=100,
                                    biasExp=6,
                                    vThMant=1000,
                                    functionalState=2,
                                    compartmentVoltageDecay=256,
                                    compartmentCurrentDecay=410)

neuron1 = net.createCompartment(prototype1)
```
## Formulas
### Bias Formula: 

$$
 biasMant * (2 ^{biasExp}) = biasCurrent
$$
### Voltage Threshold Formula: 
$$
 vthMant * 2^6 = Vth
$$
### Compartment Voltage Decay (default = 0): 
$$
(1/\tau)*2^12 = \text{Voltage Decay}
$$
### Compartment Current Decay (default = 4096): 
$$
 (1/\tau)*2^12 = \text{Current Decay}
$$

## Spike Receivers
- The spikeReceiver() class requires a callback method, weirdly the callback method does not work unless you use `net.runAsync()`. Originally, I was defining the network then compiling it with the compiler tool to get the board object. I would then run the network with `board.run(Async = True)`-> Not sure why this wouldn't work other than that the spikeReceiver() class is part of the NxNet() API. 

## Creating SNIPs
- `Note` do not use the `board.createProcess()` method, this has been deprecated. Use `board.createSnip()` instead, as this gave me less troubles. 
- I realized during this project that you can use `net.createSnip()` or `board.createSnip()` , both work. 


**Here's my current implementation of a SNIP (not implemented in this code but useful for later use)**
```python
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
```
**SNIP Code**
```C
#include <stdlib.h>
#include <string.h>
#include "runmgmt.h"
#include <time.h>
#include <unistd.h>

/*
    Run management functions for exiting the simulation after a certain number of steps
*/

#define NUMSTEPS 500

int spikeCountCx = 0;
int channelID = -1;
int probe_id = 0; // Represents the id of the spike_probe, e.g.: If 5 probes are
                  // created this will be 0,1,2,3,4 corresponding to the spike probes
                  // in the order in which they were created

int do_run_mgmt(runState *s) {
        if (s->time_step==1){
            channelID = getChannelID("nxRecvChannel");
            return 0;
        }
        if(channelID == -1){
            return 0;
        }
        if(s->time_step == NUMSTEPS){
            return 1;
        }
    return 0;    
}

void run_mgmt(runState *s) {
    int time = s->time_step;
    printf("Time: %d\n", time);
    writeChannel(channelID, &time, 1);
}
```
**You then can use the run-time management snip for knowing the current time-step, this was helpful in ensuring the sendSpikes method was NOT hanging. It would generally hang if the board had finished a run but the superhost (computer) was unaware of the run finishing.**
```python
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
                    interactiveSpikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
                elif neuron_id == 1:
                    # print("Spiking neuron 2")
                    interactiveSpikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])
            
            time.sleep(0.005)

    except KeyboardInterrupt:
        print("Keyboard interrupt detected. Stopping run.")
        pass
    

    finally: 
        oscillator.stop()
        board.finishRun()
        board.disconnect()
        print("Finished run successfully.")
```

## Interactive Spike Senders
- Spike senders use `spikeInputPortNodeIds` to identify where spikes are send, the index of these node ids are created in order starting at 0. See the example below: 
```python
if neuron_id == 0:
    # print("Spiking neuron 1")
    spikeGen1.sendSpikes(spikeInputPortNodeIds=[0], numSpikes=[1])
elif neuron_id == 1:
    # print("Spiking neuron 2")
    spikeGen2.sendSpikes(spikeInputPortNodeIds=[1], numSpikes=[1])

```

## Working with probes
- `IMPORTANT` I found that if you are working at the board level that you must call the `board.finishRun()` for the probe data to be evaluated. Probe data is only evaluated and returned to the superhost after a run has finished. 
- Below is an example implementation that was used during testing this application: 
```python
    neuron1 = net.createCompartment(prototype)
    neuron2 = net.createCompartment(prototype)

    probeParameters = [nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                       nx.ProbeParameter.SPIKE]
    probeConditions = None


    probes1 = neuron1.probe(probeParameters, probeConditions)

    probes2 = neuron2.probe(probeParameters, probeConditions)

    vProbes = [probes1[0], probes2[0]]
    sProbes = [probes1[1], probes2[1]]

```

## Python Threading vs. Multiprocessing Library
- The threading library is best for I/O bound processes, while multiprocessing is best for CPU bound tasks because it sidesteps the GIL by using separate memory spaces for processes. 