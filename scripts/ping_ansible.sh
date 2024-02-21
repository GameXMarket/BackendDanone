#!/bin/bash

export $(grep -v '^#' .env | xargs -0)

if [[ "${DEBUG}" == "True" ]]; then
    ansible all -m ping -i ./scripts/ansible/debug.inventory.ini
else
    ansible all -m ping -i ./scripts/ansible/inventory.ini
fi
