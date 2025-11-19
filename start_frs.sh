#!/bin/bash
cd ~/development/frs_freies_radio
pkill -f proxy_mediathek_only.py
python3 proxy_mediathek_only.py &
flutter run -d chrome
kill %1
