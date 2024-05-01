import numpy as np
import time
import csv
import multiprocessing
import matplotlib.pyplot as plt

class OscGenProcess:
    def __init__(self, amplitude, frequency, phase_shift, duration=None):
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase_shift = phase_shift
        self.duration = duration
        self.omega = 2 * np.pi * self.frequency
        self.maxDT = 0.25e-3 #[ms]
        # Initializing manager and shared lists correctly
        manager = multiprocessing.Manager()
        self.times = manager.list()
        self.outputs = manager.list()
        self.spikes = manager.list()

        # Event for controlling the indefinite run
        self.stop_event = manager.Event()

    def generate_sine_wave(self):
        start_time = time.perf_counter()
        t_last_spike = 0
        # max_list_size = 5000  determine later if needed

        if self.duration is not None:
            end_time = start_time + self.duration

        while not self.stop_event.is_set() and (self.duration is None or current_time < end_time):
            current_time = time.perf_counter() - start_time
            # fetch current frequency from oscillator
            f_now = self.amplitude * np.sin(self.omega * current_time + self.phase_shift)
            #calculate the current T period for spike send process
            dt_now = abs(1/f_now)
            was_spike_sent = 0
            if(current_time - t_last_spike > dt_now):
                was_spike_sent = 1
                t_last_spike = current_time


            # Append current time and output to the lists
            self.times.append(current_time * 1000)  # Convert time to milliseconds
            self.outputs.append(f_now)
            self.spikes.append(was_spike_sent)


    def run(self):
        self.process = multiprocessing.Process(target=self.generate_sine_wave)
        self.process.start()

    def stop(self):
        self.stop_event.set()
        self.process.join()

    def save_results_to_csv(self, filename):
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time (ms)', 'Frequency (Hz)', 'Spike Sent'])
            for time, output, spike in zip(self.times, self.outputs, self.spikes):
                writer.writerow([time, output, spike])




if __name__ == '__main__':
    oscillator = OscGenProcess(amplitude=50, frequency=1, phase_shift=0)
    oscillator.run()  # Start generating in a separate process
    time.sleep(2)  # Let it run for 2 seconds
    oscillator.stop()  # Stop the generation
    oscillator.save_results_to_csv('OscGenProcess.csv')
    print("Finished generating the sine wave and saving to CSV.")
