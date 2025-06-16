#!/bin/bash

# Source the virtual environment
source ~/subtranslator/.venv/bin/activate

# Ask the user for their filename, suggesting a default path
# The -i option provides a default input string that the user can edit.
read -p "Please enter filename: " -e -i "/mnt/torrents/" FILENAME

# Run your Python script with the provided filename
python3 ~/subtranslator/subtranslator.py "$FILENAME"

# Wait for the user to press any single key before exiting
echo "" # Add a newline for better formatting
read -n 1 -s -r -p "Press any key to continue..."