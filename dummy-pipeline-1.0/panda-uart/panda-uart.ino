/*
  Author: Reece Wayt

  Note On Classes: 
    - Serial (USB CDC): This stands for Communication Device Class which is a USB class for serial communication. 
       The panda's core processor speaks to the Arduino Leonardo via an internal USB port "dev/ttyACM0".
    - Serial1 (TTL Serial): Transistor-Transistor Logic Serial, which describe the physical pins 0 (RX) and 1 (TX) on the Arduino 
       Leonardo 

  Prerequisites: 
    - run this in a terminal to allow user level permission of the device driver: 
        sudo chmod 666 /dev/ttyACM0

*/

// Controller Code -> (Arduino Leonardo)

#define MAX_BAUD_RATE 1000000

const byte dataToSend[] = {0x01, 0x02, 0x03, 0x04};  // Example binary data

void setup() {
  Serial1.begin(MAX_BAUD_RATE);  // Initialize UART communication at 1 Mbps
  Serial.begin(115200);  // For debugging
}

void loop() {
  // Send binary data to the slave
  Serial.println("Sending data...");
  Serial1.write(dataToSend, sizeof(dataToSend));

  // Wait for a response
  Serial.println("Waiting for response...");
  while (Serial1.available() < 4) {
    // Wait until we receive 4 bytes
  }

  byte response[4];
  for (int i = 0; i < 4; i++) {
    response[i] = Serial1.read();
  }

  // Print the received response for debugging
  Serial.print("Received response: ");
  for (int i = 0; i < 4; i++) {
    Serial.print(response[i], HEX);
    Serial.print(" ");
  }
  Serial.println();

  delay(1000);  // Wait before sending the next message
}
