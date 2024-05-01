#include <iostream>
#include <cmath>
#include <chrono>
#include <thread>
#include <vector>
#include <fstream>

class SineWaveGenerator {
private:
    double amplitude;
    double frequency;
    double phaseShift;
    double period;
    double omega;
    double delta_t;
    double last_spike_time = 0; // Initialize to zero
    std::vector<std::tuple<double, double, int>> dataPoints;
    bool running;

public:
    SineWaveGenerator(double amp, double freq, double phase)
        : amplitude(amp), frequency(freq), phaseShift(phase), running(false) {
        period = 1 / frequency;
        omega = 2 * M_PI * frequency;
        delta_t = 1e-3; // 1ms, adjust as necessary
    }

    void generateSineWave() {
        auto startTime = std::chrono::high_resolution_clock::now();
        int spikeSent;
        running = true;

        while (running) {
            auto currentTime = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - startTime;
            double currentSeconds = elapsedSeconds.count();
            double y = amplitude * std::sin(omega * currentSeconds + phaseShift);

            spikeSent = check_and_send_spike(currentSeconds);

            dataPoints.push_back(std::make_tuple(currentSeconds, y, spikeSent));
            std::this_thread::sleep_for(std::chrono::microseconds(10)); // Sleep to maintain 500 Hz
        }
    }

    int check_and_send_spike(double currentSeconds) {
        if (currentSeconds - last_spike_time > delta_t) {
            last_spike_time = currentSeconds; // Update last spike time
            return 1; // Spike sent
        }
        return 0; // No spike sent
    }

    void stop() {
        running = false;
    }

    void saveDataToFile(const std::string& filename) {
        std::ofstream file(filename);
        if (file.is_open()) {
            file << "Time,Value,SpikeSent\n";
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
    SineWaveGenerator generator(1.0, 500, 0.0); // Frequency should be correct
    std::thread waveThread(&SineWaveGenerator::generateSineWave, &generator);
    std::this_thread::sleep_for(std::chrono::milliseconds(300)); // Adjust to the desired running time
    generator.stop();
    waveThread.join();
    generator.saveDataToFile("sine_wave_data.csv");
    std::cout << "Sine wave data has been saved to 'sine_wave_data.csv' and generation stopped.\n";
    return 0;
}