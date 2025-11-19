#!/bin/bash
cd ~/development/frs_freies_radio
pkill -f proxy.py
python3 proxy.py &
flutter run -d chrome
kill %1
