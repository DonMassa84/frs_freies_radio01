#!/usr/bin/env python3
# ============================================================
#   FREIES RADIO STUTTGART
#   LIVE-SCRAPER + JSON-GENERATOR + PROXY-SERVER
#   Endpoints:
#     GET /programm   -> aktuelles Tagesprogramm
#     GET /mediathek  -> aktuelle Mediathek
# ============================================================

import os
import json
import re
import requests
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

# ------------------------------------------------------------
# Utils
# ------------------------------------------------------------
def save_json(name, data):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def safe_get(url):
    print(f"→ HTTP GET {url}")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.text

# ------------------------------------------------------------
# 1) Tagesprogramm scrapen
#    https://www.freies-radio.de/programm/tagesansicht
# ------------------------------------------------------------
def scrape_tagesprogramm():
    html = safe_get("https://www.freies-radio.de/programm/tagesansicht")
    soup = BeautifulSoup(html, "html.parser")

    entries = []

    # Jede Sendung in einem "views-row"-Block
    for row in soup.select("div.views-row"):
        title_el = row.select_one("h3")
        desc_el = row.select_one("p")

        title_raw = title_el.get_text(strip=True) if title_el else ""
        desc = desc_el.get_text(strip=True) if desc_el else ""

        # Zeit herausziehen: suche erstes HH:MM im Titel
        time_match = re.search(r"\d{2}:\d{2}(?:\s*–\s*\d{2}:\d{2})?", title_raw)
        time_str = time_match.group(0) if time_match else ""

        # "reiner" Titel = Titel ohne Zeit vorne
        title_clean = title_raw
        if time_str:
            title_clean = title_raw.replace(time_str, "").strip(" -–")

        entries.append({
            "title": title_clean,
            "time": time_str,
            "description": desc,
        })

    save_json("programm.json", entries)
    print(f"✓ Tagesprogramm: {len(entries)} Einträge")
    return entries

# ------------------------------------------------------------
# 2) Mediathek scrapen
#    https://www.freies-radio.de/mediathek
# ------------------------------------------------------------
def scrape_mediathek():
    html = safe_get("https://www.freies-radio.de/mediathek")
    soup = BeautifulSoup(html, "html.parser")

    entries = []

    for row in soup.select("div.views-row"):
        title_el = row.select_one("h3")
        title = title_el.get_text(strip=True) if title_el else ""

        text = row.get_text(" ", strip=True)

        # Datum (z.B. 12.11.2025)
        date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", text)
        date_str = date_match.group(0) if date_match else ""

        # URL
        link = row.find("a")
        url = ""
        if link and link.get("href"):
            href = link["href"]
            if href.startswith("http"):
                url = href
            elif href.startswith("/"):
                url = "https://www.freies-radio.de" + href

        entries.append({
            "title": title,
            "date": date_str,
            "url": url,
            "description": text,
        })

    save_json("mediathek.json", entries)
    print(f"✓ Mediathek: {len(entries)} Einträge")
    return entries

# ------------------------------------------------------------
# 3) Proxy-Server
# ------------------------------------------------------------
def load_raw_json(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return b"[]"
    with open(path, "rb") as f:
        return f.read()

class FRSHandler(BaseHTTPRequestHandler):
    def _headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._headers()

    def do_GET(self):
        print(f"[REQ] {self.path}")

        if self.path == "/programm":
            self.send_response(200)
            self._headers()
            self.wfile.write(load_raw_json("programm.json"))
            return

        if self.path == "/mediathek":
            self.send_response(200)
            self._headers()
            self.wfile.write(load_raw_json("mediathek.json"))
            return

        self.send_response(404)
        self._headers()
        self.wfile.write(b'{"error":"not found"}')

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    print("==========================================")
    print("  FREIES RADIO – LIVE SCRAPER + PROXY")
    print("==========================================\n")

    # 1x beim Start scrapen (Programmdaten aktualisieren)
    try:
        scrape_tagesprogramm()
    except Exception as e:
        print("Fehler beim Scrapen Tagesprogramm:", e)

    try:
        scrape_mediathek()
    except Exception as e:
        print("Fehler beim Scrapen Mediathek:", e)

    # Proxy starten
    port = 8000
    print(f"\n→ Proxy läuft auf http://localhost:{port}")
    print("   Endpoints:")
    print("     /programm")
    print("     /mediathek\n")

    httpd = HTTPServer(("", port), FRSHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    main()
