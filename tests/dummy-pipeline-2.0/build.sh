# See nxsdk/tutorials/nxcore/tutorial_23_host_snips_with_ros_integration.py for details on building shared libraries

#!/usr/bin/env bash

# Get the directory this script resides in
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# nxsdk should be available in python path
nxsdk_path=`python3 -c "import nxsdk; print(nxsdk.__path__)"`

# Update this to your actual source directory path
SKETCH_PATH="${DIR}/arduino/arduino.ino"

# Arduino compile and upload commands
COMPILE_CMD="arduino-cli compile --fqbn arduino:avr:leonardo ${SKETCH_PATH}"
UPLOAD_CMD="arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:leonardo ${SKETCH_PATH}"

# Compile and upload the Arduino sketch
echo "Compiling Arduino sketch..."
eval $COMPILE_CMD
COMPILE_RESULT=$?
if [ $COMPILE_RESULT -ne 0 ]; then
    echo "Compilation failed."
    exit 1
else
    echo "Compilation succeeded."
fi

echo "Uploading Arduino sketch..."
eval $UPLOAD_CMD
UPLOAD_RESULT=$?
if [ $UPLOAD_RESULT -ne 0 ]; then
    echo "Upload failed."
    exit 1
else
    echo "Upload succeeded."
fi

pushd $DIR

# Wipe out and re-create the build directory
rm -rf build
mkdir build
cd build

# Copy headers (nxsdkhost.h)
mkdir -p includes/nxsdk
cp -v -R ${nxsdk_path:2:-2}/include includes/nxsdk

# Run CMake/Make
echo "Building Shared Library.............."

cmake ..
make

echo "Shared Library Built................."

popd
