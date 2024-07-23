#include <Arduino.h>

#define BAUD_RATE 1000000
#define DATA_PIPELINE_BUS Serial2  // Pins: 7 (Rx), 8 (Tx)
#define HOST_COM Serial            // For debugging, and comms with host PC

#define BUFFER_SIZE 100
byte read_buffer[BUFFER_SIZE];
byte write_buffer[BUFFER_SIZE];

void setup() {
  HOST_COM.begin(BAUD_RATE);
  DATA_PIPELINE_BUS.begin(BAUD_RATE);

  // Increase receive/send buffer size
  DATA_PIPELINE_BUS.addMemoryForRead(read_buffer, BUFFER_SIZE);
  DATA_PIPELINE_BUS.addMemoryForWrite(write_buffer, BUFFER_SIZE);

  HOST_COM.println("Teensy setup complete. Waiting for data...");
}

void loop() {
  // Read from DATA_PIPELINE_BUS and echo back
  while (DATA_PIPELINE_BUS.available()) {
    byte data = DATA_PIPELINE_BUS.read();
    DATA_PIPELINE_BUS.write(data);  // Echo back to the data pipeline
    HOST_COM.write(data);           // Send to host for debugging
  }

  // Check for incoming data from the host and echo back
  while (HOST_COM.available()) {
    byte data = HOST_COM.read();
    DATA_PIPELINE_BUS.write(data);  // Send to data pipeline
    HOST_COM.write(data);           // Echo back to the host
  }
}
