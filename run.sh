#!/bin/bash

set -euo pipefail

BASE_PATH=$(pwd)
TMP_DIR=$(mktemp -d)
TAP_VENV_PATH="$TMP_DIR/.tap_venv"
TARGET_VENV_PATH="$TMP_DIR/.target_venv"

START_TIME="${TAP_START_TIME:-}"
END_TIME="${TAP_END_TIME:-}"

echo "Creating environments"
"${BASE_PATH}/scripts/setup_env.sh" "${TAP_VENV_PATH}" "${BASE_PATH}/tap_requirements.txt"
"${BASE_PATH}/scripts/setup_env.sh" "${TARGET_VENV_PATH}" "${BASE_PATH}/target_requirements.txt"
echo "Environment created"

echo "Updating tap config"
"${TAP_VENV_PATH}/bin/python" "${BASE_PATH}/scripts/setup_time_filters.py" --start-time "$START_TIME" --end-time "$END_TIME"

echo "Running sync"
"${TAP_VENV_PATH}/bin/python" "${BASE_PATH}/taktile_tap/tap.py" --config "${BASE_PATH}/tap-config.json" | "${TARGET_VENV_PATH}/bin/target-stitch" --config "${BASE_PATH}/target-config.json"
echo "Sync finished"

rm -rf "$TMP_DIR"
