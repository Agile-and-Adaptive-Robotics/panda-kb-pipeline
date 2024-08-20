import matplotlib as mpl
mpl.use('TkAgg') 
import matplotlib.pyplot as plt
from nxsdk.utils.plotutils import plotRaster
import nxsdk.api.n2a as nx


"""Helper Function for Plotting Probes, see NxSDK documentation on working with Probes"""
def plot_probes(probes, title):
        fig = plt.figure(2002, figsize=(20, 15))
        k = 1

        for comp_name, probes in probes.items():
            for probe_type, probe in probes.items():
                plt.subplot(len(probes), 3, k)
                probe.plot()
                plt.title(f'{comp_name.capitalize()} {probe_type.capitalize()}', fontsize=15)
                print(f"[INFO] Plotting {comp_name} {probe_type}, of {probe}, {probe_type}")
                k += 1

        plt.tight_layout(pad=4.0, w_pad=4.0, h_pad=4.0)
        file_name = f"{title}.png"
        print(f"[INFO] Saving plot to {file_name}")
        fig.savefig(file_name)


