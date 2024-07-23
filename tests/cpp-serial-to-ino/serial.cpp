#include <iostream>
#include <libserial/SerialPort.h>
#include <thread>
#include <chrono>
#include <vector>
#include <cstdlib> // for system()
#include <iomanip> // for std::setw and std::setfill

#define USB_SERIAL_PORT "/dev/ttyACM0"
#define BAUD_RATE 1000000

LibSerial::SerialPort serial_port;

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
    // Send the single byte data
    std::cout << "Sending data..." << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned int>(data) << std::dec << std::endl;
    std::vector<uint8_t> dataBuffer = {data};
    serial_port.Write(dataBuffer);

    while(serial_port.IsDataAvailable() == false) {
    }

    // Read back the response
    uint8_t receivedData;
    serial_port.ReadByte(receivedData);
    std::cout<< "Received data raw: " << static_cast<unsigned int>(receivedData) << std::endl;
    std::cout << "Received data: " << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned int>(receivedData) << std::dec << std::endl;

    std::cout << "Number of datas in buffer: " << serial_port.GetNumberOfBytesAvailable() << std::endl;
    std::cout << std::endl; //blank line
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
    const uint8_t dataToSend[] = {1, 2, 3, 4, 5, 6, 7, 8};  // Example data
    const size_t dataSize = sizeof(dataToSend) / sizeof(dataToSend[0]);

    for (size_t i = 0; i < dataSize; ++i) {
        sendData(dataToSend[i]);
        //std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    serial_port.Close();
    return 0;
}