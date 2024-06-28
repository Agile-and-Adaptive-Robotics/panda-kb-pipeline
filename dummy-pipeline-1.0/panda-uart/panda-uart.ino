/*
  Author: Reece Wayt

  Note On Classes: 
    - Serial (USB CDC): This stands for Communication Device Class which is a USB class for serial communication. 
       The panda's core processor speaks to the Arduino Leonardo via a internal USB port "dev/ttyACM0".
    - Serial1 (TTL Serial): Transistor-Transistor Logic Serial, which describe the physical pins 0 (RX) and 1 (TX) on the Arduino 
       Leonardo 

  Prerequisites: 
    - run this in a terminal to allow user level permission of the device driver: 
        sudo chmod 666 /dev/ttyACM0

*/

// Master (Arduino Leonardo)

#define MAX_BAUD_RATE 1000000
#define RTS_PIN 7  // Ready to Send (output)
#define CTS_PIN 8  // Clear to Send (input)

const byte dataToSend[] = {0x01, 0x02, 0x03, 0x04, 0x05};  // Example binary data

void setup() {
  Serial1.begin(MAX_BAUD_RATE);  // Initialize UART communication at 1 Mbps
  pinMode(RTS_PIN, OUTPUT);
  pinMode(CTS_PIN, INPUT);

  Serial.begin(115200);  // For debugging
}

void loop() {
  // Check if it's clear to send (CTS from slave)
  if (digitalRead(CTS_PIN) == HIGH) {
    // Check if Serial1 Tx buffer has space
    if (Serial1.availableForWrite() >= sizeof(dataToSend)) {
      digitalWrite(RTS_PIN, HIGH);  // Signal ready to send

      // Send binary data to the slave
      for (int i = 0; i < sizeof(dataToSend); i++) {
        Serial1.write(dataToSend[i]);
      }

      digitalWrite(RTS_PIN, LOW);  // Signal not ready to send
    }
  }

  delay(1000);  // Wait before sending the next message
}