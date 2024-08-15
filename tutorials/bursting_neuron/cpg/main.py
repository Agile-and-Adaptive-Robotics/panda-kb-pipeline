from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
from nxsdk.graph.monitor.probes import *
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

from bursting_neuron import BurstingNeuron

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

"""Global Params"""
NUMSTEPS = 200

if __name__ == "__main__":

    net = nx.NxNet()
    # get network class

    burst_neuron1 = BurstingNeuron(net, debug=False, num_steps=NUMSTEPS)

    burst_neuron1.add_spike_train()

    net.run(NUMSTEPS)
    net.disconnect()

    burst_neuron1.plot_probes()


    ######################END#########################
    ##################################################