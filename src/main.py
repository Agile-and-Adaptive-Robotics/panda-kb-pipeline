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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from lib import CentralPatternGenerator

"""Global Params"""
NUMSTEPS = 100

if __name__ == "__main__":

    net = nx.NxNet()
    my_cpg = CentralPatternGenerator(net)
    #my_cpg.stimulate_interneuron()

    net.run(NUMSTEPS)
    net.disconnect()

    my_cpg.plot_all_probes()
    my_cpg.plot_half_center_together()


    ######################END#########################
    ##################################################