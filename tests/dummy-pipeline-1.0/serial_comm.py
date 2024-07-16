import serial
import multiprocessing
import time


class SerialDataPipeline:
    def __init__(self, port, baud_rate, stop_event, encoder_queue, decoder_queue):
        self.port = port
        self.baud_rate = baud_rate
        self.stop_event = stop_event
        self.encoder_queue = encoder_queue
        self.decoder_queue = decoder_queue
        self.recv_data_count = 0
        self.send_data_count = 0

    def run(self):
        try:
            ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            print(f"Connected to {self.port} at {self.baud_rate} baud.")
            ser.write(b'\x00')
            print("Sent start signal to peripheral device.")
            
            while not self.stop_event.is_set():
                if ser.in_waiting > 0:
                    #print(f"Data received from peripheral device: {ser.in_waiting} bytes.")
                    data = ser.read(1)
                    self.encoder_queue.put(data)  # Pass raw bytes to encoder process
                    self.recv_data_count += 1
                    #print(f"Data put in encoder_queue: {data}")
                if not self.decoder_queue.empty():
                    data_to_send = self.decoder_queue.get()
                    ser.write(data_to_send)
                    self.send_data_count += 1
                    #print(f"Data sent to peripheral: {data_to_send}")


        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")

        finally:
            if ser.is_open:
                ser.write(b'\xFF')
                print("Sent shutdown signal to peripheral device.")
                ser.close()
            print("Serial port closed, pipeline exiting.")
            print(f"Total data received: {self.recv_data_count} bytes")
            print(f"Total data sent: {self.send_data_count} bytes")

    def get_recv_data_count(self):
        return self.recv_data_count

    def get_send_data_count(self):
        return self.send_data_count