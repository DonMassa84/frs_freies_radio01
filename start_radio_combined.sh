#!/bin/bash

# Kombiniertes Start-Skript für Freies Radio Stuttgart App und Proxy

PROJECT_DIR=$(dirname "$0")

# --- 1. Python Proxy im Hintergrund starten (Proxy Port 8000) ---
echo "📻 Starte Python Proxy Server im Hintergrund..."
# Führt das Proxy-Skript aus und hängt es in den Hintergrund (&)
( "$PROJECT_DIR/start_proxy.sh" ) & 
PROXY_PID=$! # Speichere die Prozess-ID des Proxys

# WARNUNG: Warten, bis der Proxy hochgefahren ist
echo "⏳ Warte 10 Sekunden, damit der Proxy (Web-Scraping) starten kann..."
sleep 10
echo "✅ Proxy sollte jetzt laufen."

# --- 2. Flutter App starten (im Vordergrund) ---
echo "🚀 Starte Flutter Desktop App (Linux)..."
# WICHTIG: Stellt sicher, dass das richtige Gerät (Linux) verwendet wird!
flutter run -d linux

# --- 3. Aufräumarbeiten (Wird ausgeführt, sobald flutter run beendet wird) ---
echo "🧹 Stoppe Hintergrundprozess (PID: $PROXY_PID)..."
kill $PROXY_PID
echo "✅ Proxy erfolgreich gestoppt. Auf Wiedersehen!"
