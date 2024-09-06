import os
import matplotlib as mpl
# Choose an interactive backend, like TkAgg or Qt5Agg
mpl.use('TkAgg')  # or 'TkAgg'
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx
from enum import Enum, IntEnum
import numpy as np 

haveDisplay = "DISPLAY" in os.environ

class ProbeType(IntEnum): 
    CURRENT = 0
    VOLTAGE = 1
    SPIKE = 2

class NeuronGroupType(Enum):
    Flexor = 0
    Extensor = 1

class ngCxType(Enum):
    Knee = 0
    Ankle = 1
    Hip = 3



# class CxType(Enum): 

class motorNeuronGroup:
    def __init__(self,
                 net: nx.NxNet,
                 type = None): 
        
        self.kneeVthMant=100
        self.kneeCurrentDecay=4096
        self.kneeVoltageDecay=int(1 / 1 * 2 ** 12)
        self.kneeBias = int(self.kneeVthMant * 2 ** 6)

        self.ankleVthMant=100
        self.ankleCurrentDecay=4096
        self.ankleVoltageDecay=int(1 / 1 * 2 ** 12)
        self.ankleBias = int(self.kneeVthMant * 2 ** 6)

        self.hipVthmant=100
        self.hipCurrentDecay=4096
        self.hipVoltageDecay=int(1 / 1 * 2 ** 12)
        self.hipBias = 0

        self.compartments = self.__core()

    def __core(self):
        kneeCx_pt = nx.CompartmentPrototype(
            vThMant=self.kneeVthMant,
            compartmentVoltageDecay = self.kneeVoltageDecay,
            compartmentCurrentDecay=self.kneeCurrentDecay,
            biasMant = self.kneeBias,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        kneeCx = self.net.createCompartment(kneeCx_pt)

        ankleCx_pt = nx.CompartmentPrototype(
            vThMant=self.ankleVthMant,
            compartmentVoltageDecay = self.ankleVoltageDecay,
            compartmentCurrentDecay=self.ankleCurrentDecay,
            biasMant = self.ankleBias,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        ankleCx = self.net.createCompartment(ankleCx_pt)

        hipCx_pt = nx.CompartmentPrototype(
            vThMant=self.hipVthmant,
            compartmentVoltageDecay = self.hipVoltageDecay,
            compartmentCurrentDecay=self.hipCurrentDecay,
            biasMant = self.hipBias,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        hipCx = self.net.createCompartment(hipCx_pt)

        knee_2_hip_connection_pt = nx.ConnectionPrototype(signMode =nx.SYNAPSE_SIGN_MODE.EXCITATORY,
                                                          weight = 0.5)
        kneeCx.connect(hipCx, prototype=knee_2_hip_connection_pt)

        return [kneeCx, ankleCx, hipCx]
    
    def __setup_probes(self):
        

#################################################################################
# #################################################################################
# Dont USE         
class BurstingNeuron: 
    def __init__(self, 
                 net: nx.NxNet):
        self.bnVthMant=100
        self.bnCurrentDecay=4096
        self.bnVoltageDecay=int(1 / 1 * 2 ** 12)
        self.bnBias = 0 #this will change during run time

        self.burstNeuron = self.__core()
        self.probes = self.__create_probes()

    def __core(self): 
        burstNeuron_pt = nx.CompartmentPrototype(
            vThMant=self.bnVthMant,
            compartmentVoltageDecay = self.bnVoltageDecay,
            compartmentCurrentDecay=self.bnCurrentDecay,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

        burstNeuronCx = self.net.createCompartment(burstNeuron_pt)

        return burstNeuronCx


    def __create_probes(self):
        params = [nx.ProbeParameter.COMPARTMENT_CURRENT, 
                nx.ProbeParameter.COMPARTMENT_VOLTAGE, 
                nx.ProbeParameter.SPIKE]
        
        probes = self.burstNeuron.probe(params, probeConditions = None)
        return probes
    
    def plot_probes(self, title=None):
        fig = plt.figure(2002, figsize=(20, 15))
        if title is not None:
            fig.suptitle(title, fontsize=16) 

        k = 1
        for probe in enumerate(self.probes):
            plt.subplot(len(self.probes), 3, k)
            probe.plot()
            k += 1
    
