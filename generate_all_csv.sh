#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# CSV paths generation/folder structure
python meta_data.py --root_dir $SCRIPT_DIR common

# Baseline vs. noisy
python meta_data.py --root_dir $SCRIPT_DIR baseline_noisy

# All other models
python meta_data.py --root_dir $SCRIPT_DIR others
