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

# class CxType(Enum): 


class BurstingNeuron: 
    def __init__(self, 
                 net: nx.NxNet
                 ):
        self.bnVthMant=100
        self.bnCurrentDecay=4096
        self.bnVoltageDecay=int(1 / 1 * 2 ** 12)
        self.bnBias=0 #this will change during run time

        self.burstNeuron = self.__core()
        self.probes = self.__create_probes()

    def __core(self): 
        burstNeuron_pt = nx.CompartmentPrototype(
            vThMant=self.bnVthMant,
            compartmentVoltageDecay = self.bnVoltageDecay,
            compartmentCurrentDecay=self.bnCurrentDecay,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE

        burstNeuronCx = self.net.createCompartment(burstNeuron_pt)

        return burstNeuronCx
        )

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
    


        
        
        


