from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
from nxsdk.graph.monitor.probes import *
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

import numpy as np
import sys
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

# Add the ../lib directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
from cpg.cpg import SodiumChannel



"""Global Params"""
NUMSTEPS = 200

if __name__ == "__main__":

    net = nx.NxNet()
    # get network class

    NaChannel1 = SodiumChannel(net)
    NaChannel1.inhibit_gate()

    net.run(NUMSTEPS)
    net.disconnect()

    NaChannel1.plot_probes()


    ######################END#########################
    ##################################################