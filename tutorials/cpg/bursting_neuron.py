import nxsdk.api.n2a as nx


class BurstingNeuron: 
    def __init__(self, 
                 net: nx.NxNet,
                 srVthMant = 100,
                 srCurrentDecay = int(1 / 10 * 2 ** 12),
                 srVoltageDecay = int(1 / 4 * 2 ** 12),
                 amVthMant = 100,
                 amCurrentDecay = int(1 / 10 * 2 * 12), 
                 amVoltageDecay = int(1 / 4 * 2 ** 12),
                 ciVthMant = 5000,
                 ciCurrentDecay = int(1 / 10 * 2 ** 12),
                 ciVoltageDecay = int(1 / 100 * 2 ** 12),
                 sgVthMant = 5000,
                 sgCurrentDecay = int(1 / 10 * 2 ** 12),
                 sgVoltageDecay = int(1 / 100 * 2 ** 12), 
                 inVthMant = 10000,
                 inCurrentDecay = 0,
                 inVoltageDecay = 0,
                 s_2_in_weight = 10,
                 in_2_ci_weight = -256,
                 totalCompartments = 5):
        
        # Construct Internal Properties
        self.compartments = self.__core()   #Get dictionary of all compartments

    def __core(self): 
        """Private function to setup core components of bursting neuron model"""

        #Input Compartment -> transforms input current to voltage (Non-spiking)
        spike_receiver_pt = nx.CompartmentPrototype(
            vThMant=self.srVthMant,
            compartmentVoltageDecay=self.srVoltageDecay,
            compartmentCurrentDecay=self.srCurrentDecay,
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
        #Conditional Integrator -> integrates the voltage from sr only if AM's threshold is met (Non-spiking)
        conditional_integrator_pt = nx.CompartmentPrototype(
            vThMant=self.ciVthMant,
            compartmentVoltageDecay=self.ciVoltageDecay,
            compartmentCurrentDecay=self.ciCurrentDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            compartmentJoinOperation=nx.COMPARTMENT_JOIN_OPERATION.PASS,
            stackOut = nx.COMPARTMENT_STACK_OUT.PUSH,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

        #Spiking Compartment -> Generates burst of spikes whenever CI is above threshold
        soma_pt = nx.CompartmentPrototype(
            vThMant=self.sgVthMant,
            compartmentVoltageDecay=self.sgVoltageDecay,
            compartmentCurrentDecay=self.sgCurrentDecay,
            stackIn = nx.COMPARTMENT_STACK_IN.POP_A,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )   

        #Inhibitor Compartment -> resets the conditional integrator to resting state after {x} spikes (Can be adjusted)
        inhibitor_pt = nx.CompartmentPrototype(
            vThMant=self.inVthMant,
            compartmentVoltageDecay=self.inVoltageDecay,
            compartmentCurrentDecay=self.inCurrentDecay,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        """Create Neuron with NxSDK Neuron API"""
        soma_pt.addDendrite(conditional_integrator_pt, nx.COMPARTMENT_JOIN_OPERATION.OR)
        conditional_integrator_pt.addDendrites(astrocyte_modulator_pt, spike_receiver_pt, nx.COMPARTMENT_JOIN_OPERATION.PASS)

        #Create Neuron Prototype be passing cell body compartment (i.e. tree root node)    
        neuronPrototype = nx.NeuronPrototype(soma_pt)
        neuron = net.createNeuron(neuronPrototype)

        """Create Inhibitor Compartment"""
        inhibitor_cx = net.createCompartment(inhibitor_pt)
        s_2_in_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, 
                               weight=self.s_2_in_weight)
        
        neuron.soma.connect(inhibitor_cx, s_2_in_pt)

        # Connect back to inhibitor compartment to reset conditional integrator
        in_2_ci_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY, 
                               weight=self.in_2_ci_weight)
        inhibitor_cx.connect(conditional_integrator_pt, in_2_ci_pt)
        
        return {
            'soma': neuron.soma,
            'conditional_integrator': neuron.dendrites[0],
            'inhibitor': inhibitor_cx,
            'astrocyte_modulator': neuron.dendrites[0].dendrites[0],
            'spike_receiver': neuron.dendrites[0].dendrites[1]
        }
    
    """TODO: Implement spike stimulus & probe methods"""