"""
This Python module defines the OscGenProcess class, which generates a sinusoidal waveform 
based on specified amplitude, frequency, and phase shift. The class can run the waveform generation 
in a separate process, sends spikes based on current wave output frequency, and save the 
resulting data to a CSV file. This module is designed for applications where real-time waveform 
generation is needed to model oscillator neural stimulation. 

The wave uses the below formulat to determine spike signal frequencies: 
dt_now = amplitude * sin(omega * t + phase shift)

IF enough time has passed since last spike time, send another spike

Usage:
    Create an instance of OscGenProcess with desired waveform parameters.
    Call the run method to start waveform generation in a multiprocessing environment.
    Use the stop method to halt the waveform generation.
    Save the generated data to a CSV file using save_results_to_csv.
"""

import numpy as np
import time
import csv
import multiprocessing
import matplotlib.pyplot as plt

class OscGenProcess:
    """
    A class used to generate a sinusoidal waveform with the capability to track and record spikes based on amplitude conditions.

    Attributes:
        amplitude (float): The maximum amplitude of the sine wave.
        frequency (float): The frequency of the sine wave in Hz.
        phase_shift (float): The phase shift of the sine wave in radians.
        duration (float, optional): The duration for which the wave should be generated. If None, runs indefinitely.
        omega (float): Angular frequency computed as 2*pi*frequency.
        maxDT (float): The maximum time interval (in milliseconds) for updating the output value.
        times, outputs, spikes (multiprocessing.Manager().list): Shared lists for storing time points, output values, and spike occurrences.
        stop_event (multiprocessing.Event): An event to signal the process to stop.
    """

    def __init__(self, amplitude, frequency, phase_shift, duration=None):
        """
        Initializes the OscGenProcess with specified waveform parameters and setup for multiprocessing.

        Parameters:
            amplitude (float): The peak amplitude of the sine wave.
            frequency (float): The frequency of the sine wave.
            phase_shift (float): The phase offset of the sine wave in radians.
            duration (float, optional): The total duration to generate the waveform. None for indefinite generation.
        """
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase_shift = phase_shift
        self.duration = duration
        self.omega = 2 * np.pi * self.frequency
        self.maxDT = 5e-3 #[sec] this equates to a max frequency of 200Hz
        manager = multiprocessing.Manager()
        self.times = manager.list()
        self.outputs = manager.list()
        self.spikes = manager.list()
        self.stop_event = manager.Event()

    def generate_sine_wave(self):
        """
        Generates a sine wave based on initialized parameters, recording output and spikes.
        Runs in a separate process and continues until stopped or duration is reached.
        """
        start_time = time.perf_counter()
        t_last_spike = 0

        if self.duration is not None:
            end_time = start_time + self.duration

        while not self.stop_event.is_set() and (self.duration is None or time.perf_counter() - start_time < end_time):
            current_time = time.perf_counter() - start_time
            was_spike_sent = 0
            f_now = self.amplitude * np.sin(self.omega * current_time + self.phase_shift)
            # Check to send spike if enough time has passed so not to violate max frequency
            if(current_time - t_last_spike > self.maxDT):
                dt_now = abs(1/f_now)
                # If the dt since last spike is greater than current frequency of oscillator -> send a spike
                if(current_time - t_last_spike > dt_now):
                    was_spike_sent = 1
                    t_last_spike = current_time

            #Data output for shared file
            self.times.append(current_time * 1000)  # Convert time to milliseconds
            self.outputs.append(f_now)
            self.spikes.append(was_spike_sent)

    def run(self):
        """
        Starts the waveform generation in a separate process.
        """
        self.process = multiprocessing.Process(target=self.generate_sine_wave)
        self.process.start()

    def stop(self):
        """
        Signals the waveform generation process to stop and waits for it to finish.
        """
        self.stop_event.set()
        self.process.join()

    def save_results_to_csv(self, filename):
        """
        Saves the generated waveform data to a CSV file.

        Parameters:
            filename (str): The name of the file where the data will be saved. The file will include
                            columns for time in milliseconds, frequency in Hz, and spike occurrence.

        Saves data in the format:
            Time (ms), Frequency (Hz), Spike Sent
        """
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time (ms)', 'Frequency (Hz)', 'Spike Sent'])
            for time, output, spike in zip(self.times, self.outputs, self.spikes):
                writer.writerow([time, output, spike])
        print(f"Data successfully saved to {filename}.")

if __name__ == '__main__':
    oscillator = OscGenProcess(amplitude=200, frequency=1, phase_shift=0)
    oscillator.run()  # Start generating in a separate process
    time.sleep(2)  # Let it run for 2 seconds
    oscillator.stop()  # Stop the generation
    oscillator.save_results_to_csv('OscGenProcess.csv')
    print("Finished generating the sine wave and saving to CSV.")