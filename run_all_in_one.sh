#!/bin/bash

# =================================================================
# ALL-IN-ONE START SKRIPT für Freies Radio Stuttgart
# Führt alle notwendigen Schritte in einem Befehl aus:
# 1. Installiert Flutter-Abhängigkeiten (pub get)
# 2. Startet den Python Proxy Server im Hintergrund
# 3. Startet die Flutter App
# 4. Stoppt den Proxy beim Beenden der Flutter App
# =================================================================

# Farben für die Konsole
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starte All-in-One Setup...${NC}"

# 1. Wechsle ins Projekt-Root-Verzeichnis
cd "$(dirname "$0")"

# 2. Abhängigkeiten holen (sicherstellen, dass http & just_audio installiert sind)
echo -e "${YELLOW}📦 Installiere / Aktualisiere Flutter-Abhängigkeiten (pub get)...${NC}"
flutter pub get

# Überprüfen, ob Python 3 verfügbar ist
if ! command -v python3 &> /dev/null
then
    echo -e "${RED}❌ Python 3 wurde nicht gefunden. Bitte installieren Sie Python 3.${NC}"
    exit 1
fi

# 3. Proxy Server im Hintergrund starten
PROXY_SCRIPT="proxy/proxy_server.py"
PROXY_HOST="127.0.0.1"
PROXY_PORT="8000"

echo -e "${YELLOW}🖥️ Starte Python Proxy Server auf http://${PROXY_HOST}:${PROXY_PORT}...${NC}"

# Starte den Proxy im Hintergrund und leite die Ausgabe in eine Datei um
python3 $PROXY_SCRIPT & 
PROXY_PID=$!

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Fehler beim Starten des Python Proxy Servers.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Proxy läuft im Hintergrund (PID: $PROXY_PID).${NC}"


# 4. Fange SIGINT (Strg+C) und EXIT ab, um den Proxy zu beenden
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Beende Python Proxy Server (PID: $PROXY_PID)...${NC}"
    kill $PROXY_PID 2>/dev/null # Töte den Proxy Prozess im Hintergrund
    
    # Warte kurz und erzwinge das Beenden, falls nötig
    sleep 1 
    
    if kill -0 $PROXY_PID 2>/dev/null; then
        echo -e "${RED}❌ Proxy konnte nicht regulär beendet werden. Erzwinge das Beenden...${NC}"
        kill -9 $PROXY_PID 2>/dev/null
    else
        echo -e "${GREEN}✅ Proxy erfolgreich beendet.${NC}"
    fi
    exit 0
}

# Registriere die Cleanup-Funktion für das Beenden
trap cleanup EXIT # Führe Cleanup beim Beenden des Skripts aus
trap cleanup SIGINT # Führe Cleanup bei Strg+C aus

echo -e "${BLUE}🎵 Starte Flutter App im Linux Desktop Modus...${NC}"
echo -e "${BLUE}ℹ️ Drücken Sie 'q' in der Konsole ODER Strg+C, um beide Prozesse zu beenden.${NC}"

# 5. Starte die Flutter App
flutter run -d linux

# Die Cleanup-Funktion wird automatisch durch das trap EXIT aufgerufen, 
# sobald flutter run beendet wird.
