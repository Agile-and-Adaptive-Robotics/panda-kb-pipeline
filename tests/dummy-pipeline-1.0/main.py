import serial
import time

# Define serial ports
USB_SERIAL_PORT = '/dev/ttyACM0'  #Device driver for the USB serial port to Arduino Coprocessor

# Define baud rate
BAUD_RATE = 1000000

# Define the kill command
KILL_COMMAND = 0xFF

def main():
    # Open the USB serial port
    with serial.Serial(USB_SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        print(f"Connected to {USB_SERIAL_PORT} at {BAUD_RATE} baud.")
        # start Teensy oscillator process
        ser.write(bytes([0x00]))
        start_time = time.time()

        while True:
            # Check if 60 seconds have passed
            if time.time() - start_time > 15:
                send_kill_command(ser)
                break

            # Read data from Teensy via Arduino
            if ser.in_waiting > 0:
                received_data = ser.read()
                print(f"Received from Teensy: {received_data}")

                # Echo the data back to Teensy via Arduino
                ser.write(received_data)
                print(f"Sent back to Teensy: {received_data}")

            # Sleep to avoid busy waiting
            time.sleep(0.01)

def send_kill_command(ser):
    print("Sending kill command.")
    ser.write(bytes([KILL_COMMAND]))

if __name__ == "__main__":
    main()