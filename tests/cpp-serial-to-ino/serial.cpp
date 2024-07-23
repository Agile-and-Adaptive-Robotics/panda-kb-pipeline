#include <iostream>
#include <libserial/SerialPort.h>
#include <thread>
#include <chrono>
#include <vector>
#include <cstdlib> // for system()
#include <iomanip> // for std::setw and std::setfill

#define USB_SERIAL_PORT "/dev/ttyACM0"
#define BAUD_RATE 57600

LibSerial::SerialPort serial_port;

void setup() {
    // Open the serial port at the specified baud rate
    serial_port.Open(USB_SERIAL_PORT);
    serial_port.SetBaudRate(LibSerial::BaudRate::BAUD_1000000);
    serial_port.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serial_port.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
    serial_port.SetParity(LibSerial::Parity::PARITY_NONE);
}

void sendData(uint8_t data) {
    // Send the single byte data
    std::cout << "Sending data..." << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned int>(data) << std::dec << std::endl;
    std::vector<uint8_t> dataBuffer = {data};
    serial_port.Write(dataBuffer);

    // Allow some time for the data to be sent and echoed back
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));

    // Read back the response
    uint8_t receivedData;
    if (serial_port.IsDataAvailable()) {
        serial_port.ReadByte(receivedData);
        std::cout<< "Received data raw: " << static_cast<unsigned int>(receivedData) << std::endl;
        std::cout << "Received data: " << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned int>(receivedData) << std::dec << std::endl;
    } else {
        std::cerr << "No response received" << std::endl;
    }
}

void compileAndUpload() {
    const std::string sourceDir = SOURCE_DIR;
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

int main() {
    compileAndUpload();  // Compile and upload the Arduino sketch before starting serial communication

    setup();

    // Fixed array of data to send
    const uint8_t dataToSend[] = {1, 2, 3, 4, 5, 6, 7};  // Example data
    const size_t dataSize = sizeof(dataToSend) / sizeof(dataToSend[0]);

    for (size_t i = 0; i < dataSize; ++i) {
        sendData(dataToSend[i]);
        std::this_thread::sleep_for(std::chrono::seconds(1));  // Wait for 1 second before sending the next byte
    }

    serial_port.Close();
    return 0;
}
