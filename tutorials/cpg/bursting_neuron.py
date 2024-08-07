import nxsdk.api.n2a as nx


class BurstingNeuron: 
    def __init__(self, net: nx.NxNet):
        self.net = net
        self.srVthMant = 100,
        self.srCurrentDecay = int(1 / 10 * 2 ** 12),
        self.srVoltageDecay = int(1 / 4 * 2 ** 12),
        self.amVthMant = 100,
        self.amCurrentDecay = int(1 / 10 * 2 * 12), 
        self.amVoltageDecay = int(1 / 4 * 2 ** 12),
        self.ciVthMant = 5000,
        self.ciCurrentDecay = int(1 / 10 * 2 ** 12),
        self.ciVoltageDecay = int(1 / 100 * 2 ** 12),
        self.sgVthMant = 5000,
        self.sgCurrentDecay = int(1 / 10 * 2 ** 12),
        self.sgVoltageDecay = int(1 / 100 * 2 ** 12), 
        self.inVthMant = 10000,
        self.inCurrentDecay = 0,
        self.inVoltageDecay = 0

    

    
    def __core(self): 
        """Private function to setup core components of bursting neuron model"""

        #Input Compartment -> transforms input current to voltage (Non-spiking)
        spike_receiver_pt = nx.CompartmentPrototype(
            vThMant=self.srVthMant,
            compartmentVoltageDecay=self.srVoltageDecay,
            compartmentCurrentDecay=self.srCurrentDecay
        )
        #Astrocyte Modulator -> modulates input current by integrating the input current (Non-spiking)  
        astrocyte_modulator_pt = nx.CompartmentPrototype(
            vThMant=self.amVthMant,
            compartmentVoltageDecay=self.amVoltageDecay,
            compartmentCurrentDecay=self.amCurrentDecay
        )   
        #Conditional Integrator -> integrates the voltage from sr only if AM's threshold is met (Non-spiking)
        conditional_integrator_pt = nx.CompartmentPrototype(
            vThMant=self.ciVthMant,
            compartmentVoltageDecay=self.ciVoltageDecay,
            compartmentCurrentDecay=self.ciCurrentDecay
        )

        #Spiking Compartment -> Generates burst of spikes whenever CI is above threshold
        spike_generator_pt = nx.CompartmentPrototype(
            vThMant=self.sgVthMant,
            compartmentVoltageDecay=self.sgVoltageDecay,
            compartmentCurrentDecay=self.sgCurrentDecay
        )   

        #Inhibitor Compartment -> resets the conditional integrator to resting state after {x} spikes (Can be adjusted)
        inhibitor_pt = nx.CompartmentPrototype(
            vThMant=self.inVthMant,
            compartmentVoltageDecay=self.inVoltageDecay,
            compartmentCurrentDecay=self.inCurrentDecay
        )

"""TODO: start here tomorrow"""