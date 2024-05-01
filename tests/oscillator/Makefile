# Makefile for SineWaveGenerator

CXX = g++
CXXFLAGS = -std=c++11 -pthread

# Targets for both versions
TARGET = SineWaveGenerator
SRC = SineWaveGenerator.cpp

# Default target
all: $(TARGET) 

# Target for the first version
$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
