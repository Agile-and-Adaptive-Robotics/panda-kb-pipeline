#include <unistd.h>
#include <experimental/optional>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <vector>
#include "nxsdkhost.h"
#include <libserial/SerialPort.h>
#include <thread>
#include <chrono>
#include <iomanip> // for std::setw and std::setfill
#include <cstdlib> // for system()
#include <numeric> // for std::accumulate


//***********************CONSTANTS******************************//
#define USB_SERIAL_PORT "/dev/ttyACM0"
#define BAUD_RATE 1000000
#define START_DATA_PIPE 0xFF

LibSerial::SerialPort serial_port;


static std::string precomputed_axons_file = "precomputed_axons.txt";  // NOLINT

//********************FUNCTIONS*******************************//
void setup_serial() {
    // Open the serial port at the specified baud rate
    serial_port.Open(USB_SERIAL_PORT);
    serial_port.SetBaudRate(LibSerial::BaudRate::BAUD_1000000);
    serial_port.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
    serial_port.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
    serial_port.SetParity(LibSerial::Parity::PARITY_NONE);
    serial_port.FlushIOBuffers();
}

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
//***********************END OF FUNCTIONS************************//

//***********************HOST SNIPS******************************//
// SpikeInjector class to read and handle input axons
class SpikeInjector : public PreExecutionSequentialHostSnip {
private:
    std::string channel = "nxEncoder";
    std::vector<uint32_t> inputAxons;
    int neuron = 0;

public: //run setup code as part of pre execution constructor
    SpikeInjector() { 
        readAxonsFile(precomputed_axons_file, inputAxons, true);
        printAxons(inputAxons, "Input Axons from host");
        setup_serial(); //start serial port and settings

        std::vector<uint8_t> dataBuffer = {START_DATA_PIPE};
        serial_port.Write(dataBuffer);
        while(!serial_port.IsDataAvailable()){
            //wait for response
        }

        uint32_t test_data[1] = {0};
        writeChannel(channel.c_str(), test_data, 1);
        std::cout << "Sent initial data to start the simulation" << std::endl;
    }

    virtual void run(uint32_t timestep) override {
        std::cout << "Running host snip spike injector " << timestep << std::endl;
        int numAvailable = serial_port.GetNumberOfBytesAvailable(); 
        while(numAvailable > 0) {
            uint8_t data;
            serial_port.ReadByte(data);
            //std::cout << "Received data: " << (int)data << std::endl;
            // Cast the 8-bit data to 32-bit
            uint32_t data32 = static_cast<uint32_t>(data);
            writeChannel(channel.c_str(), &data32, 1);
            numAvailable--; 
        }
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

public:
    SpikeReceiver() {
        readAxonsFile(precomputed_axons_file, outputAxons, false);
        printAxons(outputAxons, "Output Axons from host");

    }

    virtual void run(uint32_t timestep) override {
        std::cout << "Running host snip spike receiver " << timestep << std::endl;
        while(probeChannel(channel.c_str())){
            uint32_t data32;
            readChannel(channel.c_str(), &data32, 1);
            //std::cout <<"Neuron spiked " << data <<std::endl; 
            uint8_t data8 = static_cast<uint8_t>(data32 & 0xFF);
            std::vector<uint8_t> data8_vector = {data8};
            serial_port.Write(data8_vector);
        }
    }

    virtual std::valarray<uint32_t> schedule(const std::valarray<uint32_t>& timesteps) const override {
        return timesteps;
    }
};

//***********************END OF HOST SNIPS******************************//

// Register the Snips
REGISTER_SNIP(SpikeInjector, PreExecutionSequentialHostSnip);
REGISTER_SNIP(SpikeReceiver, PostExecutionSequentialHostSnip);
