//******************************INCLUDES***************************************//
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
#include "include/Logging.h"
//******************************CONSTANTS***************************************//
#define USB_SERIAL_PORT "/dev/ttyACM0"
#define BAUD_RATE 1000000
#define START_DATA_PIPE 0xFF

LibSerial::SerialPort serial_port;


static std::string precomputed_axons_file = "precomputed_axons.txt";  // NOLINT

//****************************FUNCTIONS***************************************//
// Set up the serial port with specified settings
void setup_serial() {
    try {
        serial_port.Open(USB_SERIAL_PORT);
        serial_port.SetBaudRate(LibSerial::BaudRate::BAUD_1000000);
        serial_port.SetCharacterSize(LibSerial::CharacterSize::CHAR_SIZE_8);
        serial_port.SetStopBits(LibSerial::StopBits::STOP_BITS_1);
        serial_port.SetParity(LibSerial::Parity::PARITY_NONE);
        serial_port.FlushIOBuffers();
     } catch (const LibSerial::OpenFailed&) {
        LOG_ERROR("Failed to open serial port");
        exit(EXIT_FAILURE);
    }
}
// Read generated axon file from superhost (i.e. main.py)
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


// Print axons to console, used for debugging....
void printAxons(const std::vector<uint32_t>& axons, const std::string& label) {
    std::cout << label << ": ";
    for (const auto& axon : axons) {
        std::cout << axon << " ";
    }
    std::cout << std::endl;
}

//Reads all data currently available on the serial port [HOST SNIP <--- TEENSY]
void ReadFromTeensy(int numBytes, std::string channel){
    for(int i = 0; i < numBytes; i++){
        uint8_t data;
        serial_port.ReadByte(data);
        LOG_INFO("Received data from Teensy: " << (int)data);
        uint32_t data32 = static_cast<uint32_t>(data);
        writeChannel(channel.c_str(), &data32, 1);
    }
}

//Spikes are on receive channel, read axon IDs and send to Teensy [HOST SNIP ---> TEENSY]
void WriteToTeensy(std::string channel){
    uint32_t data32;
    readChannel(channel.c_str(), &data32, 1);
    LOG_INFO("Sending data to Teensy: " << data32);
    uint8_t data8 = static_cast<uint8_t>(data32 & 0xFF);
    std::vector<uint8_t> data8_vector = {data8};
    serial_port.Write(data8_vector);
}

//*****************************HOST SNIPS*****************************************//
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
    }

    virtual void run(uint32_t timestep) override {
        LOG_INFO("Running host snip spike injector " << timestep);
        int numAvailable = serial_port.GetNumberOfBytesAvailable(); 
        if(numAvailable > 0){
            ReadFromTeensy(numAvailable, channel);
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
        LOG_INFO("Running host snip spike receiver " << timestep);
        while(probeChannel(channel.c_str())){
            WriteToTeensy(channel);
        }
    }

    virtual std::valarray<uint32_t> schedule(const std::valarray<uint32_t>& timesteps) const override {
        return timesteps;
    }
};

// Register the Snips
REGISTER_SNIP(SpikeInjector, PreExecutionSequentialHostSnip);
REGISTER_SNIP(SpikeReceiver, PostExecutionSequentialHostSnip);


//******************************END OF HOST SNIPS******************************//