#include <iostream>
#include <libserial/SerialPort.h>
#include <thread>
#include <chrono>
#include <iomanip>

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
}

void testCommunication() {
    const uint8_t testData[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE};
    const int testDataSize = sizeof(testData);

    // Send test data
    std::cout << "Sending data: ";
    for (int i = 0; i < testDataSize; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)testData[i] << " ";
    }
    std::cout << std::dec << std::endl;
    serial_port.Write(testData, testDataSize);

    // Allow some time for the data to be sent and echoed back
    std::this_thread::sleep_for(std::chrono::milliseconds(500));

    // Read back the response
    uint8_t receivedData[testDataSize] = {0};
    int bytesRead = 0;
    while (serial_port.IsDataAvailable() && bytesRead < testDataSize) {
        char byte;
        serial_port.ReadByte(byte);
        receivedData[bytesRead++] = byte;
    }

    std::cout << "Received data: ";
    for (int i = 0; i < bytesRead; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)receivedData[i] << " ";
    }
    std::cout << std::dec << std::endl;
}

int main() {
    setup();
    testCommunication();
    serial_port.Close();
    return 0;
}
