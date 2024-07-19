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
  
Teensy Code
*/

#include <Arduino.h>
#include "Oscillator.h"
#include <arm_math.h>

#define DATA_PIPELINE_BUS Serial2           //Pins:{7(Rx),8(Tx)}
#define HOST_COM Serial                     //For debugging, and comms with host PC
#define BAUD_RATE 1000000                   //1Mbs
#define LED1 10
#define LED2 11

Oscillator osc(200.0, 1.0, 0.0); // amplitude, frequency, phase_shift, duration

#define BUFFER_SIZE 100                
byte read_buffer[BUFFER_SIZE]; 
byte write_buffer[BUFFER_SIZE];

//to track data packet loss and integrity
volatile long int sent_data_count = 0;
volatile long int recv_data_count = 0;


void spikeCallback(byte neuronId) {
  if(DATA_PIPELINE_BUS.availableForWrite()){
    DATA_PIPELINE_BUS.write(neuronId & 0x01);
    sent_data_count++; 
    //HOST_COM.printf("Data sent %ld\n", sent_data_count); //debugging 
  }
  else{
    //do nothing but add error logging soon
  }
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
    DATA_PIPELINE_BUS.addMemoryForWrite(write_buffer, BUFFER_SIZE); //total is 139 bytes
    HOST_COM.println("Waiting for start command...\n");
    //HOST_COM.printf("Num bytes available for write...%d\n", DATA_PIPELINE_BUS.availableForWrite());
    while(DATA_PIPELINE_BUS.available() == 0){
        //busy waiting for start command
    }
    DATA_PIPELINE_BUS.read(); //flush out start command
    HOST_COM.println("Starting Oscillator Process...");
    delay(5);
    //start oscillator process
    osc.setSpikeCallback(spikeCallback);
    osc.begin();
}

void loop() {

    while(DATA_PIPELINE_BUS.available() > 0){
        byte data = DATA_PIPELINE_BUS.read();
        recv_data_count++;
        //HOST_COM.printf("Data received from host, %d\n", data);
        if(data == 0x01){
          //HOST_COM.println("Blinking LED 1");
          digitalWrite(LED1, HIGH);
          delay(1);
          digitalWrite(LED1, LOW);
        }
        else if(data == 0x00){
          //HOST_COM.println("Blinking LED 2");
          digitalWrite(LED2, HIGH);
          delay(1);
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
    HOST_COM.printf("Recevied this many datas: %ld\n", recv_data_count);
    HOST_COM.printf("Send this many datas: %ld\n", sent_data_count);

    while(true){
        __WFI();
    }
}
