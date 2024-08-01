#ifndef SERIALPORTMANAGER_H
#define SERIALPORTMANAGER_H

#include <libserial/SerialPort.h>
#include <vector>
#include <cstdint>

class SerialPortManager {
public:
    SerialPortManager(const std::string& port, LibSerial::BaudRate baudRate);
    ~SerialPortManager();
    void writeByte(uint8_t byte);
    void writeBytes(const std::vector<uint8_t>& bytes);
    bool isDataAvailable() const;
    uint8_t readByte();
    int getNumberOfBytesAvailable() const;

private:
    LibSerial::SerialPort serialPort;
};

#endif // SERIALPORTMANAGER_H
