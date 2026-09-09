#!/usr/bin/env bash

conda create -n payment_service python=3.12 -y
conda activate payment_service
if [ "$CONDA_DEFAULT_ENV" != "payment_service" ]; then
    echo -e "\e[31mError: failed to activate environment 'payment_service'. Aborting.\e[0m"
    return 1
fi

python -m pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    python -m pip install -r requirements.txt
else
    echo "File requirements.txt not found."
	return 1
fi
