/*
    * encoder.c
    *
    *  Created on: 2019-01-21
    * Code is based on NxSDK tutorial example 21_multilmp_snips and the oculomotor-head-controller from combra lab
    * - https://github.com/combra-lab/spiking-oculomotor-head-control
*/

#include <stdlib.h>
#include <string.h>
#include "nxsdk.h"
#include "encoder.h"

static int time= 0; // Global time variable
static int chip = 0;
static int core = 0; 
static int axon;
static int channelId = -1; // Encoder channel ID

int do_encoding(runState *s){
    if((s->time_step >= 0) & (channelId = -1)){
        // Get the channel ID of the encoder
        channelId = getChannelID("nxEncoder");
    }
    if(channelId == -1){
        printf("Error: Could not find encoder channel\n");
        return 0;
    }
    return 1;  
}

void run_encoding(runState *s){
    time = s->time_step;
    readChannel(channelId, &axon, 1);
    uint16_t axonId = 1 << 14 | (axon & 0x3FFF);
    ChipId chipId = nx_nth_chipid(chip);
    //printf("Sending spike at time : %d, axonId %d\n", time, axonId);

    //send spike
    nx_send_remote_event(time, chipId, (CoreId){.id=4+core}, axonId);
}
