#!/bin/bash

# This script is used to start the Kapoho Bay (KB) board.
# It is assumed that the KB board is connected to the host machine via USB.
# Plug board in and run this script. Run this from terminal -> source start-kb.sh

# Source the conda configuration
source $HOME/anaconda3/etc/profile.d/conda.sh

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
