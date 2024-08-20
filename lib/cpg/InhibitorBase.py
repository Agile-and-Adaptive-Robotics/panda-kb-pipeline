import matplotlib as mpl
# Choose an interactive backend, like TkAgg or Qt5Agg
mpl.use('TkAgg')  # or 'TkAgg'
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx
from . import plothelper
import numpy as np 

class Inhibitor: 
    def __init__(self, 
                 net: nx.NxNet,
                 inhVMaxExp = 9,
                 inhVthMant = 7,
                 inhVoltageDecay = int(1 / 3 * 2 * 12),
                 debug = False
                 ):
        self.net = net
        self.inhVMaxExp = inhVMaxExp
        self.inhVthMant = inhVthMant
        self.inhVoltageDecay = 0 #FIXME: Setting to zero for now
        self.debug = debug

        self.compartments = self.__core()
        self.probes = {}
        self.__create_probes()
        

    def __core(self):
        inhibitor_pt = nx.CompartmentPrototype(
            #vMaxExp = self.inhVMaxExp,
            vThMant = self.inhVthMant,
            compartmentVoltageDecay=self.inhVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.SPIKE_AND_RESET,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

        inhibitorCx = self.net.createCompartment(inhibitor_pt)
        return {'Inhibitor' : inhibitorCx}
    
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
    

    @property
    def getInhibitor(self): 
        return self.compartments['Inhibitor'] 
    
    @property
    def get_probes(self):
        return self.probes
    
