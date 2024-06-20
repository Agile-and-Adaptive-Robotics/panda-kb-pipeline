#include <stdlib.h>
#include <string.h>
#include "runmgmt.h"
#include <time.h>
#include <unistd.h>

/*
    Run management functions for exiting the simulation after a certain number of steps
*/

#define NUMSTEPS 500

int spikeCountCx = 0;
int channelID = -1;
int probe_id = 0; // Represents the id of the spike_probe, e.g.: If 5 probes are
                  // created this will be 0,1,2,3,4 corresponding to the spike probes
                  // in the order in which they were created

int do_run_mgmt(runState *s) {
        if (s->time_step==1){
            channelID = getChannelID("nxRecvChannel");
            return 0;
        }
        if(channelID == -1){
            return 0;
        }
        if(s->time_step == NUMSTEPS){
            return 1;
        }
    return 0;    
}

void run_mgmt(runState *s) {
    int time = s->time_step;
    printf("Time: %d\n", time);
    writeChannel(channelID, &time, 1);
}
