from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx 
from .SodiumChannelBase import SodiumChannel 
from .InhibitorBase import Inhibitor
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('TkAgg')


from enum import IntEnum, Enum

class ProbeType(IntEnum):
    CURRENT = 0
    VOLTAGE = 1
    SPIKE = 2

class CompartmentType(Enum):
    SpikeGenerator = 0
    HalfCenter = 1
    SodiumChannel = 2
    ActivationGate = 3
    SodiumIon = 4
    ActGateInhibitor = 5 
    #Add more as needed


class HalfCenter:
    """
    Uses Loihi's multi-compartment neuron model to create a half center oscillator with the following compartments:
        SG: Spiking Compartment, this is need to communicate with other compartments outside of neuron structure
        HalfCenter: Main compartment
        SodiumChannel: Sodium Channel
        ActivationGate: Activation Gate
        SodiumIon: Sodium Ion
        ActGateInhibitor: This simulates the close of the sodium channel once the HalfCenter becomes depolarized
        
    """
    def __init__(self,
                 net : nx.NxNet,
                 debug = False
                 ):
        self.net = net
        self.debug = debug

        self.SGVthMant = 10
        self.SGVoltageDecay = int(1 / 10 * 2 ** 12)
        self.SGCurrentDecay = 4096

        self.HCVthMant = 9
        self.HCCurrentDecay = 4096
        self.HCVoltageDecay = int(1 / 3 * 2 ** 12)

        self.SCVthMant = 10
        self.SCVoltageDecay = int(1 / 1 * 2 ** 12)
        self.SCCurrentDecay = 4096
        

        self.ActGateVthMant = 10
        self.ActGateBias = int((self.ActGateVthMant * 2 ** 6) + 1)
        self.ActGateCurrentDecay = 4096
        self.ActGateVoltageDecay = int(1 / 2 * 2 ** 12)

        self.NaIonVthMant = 10
        self.NaIonBias = int(self.NaIonVthMant * 2 ** 6)
        self.NaIonVoltageDecay = int(1 / 1 * 2 ** 12)
        self.NaIonCurrentDecay = 4096

        self.InhActGateVthMant = 10
        self.InhActGateVoltageDecay = int(1 / 10 * 2 ** 12)

        """[IMPORTANT] Only one configuration of these two settings can be used on a single neuron core"""
        self.VMaxExp = 9
        self.VMinExp = 0

        """Internal Constructor Methods"""
        self.compartments = [None] * len(CompartmentType)  # Initialize the list with None
        self.probes = [None] * len(CompartmentType)        # Initialize the list with None
        self.__core()
        self.__create_probes()


    def __core(self): 
        """Private Function to setup core components of half center"""
        ActivationGate_pt = nx.CompartmentPrototype(
            vThMant=self.ActGateVthMant,
            biasMant = self.ActGateBias,
            compartmentVoltageDecay=self.ActGateVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        SodiumIon_pt = nx.CompartmentPrototype(
            vThMant=self.NaIonVthMant,
            biasMant = self.NaIonBias,
            compartmentVoltageDecay=self.NaIonVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        SodiumChannel_pt = nx.CompartmentPrototype(
            vThMant=self.SCVthMant,
            compartmentVoltageDecay=self.SCVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        HalfCenter_pt = nx.CompartmentPrototype(
            vThMant=self.HCVthMant,
            compartmentVoltageDecay=self.HCVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        SpikeGenerator_pt = nx.CompartmentPrototype(
            vThMant = self.SGVthMant,
            compartmentVoltageDecay=self.SGVoltageDecay,
            thresholdBehavior = nx.COMPARTMENT_THRESHOLD_MODE.SPIKE_AND_RESET,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
        )

        SpikeGenerator_pt.addDendrite(HalfCenter_pt, nx.COMPARTMENT_JOIN_OPERATION.OR)
        HalfCenter_pt.addDendrite(SodiumChannel_pt, nx.COMPARTMENT_JOIN_OPERATION.ADD)
        SodiumChannel_pt.addDendrites(ActivationGate_pt, SodiumIon_pt, nx.COMPARTMENT_JOIN_OPERATION.PASS)

        
        neuronPrototype = nx.NeuronPrototype(SpikeGenerator_pt)
        HalfCenterTree = self.net.createNeuron(neuronPrototype)

        InhActGate_pt = nx.CompartmentPrototype(
            vThMant= self.InhActGateVthMant,
            compartmentVoltageDecay=self.InhActGateVoltageDecay,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        InhActGateCx = self.net.createCompartment(InhActGate_pt)
        
        SG_2_InhAct_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight=15)
        HalfCenterTree.soma.connect(InhActGateCx, SG_2_InhAct_conn_pt)

        InhAct_2_SodiumGate_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY, weight=-15)
        InhActGateCx.connect(HalfCenterTree.dendrites[0].dendrites[0].dendrites[0], InhAct_2_SodiumGate_conn_pt)

        
        # Store compartments in the list using the enum values as indices
        self.compartments[CompartmentType.SpikeGenerator.value] = HalfCenterTree.soma
        self.compartments[CompartmentType.HalfCenter.value] = HalfCenterTree.dendrites[0]
        self.compartments[CompartmentType.SodiumChannel.value] = HalfCenterTree.dendrites[0].dendrites[0]
        self.compartments[CompartmentType.ActivationGate.value] = HalfCenterTree.dendrites[0].dendrites[0].dendrites[0]
        self.compartments[CompartmentType.SodiumIon.value] = HalfCenterTree.dendrites[0].dendrites[0].dendrites[1]
        self.compartments[CompartmentType.ActGateInhibitor.value] = InhActGateCx
        

    def __create_probes(self):
        
        params = [nx.ProbeParameter.COMPARTMENT_CURRENT, 
                nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                nx.ProbeParameter.SPIKE]


        for i, compartment in enumerate(self.compartments): 
            self.probes[i] = compartment.probe(params, probeConditions=None)

   
    def plot_all_probes(self):
        fig = plt.figure(2002, figsize=(20, 15))
        k = 1
        for i, compartment_probes in enumerate(self.probes): 
            if compartment_probes is not None:  # Ensure compartment has probes
                for j, probe in enumerate(compartment_probes): 
                    plt.subplot(len(self.probes), 3, k)
                    probe.plot()
                    plt.title(f'{CompartmentType(i).name} - {ProbeType(j).name}')
                    k += 1

        plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
        plt.show()


####################################################END OF CLASS##########################################################
##########################################################################################################################
    
