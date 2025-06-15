#!/bin/bash

# Source the virtual environment
source ~/subtranslator/.venv/bin/activate

# Ask the user for their filename, suggesting a default path
# The -i option provides a default input string that the user can edit.
read -p "Please enter filename: " -e -i "/mnt/torrents/" FILENAME

# Run your Python script with the provided filename
python3 ~/subtranslator/subtranslator.py "$FILENAME"


