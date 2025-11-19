#!/usr/bin/env bash
set -e

echo ">>> GitHub Auto-Deploy gestartet"

# Git korrekt setzen
git config --global user.name "DonMassa84"
git config --global user.email "massa.daniel@proton.me"

# Add
git add -A

# Commit
git commit -m "auto-deploy: $(date '+%Y-%m-%d %H:%M:%S')" || echo "Nichts zu committen"

# Push
git branch -M main
git push origin main

echo ">>> ✔ GitHub Deploy abgeschlossen"
echo "Live: https://donmassa84.github.io/frs_freies_radio/"
