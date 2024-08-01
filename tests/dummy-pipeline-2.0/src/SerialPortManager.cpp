#include "SerialPortManager.h"

SerialPortManager::SerialPortManager(const std::string& port, LibSerial::BaudRate baudRate) {
    serialPort.Open(port);
    serialPort.SetBaudRate(baudRate);
    serialPort.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serialPort.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
    serialPort.SetParity(LibSerial::Parity::PARITY_NONE);
    serialPort.FlushIOBuffers();
}

SerialPortManager::~SerialPortManager() {
    if (serialPort.IsOpen()) {
        serialPort.Close();
    }
}

// Write a byte to the serial port
void SerialPortManager::writeByte(uint8_t byte) {
    unsigned char c = static_cast<unsigned char>(byte);
    serialPort.WriteByte(c); 
}
// Write a vector of bytes to the serial port, i.e. buffer to serial port
void SerialPortManager::writeBytes(const std::vector<uint8_t>& bytes) {
    serialPort.Write(bytes);
}

bool SerialPortManager::isDataAvailable() const {
    return serialPort.IsDataAvailable();
}

// Read a byte and casts it to uint32_t for snips
uint32_t SerialPortManager::readByte() {
    uint8_t data; 
    serialPort.ReadByte(data);
    return static_cast<uint32_t>(data);
}

int SerialPortManager::getNumberOfBytesAvailable() const {
    return serialPort.GetNumberOfBytesAvailable();
}
