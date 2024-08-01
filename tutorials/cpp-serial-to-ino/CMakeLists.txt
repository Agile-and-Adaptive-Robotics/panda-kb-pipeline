cmake_minimum_required(VERSION 3.10)
project(MySerialProject)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Find required packages
find_package(Threads REQUIRED)

# Find libserial include directory
find_path(LIBSERIAL_INCLUDE_DIR libserial/SerialPort.h
  HINTS /usr/local/include /usr/include
)

# Find libserial library
find_library(LIBSERIAL_LIBRARY NAMES serial
  HINTS /usr/local/lib /usr/lib
)

# Check if the paths exist
if (NOT LIBSERIAL_INCLUDE_DIR)
  message(FATAL_ERROR "libserial include directory not found")
endif()

if (NOT LIBSERIAL_LIBRARY)
  message(FATAL_ERROR "libserial library not found")
endif()

# Add the source file
add_executable(serial_app serial.cpp)

# Include directories
include_directories(${LIBSERIAL_INCLUDE_DIR})

# Link libraries
target_link_libraries(serial_app ${LIBSERIAL_LIBRARY} ${CMAKE_THREAD_LIBS_INIT})

# Pass the source directory to the executable
target_compile_definitions(serial_app PRIVATE SOURCE_DIR="${CMAKE_SOURCE_DIR}")