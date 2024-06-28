/*
  Author: Reece Wayt

  Parameters: 
    - CSPin (10): The pin that will be used as the chip select pin. This is the pin that will be used to enable the slave device. 
    - MAXCPUSPEED: The maximum speed of the CPU in Hz. This is used to set the SPI bus speed.
    - CIPO (11): Controller In Peripheral Out. 
    - COPI (12): Controller Out Peripheral In. 
    - SCLK (13): Serial Clock.

    From Teensy (Peripheral)
    - CIPO (Output)
    - COPI (Input)

  Sources: 
    How to use interrupts: https://www.pjrc.com/teensy/interrupts.html
      -> Example code on interrupts with SPI: http://www.gammon.com.au/forum/?id=10892&reply=1#reply1
    See "avr_emulation.h" library for macros and definitions
      -> https://github.com/PaulStoffregen/cores/blob/master/teensy4/avr_emulation.h

    https://docs.arduino.cc/learn/communication/wire/?_gl=1*1h96dhx*_gcl_au*NTU5NTg1MjY2LjE3MTk0NDA2NjM.*FPAU*NTU5NTg1MjY2LjE3MTk0NDA2NjM.*_ga*NTUxMzM5NDM2LjE3MTk0NDA2NjI.*_ga_NEXN8H46L5*MTcxOTUyMzU3NC41LjEuMTcxOTUyOTY3OS4wLjAuMTQ0MjM5ODQ0MQ..*_fplc*bCUyQlV4Q2VGNXklMkY2WmtMS0NrJTJCTEJ6d2Y3RUhVVEZaN3dCZ2pVN0FRbjc5TEtNWXUyOW1WQnh3YVkzTWxJeXplZzJsS3RXV05aZ2E4bjhRUjI5dHpBU0dPRzV0V04lMkJ3SmJmalIxcmp1RmFaRnB0MEx5UXRiS25EOVltNkFlJTJCQSUzRCUzRA..

  Purpose: 
    Very simple test program to get communication between teensy and Panda's onboard Coprocessor (ATMega) 
*/


#include <SPI.h>

volatile byte buf[100];
volatile byte pos;
volatile boolean process_it;

const int CSPin = 10;
const int CIPO = 11;
const int COPI = 12;
const int SCLK = 13;

char buff [50];
volatile byte indx;
volatile boolean process;


//Mode 0 -> Data is sampled on rising edge; Data can change on trailing edge
void spiISR() {
  byte incoming = 0; 
  for(int i = 0; i < 8; i++){
    while(digitalRead(SCLK) == LOW); // Wait for clock to go high
    incoming |= (digitalRead(COPI) << (7 - i));
    while(digitalRead(SCLK) == HIGH); // Wait for clock to go low
  }
  if (pos < sizeof(buf)){
      buf[pos++] = incoming;
    }
}

void setup (void)
{ 
  Serial.begin(115200);
  pinMode(SCLK, INPUT);
  pinMode(CSPin, INPUT);
  pinMode(CIPO, OUTPUT);
  pinMode(COPI, INPUT);

  interrupts(); // enable global interrupts
  
  attachInterrupt(digitalPinToInterrupt(CSPin), spiISR, FALLING);
   
  pos = 0;  

}  // end of setup


    // main loop - wait for flag set in interrupt routine
void loop(void) {
  if (pos > 0) {
    noInterrupts(); // disable interrupts while processing buffer
    for (byte i = 0; i < pos; i++) {
      Serial.println(buf[i], HEX);
    }
    pos = 0; // reset buffer position
    interrupts(); // re-enable interrupts
  }
} // end of loop

