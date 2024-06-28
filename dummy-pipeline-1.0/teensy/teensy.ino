/*
  Author: Reece Wayt

  Notes on Teensys: 
   -  All serial ports on Teensy 4.0 and 4.1 have 4 byte transmit and receive FIFOs. 
   -  At very high baud rates, even small software delays can cause a receive buffer to overflow and data will be lost. 

  This is a very simple UART test program
*/
#define MAX_BAUD_RATE 1000000 //1 Mbps is max speed
#define RTS_PIN 7 // Ready to Send (Output)
#define CTS_PIN 8 // Clear to Send (Input)
#define BUFFER_SIZE 50

volatile byte buf[BUFFER_SIZE];
volatile byte pos = 0;

void setup() {
  Serial1.begin(MAX_BAUD_RATE);  // Initialize UART communication at 1 Mbps
  pinMode(RTS_PIN, INPUT);
  pinMode(CTS_PIN, OUTPUT);

  Serial.begin(115200);  // For debugging
}

void loop() {
  // Check if Serial1 Rx buffer has data
  if (Serial1.available() > 0) {
    // Check if Serial buffer has space
    if (Serial.availableForWrite() > 0) {
      digitalWrite(CTS_PIN, HIGH);  // Signal clear to send

      // Read incoming binary data
      while (Serial1.available() > 0 && pos < BUFFER_SIZE) {
        buf[pos++] = Serial1.read();
      }

      // Print received binary data for debugging
      Serial.print("Received: ");
      for (int i = 0; i < pos; i++) {
        Serial.print(buf[i], HEX);
        Serial.print(" ");
      }
      Serial.println();

      pos = 0;  // Reset buffer position

      digitalWrite(CTS_PIN, LOW);  // Signal not clear to send
    }
  }
}

