#!/bin/bash

# Define the path to check for the volume
LOCAL_DAPLA_CLI_DIR="/mnt/dapla-cli"

# Check if the volume is present
if [ -d "$LOCAL_DAPLA_CLI_DIR" ]; then
    echo "Local source found at $LOCAL_DAPLA_CLI_DIR. Installing dapla-cli in editable mode..."
    pipx install --editable "$LOCAL_DAPLA_CLI_DIR"
else
    echo "Installing dapla-cli from from PyPI..."
    pipx install dapla-cli
fi

# Start a shell
/bin/bash
