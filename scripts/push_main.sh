#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/push_main.sh "your commit message"
# If you forget a message, it will use a default.

MSG="${1:-site tweak}"

echo "→ Switching to main and syncing..."
git checkout main
git pull origin main

echo "→ Staging all changes..."
git add -A

echo "→ Committing..."
git commit -m "$MSG" || echo "No changes to commit."

echo "→ Pushing to main..."
git push origin main

echo "✓ Done! Render should redeploy from main shortly."
