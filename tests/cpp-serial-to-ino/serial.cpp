//USB_SERIAL_PORT = '/dev/ttyACM0'

#include <iostream>
#include <libserial/SerialPort.h>
#include <libserial/SerialStream.h>
#include <Firmata.h>

#define USB_SERIAL_PORT "/dev/ttyACM0"

using namespace LibSerial;

// Define the serial port object
SerialPort serial_port;

// Define a Firmata object
FirmataClass Firmata;

void setup() {
    // Open the serial port at 1 Mbps
    serial_port.Open(USB_SERIAL_PORT);
    serial_port.SetBaudRate(BaudRate::BAUD_1000000);
    serial_port.SetCharacterSize(CharacterSize::CHAR_SIZE_8);
    serial_port.SetStopBits(StopBits::STOP_BITS_1);
    serial_port.SetParity(Parity::PARITY_NONE);

    // Initialize Firmata
    Firmata.begin([&](uint8_t byte) { serial_port.WriteByte(byte); });
}

void sendToPeripheral(const std::vector<uint8_t>& data) {
    Firmata.startSysex();
    Firmata.write(0x10); // Custom command
    for (auto byte : data) {
        Firmata.write(byte);
    }
    Firmata.endSysex();
}

std::vector<uint8_t> readFromPeripheral() {
    std::vector<uint8_t> data;
    while (serial_port.IsDataAvailable()) {
        uint8_t byte;
        serial_port.ReadByte(byte);
        data.push_back(byte);
    }
    return data;
}

void loop() {
    // Read from the serial port and process data with Firmata
    if (serial_port.IsDataAvailable()) {
        uint8_t byte;
        serial_port.ReadByte(byte);
        Firmata.processInput(byte);
    }

    // Example: Send data to the peripheral and read the response
    sendToPeripheral({0x01, 0x02, 0x03});
    std::vector<uint8_t> response = readFromPeripheral();
    for (auto byte : response) {
        std::cout << "Received: " << std::hex << static_cast<int>(byte) << std::endl;
    }
}

int main() {
    setup();

    while (true) {
        loop();
    }

    // Close the serial port
    serial_port.Close();

    return 0;
}
