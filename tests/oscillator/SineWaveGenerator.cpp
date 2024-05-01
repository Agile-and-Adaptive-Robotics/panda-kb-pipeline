//to compile - g++ -std=c++11 -o SineWaveGenerator SineWaveGenerator.cpp -pthread

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
    double spk_threshold;
    std::vector<std::tuple<double, double, int>> dataPoints;
    std::vector<double> thresholds;
    bool running;
    int current_threshold_index; // Index to track the current threshold


public:
    SineWaveGenerator(double amp, double freq, double phase, double spk_threshold)
        : amplitude(amp), frequency(freq), phaseShift(phase), spk_threshold(spk_threshold), running(false), current_threshold_index(0) {
        int num_steps = static_cast<int>(amplitude / (amplitude * spk_threshold));
        for (int i = 1; i <= num_steps; ++i) {
            thresholds.push_back(amplitude * spk_threshold * i); //activation levels as y values
        }
    }

    void generateSineWave() {
        auto startTime = std::chrono::high_resolution_clock::now();
        double omega = 2 * M_PI * frequency;
        double activation_lvl;
        double last_y = 0; //Last sine wave value to track direction for spike send process
        int spikeSent;
        bool increasing;
        running = true; //start sin wave

        while (running) {
            auto currentTime = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsedSeconds = currentTime - startTime;
            double currentSeconds = elapsedSeconds.count();
            double y = amplitude * std::sin(omega * currentSeconds + phaseShift);
            activation_lvl = (y / amplitude) * 100;
            increasing = (std::abs(y) > std::abs(last_y)); 
            spikeSent = check_and_send_spike(y, last_y, increasing);
            //std::cout << "y = " << y << ", last_y = " << last_y << std::endl;
            dataPoints.push_back(std::make_tuple(currentSeconds, y, spikeSent));
            last_y = y; 
            std::this_thread::sleep_for(std::chrono::microseconds(10)); // Sleep to maintain 500 Hz
        }
    }

    int check_and_send_spike(double y, double last_y, bool increasing) {
        int spikeSent = 0;
        increasing = (std::abs(y) > std::abs(last_y)); 
        std::cout << "Is it increasing = " << increasing << std::endl;
        if(isThresholdCrossed(y, last_y, thresholds[current_threshold_index])){
            spikeSent = 1;
            // Only increment or decrement the index if a spike was actually sent
            if (increasing && current_threshold_index < thresholds.size() - 1) {
                current_threshold_index++;
            } else if (!increasing && current_threshold_index > 0) {
                current_threshold_index--;
            }
        }
        
        return spikeSent;
    }
    
    bool isThresholdCrossed(double y, double last_y, double threshold) {
        const double epsilon = 0.0001 * amplitude; // Epsilon is 1% of the amplitude
        std::cout << "y = " << y << ", last_y = " << last_y << ", threshold =" << threshold << std::endl;
        // Check if the current or last values are within epsilon range of the threshold
        bool currentClose = std::abs(std::abs(y) - threshold) < epsilon;

        return (std::abs(last_y) <= threshold && (std::abs(y) >= threshold)) || (currentClose) ||
               (std::abs(last_y) >= threshold && (std::abs(y) <= threshold));
    }
    
    void stop() {
        running = false; //Set running to false to stop the loop
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
    SineWaveGenerator generator(1.0, 2, 0.0, 0.25); // Correct frequency to 500 if needed
    std::thread waveThread(&SineWaveGenerator::generateSineWave, &generator);
    std::this_thread::sleep_for(std::chrono::milliseconds(300)); // Adjust to the desired running time
    generator.stop();
    waveThread.join(); // Wait for the thread to finish
    generator.saveDataToFile("sine_wave_data.csv");
    std::cout << "Sine wave data has been saved to 'sine_wave_data.csv' and generation stopped.\n";
    return 0;
}