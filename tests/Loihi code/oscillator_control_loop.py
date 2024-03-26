"""
Loihi end of Arduino-Loihi oscillator

Adpated from https://github.com/michaelgzt/loihi-control-loop-demo/blob/main/loihi_control_loop.py
and INTEL NxCore Tutorial 24 

Author: Flora Huang

Last Updated: 7/24/2023
"""

# -----------------------------------------------------------------------------
# Import modules
# -----------------------------------------------------------------------------

import sys
sys.path.append('./')
from oscillator_network import LoihiNetwork
from nxsdk.graph.channel import Channel
import rospy
from std_msgs.msg import Int8MultiArray

# -----------------------------------------------------------------------------
# Initialize variables
# -----------------------------------------------------------------------------

# ROS Topics
SUB_ROS_TOPIC = "to_loihi"
PUB_ROS_TOPIC = "to_arduino"

# Neural network information
LAYER_DIM = 2

# Loihi simulation parameters
SNIP_DIR = './snip_window_regular'
SIM_STEPS = 102
TOTAL_STEPS = 1000

# Runtime variables
end_of_run = False
num_steps = 0
published_value = Int8MultiArray()

# Lists of input and output spikes
spike_input = []
spike_output = []


class ROSProcess():
    """Manages subscribing and publishing to ROS topics"""
    def __init__(self, sub_topic: str, pub_topic: str, input_channel: Channel, feedback_channel: Channel):
        # Channels for communication with SNIPs
        self.input_channel = input_channel
        self.feedback_channel = feedback_channel
        
        # Subscriber and publisher
        rospy.Subscriber(
            name=sub_topic, data_class=Int8MultiArray, callback=self.callback, queue_size=1000)
        self.publisher = rospy.Publisher(
            name=pub_topic, data_class=Int8MultiArray, queue_size=1000, latch=False)
        
    def callback(self, data):
        """This function is called whenever data is received on subscriber"""
        global num_steps
        global end_of_run
        
        if num_steps < TOTAL_STEPS:
            # Write data to encoder channel to inject spikes
            input_spikes = data.data
            self.input_channel.write(LAYER_DIM, input_spikes)
            spike_input.append(input_spikes)
            
            # Read output spikes from decoder channel
            output_spikes = self.feedback_channel.read(LAYER_DIM)
            published_value.data = output_spikes
            self.publisher.publish(published_value)
            spike_output.append(tuple(output_spikes))
            
            num_steps += 1
        else:
            end_of_run = True
            rospy.loginfo("End of run.")
            

def run_loihi_network(layer_dim, core_lists, snip_dir, sim_steps):
    """
    Setup neural network and begin Loihi/ROS processes
    Args:
        layer_dim (int): number of neurons per layer
        core_lists (list): cores in each layer
        snip_dir (str): SNIP directory
        sim_steps (int): steps per simultaion window
    """
    # Set up SNN and communication channels
    loihi_snn = LoihiNetwork(layer_dim, core_lists)
    board, encoder_channel, decoder_channel = loihi_snn.setup_loihi_snn(layer_dim, layer_dim, snip_dir)
 
    # Start board
    board.start()
    
    # Run asynchronously (non-blocking)
    board.run(sim_steps * TOTAL_STEPS, aSync=True)
    
    # Start the subscriber and publisher
    rosProcess = ROSProcess(SUB_ROS_TOPIC, PUB_ROS_TOPIC, encoder_channel, decoder_channel)

    # Spin till end of run
    while end_of_run is False:
        rospy.spin()
        
    # Cleanup 
    try:
        rosProcess.cleanup()
        board.finishRun()
        board.disconnect()
    except BaseException:
        # Ignore any exceptions
        pass


if __name__ == "__main__":
    # Initialize the ROS Node so that publishers and subscribers can be created
    rospy.init_node('pubsub', anonymous=True)
    
    # Initialize core lists
    core_layer = [0 for i in range(LAYER_DIM)]
    core_lists = [core_layer for i in range(LoihiNetwork.get_num_layers())]
    
    # Initialize and run Loihi network
    run_loihi_network(LAYER_DIM, core_lists, SNIP_DIR, SIM_STEPS)