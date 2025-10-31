#!/bin/bash

echo "======================================"
echo "Seat Occupancy Detection Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    deactivate
    exit 1
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run: python3 calibrate.py  (to define seat zones)"
echo "3. Run: python3 main.py       (to start detection)"
echo ""
echo "4. When done, deactivate the environment:"
echo "   deactivate"
echo ""
echo "For help, see README.md"
