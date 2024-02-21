#!/bin/bash

export $(grep -v '^#' .env | xargs -0)

if [[ "${DEBUG}" == "True" ]]; then
    ansible-playbook -i ./scripts/ansible/debug.inventory.ini ./scripts/ansible/debug.playbook.yaml
else
    ansible-playbook -i ./scripts/ansible/inventory.ini ./scripts/ansible/playbook.yaml
fi
