import serial

class SerialDataPipeline:
    def __init__(self, port, baud_rate, stop_event, encoder_queue, decoder_queue):
        self.port = port
        self.baud_rate = baud_rate
        self.stop_event = stop_event
        self.encoder_queue = encoder_queue
        self.decoder_queue = decoder_queue

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Connected to {self.port} at {self.baud_rate} baud.")
            
            while not self.stop_event.is_set():
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    self.encoder_queue.put(data)  # Pass raw bytes to encoder process

                if not self.decoder_queue.empty():
                    data_to_send = self.decoder_queue.get()
                    ser.write(data_to_send)
                    print(f"Data sent to peripheral: {data_to_send}")


        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")

        finally:
            if ser.is_open:
                # Shut down peripheral device to shut down oscillator process
                ser.write(bytes[0xFF])
                print("Sent shutdown signal to peripheral device.")
                ser.close()
            print("Serial port closed, pipeline exiting.")
