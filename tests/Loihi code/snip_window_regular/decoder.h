#include "nxsdk.h"
#define output_dim 2  // Output neuron layer dimension
#define decode_window_step 102  // Number of steps for each window
#define decode_window_start 3  // Starting step for spike recorder

/****************************************************************************************
Decoder SNIP in snip_window_regular record and add spike from output neurons
at every step of Loihi operation and send through decoder channel at every control step.
****************************************************************************************/

int do_decoder(runState *s);
void run_decoder(runState *s);