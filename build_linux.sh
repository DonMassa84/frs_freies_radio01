#!/bin/bash

# Build-Skript für Freies Radio Stuttgart Linux Desktop
# Erstellt am $(date)

set -e

echo "🚀 Starte Linux Desktop Build für Freies Radio Stuttgart..."

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe ob flutter installiert ist
if ! command -v flutter &> /dev/null; then
    echo -e "${RED}❌ Flutter ist nicht installiert. Bitte installieren Sie Flutter zuerst.${NC}"
    echo "📥 Installation: [https://docs.flutter.dev/get-started/install/linux](https://docs.flutter.dev/get-started/install/linux)"
    exit 1
fi

# Wechsle in Projekt-Verzeichnis
cd "$(dirname "$0")"

echo -e "${YELLOW}📦 Installiere Abhängigkeiten...${NC}"
flutter pub get

echo -e "${YELLOW}🔍 Prüfe Linux-Toolchain...${NC}"
flutter doctor

echo -e "${YELLOW}🏗️ Baue Linux-Desktop App...${NC}"
flutter build linux --release

echo -e "${GREEN}✅ Build erfolgreich abgeschlossen!${NC}"
echo "📁 Installationsverzeichnis: ./build/linux/x64/release/"
echo ""
echo "🔧 Desktop-Integration:"
echo "   • Desktop-Datei: ./linux/data/freies_radio_stuttgart.desktop"
echo "   • Symbol-Installation: ./build/linux/x64/release/bundle/"
echo ""
echo -e "${YELLOW}🚀 Ausführen:${NC}"
echo "   ./build/linux/x64/release/bundle/freies_radio_stuttgart"
