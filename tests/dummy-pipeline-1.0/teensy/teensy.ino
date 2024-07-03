/*
  Author: Reece Wayt

  Notes on Teensys: 
   -  All serial ports on Teensy 4.0 and 4.1 have 4 byte transmit and receive FIFOs. 
   -  At very high baud rates, even small software delays can cause a receive buffer to overflow and data will be lost. 
   -  Serial 2 uses pins: 7 (RX) and 8 (TX) on Teensy 4.0 and 4.1
  This is a very simple UART test program

  Flow control diagram: 
  Controller MCU                   Peripheral MCU
+-----------------+              +-----------------+
|                 |              |                 |
|   TX  --------> | ------------>|  RX             |
|   RX  <-------- | <------------|  TX             |
|                 |              |                 |
|  RTS1 --------> | ------------>|  CTS1           |
|  CTS1 <-------- | <------------|  RTS1           |
|                 |              |                 |
|  RTS2 <-------- | <------------|  CTS2           |
|  CTS2 --------> | ------------>|  RTS2           |
+-----------------+              +-----------------+
  
*/


//**Teensy Code**

#include <Arduino.h>
#include "Oscillator.h"

#define LATTE_SERIAL Serial1
#define BAUD_RATE 1000000
#define BUFFER_SIZE 100 //FIFO buffer size

//*******UART FLOW CONTROL LINES************/
// Used when Teensy is receiving data from controller
#define CONTROLLER_CTS 2  // Clear to send pin (input)
#define CONTROLLER_RTS 3  // Request to send pin (output)
// Used when Teensy is sending data to controller
#define PERIPHERAL_CTS 4  // Clear to send pin (input)
#define PERIPHERAL_RTS 5  // Request to send pin (output)
//******************************************/

Oscillator osc(200.0, 1.0, 0.0); // amplitude, frequency, phase_shift, duration

byte fifo_buffer[BUFFER_SIZE]; // Buffer to store data for processing
int fifo_head = 0; // Index to write data to

void spikeCallback(int neuronId) {
    Serial.print("Spike sent from neuron: ");
    Serial.println(neuronId);
    // Assert RTS to indicate data ready to send
    digitalWrite(PERIPHERAL_RTS, LOW);
    delay(1); // Small delay to allow controller to read RTS
    LATTE_SERIAL.write(neuronId & 0x01); // Send the neuronId as 1-bit data
    digitalWrite(PERIPHERAL_RTS, HIGH);
}

void clearRxHwBuffer() {
    while(LATTE_SERIAL.available() > 0 && fifo_head < BUFFER_SIZE) {
        fifo_buffer[fifo_head++] = LATTE_SERIAL.read();
    }
}

// ISR function -> controller is trying to talk to us
void handleControllerRTS() {
    clearRxHwBuffer(); // Clear the hardware buffer make room for next data
    digitalWrite(CONTROLLER_RTS, LOW); // Indicate we are ready to receive data
    while(digitalRead(CONTROLLER_CTS) == LOW) {
        if(LATTE_SERIAL.available() > 0 && fifo_head < BUFFER_SIZE) {
            fifo_buffer[fifo_head++] = LATTE_SERIAL.read();
        }
        else {
           //TODO: Add a timeout to break out of this loop
           //TODO: Add a buffer check, if buffer is full, process buffer to make room
        }
        
    }
    digitalWrite(CONTROLLER_RTS, HIGH); 
    //transmission done
}

void setup() {
    Serial.begin(BAUD_RATE);
    LATTE_SERIAL.begin(BAUD_RATE);
    
    pinMode(CONTROLLER_CTS, INPUT);
    pinMode(CONTROLLER_RTS, OUTPUT);
    digitalWrite(CONTROLLER_RTS, HIGH); // Default RTS to HIGH (not ready to receive)
    pinMode(PERIPHERAL_CTS, INPUT);
    pinMode(PERIPHERAL_RTS, OUTPUT);
    digitalWrite(PERIPHERAL_RTS, HIGH); // Default RTS to HIGH (not ready to send)
    
    digitalWrite(PERIPHERAL_RTS, HIGH); // Default RTS to HIGH (not ready to send)

    // Attach an interrupt to handle RTS from the controller
    attachInterrupt(digitalPinToInterrupt(CONTROLLER_CTS), handleControllerRTS, FALLING);
    
    osc.setSpikeCallback(spikeCallback);
    osc.begin();
}

void loop() {
    // Check for serial input
    if (Serial.available() > 0) {
        char command = Serial.read();
        if (command == 'K' || command == 'k') {
            osc.stop();
            Serial.println("Oscillator stopped by kill signal.");
            while (1) { // Halt execution
                delay(100);
            }
        }
    }
    
    // Other main loop code
}