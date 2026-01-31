#!/bin/bash
# Setup Git Sync for Obsidian Vault
#
# This script sets up bidirectional git sync between:
# - Local Obsidian vault
# - Remote bare repository on VPS
#
# Usage:
#   ./setup_git_sync.sh <remote_url>
#
# Example:
#   ./setup_git_sync.sh user@vps.example.com:/var/git/obsidian-vault.git

set -e

REMOTE_URL="$1"

if [ -z "$REMOTE_URL" ]; then
    echo "Error: Remote URL required"
    echo "Usage: $0 <remote_url>"
    echo "Example: $0 user@vps.example.com:/var/git/vault.git"
    exit 1
fi

VAULT_PATH="../obsidian-vault"

echo "🔧 Setting up Git sync for Obsidian vault..."
echo ""

# Navigate to vault
cd "$VAULT_PATH" || exit 1

# Check if already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    git config user.email "bot@productivity.local"
    git config user.name "Productivity Bot"
else
    echo "✅ Git repository already initialized"
fi

# Add remote if not exists
if ! git remote | grep -q "origin"; then
    echo "🔗 Adding remote: $REMOTE_URL"
    git remote add origin "$REMOTE_URL"
else
    echo "✅ Remote already configured"
    git remote set-url origin "$REMOTE_URL"
fi

# Initial commit if needed
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
    echo "📝 Creating initial commit..."
    git add .
    git commit -m "Initial vault commit" || true
fi

# Push to remote
echo "⬆️  Pushing to remote..."
git push -u origin master || git push -u origin main

echo ""
echo "✅ Git sync setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up post-receive hook on VPS"
echo "2. Configure automatic sync in bot"
echo ""
echo "VPS post-receive hook should:"
echo "  - Update working directory"
echo "  - Trigger database index rebuild"
echo ""

# Create example post-receive hook
cat > post-receive.example << 'EOF'
#!/bin/bash
# Post-receive hook for Obsidian vault
# Place this in: <bare-repo>/hooks/post-receive

WORK_TREE="/path/to/working/vault"
GIT_DIR="/path/to/bare/vault.git"

# Update working directory
git --work-tree="$WORK_TREE" --git-dir="$GIT_DIR" checkout -f

# Trigger index rebuild (if bot is running)
# This could be done via API endpoint or touching a trigger file
touch "$WORK_TREE/.rebuild_index"

echo "✅ Vault updated and index rebuild triggered"
EOF

echo "Example post-receive hook saved to: post-receive.example"
