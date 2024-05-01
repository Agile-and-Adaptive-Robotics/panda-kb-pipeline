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
        for (int i = 0; i <= num_steps; ++i) {
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
            spikeSent = check_and_send_spike(y, increasing);

            dataPoints.push_back(std::make_tuple(currentSeconds, y, spikeSent));
            last_y = y; 
            std::this_thread::sleep_for(std::chrono::microseconds(1)); // Sleep to maintain 500 Hz
        }
    }

    int check_and_send_spike(double y, bool increasing) {
        int spikeSent = 0;
    
        if (increasing) { //absolut value increasing
            // Only increment the index if y surpasses the next threshold
            if (current_threshold_index < thresholds.size() - 1 && std::abs(y) > thresholds[current_threshold_index]) {
                spikeSent = 1;
                current_threshold_index++;
            }
        } else {
            // Only decrement the index if y drops below the current threshold and we're not at the first threshold
            if (current_threshold_index >= 0 && std::abs(y) < thresholds[current_threshold_index - 1]) {
                spikeSent = 1;
                current_threshold_index--;
            }
        }
        if(current_threshold_index < 0){
            current_threshold_index = 0;
        }
        return spikeSent;
    }
    /*
    bool isThresholdCrossed(double y, double last_y,  double threshold) {
        static bool crossedThreshold = false; //static so holds state between calls
        
        if(std::abs(y) >= threshold && std::abs(last_y) <= threshold){
            //threshold crossed on absolute value increasing
            crossedThreshold = true;
        }
        else if(std::abs(y) <= threshold && std::abs(last_y) >= threshold){
            //threshold crossed on absolut value decreasing
            crossedThreshold = true; 
        }
        else{
            crossedThreshold = false;
        }
        return crossedThreshold;
    }
    */
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
    SineWaveGenerator generator(1.0, 5, 0.0, 0.25); // Correct frequency to 500 if needed
    std::thread waveThread(&SineWaveGenerator::generateSineWave, &generator);
    std::this_thread::sleep_for(std::chrono::seconds(1)); // Adjust to the desired running time
    generator.stop();
    waveThread.join(); // Wait for the thread to finish
    generator.saveDataToFile("sine_wave_data.csv");
    std::cout << "Sine wave data has been saved to 'sine_wave_data.csv' and generation stopped.\n";
    return 0;
}