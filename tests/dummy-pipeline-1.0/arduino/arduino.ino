/*
  Author: Reece Wayt

  Note On Classes: 
    - Serial (USB CDC): This stands for Communication Device Class which is a USB class for serial communication. 
       The panda's core processor speaks to the Arduino Leonardo via an internal USB port "dev/ttyACM0".
    - Serial1 (TTL Serial): Transistor-Transistor Logic Serial, which describe the physical pins 0 (RX) and 1 (TX) on the Arduino 
       Leonardo 
    - Serial Receive & Transmitter buffer holds 64 bytes on the Leonardo
    - Great resource for learning about UART https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html


  Prerequisites: 
    - run this in a terminal to allow user level permission of the device driver: 
        sudo chmod 666 /dev/ttyACM0

*/

#include <Arduino.h>
// Communication with the peripheral: pins{0(Rx), 1(Tx)}
#define BAUD_RATE 1000000
#define HOST_COM Serial
#define DATA_PIPELINE_BUS Serial1

//Fifo buffers
#define BUFFER_SIZE 100
byte read_buffer[BUFFER_SIZE];
int read_head = 0;
byte write_buffer[BUFFER_SIZE];
int write_head = 0;


void setup() {
  HOST_COM.begin(BAUD_RATE);
  DATA_PIPELINE_BUS.begin(BAUD_RATE);
  while(HOST_COM.available() == 0){
     //busy wait for first command to start pipeline
  }
  byte pass_to_teensy = HOST_COM.read();  //start command received
  DATA_PIPELINE_BUS.write(pass_to_teensy);
}

void loop() {
  //peripheral bound spike train
  if (HOST_COM.available()) {
    byte pass_to_teensy = HOST_COM.read(); 
    //send to teensy
    DATA_PIPELINE_BUS.write(pass_to_teensy);
  }
  //incoming spike train
  if (DATA_PIPELINE_BUS.available()) {
    byte pass_to_host = DATA_PIPELINE_BUS.read();
    HOST_COM.write(pass_to_host);
  }
}