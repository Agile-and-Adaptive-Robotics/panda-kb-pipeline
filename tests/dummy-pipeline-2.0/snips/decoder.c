#include <stdlib.h>
#include <string.h>
#include "decoder.h"
#include <time.h>
#include <unistd.h>

#define OUTPUT_DIM 2
#define NEURON_COUNT 4

int spikeCountCx = 0;
int channelID = -1;

volatile int output_spike_activity[NEURON_COUNT] = {0};
                  

int do_decoding(runState *s) {
    if (s->time_step==1){
        channelID = getChannelID("nxDecoder"); 
    }
    return 1;
}

void run_decoding(runState *s) {
    int time = s->time_step;
    //printf("Checking for spike\n");
    for(int ii = 0; ii < NEURON_COUNT; ii++){
        volatile int count = SPIKE_COUNT[(time)&3][0x20+ii];
        //printf("Neuron id %d, spike count %d, at time %d", ii, count, time);
        if(count > 0){
            output_spike_activity[ii]+= 1; 
            writeChannel(channelID, &ii, 1); // Outputs which neuron spiked
            //writeChannel(channelID, &s->time_step, 1); // Outputs the time step
            SPIKE_COUNT[(s->time_step-1)&3][0x20+ii] = 0;    // Lakemont spike counters need to be cleared after reading to prevent overflow 
        }
    }

    if(time == 49){
        for(int ii = 0; ii < NEURON_COUNT; ii++){
            printf("Neuron %d spiked %d times\n", ii, output_spike_activity[ii]);
        }    
    }
}
