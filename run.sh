#!/bin/sh
cd $(dirname $0)

# Create virtual environment if it doesn't exist
if [ ! -d "viam-env" ]; then
    python3 -m venv viam-env
    viam-env/bin/pip install -r requirements.txt
fi

# Activate virtual environment and run the module
exec viam-env/bin/python3 -m src $@
