#!/bin/bash
set -e
echo "Installing system dependencies..."
apt-get update -y
apt-get install -y ffmpeg
echo "ffmpeg installed successfully"
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "All dependencies installed"
