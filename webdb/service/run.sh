#!/bin/bash

#Get the directory of this file
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR
source venv/bin/activate
python3 server.py