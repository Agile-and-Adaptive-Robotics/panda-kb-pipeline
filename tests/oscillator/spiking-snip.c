#include <stdlib.h>
#include <string.h>
#include "nxsdk.h"
#include "spiking-snip.h"

static int time = 0;

int do_spiking(runState *s) {
    return 1;
}

void run_spiking(runState *s) {
     // convert logical chip id and logical axon id to physical ids
    int channelID = getChannelID("nxRecvChannel");
    time = s->time_step;
    
    //TODO: Implement the spiking process later

    writeChannel(channelID, &time, 1);

}