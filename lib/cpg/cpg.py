import nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx 
import numpy as np


from SodiumChannelBase import SodiumChannel 


class CentralPatternGenerator: 
    def __init__(self,
                 net : nx.NxNet,
                 leftHCVMaxExp = 9,
                 leftHCVMinExp = 9,
                 leftHCVthMant = 7,
                 leftHCVoltageDecay = int(1 /10 * 2 ** 12),
                 rightHCVMaxExp = 9,
                 rightHCVMinExp = 9,
                 rightHCVthMant = 7,
                 rightHCVoltageDecay = int(1 /10 * 2 ** 12),    
                 debug = False            
                 ):
        self.net = net
        self.leftHCVMaxExp = leftHCVMaxExp
        self.leftHCVMinExp = leftHCVMinExp
        self.leftHCVthMant = leftHCVthMant
        self.leftHCVoltageDecay = leftHCVoltageDecay
        self.rightHCVMaxExp = rightHCVMaxExp
        self.rightHCVMinExp = rightHCVMinExp
        self.rightHCVthMant = rightHCVthMant
        self.rightHCVoltageDecay = rightHCVoltageDecay
        self.debug = debug

        """Internal Constructor Method"""
        self.__core()



    def __core(self):
        """"
        Private constructor of internal compartment structure
            Depends on SodiumChannelBase.py, FIXME: create better documentation

        """
        leftSC = SodiumChannel() #Left sodium channel
        rightSC= SodiumChannel() #Right sodium channel

        leftHalfCenter = nx.CompartmentPrototype(
            vMaxExp = self.leftHCVMaxExp,
            vMinExp = self.leftHCVMinExp,
            vThMant = self.leftHCVthMant,
            compartmentVoltageDecay = self.leftHCVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )
        rightHalfCenter = nx.CompartmentPrototype(
            vMaxExp = self.rightHCVMaxExp,
            vMinExp = self.rightHCVMinExp,
            vThMant = self.rightHCVthMant,
            compartmentVoltageDecay = self.rightHCVoltageDecay,
            thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
            functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
        )

#FIXME: 
"""Start here next week, sodium channel is create, finish inhibitor base methods then continue with cpg.py"""

