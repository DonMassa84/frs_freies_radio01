#!/usr/bin/env bash
set -e

echo ">>> Vercel Deploy gestartet"

# Prüfen ob vercel CLI installiert ist
if ! command -v vercel >/dev/null 2>&1; then
  echo "❌ Vercel CLI nicht gefunden. Installiere mit:"
  echo "   npm install -g vercel"
  exit 1
fi

# Deploy
vercel ./docs --prod --yes

echo ">>> ✔ Vercel Deploy abgeschlossen"
echo "Live: https://frs-freies-radio.vercel.app/"
