#!/data/data/com.termux/files/usr/bin/bash
set -e

REPO="$HOME/frs_freies_radio"

echo ">>> FRS ALL-IN-ONE gestartet"

# 1) Ins Repo wechseln
cd "$REPO" || { echo "❌ Repo nicht gefunden: $REPO"; exit 1; }

# 2) README erzeugen
echo ">>> README aktualisieren"
cat > README.md <<'EOF'
# Freies Radio Stuttgart – Progressive Web App (PWA)

Live-Stream, Programm, Mediathek. Mobile-optimiert, PWA-fähig, GitHub Pages & Vercel Deploy.

---

## 🚀 Features
- Live-Stream Player (Proxy + Fallbacks + Range)
- Programm via Worker /api
- Mediathek
- Dark/Light Theme
- PWA Install (Service Worker, Manifest)
- Offline-Fallback
- GitHub Pages Deployment
- Vercel Deployment

---

## 🌐 Live Deployments
GitHub Pages: https://donmassa84.github.io/frs_freies_radio/
Vercel: https://frs-freies-radio.vercel.app/

---

## 🧪 Lokal testen
cd docs
python3 -m http.server 8080
EOF

# 3) Git Commit + Push
echo ">>> Git commit + push"
git add .
git commit -m "auto: all-in-one update" || true
git push -u origin main

# 4) Vercel Deploy
echo ">>> Vercel Deployment"
vercel --prod || echo "⚠ Vercel Deployment fehlgeschlagen"

echo ">>> ✔ FERTIG"
echo "GitHub:  https://donmassa84.github.io/frs_freies_radio/"
echo "Vercel:  https://frs-freies-radio.vercel.app/"
