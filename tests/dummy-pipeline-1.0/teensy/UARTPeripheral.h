#ifndef UARTPERIPHERAL_H
#define UARTPERIPHERAL_H

#include <Arduino.h>

/**
 * @brief Peripheral class for UART communication with RTS/CTS flow control.
 *
 * UART Connections Between Device 1 and Device 2:
 *
 *      +------------+             +------------+
 *      | Controller |             | Peripheral |
 *      |            |             |            |
 *      |  TX  --->  |------------>|  RX        |
 *      | ~RTS --->  |------------>| ~CTS       |
 *      | ~CTS <---  |<------------| ~RTS       |
 *      |  RX  <---  |<------------|  TX        |
 *      +------------+             +------------+
 *
 */

#define HWSERIAL Serial1 //pins 0 (rx) and 1 (tx)
#define MAX_BAUD_RATE 1000000 //1 Mbps is max speed
#define BUFFER_SIZE 50
#define CTS 30    //Clear to send pin (input)
#define RTS 31   //Request to send pin (output)


template <uint8_t UARTNum>
class UARTPeripheral {
public:
    UARTPeripheral(unsigned long baudRate);
    void transmit(const String& data);
    String receive();
    void setDebug(bool debug);
    void streamData();

private:
    HardwareSerial& serial;
    unsigned long baudRate;
    bool debug;
};

#endif // UARTPERIPHERAL_H