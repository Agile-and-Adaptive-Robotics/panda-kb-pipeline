#include "UARTPeripheral.h"

template <uint8_t UARTNum>
UARTPeripheral<UARTNum>::UARTPeripheral(unsigned long baudRate)
    : serial(*(HardwareSerial*)HardwareSerial::getAvailable<UARTNum>()), baudRate(baudRate), debug(false) {
    serial.begin(baudRate);
    serial.attachRts(RTS); // Set RTS pin
    serial.attachCts(CTS); // Set CTS pin
}

template <uint8_t UARTNum>
void UARTPeripheral<UARTNum>::transmit(const uint8_t* data, size_t length) {
    serial.write(data, length);
    if (debug) {
        Serial.print("Transmitting: ");
        for (size_t i = 0; i < length; i++) {
            Serial.print(data[i], HEX);
            Serial.print(" ");
        }
        Serial.println();
    }
}

template <uint8_t UARTNum>
size_t UARTPeripheral<UARTNum>::receive(uint8_t* buffer, size_t length) {
    size_t bytesRead = 0;
    while (serial.available() && bytesRead < length) {
        buffer[bytesRead++] = serial.read();
    }
    if (debug && bytesRead > 0) {
        Serial.print("Received: ");
        for (size_t i = 0; i < bytesRead; i++) {
            Serial.print(buffer[i], HEX);
            Serial.print(" ");
        }
        Serial.println();
    }
    return bytesRead;
}

template <uint8_t UARTNum>
void UARTPeripheral<UARTNum>::setDebug(bool debug) {
    this->debug = debug;
}

template <uint8_t UARTNum>
void UARTPeripheral<UARTNum>::streamData() {
    while (serial.available()) {
        Serial.write(serial.read());
    }
}


/*example usage...
#include "UARTPeripheral.h"

UARTPeripheral<1> peripheral1(9600);

void setup() {
    Serial.begin(9600); // Begin the default serial for debugging
    peripheral1.setDebug(true);
}

void loop() {
    // Example binary data
    uint8_t data[] = {0x01, 0x02, 0x03, 0x04};
    peripheral1.transmit(data, sizeof(data));

    // Buffer to store received data
    uint8_t buffer[BUFFER_SIZE];
    size_t length = peripheral1.receive(buffer, BUFFER_SIZE);

    if (length > 0) {
        Serial.print("Peripheral received: ");
        for (size_t i = 0; i < length; i++) {
            Serial.print(buffer[i], HEX);
            Serial.print(" ");
        }
        Serial.println();
    }

    // Stream data
    peripheral1.streamData();

    delay(1000); // Add delay for demonstration purposes
}


*/