#!/usr/bin/env python3
import json, logging, requests, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

HOST = "127.0.0.1"
PORT = 8000
BASE = "https://www.freies-radio.de"

cache = {"programm": [], "mediathek": [], "stream": "https://streaming.fueralle.org/frs-hi.mp3"}

# ---------------- HELFER ----------------

def cors(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "*")

def update_data():
    while True:
        try:
            logging.info("[SCRAPER] PROGRAMM → /programm/tagesansicht")
            P = BeautifulSoup(requests.get(f"{BASE}/programm/tagesansicht").text, "html.parser")
            programm = []
            for b in P.select(".calendar-day .broadcast"):
                t = b.select_one("div")
                h = b.select_one("h2 a")
                d = b.select_one("p:not(.font-bold)")
                programm.append({
                    "time": t.get_text(strip=True) if t else "",
                    "title": h.get_text(strip=True) if h else "",
                    "description": d.get_text(strip=True) if d else "",
                    "link": BASE + h["href"] if h and h.get("href","").startswith("/") else (h["href"] if h else "")
                })
            cache["programm"] = programm

            logging.info("[SCRAPER] MEDIATHEK → /mediathek")
            M = BeautifulSoup(requests.get(f"{BASE}/mediathek").text, "html.parser")
            mediathek = []
            for b in M.select(".views-row"):
                h = b.select_one("h2 a")
                d = b.select_one(".date")
                p = b.select_one("p")
                a = b.select_one("audio source")
                mediathek.append({
                    "title": h.get_text(strip=True) if h else "",
                    "date": d.get_text(strip=True) if d else "",
                    "teaser": p.get_text(strip=True) if p else "",
                    "link": BASE + h["href"] if h and h.get("href","").startswith("/") else (h["href"] if h else ""),
                    "mp3": a.get("src","") if a else ""
                })
            cache["mediathek"] = mediathek

        except Exception as e:
            logging.error("[SCRAPER ERROR] %s", e)

        time.sleep(60)

# ---------------- HTTP HANDLER ----------------

class Handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        cors(self)
        self.end_headers()

    def do_GET(self):
        logging.info("▶ %s", self.path)

        if self.path == "/programm":
            self.send_response(200)
            cors(self)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return self.wfile.write(json.dumps(cache["programm"]).encode())

        if self.path == "/mediathek":
            self.send_response(200)
            cors(self)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return self.wfile.write(json.dumps(cache["mediathek"]).encode())

        if self.path == "/stream":
            self.send_response(200)
            cors(self)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            return self.wfile.write(json.dumps({"stream": cache["stream"]}).encode())

        self.send_response(404)
        cors(self)
        self.end_headers()
        self.wfile.write(b'{"error":"unknown endpoint"}')

# ---------------- START ----------------

threading.Thread(target=update_data, daemon=True).start()

logging.info(f"🚀 Proxy v8 läuft auf http://{HOST}:{PORT}")
HTTPServer((HOST, PORT), Handler).serve_forever()
