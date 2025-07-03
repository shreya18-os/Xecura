#!/bin/bash

# Create data directory if it doesn't exist
mkdir -p data

# Set directory permissions
chmod 777 data

# Create database file with proper permissions if it doesn't exist
touch data/data.db
chmod 666 data/data.db

echo "Permissions set up successfully!"
echo "data directory: $(ls -ld data)"
echo "database file: $(ls -l data/data.db)"
