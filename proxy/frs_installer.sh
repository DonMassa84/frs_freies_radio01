#!/usr/bin/env bash
set -e

echo "=== FRS ALL-IN-ONE INSTALLER v19 START ==="

PROJECT=~/development/frs_freies_radio

echo "[1/20] Projekt erstellen..."
mkdir -p $PROJECT
cd $PROJECT

echo "[2/20] Flutter-Projekt initialisieren..."
flutter create frs_freies_radio_temp >/dev/null 2>&1 || true
cp -r frs_freies_radio_temp/* .
rm -rf frs_freies_radio_temp

echo "[3/20] Ordnerstruktur anlegen..."
mkdir -p lib/screens
mkdir -p lib/services
mkdir -p assets/images
mkdir -p proxy

echo "[4/20] Proxy vorbereiten..."
cat > proxy/requirements.txt << 'EOT'
playwright
beautifulsoup4
requests
lxml
EOT

cat > proxy/proxy_server.py << 'EOT'
# --- DIESER BLOCK WIRD IN NACHRICHT 2 WEITERGEFÜHRT ---
EOT

echo "[5/20] Proxy Python-Code schreiben..."

cat > proxy/proxy_server.py << 'EOT'
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json, datetime

HOST = "localhost"
PORT = 8000

# =============================================================================
# Hilfsfunktion: HTML mit Playwright (Firefox)
# =============================================================================
def fetch_html(url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = page.content()
        browser.close()
        return html

# =============================================================================
# MP3 / Audio-Extraktor
# =============================================================================
def extract_mp3_links(html):
    soup = BeautifulSoup(html, "lxml")
    links = []

    for audio in soup.find_all("audio"):
        if audio.get("src"):
            links.append(audio["src"])

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().endswith(".mp3") or ".m3u" in href:
            links.append(href)

    return list(dict.fromkeys(links))


# =============================================================================
# SCRAPER: Heute
# =============================================================================
def scrape_today():
    url = "https://www.freies-radio.de/programm/tagesansicht"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for row in soup.select(".views-row"):
        title = row.get_text(" ", strip=True)
        a = row.find("a")
        link = None
        if a:
            link = a.get("href")
            if link and not link.startswith("http"):
                link = "https://www.freies-radio.de" + link
        items.append({"title": title, "link": link})

    return items


# =============================================================================
# SCRAPER: Woche (Mo–So)
# =============================================================================
def scrape_week():
    today = datetime.date.today()
    week_data = []

    for offset in range(7):
        day = today + datetime.timedelta(days=offset)
        day_string = day.strftime("%Y-%m-%d")

        url = f"https://www.freies-radio.de/programm/tagesansicht?day={day_string}"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        day_items = []
        for row in soup.select(".views-row"):
            title = row.get_text(" ", strip=True)
            a = row.find("a")
            link = None
            if a:
                link = a.get("href")
                if link and not link.startswith("http"):
                    link = "https://www.freies-radio.de" + link

            day_items.append({"title": title, "link": link})

        week_data.append({
            "date": day_string,
            "items": day_items
        })

    return week_data


# =============================================================================
# SCRAPER: Mediathek
# =============================================================================
def scrape_mediathek():
    url = "https://www.freies-radio.de/mediathek"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for row in soup.select(".views-row"):
        title = row.get_text(" ", strip=True)
        a = row.find("a")
        link = None
        if a:
            link = a["href"]
            if link and not link.startswith("http"):
                link = "https://www.freies-radio.de" + link
        items.append({
            "title": title,
            "url": link
        })

    return items


# =============================================================================
# SCRAPER: Detailseite
# =============================================================================
def scrape_detail(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    desc = soup.get_text(" ", strip=True)
    mp3 = extract_mp3_links(html)

    return {
        "url": url,
        "description": desc[:4000],
        "audios": mp3
    }


# =============================================================================
# HTTP API
# =============================================================================
class Handler(BaseHTTPRequestHandler):
    def _json(self, obj):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/schedule/today":
            return self._json(scrape_today())

        if parsed.path == "/schedule/week":
            return self._json(scrape_week())

        if parsed.path == "/mediathek":
            return self._json(scrape_mediathek())

        if parsed.path == "/item":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [""])[0]
            return self._json(scrape_detail(url))

        self.send_error(404, "Unknown endpoint")


# =============================================================================
# START SERVER
# =============================================================================
print(f"FRS Proxy läuft auf http://{HOST}:{PORT}")
HTTPServer((HOST, PORT), Handler).serve_forever()
EOT

echo "[6/20] Python venv installieren..."
cd proxy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
venv/bin/playwright install firefox
deactivate
cd ..

echo "[7/20] Schreibe Flutter Services..."

mkdir -p lib/services

# ---------------------------------------------------------------------------
# schedule_service.dart
# ---------------------------------------------------------------------------
cat > lib/services/schedule_service.dart << 'EOT'
import 'dart:convert';
import 'package:http/http.dart' as http;

class ScheduleService {
  static const String _base = "http://localhost:8000";

  /// HEUTE
  static Future<List<dynamic>> loadToday() async {
    try {
      final res = await http.get(Uri.parse("$_base/schedule/today"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("ScheduleService ERROR (today): $e");
      return [];
    }
  }

  /// WOCHE (Mo–So)
  static Future<List<dynamic>> loadWeek() async {
    try {
      final res = await http.get(Uri.parse("$_base/schedule/week"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("ScheduleService ERROR (week): $e");
      return [];
    }
  }
}
EOT


# ---------------------------------------------------------------------------
# mediathek_service.dart
# ---------------------------------------------------------------------------
cat > lib/services/mediathek_service.dart << 'EOT'
import 'dart:convert';
import 'package:http/http.dart' as http;

class MediathekService {
  static const String _base = "http://localhost:8000";

  /// LISTE
  static Future<List<dynamic>> loadItems() async {
    try {
      final res = await http.get(Uri.parse("$_base/mediathek"));
      if (res.statusCode != 200) return [];
      return json.decode(res.body) as List<dynamic>;
    } catch (e) {
      print("MediathekService ERROR (list): $e");
      return [];
    }
  }

  /// DETAIL
  static Future<Map<String, dynamic>> loadDetail(String url) async {
    try {
      final uri = Uri.parse("$_base/item").replace(queryParameters: {"url": url});
      final res = await http.get(uri);
      if (res.statusCode != 200) return {};
      return json.decode(res.body) as Map<String, dynamic>;
    } catch (e) {
      print("MediathekService ERROR (detail): $e");
      return {};
    }
  }
}
EOT


# ---------------------------------------------------------------------------
# player_service.dart (Live Stream Player)
# ---------------------------------------------------------------------------
cat > lib/services/player_service.dart << 'EOT'
import 'package:just_audio/just_audio.dart';

class PlayerService {
  static final PlayerService _instance = PlayerService._internal();
  factory PlayerService() => _instance;

  PlayerService._internal();

  final AudioPlayer _player = AudioPlayer();
  bool isPlaying = false;

  static const String streamUrl = 
    "http://streaming.fueralle.org:8000/frs-hi.mp3";

  AudioPlayer get player => _player;

  Future<void> init() async {
    try {
      await _player.setUrl(streamUrl);
      _player.playerStateStream.listen((state) {
        isPlaying = state.playing;
      });
    } catch (e) {
      print("PlayerService init ERROR: $e");
    }
  }

  Future<void> play() async {
    try {
      await _player.play();
    } catch (e) {
      print("PlayerService play ERROR: $e");
      await Future.delayed(Duration(seconds: 2));
      await _player.setUrl(streamUrl);
      await _player.play();
    }
  }

  Future<void> pause() async {
    try {
      await _player.pause();
    } catch (e) {
      print("PlayerService pause ERROR: $e");
    }
  }

  Future<void> stop() async {
    try {
      await _player.stop();
    } catch (e) {}
  }

  Future<void> dispose() async {
    await _player.dispose();
  }
}
EOT

echo "[8/20] Schreibe Flutter UI..."

mkdir -p lib/screens

# ---------------------------------------------------------------------------
# main.dart
# ---------------------------------------------------------------------------
cat > lib/main.dart << 'EOT'
import 'package:flutter/material.dart';
import 'services/player_service.dart';
import 'screens/live_screen.dart';
import 'screens/today_screen.dart';
import 'screens/week_screen.dart';
import 'screens/mediathek_screen.dart';
import 'screens/mediathek_detail.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await PlayerService().init();
  runApp(const FRSApp());
}

class FRSApp extends StatelessWidget {
  const FRSApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Freies Radio Stuttgart",
      theme: ThemeData(
        primaryColor: Colors.orange,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: Colors.black,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.black,
          foregroundColor: Colors.white,
        ),
      ),
      home: const MainTabs(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class MainTabs extends StatefulWidget {
  const MainTabs({super.key});

  @override
  State<MainTabs> createState() => _MainTabsState();
}

class _MainTabsState extends State<MainTabs> {
  int index = 0;

  final screens = const [
    LiveScreen(),
    TodayScreen(),
    WeekScreen(),
    MediathekScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: screens[index],
      bottomNavigationBar: NavigationBar(
        height: 70,
        selectedIndex: index,
        backgroundColor: Colors.black,
        indicatorColor: Colors.orange,
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.radio), label: "Live"),
          NavigationDestination(
              icon: Icon(Icons.today), label: "Heute"),
          NavigationDestination(
              icon: Icon(Icons.calendar_month), label: "Woche"),
          NavigationDestination(
              icon: Icon(Icons.library_music), label: "Mediathek"),
        ],
        onDestinationSelected: (i) => setState(() => index = i),
      ),
    );
  }
}
EOT


# ---------------------------------------------------------------------------
# Live Screen
# ---------------------------------------------------------------------------
cat > lib/screens/live_screen.dart << 'EOT'
import 'package:flutter/material.dart';
import '../services/player_service.dart';

class LiveScreen extends StatefulWidget {
  const LiveScreen({super.key});

  @override
  State<LiveScreen> createState() => _LiveScreenState();
}

class _LiveScreenState extends State<LiveScreen> {
  final player = PlayerService();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Live Radio")),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.radio, size: 120, color: Colors.orange),
            const SizedBox(height: 20),
            Text(
              player.isPlaying ? "Live läuft…" : "Bereit zum Abspielen",
              style: const TextStyle(color: Colors.white, fontSize: 18),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
                foregroundColor: Colors.black,
                padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 15),
              ),
              onPressed: () {
                if (player.isPlaying) {
                  player.pause();
                } else {
                  player.play();
                }
                setState(() {});
              },
              child: Text(player.isPlaying ? "Pause" : "Play"),
            )
          ],
        ),
      ),
    );
  }
}
EOT


# ---------------------------------------------------------------------------
# Today Screen
# ---------------------------------------------------------------------------
cat > lib/screens/today_screen.dart << 'EOT'
import 'package:flutter/material.dart';
import '../services/schedule_service.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});

  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  List items = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await ScheduleService.loadToday();
    setState(() {
      items = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Heute")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: items.length,
              itemBuilder: (_, i) {
                final e = items[i];
                return ListTile(
                  title: Text(e["title"] ?? "-", style: const TextStyle(color: Colors.white)),
                  subtitle: e["link"] != null
                      ? Text(e["link"], style: const TextStyle(color: Colors.grey))
                      : null,
                );
              }),
    );
  }
}
EOT


# ---------------------------------------------------------------------------
# Week Screen (Mo–So)
# ---------------------------------------------------------------------------
cat > lib/screens/week_screen.dart << 'EOT'
import 'package:flutter/material.dart';
import '../services/schedule_service.dart';

class WeekScreen extends StatefulWidget {
  const WeekScreen({super.key});

  @override
  State<WeekScreen> createState() => _WeekScreenState();
}

class _WeekScreenState extends State<WeekScreen> {
  List days = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await ScheduleService.loadWeek();
    setState(() {
      days = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Woche")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: days.length,
              itemBuilder: (_, i) {
                final d = days[i];
                return ExpansionTile(
                  title: Text(
                    d["date"],
                    style: const TextStyle(color: Colors.orange, fontSize: 18),
                  ),
                  children: [
                    for (final e in d["items"])
                      ListTile(
                        title: Text(e["title"], style: const TextStyle(color: Colors.white)),
                      )
                  ],
                );
              }),
    );
  }
}
EOT


# ---------------------------------------------------------------------------
# Mediathek Screen
# ---------------------------------------------------------------------------
cat > lib/screens/mediathek_screen.dart << 'EOT'
import 'package:flutter/material.dart';
import '../services/mediathek_service.dart';
import 'mediathek_detail.dart';

class MediathekScreen extends StatefulWidget {
  const MediathekScreen({super.key});

  @override
  State<MediathekScreen> createState() => _MediathekScreenState();
}

class _MediathekScreenState extends State<MediathekScreen> {
  List items = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final data = await MediathekService.loadItems();
    setState(() {
      items = data;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mediathek")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : ListView.builder(
              itemCount: items.length,
              itemBuilder: (_, i) {
                final e = items[i];
                return ListTile(
                  title: Text(e["title"], style: const TextStyle(color: Colors.white)),
                  onTap: () {
                    if (e["url"] != null) {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => MediathekDetailScreen(url: e["url"]),
                        ),
                      );
                    }
                  },
                );
              }),
    );
  }
}
EOT


# ---------------------------------------------------------------------------
# Mediathek Detail Screen
# ---------------------------------------------------------------------------
cat > lib/screens/mediathek_detail.dart << 'EOT'
import 'package:flutter/material.dart';
import '../services/mediathek_service.dart';
import 'package:url_launcher/url_launcher.dart';

class MediathekDetailScreen extends StatefulWidget {
  final String url;
  const MediathekDetailScreen({super.key, required this.url});

  @override
  State<MediathekDetailScreen> createState() => _MediathekDetailScreenState();
}

class _MediathekDetailScreenState extends State<MediathekDetailScreen> {
  Map data = {};
  bool loading = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final d = await MediathekService.loadDetail(widget.url);
    setState(() {
      data = d;
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Details")),
      body: loading
          ? const Center(child: CircularProgressIndicator(color: Colors.orange))
          : Padding(
              padding: const EdgeInsets.all(16.0),
              child: ListView(
                children: [
                  Text(
                    data["description"] ?? "",
                    style: const TextStyle(color: Colors.white),
                  ),
                  const SizedBox(height: 20),
                  const Text("Audio:", style: TextStyle(color: Colors.orange, fontSize: 20)),
                  const SizedBox(height: 10),
                  for (final a in data["audios"] ?? [])
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.orange,
                        foregroundColor: Colors.black,
                      ),
                      onPressed: () => launchUrl(Uri.parse(a), mode: LaunchMode.externalApplication),
                      child: Text("Play $a"),
                    )
                ],
              ),
            ),
    );
  }
}
EOT

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

