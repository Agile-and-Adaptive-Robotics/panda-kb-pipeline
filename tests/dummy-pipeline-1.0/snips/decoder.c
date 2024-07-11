#include <stdlib.h>
#include <string.h>
#include "runmgmt.h"
#include <time.h>
#include <unistd.h>

int spikeCountCx = 0;
int channelID = -1;
int output_spike_activity[output_dim] = {0};
int output_dim = 2; 
                  

int do_run_mgmt(runState *s) {
        if (s->time_step==1){
            channelID = getChannelID("nxspkcntr");
        }
        return 1;
}

void run_mgmt(runState *s) {
    for(int ii = 0; ii < output_dim; ii++){
        //output synapses start at 0x20, and increment in the order they are created
        output_spike_activity[ii] += SPIKE_COUNT[(s->time_step-1)&3][0x20+ii];
        if(output_spike_activity[ii] > 0){
            printf("Output neuron %d spiked %d times\n", ii, output_spike_activity[ii]);
            writeChannel(channelID, &ii, 1); // Outputs which neuron spiked
            output_spike_activity[ii] = 0; //always reset to zero after reading as well
        }
        SPIKE_COUNT[(s->time_step-1)&3][0x20+ii] = 0;    // Lakemont spike counters need to be cleared after reading to prevent overflow 
    
    }
}
