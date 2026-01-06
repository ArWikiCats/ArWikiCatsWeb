#!/bin/bash

# use bash strict mode
set -euo pipefail

# Activate the virtual environment and install dependencies
source $HOME/www/python/venv/bin/activate

pip install pip -U
pip install -r $HOME/www/python/src/requirements.txt -U

# toolforge-jobs run pipup --image python3.11 --command ~/web_sh/pip.sh --wait
