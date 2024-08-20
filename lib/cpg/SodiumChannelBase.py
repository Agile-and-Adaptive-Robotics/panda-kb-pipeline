"""
@Author: Reece Wayt
@Date: 8/15/2024
@Description: This module defines a half-center oscillator model based on the following paper:
    - Szczecinski, Nicholas & Hunt, Alexander & Quinn, Roger:
    - "Design process and tools for dynamic neuromechanical models and robot controllers"
"""

import os
import matplotlib as mpl
# Choose an interactive backend, like TkAgg or Qt5Agg
mpl.use('TkAgg')  # or 'TkAgg'
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx
import numpy as np 
from . import plothelper

haveDisplay = "DISPLAY" in os.environ


class SodiumChannel:
    def __init__(self,
                 net: nx.NxNet,
                 scVMaxExp = 9,
                 scVthMant = 7,
                 scVoltageDecay=int(1 / 3 * 2 ** 12),
                 ActGateVthMant = 7,
                 ActGateVMaxExp = 9, 
                 ActGateVMinExp = 0, 
                 NaIonVMaxExp = 9, 
                 NaIonVthMant = 7, #arbitrary for non-spiking neuron
                 debug = False
                 ):
        self.net = net
        self.scVMaxExp = scVMaxExp
        self.scVthMant = scVthMant
        self.scVoltageDecay = scVoltageDecay
        self.ActGateVthMant = ActGateVthMant
        self.ActGateVMaxExp = ActGateVMaxExp
        self.ActGateVMinExp = ActGateVMinExp
        self.NaIonVMaxExp = NaIonVMaxExp
        self.NaIonVthMant = NaIonVthMant

        # Calculate ActGateBias based on ActGateVthMant
        self.ActGateBias = int(self.ActGateVthMant * 2 ** 6)
        self.NaIonBias = int(self.NaIonVthMant * 2 ** 6)

        self.debug = debug
        

        """Internal Constructor Methods"""
        self.compartments = self.__core()
        self.probes = {}
        self.__create_probes() 

    def __core(self): 
        """Private constructor of internal compartment structure"""
        
        #simplified model of voltage-gated sodium channel for input to CPG Half Center
        SodiumChannel_pt = nx.CompartmentPrototype(
            #vMaxExp = self.scVMaxExp,
            vThMant = self.scVthMant,
            compartmentVoltageDecay=self.scVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT_AND_SATURATE_V,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        #Responsible for opening and closing ion channel
        ActivationGate = nx.CompartmentPrototype(
            #vMaxExp = self.ActGateVMaxExp,
            vThMant = self.ActGateVthMant,
            biasMant = self.ActGateBias, 
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
        )
        # Represents Na Ion which will be input to Sodium channel
        NaIon = nx.CompartmentPrototype(
            #vMaxExp = self.NaIonVMaxExp,
            vThMant = self.NaIonVthMant,
            biasMant = self.NaIonBias,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT_AND_SATURATE_V,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Create multi-compartment neuron structure, see NxSDK Neuron Documentation for details
        SodiumChannel_pt.addDendrites(ActivationGate, NaIon, nx.COMPARTMENT_JOIN_OPERATION.PASS)
        neuronPrototype = nx.NeuronPrototype(SodiumChannel_pt)
        neuron = self.net.createNeuron(neuronPrototype)

        

        # Create Neuron Prototype be passing cell body compartment (i.e. tree root node)
        neuronPrototype = nx.NeuronPrototype(SodiumChannel_pt)
        neuron = self.net.createNeuron(neuronPrototype)

        return {
            'SodiumChannel' : neuron.soma, 
            'ActivationGate' : neuron.dendrites[0],
            'NaIon' : neuron.dendrites[1]
        }
    
    def __create_probes(self):
        """Private function to setup probes for compartments"""
        probe_types = {
            "curr": nx.ProbeParameter.COMPARTMENT_CURRENT,
            "volt": nx.ProbeParameter.COMPARTMENT_VOLTAGE,
            "spike": nx.ProbeParameter.SPIKE
        }

        for comp_name, comp in self.compartments.items():
            self.probes[comp_name] = {}
            for probe_name, probe_param in probe_types.items():
                self.probes[comp_name][probe_name] = comp.probe(probe_param)[0]
                if self.debug:
                    print(f"Probe set up: {comp_name} {probe_name}")

    def inhibit_gate(self):
        """For simulation purposes, adjust times as needed"""
        nxSpikeGen = self.net.createSpikeGenProcess(numPorts=1)
        sGenConn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY, weight = -15)

        nxSpikeGen.connect(self.compartments['ActivationGate'], prototype=sGenConn_pt)
        spikeTimes = np.arange(100, 150, 1)

        nxSpikeGen.addSpikes([0], [spikeTimes.tolist()])

    @property
    def get_sodiumChannel(self): 
        return self.compartments['SodiumChannel']
    
    @property
    def get_sodiumGate(self):
        return self.compartments['ActivationGate']
    
    @property 
    def get_probes(self):
        return self.probes
    
    @property
    def set_debug(self, debug):
        self.debug = debug 

    def plot_probes(self):
        fig = plt.figure(2002, figsize=(20, 15))
        k = 1
        for comp_name, probes in self.probes.items():
            for probe_type, probe in probes.items():
                if self.debug:
                    print(f"Plotting {comp_name} {probe_type}, of {probe}, {probe_type}")
                plt.subplot(len(self.probes), 3, k)
                probe.plot()
                plt.title(f'{comp_name.capitalize()} {probe_type.capitalize()}', fontsize=15)
                k += 1

        plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
        file_name = "SodiumChannelBehavior2.png"
        print(f"[INFO] Saving plot to {file_name}")
        fig.savefig(file_name)

    def plot(self):
        plothelper.plot_probes(self.probes, title = "SodiumChannel")




###############################################################################################
###############################################################################################
