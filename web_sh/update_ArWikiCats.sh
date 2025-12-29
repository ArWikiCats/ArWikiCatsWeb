#!/bin/bash
# toolforge-jobs run installar --image python3.11 --command "~/web_sh/update_ArWikiCats.sh" --wait

# use bash strict mode
set -euo pipefail

source ~/.bashrc

# GitHub token must be provided via environment variable
TOKEN="${GH_TOKEN}"

# Branch name (default: main)
BRANCH="${1:-main}"

echo ">>> clone --branch ${BRANCH}"

REPO_URL="https://MrIbrahem:${TOKEN}@github.com/MrIbrahem/ArWikiCats.git"
CLONE_DIR="/data/project/armake/arwikicats_x"

# Navigate to the base working directory
cd /data/project/armake/ || exit 1

# Remove any existing clone directory
rm -rf "$CLONE_DIR"

# Clone the repository
if git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"; then
    echo "Repository cloned successfully."
else
    echo "Failed to clone the repository." >&2
    exit 1
fi

# Enter the cloned repository
cd "$CLONE_DIR" || exit 1

# Activate the virtual environment and install dependencies
source $HOME/www/python/venv/bin/activate

# Install the package in upgrade mode
pip install -r requirements.in -U
pip install . -U

# Optional: clean up the clone directory after installation
rm -rf "$CLONE_DIR"

# toolforge-jobs run installar --image python3.11 --command "~/web_sh/update_ArWikiCats.sh" --wait
