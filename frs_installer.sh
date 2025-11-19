echo "[9/20] pubspec.yaml schreiben..."

cat > pubspec.yaml << 'EOT'
name: frs_freies_radio
description: Freies Radio Stuttgart App – Live, Heute, Woche, Mediathek
publish_to: "none"

environment:
  sdk: ">=3.0.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter

  cupertino_icons: ^1.0.6
  just_audio: ^0.9.36
  http: ^1.2.0
  url_launcher: ^6.2.5
  provider: ^6.1.2

flutter:
  uses-material-design: true
  assets:
    - assets/images/
EOT


echo "[10/20] Logos kopieren..."
mkdir -p assets/images
cp ~/Bilder/Web/*.png assets/images/ 2>/dev/null || true
cp ~/Bilder/Web/*.jpg assets/images/ 2>/dev/null || true
cp ~/Bilder/Web/*.jpeg assets/images/ 2>/dev/null || true
cp ~/Bilder/Web/*.svg assets/images/ 2>/dev/null || true


echo "[11/20] flutter_launcher_icons.yaml schreiben..."

cat > flutter_launcher_icons.yaml << 'EOT'
flutter_icons:
  android: true
  ios: true
  image_path: "assets/images/Logo-FRS-99_2_RGB_WEB.png"
  remove_alpha_ios: true
EOT


echo "[12/20] flutter_native_splash.yaml schreiben..."

cat > flutter_native_splash.yaml << 'EOT'
flutter_native_splash:
  color: "#000000"
  image: assets/images/Logo-FRS-99_2_RGB_gross_WEB.png
  branding: assets/images/Logo-FRS-99_2_RGB_WEB.png
  android_12:
    image: assets/images/Logo-FRS-99_2_RGB_gross_WEB.png
    icon_background_color: "#000000"
EOT


echo "[13/20] Flutter Pakete installieren..."
flutter pub get


echo "[14/20] Icons generieren..."
flutter pub run flutter_launcher_icons


echo "[15/20] Splashscreen generieren..."
flutter pub run flutter_native_splash:create


echo "[16/20] Proxy Startskript erstellen..."

cat > start_proxy.sh << 'EOT'
#!/usr/bin/env bash
cd proxy
source venv/bin/activate
python3 proxy_server.py
EOT
chmod +x start_proxy.sh


echo "[17/20] Flutter Startskript erstellen..."

cat > start_app.sh << 'EOT'
#!/usr/bin/env bash
cd ~/development/frs_freies_radio
flutter run -d chrome
EOT
chmod +x start_app.sh


echo "[18/20] Android APK Build Skript..."

cat > build_android.sh << 'EOT'
#!/usr/bin/env bash
cd ~/development/frs_freies_radio
flutter build apk --release
EOT
chmod +x build_android.sh


echo "[19/20] Android AAB Build Skript..."

cat > build_aab.sh << 'EOT'
#!/usr/bin/env bash
cd ~/development/frs_freies_radio
flutter build appbundle --release
EOT
chmod +x build_aab.sh


echo "[20/20] Installer abgeschlossen!"
echo "==============================================="
echo " FRS ALL-IN-ONE INSTALLER v19 ERFOLGREICH!"
echo "-----------------------------------------------"
echo " Proxy starten:   ./start_proxy.sh"
echo " App starten:     ./start_app.sh"
echo " Build APK:       ./build_android.sh"
echo " Build AAB:       ./build_aab.sh"
echo "==============================================="

