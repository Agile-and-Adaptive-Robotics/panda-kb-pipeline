#!/bin/bash

# Activate the loihi Conda environment
conda activate loihi

# Set the KAPOHOBAY environment variable
export KAPOHOBAY=1

# List USB devices and their hierarchy
lsusb -t

# Remove the ftdi_sio module from the kernel (requires sudo privileges)
sudo rmmod ftdi_sio
echo "Removing ftdi driver"

# List USB devices again
lsusb -t

# Print a message
echo "checking KB connection"

# Find the nxsdk path and run the nx --test-fpio command
`python3 -c "import nxsdk; print(nxsdk.__path__[0])"`/bin/x86/kb/nx --test-fpio
