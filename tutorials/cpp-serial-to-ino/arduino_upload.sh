#!/bin/bash

#Path to the Arduino sketch: FIXME if needed 
SKETCH_PATH="./arduino/arduino.ino"
PORT="/dev/ttyACM0"
FQBN="arduino:avr:leonardo"

# Function to compile and upload the Arduino sketch
compile_and_upload() {
    local sketch_path=$1
    local fqbn=$2
    local port=$3
    
    compile_cmd="arduino-cli compile --fqbn $fqbn $sketch_path"
    compile_result=$(eval $compile_cmd)
    
    if [[ $? -ne 0 ]]; then
        echo "Compilation failed:"
        echo "$compile_result"
        exit 1
    else
        echo "Compilation succeeded."
    fi
    
    upload_cmd="arduino-cli upload -p $port --fqbn $fqbn $sketch_path"
    upload_result=$(eval $upload_cmd)
    
    if [[ $? -ne 0 ]]; then
        echo "Upload failed:"
        echo "$upload_result"
        exit 1
    else
        echo "Upload succeeded."
    fi
}

# Main script execution
compile_and_upload $SKETCH_PATH $FQBN $PORT

echo "Arduino sketch compiled and uploaded successfully."
