#!/usr/bin/env bash
set -e

REPO="https://github.com/DonMassa84/frs_freies_radio.git"
DIR="$HOME/frs_freies_radio"

echo ">>> 1) Repository-Ordner prüfen"
mkdir -p "$DIR"
cd "$DIR"

echo ">>> 2) Git initialisieren (falls nötig)"
git init 2>/dev/null || true

echo ">>> 3) origin setzen"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO"

echo ">>> 4) docs-Ordner sicherstellen"
mkdir -p docs

echo ">>> 5) Dateien hinzufügen"
git add .

echo ">>> 6) Commit (falls Änderungen)"
git commit -m "all-in-one deploy from termux" || true

echo ">>> 7) main-Branch setzen"
git branch -M main

echo ">>> 8) Push nach GitHub"
git push -u origin main

echo ">>> ✔ FERTIG — Live unter:"
echo "https://donmassa84.github.io/frs_freies_radio/"
