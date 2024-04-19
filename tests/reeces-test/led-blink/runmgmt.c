#include <stdlib.h>
#include <string.h>
#include "runmgmt.h"
#include <time.h>
#include <unistd.h>

int spikeCountCx = 0;
int channelID = -1;
int probe_id = 0; // Represents the id of the spike_probe, e.g.: If 5 probes are
                  // created this will be 0,1,2,3,4 corresponding to the spike probes
                  // in the order in which they were created

int do_run_mgmt(runState *s) {
        if (s->time_step==1){
            channelID = getChannelID("nxspkcntr");
        }
        return 1;
}

void run_mgmt(runState *s) {
     spikeCountCx += SPIKE_COUNT[(s->time_step-1)&3][0x20+probe_id]; // This macro is used to read the lakemont spike counter
     SPIKE_COUNT[(s->time_step-1)&3][0x20+probe_id] = 0;    // Lakemont spike counters need to be cleared after reading to prevent overflow  
     printf("Spike received %d...\n", spikeCountCx);
     printf("Time step, %d", s->time_step);
     writeChannel(channelID, &spikeCountCx, 1);             // Write the spike counter value back to the channel
}
