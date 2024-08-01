cmake_minimum_required(VERSION 3.10)
project(MySerialProject)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Find required packages
find_package(Threads REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBSERIAL REQUIRED libserial)

# Set up our program
add_library(host_snip SHARED host_snip.cpp)

# Set the output directory for shared libraries
set_target_properties(host_snip PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/build
)

# Include directories
target_include_directories(host_snip
    PUBLIC ${PROJECT_SOURCE_DIR}/build/includes/nxsdk/include
    PUBLIC ${LIBSERIAL_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(host_snip
    PUBLIC ${LIBSERIAL_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT}
)
