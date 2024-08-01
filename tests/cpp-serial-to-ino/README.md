# /tests/cpp-serial-to-arduino
The purpose of this test case was to familiarize myself with the c++ ecosystem and begin some performance benchmarking of the data pipeline
- Statistics Measured: 
    - Rount trip latency
    - Latency from host (lattePanda) to peripheral (Teensy)
    - Latency from Teensy to lattePanda

### Sample data for average round trip latency
```bash
Average Round-Trip Latency: 948.7 microseconds
Packet Loss Rate: 0.00%
Sample0:503.00 microseconds
Sample1:992.00 microseconds
Sample2:1000.00 microseconds
Sample3:1008.00 microseconds
Sample4:969.00 microseconds
Sample5:1003.00 microseconds
Sample6:1018.00 microseconds
Sample7:1011.00 microseconds
Sample8:995.00 microseconds
Sample9:988.00 microseconds

```

### Data for round trip latency and throughput
Throughput was measured generally as number of bytes send in a fixed duration. Below is example code: 
```cpp
// HOST CODE
void measureThroughput(size_t durationSeconds) {
    auto start = std::chrono::high_resolution_clock::now();
    size_t bytesSent = 0;
    while (std::chrono::duration_cast<std::chrono::seconds>(std::chrono::high_resolution_clock::now() - start).count() < durationSeconds) {
            sendData(0xAA); // Example data byte
            bytesSent++;

    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::seconds>(end - start).count();
    double throughput = static_cast<double>(bytesSent) / duration;
    std::cout << "Throughput: " << throughput << " bytes/second" << std::endl;
}

// TEENSY CODE

void setup() {
  ...Additional code left out
  // Wait for initial data to start the measurement
  while(DATA_PIPELINE_BUS.available() == 0) {
    // Busy wait
  }
  start = true;
  start_time = millis(); 
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

  if(start && (millis() - start_time > duration)) {
    start = false; // End throughput measurement
    unsigned long end_time = millis(); // End time
    double total_duration = (end_time - start_time) * 1e-3; // Convert to seconds
    double throughput = total_bytes / total_duration;
    HOST_COM.printf("Total throughput = %ld bytes per second\n", (long)throughput);
  }
}
```
  
**Results**
```bash
Throughput: 455.9 bytes/second
Average Round-Trip Latency: 250865 microseconds
Packet Loss Rate: 100.00%
Round-Trip Latency 0: 250836.00 microseconds
Round-Trip Latency 1: 250855.00 microseconds
Round-Trip Latency 2: 250879.00 microseconds
Round-Trip Latency 3: 250874.00 microseconds
Round-Trip Latency 4: 250847.00 microseconds
Round-Trip Latency 5: 250899.00 microseconds
Round-Trip Latency 6: 250876.00 microseconds
Round-Trip Latency 7: 250846.00 microseconds
Round-Trip Latency 8: 250908.00 microseconds
Round-Trip Latency 9: 250831.00 microseconds
```
- Generally note happy with this, and what I found was my original implementation of throughput introduced too much overhead due to the frequent sampling of the high resolution system clock. 

### Final results
See code base for implementation
```bash
One-Way Throughput: 1076.89 bytes per second
Two-Way Throughput: 2153.78 bytes per second
Average Round-Trip Latency: 928 microseconds
Packet Loss Rate: 0.00%
Round-Trip Latency 0: 271.00 microseconds
Round-Trip Latency 1: 1014.00 microseconds
Round-Trip Latency 2: 1006.00 microseconds
Round-Trip Latency 3: 994.00 microseconds
Round-Trip Latency 4: 948.00 microseconds
Round-Trip Latency 5: 1007.00 microseconds
Round-Trip Latency 6: 1050.00 microseconds
Round-Trip Latency 7: 967.00 microseconds
Round-Trip Latency 8: 972.00 microseconds
Round-Trip Latency 9: 1051.00 microseconds
```