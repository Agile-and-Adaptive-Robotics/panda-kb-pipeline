#include <Arduino.h>
// Communication with the peripheral: pins{0(Rx), 1(Tx)}
#define BAUD_RATE 1000000
#define HOST_COM Serial
#define DATA_PIPELINE_BUS Serial1

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