#!/bin/bash

sudo apt update
sudo apt install python-is-python3 python3-pip python3.10-venv


if [ -d "Venv" ]; then
    echo "Virtual environment 'Venv' already exists, deleting..."
    rm -r Venv
fi


python3 -m venv Venv
echo "New virtual environment 'Venv' created."


if [ -d "Venv" ]; then
    source Venv/bin/activate
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        echo "Requirements installed."
    else
        echo "requirements.txt not found."
    fi
else
    echo "Virtual environment 'Venv' not found."
fi
