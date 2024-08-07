from nxsdk.utils.plotutils import plotRaster
from nxsdk.graph.channel import Channel
from nxsdk.graph.monitor.probes import *
import nxsdk.api.n2a as nx
from nxsdk.arch.n2a.n2board import N2Board
from nxsdk.graph.processes.phase_enums import Phase

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib as mpl

haveDisplay = "DISPLAY" in os.environ
if not haveDisplay:
    mpl.use('Agg')

def plot_probes(u_probes, v_probes, s_probes, compartment_names):
        fig = plt.figure(2002, figsize=(35, 25))
        k = 1
        for i in range(len(u_probes)):
            plt.subplot(len(u_probes), 3, k)
            u_probes[i].plot()
            plt.title(f'{compartment_names[i]} Current')
            k += 1

            plt.subplot(len(v_probes), 3, k)
            v_probes[i].plot()
            plt.title(f'{compartment_names[i]} Voltage')
            k += 1

            plt.subplot(len(s_probes), 3, k)
            s_probes[i].plot()
            plt.title(f'{compartment_names[i]} Spikes')
            k += 1

        plt.tight_layout(pad=3.0, w_pad=3.0, h_pad=3.0)
        if haveDisplay:
            plt.show()
        else:
            fileName = "probes_plot.png"
            print(f"No display available. Saving plot to {fileName}")
            fig.savefig(fileName)


srVthMant = 100
srCurrentDecay = 800
srVoltageDecay = 800
amVthMant = 1562
amCurrentDecay = 400
amVoltageDecay = 400
ciVthMant = 100
ciCurrentDecay = int(1 / 10 * 2 ** 12)
ciVoltageDecay = int(1 / 100 * 2 ** 12)
sgVthMant = 5000
sgCurrentDecay = int(1 / 10 * 2 ** 12)
sgVoltageDecay = int(1 / 100 * 2 ** 12)
inVthMant = 10000
inCurrentDecay = 0
inVoltageDecay = 0


if __name__ == "__main__":

    net = nx.NxNet()
    # get network class

    # Input Compartment -> transforms input current to voltage (Non-spiking)
    spike_receiver_pt = nx.CompartmentPrototype(
        vThMant=srVthMant,
        compartmentVoltageDecay=srVoltageDecay,
        compartmentCurrentDecay=srCurrentDecay,
        thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
        functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
    )
    # Astrocyte Modulator -> modulates input current by integrating the input current (Non-spiking)
    astrocyte_modulator_pt = nx.CompartmentPrototype(
        vThMant=amVthMant,
        compartmentVoltageDecay=amVoltageDecay,
        compartmentCurrentDecay=amCurrentDecay,
        thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH_TO_PARENT,
        functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
    )
    # Conditional Integrator -> integrates the voltage from sr only if AM's threshold is met (Non-spiking)
    conditional_integrator_pt = nx.CompartmentPrototype(
        vThMant=ciVthMant,
        compartmentVoltageDecay=ciVoltageDecay,
        compartmentCurrentDecay=ciCurrentDecay,
        thresholdBehavior=nx.COMPARTMENT_THRESHOLD_MODE.NO_SPIKE_AND_PASS_V_LG_VTH
        functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
    )

    #Spiking Compartment -> Generates burst of spikes whenever CI is above threshold
    spike_generator_pt = nx.CompartmentPrototype(
        vThMant=sgVthMant,
        compartmentVoltageDecay=sgVoltageDecay,
        compartmentCurrentDecay=sgCurrentDecay,
        functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
    )   

    #Inhibitor Compartment -> resets the conditional integrator to resting state after {x} spikes (Can be adjusted)
    inhibitor_pt = nx.CompartmentPrototype(
        vThMant=inVthMant,
        compartmentVoltageDecay=inVoltageDecay,
        compartmentCurrentDecay=inCurrentDecay,
        functionalState=nx.COMPARTMENT_FUNCTIONAL_STATE.IDLE
    )

    conditional_integrator_pt.addDendrites(astrocyte_modulator_pt, spike_receiver_pt, nx.COMPARTMENT_JOIN_OPERATION.PASS)


    # Creates multi compartment neuron
    somaProto = nx.NeuronPrototype(conditional_integrator_pt)
    neuron = net.createNeuron(somaProto)

    sensor_generator = net.createSpikeGenProcess(numPorts=1)
    sensor_conn_pt = nx.ConnectionPrototype(signMode=nx.SYNAPSE_SIGN_MODE.EXCITATORY, weight=100)
    sensor_generator.connect(neuron.dendrites[0], prototype=sensor_conn_pt)
    sensor_generator.connect(neuron.dendrites[1], prototype=sensor_conn_pt)


    sensor_generator.addSpikes(0, [1, 2, 3, 4, 5, 6])

    probe_parameters = [nx.ProbeParameter.COMPARTMENT_CURRENT,
                        nx.ProbeParameter.COMPARTMENT_VOLTAGE,
                        nx.ProbeParameter.SPIKE]

    compartments = []
    soma = neuron.soma
    ast_m = neuron.dendrites[0]
    sr = neuron.dendrites[1]
    compartments.append(soma)
    compartments.append(ast_m)
    compartments.append(sr)

    print(compartments[0].compartmentCurrentDecay)
    print(compartments[0].compartmentCurrentTimeConstant)
    print(compartments[0].compartmentVoltageDecay)
    print(compartments[0].compartmentVoltageTimeConstant)

    probes = []
    for compartment in compartments:
        probes.append(compartment.probe(probe_parameters))

    u_probes, v_probes, s_probes = zip(*probes)

    compartment_names = ["Conditional Integrator", "Astrocyte Modulator", "Spike Receiver"]

    net.run(200)
    net.disconnect()

    plot_probes(u_probes, v_probes, s_probes, compartment_names)
