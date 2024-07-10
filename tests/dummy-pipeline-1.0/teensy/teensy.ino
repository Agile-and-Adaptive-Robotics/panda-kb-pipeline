/*
  Author: Reece Wayt

  Notes on Teensys: 
   -  All serial ports on Teensy 4.0 and 4.1 have 4 byte transmit and receive FIFOs. 
   -  At very high baud rates, even small software delays can cause a receive buffer to overflow and data will be lost. 
   -  Serial 2 uses pins: 7 (RX) and 8 (TX) on Teensy 4.0 and 4.1
  This is a very simple UART test program
  -   Great resource for learning about UART https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html

  Flow control diagram: 
  Controller MCU                   Peripheral MCU
+-----------------+              +-----------------+
|                 |              |                 |
|   TX  --------> | ------------>|  RX             |
|   RX  <-------- | <------------|  TX             |
|                 |              |                 |
+-----------------+              +-----------------+
  
//**Teensy Code**/

#include <Arduino.h>
#include "Oscillator.h"

#define DATA_PIPELINE_BUS Serial1           //Pins:{0(Rx),1(Tx)}
#define HOST_COM Serial                     //For debugging, and comms with host PC
#define BAUD_RATE 1000000                   //1Mbs
#define LED1 10
#define LED2 11

Oscillator osc(200.0, 1.0, 0.0); // amplitude, frequency, phase_shift, duration

#define BUFFER_SIZE 100                
byte read_buffer[BUFFER_SIZE]; 
byte write_buffer[BUFFER_SIZE]


void spikeCallback(byte neuronId) {
    DATA_PIPELINE_BUS.write(neuronId & 0x01); 
}


void setup() {
    HOST_COM.begin(BAUD_RATE);
    DATA_PIPELINE_BUS.begin(BAUD_RATE);

    pinMode(LED1, OUTPUT);
    pinMode(LED2, OUTPUT);

    /* 
     * Increase receive/send buffer size
     * By default teensy 4.1 only has 4 byte FIFO for receive and transmit, 
     * this code increases the buffer size to 104 bytes (i.e. 100 bytes + 4 bytes FIFO)
     */
    DATA_PIPELINE_BUS.addMemoryForRead(read_buffer, BUFFER_SIZE);
    DATA_PIPELINE_BUS.addMemoryForWrite(write_buffer, BUFFER_SIZE);

    while(DATA_PIPELINE_BUS.available() == 0){
        //busy waiting for start command
    }
    DATA_PIPELINE_BUS.read(); //flush out start command
    
    //start oscillator process
    osc.setSpikeCallback(spikeCallback);
    osc.begin();
}

void loop() {

    while(DATA_PIPELINE_BUS.available() > 0){
        byte data = DATA_PIPELINE_BUS.read();
        HOST_COM.println("Data received from host, %d", data);
        if(data == 0x01){
            digitalWrite(LED1, HIGH);
            delay(5);
            digitalWrite(LED1, LOW);
        }
        else if(data == 0x00){
            digitalWrite(LED2, HIGH);
            delay(5);
            digitalWrite(LED2, LOW);
        }
        else if(data == 0xFF){
            //kill command
            handleKillCommand();
        }
    }

}

void handleKillCommand(){
    osc.stop();

    //turn off leds
    digitalWrite(LED1, LOW);
    digitalWrite(LED2, LOW);

    HOST_COM.println("Kill command received. Shutting Down.");

    while(true){
        __WFI();
    }
}
