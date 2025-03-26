#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create directories if they don't exist
mkdir -p api

# Ensure all static assets are properly set up
cp -r static api/
cp -r templates api/

# Make sure Python can find the modules
touch api/__init__.py

echo "Build completed successfully" 