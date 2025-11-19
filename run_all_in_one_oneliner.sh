#!/bin/bash

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe, ob das Python-Skript existiert
if [ ! -f "proxy/proxy_server.py" ]; then
    echo -e "${RED}❌ Fehler: proxy/proxy_server.py nicht gefunden.${NC}"
    exit 1
fi

echo -e "${YELLOW}🚀 Starte Python-Proxy (im Hintergrund)...${NC}"
# Starte den Python-Proxy-Server im Hintergrund
python3 proxy/proxy_server.py &

# Speichere die PID des Hintergrundprozesses
PROXY_PID=$!
echo -e "${GREEN}✅ Proxy gestartet mit PID: ${PROXY_PID}${NC}"

# Warte kurz, um dem Server Zeit zum Starten zu geben
sleep 2

echo -e "${YELLOW}🎵 Starte Flutter-App im Linux-Modus...${NC}"
# Starte die Flutter-App. Diese wird im Vordergrund bleiben.
flutter run -d linux

# Wenn die Flutter-App beendet wird (z.B. durch Strg+C), wird der folgende Befehl ausgeführt
echo -e "${YELLOW}🧹 Beende den Hintergrund-Proxy (PID: ${PROXY_PID})...${NC}"
kill $PROXY_PID

echo -e "${GREEN}✅ Erfolgreich beendet.${NC}"
