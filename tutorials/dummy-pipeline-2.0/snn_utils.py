"""See NxNet tutorials for context"""

import os
import atexit
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

class NeuralNetworkHelper:
    def __init__(self, net):
        self.net = net
        self.modified_path = None
        self.precomputed_axon_file_name = "precomputed_axons.txt"

    def create_neuron(self, prototype):
        neuron = self.net.createCompartment(prototype)
        return neuron

    def create_input_layer(self, prototype, neurons):
        inputSynapseIds = []
        for neuron in neurons: 
            spikeInputPort = self.net.createSpikeInputPort()
            spikeInputPort.connect(neuron, prototype = prototype)
            inputSynapseIds.append(spikeInputPort.nodeId)
        return inputSynapseIds

    def create_output_layer(self, neurons):
        outputSynapseIds = []
        for neuron in neurons: 
            spikeOutputPort = self.net.createSpikeOutputPort()
            neuron.connect(spikeOutputPort)
            outputSynapseIds.append(spikeOutputPort.nodeId)
        return outputSynapseIds

    def get_resource_map(self, neuron, inputSynapseId, outputSynapseId):
        boardId, chipId, coreId, compartmentId, cxProfileCfgId, vthProfileCfgId = self.net.resourceMap.compartment(neuron.nodeId)
        inputSynapseData = self.net.resourceMap.inputAxon(inputSynapseId)
        inputSynapseId = inputSynapseData[0][3]  # Unpack the inputAxonId from the inputAxonData
        outputSynapseData = self.net.resourceMap.synapse(outputSynapseId)
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

    def store_resource_maps(self, neurons, inputSynapseIds, outputSynapseIds):
        resource_maps = {}
        for idx, (neuron, inputSynapseId, outputSynapseId) in enumerate(zip(neurons, inputSynapseIds, outputSynapseIds)):
            neuron_name = f"Neuron{idx}"
            resource_maps[neuron_name] = self.get_resource_map(neuron, inputSynapseId, outputSynapseId)
        return resource_maps

    def write_precomputed_axons_file(self, logicalInputAxonIds, logicalOutputAxonIds):
        physicalInputAxonIds = []
        physicalOutputAxonIds = []

        for logicalAxonId in logicalInputAxonIds:
            _, _, _, physicalAxonId = self.net.resourceMap.inputAxon(logicalAxonId)[0]
            physicalInputAxonIds.append(physicalAxonId)

        for logicalAxonId in logicalOutputAxonIds:
            _, _, _, physicalAxonId = self.net.resourceMap.synapse(logicalAxonId)
            physicalOutputAxonIds.append(physicalAxonId)

        with open(self.precomputed_axon_file_name, "w") as f:
            f.write("Input Axons:\n")
            f.write("\n".join(str(axon) for axon in physicalInputAxonIds))
            f.write("\n\nOutput Axons:\n")
            f.write("\n".join(str(axon) for axon in physicalOutputAxonIds))

    
    def update_host_snip_with_path_to_precomputed_axons_file(self, filePath):
        with open(filePath, 'r') as file:
            data = file.readlines()

        for index, line in enumerate(data):
            if 'static std::string precomputed_axons_file' in line:
                data[index] = 'static std::string precomputed_axons_file = "{}";\n'.format(
                    self.precomputed_axon_file_name)

        tokens = os.path.split(filePath)
        modified_fileName = "modified_" + tokens[-1]

        self.modified_path = os.path.join(tokens[0], modified_fileName)

        with open(self.modified_path, 'w') as file:
            file.writelines(data)

        atexit.register(self.cleanup)
        return self.modified_path

    def cleanup(self):
        if self.modified_path:
            os.remove(self.modified_path)
            os.remove(self.precomputed_axon_file_name)

    def create_probes(self, neurons, probe_parameters, probe_conditions=None):
        probes = []
        for neuron in neurons:
            probes.append(neuron.probe(probe_parameters, probe_conditions))
        return probes

    def plot_probes(self, u_probes, v_probes, s_probes):
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
