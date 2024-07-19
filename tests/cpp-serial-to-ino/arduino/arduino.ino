/*
  Author: Reece Wayt

  This Arduino code uses Firmata to communicate with the arduino from my 
  cpp code. Note that Host communication is done over the firmata firmware
*/

#include <Firmata.h>
#include <Arduino.h>

#define BAUD_RATE 1000000
#define DATA_PIPELINE_BUS Serial1 //pins {0 Rx, 1 Tx}

void setup() {
    // Initialize Firmata
    Firmata.begin(BAUD_RATE);
    // Initialize hardware serial (Serial1)
    DATA_PIPELINE_BUS.begin(BAUD_RATE);
    Firmata.attach(START_SYSEX, sysexCallback);
}

void loop() {
    while (Firmata.available()) {
        Firmata.processInput();
        if (DATA_PIPELINE_BUS.available()){
          Firmata.sendSysex(0x12, 1, (byte*)DATA_PIPELINE_BUS.read())
        }
    }
}

//System exclusion command, basically custom code for our application
void sysexCallback(byte command, byte argc, byte* argv) {
    if (command == 0x10) { // Custom command for UART communication
        // Send data to the secondary UART (Serial1)
        for (byte i = 0; i < argc; i++) {
            Serial1.write(argv[i]);
        }
    }
}
