#include <iostream>
#include <libserial/SerialPort.h>
#include <thread>
#include <chrono>
#include <vector>
#include <iomanip> // for std::setw and std::setfill
#include <cstdlib> // for system()
#include <string>
#include <numeric> // for std::accumulate

#define USB_SERIAL_PORT "/dev/ttyACM0"
#define BAUD_RATE 1000000

//int packet loss
int packet_loss = 0;

LibSerial::SerialPort serial_port;

void compileAndUpload() {
    const std::string sourceDir = SOURCE_DIR; // Update this to your actual path
    const std::string sketchPath = sourceDir + "/arduino/arduino.ino";
    const std::string compile_cmd = "arduino-cli compile --fqbn arduino:avr:leonardo " + sketchPath;
    const std::string upload_cmd = "arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo " + sketchPath;
    
    std::cout << "Compiling Arduino sketch..." << std::endl;
    int compile_result = system(compile_cmd.c_str());
    if (compile_result != 0) {
        std::cerr << "Compilation failed." << std::endl;
        exit(1);
    } else {
        std::cout << "Compilation succeeded." << std::endl;
    }

    std::cout << "Uploading Arduino sketch..." << std::endl;
    int upload_result = system(upload_cmd.c_str());
    if (upload_result != 0) {
        std::cerr << "Upload failed." << std::endl;
        exit(1);
    } else {
        std::cout << "Upload succeeded." << std::endl;
    }
}

void setup() {
    // Open the serial port at the specified baud rate
    serial_port.Open(USB_SERIAL_PORT);
    serial_port.SetBaudRate(LibSerial::BaudRate::BAUD_1000000);
    serial_port.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serial_port.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
    serial_port.SetParity(LibSerial::Parity::PARITY_NONE);
    serial_port.FlushIOBuffers();
}

void sendData(uint8_t data) {
    std::vector<uint8_t> dataBuffer = {data};
    serial_port.Write(dataBuffer);
}

uint8_t receiveData() {
    uint8_t receivedData;
    serial_port.ReadByte(receivedData);
    return receivedData;
}

double measureRoundTripLatency() {
    auto start = std::chrono::high_resolution_clock::now();
    sendData(0xAA); // Example data byte
    while (serial_port.IsDataAvailable() == false) {
    }
    uint8_t receivedData = receiveData();
    auto end = std::chrono::high_resolution_clock::now();
    auto roundTripTime = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    if(receivedData != 0xAA){ //measure packet loss
        packet_loss++;
    }

    return roundTripTime; // us (microseconds resolution)
}

int main() {
    const size_t numSamples = 1000; // Number of samples to average over
    std::vector<double> roundTripLatencies(numSamples);
    compileAndUpload();  // Compile and upload the Arduino sketch before starting serial communication
    setup();

    auto start = std::chrono::high_resolution_clock::now(); //measure throughput
    for (size_t i = 0; i < numSamples; ++i) {
        roundTripLatencies[i] = measureRoundTripLatency();
    }
    auto end = std::chrono::high_resolution_clock::now();

   auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count() / 1e6; // Convert to seconds


    double oneWayThroughput = (static_cast<double>(numSamples) / duration);
    double twoWayThroughput =  (static_cast<double>(numSamples) / duration) * 2;

    std::cout << "One-Way Throughput: " << oneWayThroughput << " bytes per second" << std::endl;
    std::cout << "Two-Way Throughput: " << twoWayThroughput << " bytes per second" << std::endl;
    
    double averageRoundTripLatency = std::accumulate(roundTripLatencies.begin(), roundTripLatencies.end(), 0.0) / numSamples;
    std::cout << "Average Round-Trip Latency: " << averageRoundTripLatency << " microseconds" << std::endl;
    
    double packetLossRate = (static_cast<double>(packet_loss) / numSamples) * 100;
    std::cout << "Packet Loss Rate: " << std::setprecision(2) << std::fixed << packetLossRate << "%" << std::endl;

    /*
    for(size_t i = 0; i < numSamples; ++i){
        std::cout << "Round-Trip Latency " << i << ": " << roundTripLatencies[i] << " microseconds" << std::endl;
    }
    */
    serial_port.Close();
    return 0;
}
