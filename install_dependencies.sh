#!/bin/bash

# Create a virtual environment named 'myenv'
python3 -m venv myenv

# Activate the virtual environment
source myenv/bin/activate

# Install dependencies from the 'dependencies.txt' file
pip install -r dependencies.txt

# Deactivate the virtual environment
deactivate
