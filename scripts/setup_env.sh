#!/bin/bash

set -eo pipefail

DIRECTORY="$1"
REQUIREMENTS_FILE="$2"

echo "Creating venv in ${DIRECTORY} using ${REQUIREMENTS_FILE}"

# Create a virtual environment and install specific dependencies
python -m venv $DIRECTORY
source "${DIRECTORY}/bin/activate"
pip install -r $REQUIREMENTS_FILE
deactivate

echo "Venv is created"
