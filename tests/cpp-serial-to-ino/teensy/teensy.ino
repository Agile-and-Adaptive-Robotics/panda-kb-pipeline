#include <Arduino.h>

#define BAUD_RATE 1000000
#define DATA_PIPELINE_BUS Serial2  // Pins: 7 (Rx), 8 (Tx)
#define HOST_COM Serial            // For debugging, and comms with host PC

#define BUFFER_SIZE 100
#define MAX_BYTES 100
byte read_buffer[BUFFER_SIZE];
byte write_buffer[BUFFER_SIZE];

// Measuring throughput
bool start = false; 
unsigned long duration = 10000; // Ten seconds
unsigned long start_time = 0; 
unsigned long total_bytes = 0; 

void setup() {
  HOST_COM.begin(BAUD_RATE);
  DATA_PIPELINE_BUS.begin(BAUD_RATE);

  // Increase receive/send buffer size
  DATA_PIPELINE_BUS.addMemoryForRead(read_buffer, BUFFER_SIZE);
  DATA_PIPELINE_BUS.addMemoryForWrite(write_buffer, BUFFER_SIZE);

  HOST_COM.println("Teensy setup complete. Waiting for data..."); 
  while(DATA_PIPELINE_BUS.available() == 0){
    //busy wait for start
  }
  start = true;
  start_time = micros(); 

}

void loop() {
  // Read from DATA_PIPELINE_BUS and echo back
  if(DATA_PIPELINE_BUS.available()) {
    byte data = DATA_PIPELINE_BUS.read();
    DATA_PIPELINE_BUS.write(data);  // Echo back to the data pipeline
    if(start) {
      total_bytes += 1; 
    }
    //HOST_COM.printf("Received this data: %d\n", data);
  }

  if(total_bytes >= MAX_BYTES && start){ //sample size reached process throughput
    start = false; 
    unsigned long end_time = micros(); 
    double total_duration = (end_time - start_time) / 1e6; // Correct the conversion to seconds
    double throughput = total_bytes / total_duration; 
    HOST_COM.printf("Total throughput = %ld bytes per second \n", (long)throughput);
  }
}
