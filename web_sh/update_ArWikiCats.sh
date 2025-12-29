#!/bin/bash
# toolforge-jobs run installar --image python3.11 --command "~/web_sh/update_ArWikiCats.sh" --wait

# use bash strict mode
set -euo pipefail

source ~/.bashrc

: "${GH_TOKEN:?GH_TOKEN is not set}"

BRANCH="${1:-main}"

CLONE_DIR="/data/project/armake/arwikicats_x"
REPO_URL="https://github.com/MrIbrahem/ArWikiCats.git"

# Navigate to the base working directory
cd /data/project/armake/ || exit 1

# Remove any existing clone directory
rm -rf "$CLONE_DIR"

# Create a temporary askpass helper
ASKPASS_SCRIPT="$(mktemp)"
cat > "$ASKPASS_SCRIPT" <<'EOF'
#!/bin/sh
echo "$GH_TOKEN"
EOF
chmod 700 "$ASKPASS_SCRIPT"

export GIT_ASKPASS="$ASKPASS_SCRIPT"
export GIT_USERNAME="MrIbrahem"
export GIT_TERMINAL_PROMPT=0

echo ">>> clone --branch ${BRANCH}"

git clone --branch "$BRANCH" "$REPO_URL" "$CLONE_DIR"

# Cleanup credentials helper immediately
rm -f "$ASKPASS_SCRIPT"
unset GIT_ASKPASS GIT_USERNAME GIT_TERMINAL_PROMPT


# Enter the cloned repository
cd "$CLONE_DIR" || exit 1

# Activate the virtual environment and install dependencies
source "$HOME/www/python/venv/bin/activate"

# Install the package in upgrade mode
pip install -r requirements.in -U
pip install . -U

# Optional: clean up the clone directory after installation
rm -rf "$CLONE_DIR"

# toolforge-jobs run installar --image python3.11 --command "~/web_sh/update_ArWikiCats.sh" --wait
