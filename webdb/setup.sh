#!/bin/bash

# This file is part of the WebDB project.
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root / sudo" 1>&2
    exit 1
fi

pysetup() {
    #Create a virtual environment
    python3 -m venv venv
    #Activate the virtual environment
    source venv/bin/activate
    #Install the required packages
    pip3 install -r requirements.txt
    #Deactivate the virtual environment
    deactivate
}
