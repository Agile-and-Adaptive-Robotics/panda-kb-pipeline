import serial
import time

# Open the serial port. Make sure the port matches the one your Arduino is connected to.
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

# Give some time for the serial connection to initialize
time.sleep(2)

def read_data():
    # Read response from the Arduino
    response = ser.read(4)  # Read 4 bytes
    if len(response) == 4:
        print("Received response:", [hex(b) for b in response])
    else:
        print("No response or incomplete response received")

# Read data from Arduino with a finite loop
loop_count = 50

for _ in range(loop_count):
    read_data()
    time.sleep(1)  # Adjust the sleep time as needed

# Close the serial connection when done
ser.close()
