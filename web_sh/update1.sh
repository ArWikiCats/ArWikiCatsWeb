#!/bin/bash

set -euo pipefail

BRANCH="${1:-main}"

echo ">>> clone --branch ${BRANCH} ."

REPO_URL="https://github.com/WikiAr/make2-web.git"

TARGET_DIR="$HOME/www/python/src"

CLONE_DIR="$HOME/srcx"

# Navigate to the project directory
cd $HOME || exit

# Remove any existing clone directory
rm -rf "$CLONE_DIR"

# Clone the repository
if git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"; then
    echo "Repository cloned successfully."
else
    echo "Failed to clone the repository." >&2
    exit 1
fi

# Copy the required files to the target directory
# cp -rf ~/srcx/src/* "$HOME/www/python/src/" -v
cp -rf "$HOME"/srcx/src/* "$TARGET_DIR/" -v || exit 1

# Remove the "$CLONE_DIR" directory.
# rm -rf "$CLONE_DIR"

# source $HOME/www/python/venv/bin/activate

if source "$HOME/www/python/venv/bin/activate"; then
    # pip install -r $HOME/www/python/src/requirements.txt
    pip install -r "$TARGET_DIR"/requirements.txt -U
    # exit 1
else
    echo "Failed to activate virtual environment" >&2
fi


# webservice python3.11 restart

# toolforge-jobs run updatex --image python3.11 --command "$HOME/web_sh/update1.sh update" --wait
