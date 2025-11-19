#!/usr/bin/env bash
set -e

echo ">>> FRS MASTER SUITE gestartet"

# 1) GitHub Auto-Deploy
if [ -f frs_auto.sh ]; then
  echo "1) GitHub Auto-Deploy..."
  bash frs_auto.sh || true
else
  echo "❌ frs_auto.sh fehlt"
fi

# 2) Vercel Deploy
if [ -f frs_vercel_deploy.sh ]; then
  echo "2) Vercel Deploy..."
  bash frs_vercel_deploy.sh || true
else
  echo "❌ frs_vercel_deploy.sh fehlt"
fi

echo ">>> ✔ MASTER SUITE abgeschlossen"
echo "GitHub: https://donmassa84.github.io/frs_freies_radio/"
echo "Vercel: https://frs-freies-radio.vercel.app/"
