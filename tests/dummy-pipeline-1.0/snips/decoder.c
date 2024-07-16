#include <stdlib.h>
#include <string.h>
#include "decoder.h"
#include <time.h>
#include <unistd.h>

#define OUTPUT_DIM 2

int spikeCountCx = 0;
int channelID = -1;
int data[4] = {1, 2, 3, 4};

int output_spike_activity[OUTPUT_DIM] = {0};
                  

int do_decoding(runState *s) {
    if (s->time_step==1){
        channelID = getChannelID("nxDecoder"); 
    }
    return 1;
}

void run_decoding(runState *s) {
    int time = s->time_step;
    for(int ii = 0; ii < OUTPUT_DIM; ii++){
        if(SPIKE_COUNT[(time)&3][0x20+ii] > 0){
            //printf("Spike output here\n");
            writeChannel(channelID, &ii, 1); // Outputs which neuron spiked
            //writeChannel(channelID, &s->time_step, 1); // Outputs the time step
            SPIKE_COUNT[(s->time_step-1)&3][0x20+ii] = 0;    // Lakemont spike counters need to be cleared after reading to prevent overflow 
        }
    }
    /*
    int time = s->time_step;
    for(int ii = 0; ii < OUTPUT_DIM; ii++){
        //output synapses start at 0x20, and increment in the order they are created
        output_spike_activity[ii] += SPIKE_COUNT[(time)&3][0x20+ii];
        //printf("Output synapse %d count %d \n", ii, output_spike_activity[ii]);
        if(output_spike_activity[ii] > 0){
            //printf("Output synapse %d spiked at time %d \n", ii, time);
            writeChannel(channelID, &ii, 1); // Outputs which neuron spiked
            writeChannel(channelID, &time, 1); // Outputs the time step
            output_spike_activity[ii] = 0; //always reset to zero after reading as well
        }
        SPIKE_COUNT[(s->time_step-1)&3][0x20+ii] = 0;    // Lakemont spike counters need to be cleared after reading to prevent overflow 
    }
    */
}
