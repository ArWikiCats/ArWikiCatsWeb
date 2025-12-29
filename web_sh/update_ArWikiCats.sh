#!/bin/bash
source ~/.bashrc
TOKEN="${GH_TOKEN}"

BRANCH="${1:-main}"

echo ">>> clone --branch ${BRANCH} ."

REPO_URL="https://MrIbrahem:${TOKEN}@github.com/MrIbrahem/ArWikiCats.git"
CLONE_DIR="/data/project/armake/arwikicats_x"

# Navigate to the project directory
cd /data/project/armake/ || exit

# Remove any existing clone directory
rm -rf "$CLONE_DIR"

# Clone the repository
if git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"; then
    echo "Repository cloned successfully."
else
    echo "Failed to clone the repository." >&2
    exit 1
fi

TARGET_DIR="bots/ma/ArWikiCats"
# Copy the required files to the target directory
cp -rf "$CLONE_DIR/ArWikiCats/"* "$TARGET_DIR/" -v

# Optional: Install dependencies
#"$HOME/local/bin/python3" -m pip install -r "$TARGET_DIR/requirements.in"

# Remove the "$CLONE_DIR" directory.
rm -rf "$CLONE_DIR"
