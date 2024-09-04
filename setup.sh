#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to print error messages
error() {
    echo "Error: $1" >&2
    exit 1
}

# Check Anaconda installation
echo "Checking Anaconda installation..."
conda --version || error "Anaconda is not installed or not in PATH"

# Check Conda environment
echo "Checking Conda environment..."
conda activate loihi || error "Failed to activate loihi environment"

# Check Python version
echo "Checking Python version..."
python --version | grep "3.7" || error "Python version is not 3.7"

# Check NxSDK installation
echo "Checking NxSDK installation..."
python -c "import nxsdk; print(nxsdk.__version__)" || error "NxSDK is not installed"

# Check udev rules
echo "Checking udev rules..."
ls /etc/udev/rules.d/99-kapoho_bay.rules || error "Kapoho Bay udev rules not found"

# Check libgrpc installation
echo "Checking libgrpc installation..."
dpkg -l | grep libgrpc || error "libgrpc packages not found"

echo "All checks passed successfully!"