"""
@Author: Reece Wayt

@Date: 08/09/2024

@Description: 
    This is a helper utility for the loihi_math jupyter notebook found in the projects root directory. 
    Widgets are created for a simply way to calc and display values for the Loihi Board
"""
import numpy as np
import ipywidgets as widgets
from IPython.display import display

class WidgetApplication:
    def __init__(self):
        self.vthMant_input = widgets.IntSlider(value=1, min=1, max=100, step=1, description='VthMant:')
        self.vth_output = widgets.Text(value=f"Vth = {self.get_vth(self.vthMant_input.value)} mV", description='Voltage:', disabled=True)
        self.vthMant_input.observe(self.update_vth, names='value')

        self.weight_input = widgets.IntSlider(value=0, min=-256, max=256, step=1, description='Weight:')
        self.weight_output = widgets.Text(value=f"Weight = {self.calculate_actual_weight(self.weight_input.value, num_weight_bits=8, wgt_exp=1, is_mixed=0)}", 
                                          description='Weight Component:', disabled=True)
        self.weight_input.observe(self.update_weight, names='value')

        self.header = widgets.HTML(value="<b> Calculate Loihi Values and Tune Parameters </b>")
        self.calc_button = widgets.Button(description='Calculate Values', disabled=False, button_style='success', tooltip='Description', icon='check')
        self.console = widgets.Output(layout={'border': '1px solid black'})

        self.calc_button.on_click(self.on_calc_button_clicked)

    def display(self):
        display(self.header)
        display(self.vthMant_input, self.vth_output)
        display(self.weight_input, self.weight_output)
        display(self.calc_button)
        display(self.console) 


    def get_vth(self, vthMant):
        return vthMant * (2 ** 6)

    def update_vth(self, change):
        vth = self.get_vth(change['new'])
        self.vth_output.value = f"Vth = {vth} mV"

    def calculate_actual_weight(self, weight, num_weight_bits, wgt_exp, is_mixed):
        num_lsb_bits = 8 - (num_weight_bits - is_mixed)
        act_weight = (weight >> num_lsb_bits) << num_lsb_bits
        weight_component = act_weight * (2 ** (6 + wgt_exp))
        return weight_component

    def update_weight(self, change):
        weight_value = change['new']
        act_weight = self.calculate_actual_weight(weight_value, num_weight_bits=8, wgt_exp=1, is_mixed=0)
        self.weight_output.value = f"Weight = {act_weight}"

    def on_calc_button_clicked(self, b):
        with self.console:
            print("Calculation done!")  # Just as an example action

    
