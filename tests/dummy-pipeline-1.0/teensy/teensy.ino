/*
  Author: Reece Wayt

  Notes on Teensys: 
   -  All serial ports on Teensy 4.0 and 4.1 have 4 byte transmit and receive FIFOs. 
   -  At very high baud rates, even small software delays can cause a receive buffer to overflow and data will be lost. 
   -  Serial 2 uses pins: 7 (RX) and 8 (TX) on Teensy 4.0 and 4.1
  This is a very simple UART test program
*/

//**Teensy Code**

#define MAX_BAUD_RATE 1000000 //1 Mbps is max speed
#define BUFFER_SIZE 50

volatile byte buf[BUFFER_SIZE];
volatile byte pos = 0;

void setup() {
  Serial2.begin(MAX_BAUD_RATE);  // Initialize UART communication at 1 Mbps
  Serial.begin(115200);  // For debugging
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
}

void loop() {
  // Check if Serial1 Rx buffer has data
  Serial.println(Serial2.available());
  if (Serial2.available() >= 4) {
    byte receivedData[4];
    for (int i = 0; i < 4; i++){
      receivedData[i] = Serial2.read();
    }

    Serial.print("Received data: ");
    for (int i = 0; i < 4; i++) {
      Serial.print(receivedData[i], HEX);
      Serial.print(" ");
    }
    Serial.println();

    byte responseData[] = {0x0F, 0x0A, 0x0F, 0x04};
    Serial2.write(responseData, sizeof(responseData));

    Serial.println("Response Sent");

  }
  delay(1000); 
}

