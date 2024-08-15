import matplotlib as mpl
# Choose an interactive backend, like TkAgg or Qt5Agg
mpl.use('TkAgg')  # or 'TkAgg'
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx
import numpy as np 

class Inhibitor: 
    def __init__(self, 
                 net: nx.Net,
                 inhVMaxExp = 9,
                 inhVthMant = 7,
                 inhVoltageDecay = int(1 / 3 * 2 * 12),
                 debug = False
                 ):
        self.net = net
        self.inhVMaxExp = inhVMaxExp
        self.inhVthMant = inhVthMant
        self.inhVoltageDecay = inhVoltageDecay
        self.debug = debug

        self.compartment = self.__core()
        self.probes = {}
        

    def __core(self):
        inhibitor_pt = nx.CompartmentPrototype(
            vMaxExp = self.inhinhibitor_cx = self.net.createCompartment(inhibitor_pt)thMant,
            compartmentVoltageDecay=self.inhVoltageDecay,
            thresholdBehavior=nx.SPIKE_AND_RESET,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

        inhibitorCx = self.net.createCompartment(inhibitor_pt)
        return inhibitorCx
    

    @property
    def getCompartment(self): 
        return self.compartment 
