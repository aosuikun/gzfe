#!/bin/bash
if [ -f "./venv/bin/activate" ]; then
    source ./venv/bin/activate
else
    python3 -m venv ./venv
    source ./venv/bin/activate
    pip install pygame
fi

python gzfe.py
