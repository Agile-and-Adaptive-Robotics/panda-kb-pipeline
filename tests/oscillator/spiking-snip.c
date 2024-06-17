#include <stdlib.h>
#include <string.h>
#include "nxsdk.h"
#include "spiking-snip.h"

static int time=0;
static int chip;
static int core;
static int axon;

int do_spiking(runState *s) {
    return 1;
}

void run_spiking(runState *s) {
     // convert logical chip id and logical axon id to physical ids
    int channelID = getChannelID("spikingProcess");
    time = s->time_step;
    /*
    readChannel(channelID, &chip, 1);
    readChannel(channelID, &core, 1);
    readChannel(channelID, &axon, 1);
    uint16_t  axonId = 1<<14 | (axon & 0x3FFF);
    ChipId    chipId = nx_nth_chipid(chip);
    printf("Sending Spike at Time : %d chip %d core %d axon %d\n",s->time_step,chip,core,axon);

    // send the spike
    nx_send_remote_event(time, chipId, (CoreId){.id=core}, axonId);
    
    */
    printf("Current timestep %d...\n", time);
}