#!/usr/bin/env bash
# push-dist.sh — Commit and push dist/prod if there are changes.

set -euo pipefail

read -r -p "Export, commit, and push dist/prod to origin? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

.venv/bin/python3 calendar-export.py -v

cd "$(dirname "$0")/dist/prod"

if [ -z "$(git status --porcelain)" ]; then
  echo "No changes to commit."
  exit 0
fi

git add -A
git commit -m "Daily commit."
git push origin
