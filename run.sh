#!/bin/bash

echo "=========================================="
echo "Voice-Assisted Teacher Workload Manager"
echo "Setup and Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    echo "✓ $python_version"
else
    echo "✗ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Dependencies installed successfully!"
    echo ""
    echo "=========================================="
    echo "Starting application..."
    echo "=========================================="
    echo ""
    echo "The application will open in your browser."
    echo "Press Ctrl+C to stop the server."
    echo ""
    
    streamlit run app.py
else
    echo "✗ Failed to install dependencies."
    echo "Please check your internet connection and try again."
    exit 1
fi
