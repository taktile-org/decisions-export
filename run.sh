#!/bin/bash

set -eo pipefail

BASE_PATH=$(pwd)
TMP_DIR=$(mktemp -d)
TAP_VENV_PATH="$TMP_DIR/.tap_venv"
TARGET_VENV_PATH="$TMP_DIR/.target_venv"

echo "Creating environments"
./scripts/setup_env.sh "${TAP_VENV_PATH}" "${BASE_PATH}/tap_requirements.txt"
./scripts/setup_env.sh "${TARGET_VENV_PATH}" "${BASE_PATH}/target_requirements.txt"
echo "Environment created"

echo "Running sync"
"${TAP_VENV_PATH}/bin/python" "${BASE_PATH}/taktile_tap/tap.py" --config "${BASE_PATH}/tap-config.json" | "${TARGET_VENV_PATH}/bin/target-stitch" --config "${BASE_PATH}/target-config.json"
echo "Sync finished"

rm -rf "$TMP_DIR"
