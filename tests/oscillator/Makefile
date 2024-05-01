# Makefile for SineWaveGenerator

CXX = g++
CXXFLAGS = -std=c++11 -pthread
TARGET = SineWaveGenerator
SRC = SineWaveGenerator.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
