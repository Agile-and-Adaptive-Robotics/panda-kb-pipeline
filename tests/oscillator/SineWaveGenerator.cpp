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
    SineWaveGenerator(double amp, double freq, double phase)
        : amplitude(amp), frequency(freq), phaseShift(phase) {
    }

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

    void stop() {
        running = false;
    }

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
