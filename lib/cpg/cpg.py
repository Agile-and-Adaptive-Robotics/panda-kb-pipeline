##########################################################################################################################
# @File Name: cpg.py
# @Description: This file contains the implementation of the Central Pattern Generator (CPG) using the Loihi
#             neuromorphic chip. [IMPORTANT] - The cpg library is simply an architectural idea that is suited for the loihi
#             there is still a lot of optimization and numberical work that needs to be done to make this library functional
#
# @Author: Reece Wayt
#
##########################################################################################################################
##########################################################################################################################


from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx 
from .SodiumChannelBase import SodiumChannel 
from .InhibitorBase import Inhibitor
import matplotlib.pyplot as plt
import matplotlib as mpl
mpl.use('TkAgg')


from enum import IntEnum, Enum

"""
Enum Classes are used generally for the following reasons: 
 - To index into a list of objects (i.e. compartments & probes objects)
 - To the above note, lists are organized inheritely by the order of the enum values
 - To make the code more readable and maintainable
 - To avoid using magic numbers in the code

"""
class ProbeType(IntEnum):
    CURRENT = 0
    VOLTAGE = 1
    SPIKE = 2

class hcCxType(Enum):
    SpikeGenerator = 0
    HalfCenter = 1
    SodiumChannel = 2
    ActivationGate = 3
    SodiumIon = 4
    #Add more as needed

class cpgCxType(Enum):
    ExtensionInterneuron = 0 
    FlexionInterneuron = 1
    SwitchGate = 2


class CentralPatternGenerator:
    """
    Class to create a Central Pattern Generator (CPG) using two coupled half centers. 
    """
    def __init__(self, 
                 net: nx.NxNet,
                 debug = False
                 ):
        self.net = net
        self.debug = debug

        self.intIntVth = 7
        self.intIntVoltageDecay = int(1 / 10 * 2 ** 12)

        self.switchGateVth = 7
        self.switchGateVoltageDecay = int(1 / 10 * 2 ** 12)

        self.vMaxExp = 9

        self.ExtHC = HalfCenter(self.net, extensor=True)
        self.FlexHC = HalfCenter(self.net)

        self.compartments = [None] * len(cpgCxType)  
        self.probes = [None] * len(cpgCxType)        

        self.__connect_half_centers()
        self.__create_probes()

    def __connect_half_centers(self):
        """
        Private method to create reciprocal inhibitory connections between the two half centers.
        """
        IntNeuron_pt = nx.CompartmentPrototype(
            vThMant = self.intIntVth,
            compartmentVoltageDecay=self.intIntVoltageDecay,
            vMaxExp=self.vMaxExp,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        IntNeuronGrp = self.net.createCompartmentGroup(size=2, prototype=IntNeuron_pt)
        self.compartments[cpgCxType.ExtensionInterneuron.value] = IntNeuronGrp[0]
        self.compartments[cpgCxType.FlexionInterneuron.value] = IntNeuronGrp[1]

        excitatory_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight=5)
        halfcenter_link_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY, weight=-3)

        self.ExtHC.spikegen_cx.connect(self.ExtensionInterneuron, excitatory_conn_pt)
        self.ExtensionInterneuron.connect(self.FlexHC.halfcenter_cx, halfcenter_link_conn_pt)

        self.FlexHC.spikegen_cx.connect(self.FlexionInterneuron, excitatory_conn_pt)
        self.FlexionInterneuron.connect(self.ExtHC.halfcenter_cx, halfcenter_link_conn_pt)

        SwitchGate_pt = nx.CompartmentPrototype(
            vThMant= self.switchGateVth,
            compartmentVoltageDecay=self.switchGateVoltageDecay,
            vMaxExp=self.vMaxExp,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

        self.compartments[cpgCxType.SwitchGate.value] = self.net.createCompartment(SwitchGate_pt)
        switchGate_excitatory_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight=12)
        switchGate_inhibitory_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.INHIBITORY, weight=-9)

        self.ExtHC.spikegen_cx.connect(self.SwitchGate, switchGate_excitatory_conn_pt)
        self.SwitchGate.connect(self.ExtHC.activationGate, switchGate_inhibitory_conn_pt)
        self.SwitchGate.connect(self.FlexHC.activationGate, switchGate_excitatory_conn_pt)

          
        
    def __create_probes(self):
        params = [nx.ProbeParameter.COMPARTMENT_CURRENT, 
                nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                nx.ProbeParameter.SPIKE]

        for i, compartment in enumerate(self.compartments): 
            self.probes[i] = compartment.probe(params, probeConditions=None)

    def plot_cpg_probes(self, title=None):
        fig = plt.figure(2002, figsize=(20, 15))
        if title is not None:
            fig.suptitle(title, fontsize=16)

        k = 1
        for i, compartment_probes in enumerate(self.probes): 
            if compartment_probes is not None:  # Ensure compartment has probes
                for j, probe in enumerate(compartment_probes): 
                    plt.subplot(len(self.probes), 3, k)
                    probe.plot()
                    plt.title(f'{cpgCxType(i).name} - {ProbeType(j).name}')
                    k += 1

        plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
        filename = f"{title}.png"
        print(f"[INFO] Save plot >>> {filename}")

        plt.savefig(filename)

    def plot_all_probes(self):
        self.plot_cpg_probes(title = 'InterNeuron Connections')
        self.ExtHC.plot_probes(title = 'Extension Half Center Cxs')
        self.FlexHC.plot_probes(title = 'Flexion Half Center Cxs')

    def plot_half_center_together(self):
        fig, ax = plt.subplots(figsize=(18,10))
        self.ExtHC.halfcenter_volt_probe.plot()
        self.FlexHC.halfcenter_volt_probe.plot()

        ax.legend(['ExtHC', 'FlexHC'])
        plt.show()
    """FIXME:
    def stimulate_interneuron(self):
        
        #Stimulate the interneuron on the specified side
        
        if == 'extension':
            nxSpikeGen = self.net.createSpikeGenProcess(numPorts=1)
            sGenConn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight = 15)
            nxSpikeGen.connect(self.ExtensionInterneuron, prototype=sGenConn_pt)
            nxSpikeGen.addSpikes([0], [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]])
        else:
            print("Not implemented yet...")
    """
    @property
    def ExtensionInterneuron(self):
        return self.compartments[cpgCxType.ExtensionInterneuron.value]

    @property
    def FlexionInterneuron(self):
        return self.compartments[cpgCxType.FlexionInterneuron.value]
    
    @property
    def SwitchGate(self):
        return self.compartments[cpgCxType.SwitchGate.value]


##################################################################################################################
################################CLASS DEFINITION#################################################################

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
                 debug = False,
                 extensor = False
                 ):
        self.net = net
        self.debug = debug
        """
        Spike Generator (SG):
        Functions as the communicate to other neuron trees, or compartments that are external to the neuron tree define in the __core() method
        """   
        self.SGVthMant = 7
        self.SGVoltageDecay = int(1 / 10 * 2 ** 12) # 1/t of the voltage is decayed every time step, it will take t steps to decay to 0
        self.SGCurrentDecay = 4096
        """
        Half Center (HC): 
        Main compartment of the half center oscillator as seen in the paper: 
         - "Design process and tools for dynamic neuromechanical models and robot controllers"
        """
        self.HCVthMant = 7
        self.HCBias = int((self.HCVthMant * 2 ** 6) - 100)
        self.HCCurrentDecay = 4096
        self.HCVoltageDecay = int(1 / 10 * 2 ** 12)
        """
        Sodium Channel (SC): 
        Used to model a persistent sodium channel, sodium Ions are added to the 
        half center compartment when the activation gate is open. 
        """
        self.SCVthMant = 7
        self.SCVoltageDecay = int(1 / 1 * 2 ** 12)
        self.SCCurrentDecay = 4096
        """
        Activation Gate (ActGate):
        Basic compartment that allows for the opening and closing of the sodium channel
        """
        self.extensor = extensor
        self.ActGateVthMant = 7
        if extensor == True: 
            self.ActGateBias = int((self.ActGateVthMant / 10) * 2 **6)
            self.ActGateCurrentDecay = 4096
            self.ActGateVoltageDecay = int(1 / 100 * 2 ** 12)

        else:
            self.ActGateBias = 0
            self.ActGateCurrentDecay = 4096
            self.ActGateVoltageDecay = int(1 / 10 * 2 ** 12)

        """
        Sodium Ion (NaIon):
        Used to model the sodium ions that are responsible for the depolarization of the half center compartment
        V_Na+ = NaIonVthMant * 2 ^ 6
        """
        self.NaIonVthMant = 7
        self.NaIonBias = int(self.NaIonVthMant * 2 ** 6)
        self.NaIonVoltageDecay = int(1 / 1 * 2 ** 12)
        self.NaIonCurrentDecay = 4096
        """
        Inhibitory Activation Gate (InhActGate):
        Used to model the inhibition of the activation gate when the half center compartment is depolarized,
        this compartment is necessary, as the binary tree structure of the neuron model does not allow for
        direct connections between the activation gate and the sodium channel
        """
        self.InhActGateVthMant = 7
        self.InhActGateVoltageDecay = int(1 / 10 * 2 ** 12)

        """
        [IMPORTANT] 
        Only one configuration of these two settings can be used on a single neuron core 
        because these registers are shared by multiple compartments
        """
        self.VMaxExp = 9
        self.VMinExp = 0

        """Internal Constructor Methods"""
        self.compartments = [None] * len(hcCxType)  # Initialize the list with None
        self.probes = [None] * len(hcCxType)        # Initialize the list with None
        self.__core()
        self.__create_probes()


    def __core(self): 
        """Private Function to setup core components of half center"""
        ActivationGate_pt = nx.CompartmentPrototype(
            vThMant=self.ActGateVthMant,
            biasMant = self.ActGateBias,
            compartmentVoltageDecay=self.ActGateVoltageDecay,
            vMaxExp = self.VMaxExp,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        SodiumIon_pt = nx.CompartmentPrototype(
            vThMant=self.NaIonVthMant,
            biasMant = self.NaIonBias,
            compartmentVoltageDecay=self.NaIonVoltageDecay,
            vMaxExp = self.VMaxExp,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        SodiumChannel_pt = nx.CompartmentPrototype(
            vThMant=self.SCVthMant,
            compartmentVoltageDecay=self.SCVoltageDecay,
            vMaxExp = self.VMaxExp,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        HalfCenter_pt = nx.CompartmentPrototype(
            vThMant=self.HCVthMant,
            compartmentVoltageDecay=self.HCVoltageDecay,
            vMaxExp= self.VMaxExp,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
        )
        SpikeGenerator_pt = nx.CompartmentPrototype(
            vThMant = self.SGVthMant,
            compartmentVoltageDecay=self.SGVoltageDecay,
            vMaxExp = self.VMaxExp,
            thresholdBehavior = nx.COMPARTMENT_THRESHOLD_MODE.SPIKE_AND_RESET,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE,
        )

        SpikeGenerator_pt.addDendrite(HalfCenter_pt, nx.COMPARTMENT_JOIN_OPERATION.OR)
        HalfCenter_pt.addDendrite(SodiumChannel_pt, nx.COMPARTMENT_JOIN_OPERATION.ADD)
        SodiumChannel_pt.addDendrites(ActivationGate_pt, SodiumIon_pt, nx.COMPARTMENT_JOIN_OPERATION.PASS)

        
        neuronPrototype = nx.NeuronPrototype(SpikeGenerator_pt)
        HalfCenterTree = self.net.createNeuron(neuronPrototype)


        
        # Store compartments in the list using the enum values as indices
        self.compartments[hcCxType.SpikeGenerator.value] = HalfCenterTree.soma
        self.compartments[hcCxType.HalfCenter.value] = HalfCenterTree.dendrites[0]
        self.compartments[hcCxType.SodiumChannel.value] = HalfCenterTree.dendrites[0].dendrites[0]
        self.compartments[hcCxType.ActivationGate.value] = HalfCenterTree.dendrites[0].dendrites[0].dendrites[0]
        self.compartments[hcCxType.SodiumIon.value] = HalfCenterTree.dendrites[0].dendrites[0].dendrites[1]

        

    def __create_probes(self):
        params = [nx.ProbeParameter.COMPARTMENT_CURRENT, 
                nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                nx.ProbeParameter.SPIKE]

        for i, compartment in enumerate(self.compartments): 
            self.probes[i] = compartment.probe(params, probeConditions=None)

   
    def plot_probes(self, title=None):
        fig = plt.figure(2002, figsize=(20, 15))
        if title is not None:
            fig.suptitle(title, fontsize=16)

        k = 1
        for i, compartment_probes in enumerate(self.probes): 
            if compartment_probes is not None:  # Ensure compartment has probes
                for j, probe in enumerate(compartment_probes): 
                    plt.subplot(len(self.probes), 3, k)
                    probe.plot()
                    plt.title(f'{hcCxType(i).name} - {ProbeType(j).name}')
                    k += 1

        plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
        
        filename = f"{title}.png"
        print(f"[INFO] Save plot >>> {filename}")

        plt.savefig(filename)

    
    @property
    def halfcenter_cx(self):
        return self.compartments[hcCxType.HalfCenter.value]

    @property
    def spikegen_cx(self):
        return self.compartments[hcCxType.SpikeGenerator.value]
    
    @property
    def activationGate(self):
        return self.compartments[hcCxType.ActivationGate.value]
    
    @property
    def halfcenter_volt_probe(self):
        return self.probes[hcCxType.HalfCenter.value][ProbeType.VOLTAGE]
    
    

    
