import os
import matplotlib.pyplot as plt
import matplotlib as mpl
from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

haveDisplay = "DISPLAY" in os.environ
if not haveDisplay:
    mpl.use('Agg')


def create_neuron(net, prototype):
    neuron = net.createCompartment(prototype)
    return neuron

def create_input_layer(net, prototype, neurons):
    inputSynapseIds = []
    for neuron in neurons: 
        spikeInputPort = net.createSpikeInputPort()
        spikeInputPort.connect(neuron, prototype = prototype)
        inputSynapseIds.append(spikeInputPort.nodeId)
    return inputSynapseIds

def create_output_layer(net, neurons):
    outputSynapseIds = []
    for neuron in neurons: 
        spikeOutputPort = net.createSpikeOutputPort()
        neuron.connect(spikeOutputPort)
        outputSynapseIds.append(spikeOutputPort.nodeId)
    return outputSynapseIds


def get_resource_map(net, neuron, inputSynapseId, outputSynapseId):
    boardId, chipId, coreId, compartmentId, cxProfileCfgId, vthProfileCfgId = net.resourceMap.compartment(neuron.nodeId)
    inputSynapseData = net.resourceMap.inputAxon(inputSynapseId)
    inputSynapseId = inputSynapseData[0][3]  # Unpack the inputAxonId from the inputAxonData
    outputSynapseData = net.resourceMap.synapse(outputSynapseId)
    return {
        "boardId": boardId,
        "chipId": chipId,
        "coreId": coreId,
        "compartmentId": compartmentId,
        "cxProfileCfgId": cxProfileCfgId,
        "vthProfileCfgId": vthProfileCfgId,
        "inputSynapseId": inputSynapseId,
        "outputSynapseId": outputSynapseId
    }

"""
@Brief:
    This function takes a neural network, a list of neurons, and their corresponding
    input and output synapse IDs, and maps the logical IDs to physical hardware IDs. 
    The mappings are then stored in a dictionary with neuron names as keys.

@Parameters:
    net (nx.NxNet): The neural network object containing the neurons and synapses.
    neurons (list of nx.NxCompartment): A list of neuron objects to be mapped.
    inputSynapseIds (list of int): A list of input synapse logical IDs corresponding to the neurons.
    outputSynapseIds (list of int): A list of output synapse logical IDs corresponding to the neurons.

@Returns:
    dict: A dictionary containing the resource mappings for each neuron. The keys are 
          neuron names (e.g., "Neuron0", "Neuron1"), and the values are the results 
          of the `get_resource_map` function, which maps the logical IDs to physical IDs.
"""
def store_resource_maps(net, neurons, inputSynapseIds, outputSynapseIds):
    resource_maps = {}
    for idx, (neuron, inputSynapseId, outputSynapseId) in enumerate(zip(neurons, inputSynapseIds, outputSynapseIds)):
        neuron_name = f"Neuron{idx}"
        resource_maps[neuron_name] = get_resource_map(net, neuron, inputSynapseId, outputSynapseId)
    return resource_maps

"""
@Brief: 
    This function creates probes for the given neurons and probe parameters. 

@Parameters: 
    neurons (list of nx.NxCompartment): A list of neuron objects to be probed.
    probe_parameters (list of nx.ProbeParameter): A list of probe parameters to be probed.
    probe_conditions (list of nx.ProbeCondition): A list of probe conditions to be probed. Usually set to None. 

@Returns:
    2D list of probes. Each sublist contains the probes for a single neuron [u, v, s].
"""
def create_probes(neurons, probe_parameters, probe_conditions=None):
    probes = []
    for neuron in neurons:
        probes.append(neuron.probe(probe_parameters, probe_conditions))
    return probes

def plot_probes(u_probes, v_probes, s_probes):
    fig = plt.figure(2002, figsize = (35, 25))
    k = 1
    for i in range(len(u_probes)):
        plt.subplot(len(u_probes), 3, k)
        u_probes[i].plot()
        plt.title(f'Neuron {i} Current')
        k += 1

        plt.subplot(len(v_probes), 3, k)
        v_probes[i].plot()
        plt.title(f'Neuron {i} Voltage')
        k += 1

        plt.subplot(len(s_probes), 3, k)
        s_probes[i].plot()
        plt.title(f'Neuron {i} Spikes')
        k += 1

    plt.tight_layout(pad=3.0, w_pad=3.0, h_pad=3.0)
    if haveDisplay:
        plt.show()
    else: 
        fileName = "probes_plot.png"
        print(f"No display available. Saving plot to {fileName}")
        fig.savefig(fileName)
