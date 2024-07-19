#include <unistd.h>
#include <experimental/optional>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#include "nxsdkhost.h"

static std::string precomputed_axons_file = "precomputed_axons.txt";  // NOLINT

void readAxonsFile(const std::string& file, std::vector<uint32_t>& axons, bool isInput) {
    std::ifstream infile(file);
    if (!infile.is_open()) {
        std::cerr << "Unable to open file: " << file << std::endl;
        return;
    }

    std::string line;
    bool isSection = false;

    while (std::getline(infile, line)) {
        if ((line == "Input Axons:" && isInput) || (line == "Output Axons:" && !isInput)) {
            isSection = true;
            continue;
        }
        if ((line == "Input Axons:" && !isInput) || (line == "Output Axons:" && isInput)) {
            isSection = false;
            continue;
        }

        if (isSection && !line.empty()) {
            axons.push_back(std::stoi(line));
        }
    }

    infile.close();
}

void printAxons(const std::vector<uint32_t>& axons, const std::string& label) {
    std::cout << label << ": ";
    for (const auto& axon : axons) {
        std::cout << axon << " ";
    }
    std::cout << std::endl;
}


// SpikeInjector class to read and handle input axons
class SpikeInjector : public PreExecutionSequentialHostSnip {
private:
    std::string channel = "nxEncoder";
    std::vector<uint32_t> inputAxons;
    int neuron = 0;

public:
    SpikeInjector() {
        readAxonsFile(precomputed_axons_file, inputAxons, true);
        printAxons(inputAxons, "Input Axons from host");
    }

    virtual void run(uint32_t timestep) override {
        //std::cout << "Running host snip spike injector " << timestep << std::endl;
        writeChannel(channel.c_str(), &inputAxons[neuron], 1);
        neuron = 1 - neuron; 
    }

    //runs on every other timestep
    virtual std::valarray<uint32_t> schedule(const std::valarray<uint32_t>& timesteps) const override {
        return timesteps;
    }
};

// SpikeReceiver class to read and handle output axons
class SpikeReceiver : public PostExecutionSequentialHostSnip {
private:
    std::string channel = "nxDecoder";
    std::vector<uint32_t> outputAxons;
    int data;

public:
    SpikeReceiver() {
        readAxonsFile(precomputed_axons_file, outputAxons, false);
        printAxons(outputAxons, "Output Axons from host");
    }

    virtual void run(uint32_t timestep) override {
        if(probeChannel(channel.c_str())){
            readChannel(channel.c_str(), &data, 1);
            //std::cout <<"Neuron spiked " << data <<std::endl; 
        }
        //do nothing if channel is empty
    }

    virtual std::valarray<uint32_t> schedule(const std::valarray<uint32_t>& timesteps) const override {
        return timesteps;
    }
};

// Register the Snips
REGISTER_SNIP(SpikeInjector, PreExecutionSequentialHostSnip);
REGISTER_SNIP(SpikeReceiver, PostExecutionSequentialHostSnip);
