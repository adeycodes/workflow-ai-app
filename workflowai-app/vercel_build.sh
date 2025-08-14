#!/bin/bash
# Install Python dependencies
pip install -r backend/requirements.txt

# Create necessary directories
mkdir -p /var/task/backend

# Copy backend files
cp -r backend/* /var/task/backend/

# Set Python path
export PYTHONPATH="/var/task/backend:/var/task"

# Make the script executable
chmod +x /var/task/backend/main.py
