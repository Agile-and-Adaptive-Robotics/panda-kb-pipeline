"""
@Author: Reece Wayt

@Date: 08/09/2024

@Description: 
    This is a helper utility for the loihi_math jupyter notebook found in the projects root directory. 
    Widgets are created for a simply way to calc and display values for the Loihi Board
"""
import ipywidgets as widgets
from IPython.display import display


class widget_app():
    def __init__(self,
                 vthMant = 1):
        

        self.vthmant = vthMant
        self.myWidgets = {}


        # INTERNAL METHODS
        self.myWidgets = self.__createWidgets()




    def frontEnd(self): 
        out = self.myWidgets['console']
        with out:
            display(
                self.myWidgets['vthMant_input'],
                self.myWidgets['vth_output'],
                self.myWidgets['calc_button']
            )

        display(out)
                
        


    def __voltageThreshold(self, vthMant):
        return vthMant * (2 ** 6)
 
    def __update_weight(self, change):
        vth = get_vth(change['new'])
        vth_output.value = f"Vth = {vth} mV"


    def __createWidgets(self):
        vthMant_input = widgets.IntSlider(value=1, 
                                          min=1, 
                                          max=100, 
                                          step=1, 
                                          description='VthMant:')
        vth_output = widgets.Text(value=f"Vth = {self.__voltageThreshold(vthMant_input.value)} mV", 
                                  description='Voltage:', disabled=True)
        calc_button = widgets.Button(
            description='Calculate Values',
            disabled=False,
            button_style='success', # 'success', 'info', 'warning', 'danger'
            tooltip='Description',
            icon='check'
        )

        console = widgets.Output(layout={'border': '1px solid black'})

        return {
            'vthMant_input' : vthMant_input,
            'vth_output' : vth_output,
            'calc_button' : calc_button,
            'console' : console
        }



    
