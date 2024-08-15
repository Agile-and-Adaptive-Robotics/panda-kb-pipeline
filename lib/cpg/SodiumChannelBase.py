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
        pSodiumChannel = nx.CompartmentPrototype(
            vMaxExp = self.scVMaxExp,
            vThMant= self.scVthMant,
            compartmentVoltageDecay=self.scVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT_AND_SATURATE_V,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        #Responsible for opening and closing ion channel
        ActivationGate = nx.CompartmentPrototype(
            vMaxExp = self.ActGateVMaxExp,
            vThMant = self.ActGateVthMant,
            biasMant = self.ActGateBias, 
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
        )
        # Represents Na Ion which will be input to Sodium channel
        NaIon = nx.CompartmentPrototype(
            vMaxExp = self.NaIonVMaxExp,
            vThMant = self.NaIonVthMant,
            biasMant = self.NaIonBias,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT_AND_SATURATE_V,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Create multi-compartment neuron structure, see NxSDK Neuron Documentation for details
        pSodiumChannel.addDendrites(ActivationGate, NaIon, nx.COMPARTMENT_JOIN_OPERATION.PASS)
        neuronPrototype = nx.NeuronPrototype(pSodiumChannel)
        neuron = self.net.createNeuron(neuronPrototype)

        

        # Create Neuron Prototype be passing cell body compartment (i.e. tree root node)
        neuronPrototype = nx.NeuronPrototype(pSodiumChannel)
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
        file_name = "SodiumChannelBehavior.png"
        print(f"[INFO] Saving plot to {file_name}")
        fig.savefig(file_name)

    @property 
    def getCompartment(self, name): 
        return self.compartments['name']




###############################################################################################
###############################################################################################
class HalfCenterOscillator:
    """
    This class defines a half-center oscillator model based on the following paper:
    
        sr: Spike Receiver
        am: Astrocyte Modulator
        ci: Conditional Integrator
        sg: Spiking Compartment
        in: Inhibitor Compartment    
    See NxSDK documentation for more information on multi-compartment neuron models.    
    """
    def __init__(self,
                 net: nx.NxNet,
                 srVthMant=100,
                 srCurrentDecay=4096,
                 srVoltageDecay=int(1 / 4 * 2 ** 12),
                 amVthMant=100,
                 amCurrentDecay=int(1 / 100 * 2 ** 12),
                 amVoltageDecay=int(1 / 4 * 2 ** 12),
                 ciVthMant=100,
                 ciCurrentDecay=4096,
                 ciVoltageDecay=int(1 / 100 * 2 ** 12),
                 sgVthMant=100,
                 sgCurrentDecay=4096,
                 sgVoltageDecay=int(1 / 100 * 2 ** 12),
                 inVthMant=100,
                 inCurrentDecay=4096,
                 inVoltageDecay=0,
                 s_2_in_weight=5,
                 in_2_sr_weight=-200,
                 totalCompartments=5,
                 do_probes=True,
                 debug=False,
                 num_steps=-1):
        
        
        self.net = net
        self.srVthMant = srVthMant
        self.srCurrentDecay = srCurrentDecay
        self.srVoltageDecay = srVoltageDecay
        self.amVthMant = amVthMant
        self.amCurrentDecay = amCurrentDecay
        self.amVoltageDecay = amVoltageDecay
        self.ciVthMant = ciVthMant
        self.ciCurrentDecay = ciCurrentDecay
        self.ciVoltageDecay = ciVoltageDecay
        self.sgVthMant = sgVthMant
        self.sgCurrentDecay = sgCurrentDecay
        self.sgVoltageDecay = sgVoltageDecay
        self.inVthMant = inVthMant
        self.inCurrentDecay = inCurrentDecay
        self.inVoltageDecay = inVoltageDecay
        self.s_2_in_weight = s_2_in_weight
        self.in_2_sr_weight = in_2_sr_weight
        self.totalCompartments = totalCompartments
        self.debug = debug
        self.num_steps = num_steps

        if self.num_steps <= 0: 
            raise ValueError("Number of steps must be initialized and greater than 0")

        # Construct Internal Properties
        self.compartments = self.__core()  # Get dictionary of all compartments
        self.probes = {}

        # Setup probes if required
        if do_probes:
            self.__setup_probes()

    def __core(self):
        """Private function to setup core components of bursting neuron model"""

        # Input Compartment -> transforms input current to voltage (Non-spiking)
        spike_receiver_pt = nx.CompartmentPrototype(
            vThMant=self.srVthMant,
            compartmentVoltageDecay=self.srVoltageDecay,
            compartmentCurrentDecay=self.srCurrentDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        #Astrocyte Modulator -> modulates input current by integrating the input current (Non-spiking)
        astrocyte_modulator_pt = nx.CompartmentPrototype(
            vThMant=self.amVthMant,
            compartmentVoltageDecay=self.amVoltageDecay,
            compartmentCurrentDecay=self.amCurrentDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Conditional Integrator -> integrates the voltage from spike receiver only if AM's threshold is met (Non-spiking)
        conditional_integrator_pt = nx.CompartmentPrototype(
            vThMant=self.ciVthMant,
            compartmentVoltageDecay=self.ciVoltageDecay,
            compartmentCurrentDecay=self.ciCurrentDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            compartmentJoinOperation=nx.COMPARTMENT_JOIN_OPERATION.PASS,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Spiking Compartment -> Generates burst of spikes whenever CI is above threshold
        soma_pt = nx.CompartmentPrototype(
            vThMant=self.sgVthMant,
            compartmentVoltageDecay=self.sgVoltageDecay,
            compartmentCurrentDecay=self.sgCurrentDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.SPIKE_AND_RESET,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Inhibitor Compartment -> resets the conditional integrator to resting state after {x} spikes (Can be adjusted)
        inhibitor_pt = nx.CompartmentPrototype(
            vThMant=self.inVthMant,
            compartmentVoltageDecay=self.inVoltageDecay,
            compartmentCurrentDecay=self.inCurrentDecay,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        # Create Neuron with NxSDK Neuron API
        soma_pt.addDendrite(conditional_integrator_pt, nx.COMPARTMENT_JOIN_OPERATION.OR)
        conditional_integrator_pt.addDendrites(astrocyte_modulator_pt, spike_receiver_pt, nx.COMPARTMENT_JOIN_OPERATION.PASS)

        # Create Neuron Prototype be passing cell body compartment (i.e. tree root node)
        neuronPrototype = nx.NeuronPrototype(soma_pt)
        neuron = self.net.createNeuron(neuronPrototype)

        # Create Inhibitor Compartment
        inhibitor_cx = self.net.createCompartment(inhibitor_pt)
        s_2_in_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY,
                                           weight=self.s_2_in_weight)

        neuron.soma.connect(inhibitor_cx, prototype=s_2_in_pt)

        # Connect back to inhibitor compartment to reset conditional integrator
        in_2_sr_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY,
                                            weight=self.in_2_sr_weight)
        inhibitor_cx.connect(neuron.dendrites[0].dendrites[1], prototype=in_2_sr_pt)

        # Return dictionary of compartments
        return {
            'soma': neuron.soma,
            'conditional_integrator': neuron.dendrites[0],
            'inhibitor': inhibitor_cx,
            'astrocyte_modulator': neuron.dendrites[0].dendrites[0],
            'spike_receiver': neuron.dendrites[0].dendrites[1]
        }

    def __setup_probes(self):
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

    def __get_input_layer(self):
        """Private function to get neuron input layer, i.e. spike receiver and astrocyte modulator"""
        return [self.compartments['spike_receiver'], self.compartments['astrocyte_modulator']]
        

    def __poisson_distribution(self, rate, num_steps):
        print("Not implemented yet...")
        #TODO: Implement this function

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

        # Save the plot if no display is available
        if haveDisplay:
            plt.show()
        else:
            file_name = "probes_plot.png"
            print(f"No display available. Saving plot to {file_name}")
            fig.savefig(file_name)

    def add_spike_train(self):
        """For simulation purposes"""
        nxSpikeGen = self.net.createSpikeGenProcess(numPorts=1)
        sGenConn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight = 15)
        input_compartments = self.__get_input_layer()

        for comp in input_compartments: 
            if self.debug:
                print(comp)
            nxSpikeGen.connect(comp, prototype=sGenConn_pt)

        # Create window step distribution
        r1 = 10 
        r2 = 20 
        window = self.num_steps // 2 
        intervals = [window // r1, window // r2]

        spike_times1 = np.arange(0, window - 1, intervals[0])
        spike_times2 = np.arange(window, self.num_steps, intervals[1])
        
        spike_times = np.concatenate((spike_times1, spike_times2))
        if self.debug:
            print([spike_times])

        nxSpikeGen.addSpikes([0], [spike_times.tolist()])


