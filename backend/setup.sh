#!/bin/bash

echo "========================================"
echo "METIS Lab Admin Dashboard Backend Setup"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found. Starting setup..."
echo

# Make setup.py executable and run it
chmod +x setup.py
python3 setup.py

echo
echo "Setup completed!"
