/**
 * @file SineWaveGenerator.cpp
 * @brief This Python module defines the OscGenProcess class, which generates a sinusoidal waveform 
 * based on specified amplitude, frequency, and phase shift. The class can run the waveform generation 
 * in a separate process, sends spikes based on current wave output frequency, and save the 
 * resulting data to a CSV file. This module is designed for applications where real-time waveform 
 * generation is need to model oscillator neural stimulation. 
 *
 * The wave uses the below formulat to determine spike signal frequencies: 
 * dt_now = amplitude * sin(omega * t + phase shift)
 * --> IF enough time has passed since last spike time, send another spike <--
 *
 * Usage:
 *  - Instantiate a SineWaveGenerator object with desired waveform parameters.
 *  - Start the waveform generation in a separate thread.
 *  - Stop the waveform generation after a specified duration.
 *  - Save the collected data to a CSV file.
 *
 */
#include <iostream>
#include <cmath>
#include <chrono>
#include <thread>
#include <vector>
#include <fstream>
#include <mutex>

class SineWaveGenerator {
private:
    double amplitude;
    double frequency;
    double phaseShift;
    std::vector<std::tuple<double, double, int>> dataPoints;
    double lastTime = 0;
    bool running;
    std::mutex mtx;

public:
    /**
     * Constructor for SineWaveGenerator.
     * @param amp The amplitude of the sine wave.
     * @param freq The frequency of the sine wave in Hz.
     * @param phase The phase shift of the sine wave in radians.
     */
    SineWaveGenerator(double amp, double freq, double phase)
        : amplitude(amp), frequency(freq), phaseShift(phase) {
    }
    /**
     * Generates the sine wave continuously until stopped. Records the time, output value, and spike status.
     * Spikes are determined based on the time interval calculated from the waveform value.
     */
    void generateSineWave() {
        auto startTime = std::chrono::high_resolution_clock::now();
        double omega = 2 * M_PI * frequency;
        double current_time;
        double last_spike_time = 0;
        running = true;

        while (running) {
            auto now = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = now - startTime;
            current_time = elapsed.count();

            double y = amplitude * std::sin(omega * current_time + phaseShift);
            double dt_now = std::abs(1 / y); // Avoid division by zero by taking absolute
            int was_spike_sent = 0;

            if (current_time - last_spike_time > dt_now) {
                was_spike_sent = 1;
                last_spike_time = current_time;
            }

            {
                std::lock_guard<std::mutex> lock(mtx);
                dataPoints.emplace_back(current_time * 1000, y, was_spike_sent);
            }

            std::this_thread::sleep_for(std::chrono::milliseconds(1)); // Sleep to control the generation rate
        }
    }
    //Stops waveform generation
    void stop() {
        running = false;
    }
    //Save data to file for analysis in oscillator.ipynb
    void saveDataToFile(const std::string& filename) {
        std::ofstream file(filename);
        if (file.is_open()) {
            file << "Time (ms),Frequency (Hz),Spike Sent\n";
            for (const auto& point : dataPoints) {
                file << std::get<0>(point) << "," << std::get<1>(point) << "," << std::get<2>(point) << "\n";
            }
            file.close();
        } else {
            std::cerr << "Failed to open file for writing.\n";
        }
    }
};

int main() {
    SineWaveGenerator generator(50, 1, 0); // Amplitude 50, Frequency 1 Hz, Phase shift 0
    std::thread waveThread(&SineWaveGenerator::generateSineWave, &generator);

    std::this_thread::sleep_for(std::chrono::seconds(2)); // Let it run for 2 seconds
    generator.stop();
    waveThread.join(); // Ensure thread completes

    generator.saveDataToFile("sine_wave_data.csv");
    std::cout << "Finished generating the sine wave and saving to CSV.\n";
    return 0;
}
