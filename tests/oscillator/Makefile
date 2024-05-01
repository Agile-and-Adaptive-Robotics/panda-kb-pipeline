# Makefile for SineWaveGenerator

CXX = g++
CXXFLAGS = -std=c++11 -pthread

# Targets for both versions
TARGET1 = SineWaveGenerator
SRC1 = SineWaveGenerator.cpp

TARGET2 = SineWaveGenerator_v2
SRC2 = SineWaveGenerator_v2.cpp

# Default target
all: $(TARGET1) $(TARGET2)

# Target for the first version
$(TARGET1): $(SRC1)
	$(CXX) $(CXXFLAGS) -o $(TARGET1) $(SRC1)

# Target for the second version
$(TARGET2): $(SRC2)
	$(CXX) $(CXXFLAGS) -o $(TARGET2) $(SRC2)

clean:
	rm -f $(TARGET1) $(TARGET2)
