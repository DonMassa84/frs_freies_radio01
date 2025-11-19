#!/usr/bin/env python3
# ============================================================
#    FRS ALL-IN-ONE PROXY SERVER
#    Endpoints:
#      /programm  -> data/programm.json
#      /mediathek -> data/mediathek.json
# ============================================================

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_json(name):
    """Lädt JSON-Dateien sicher."""
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return {"error": f"{name} nicht gefunden."}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

class FRSHandler(BaseHTTPRequestHandler):

    def _headers(self):
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")  # CORS
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        print(f"[FRS] Request: {self.path}")

        if self.path == "/programm":
            self.send_response(200)
            self._headers()
            data = load_json("programm.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        if self.path == "/mediathek":
            self.send_response(200)
            self._headers()
            data = load_json("mediathek.json")
            self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        # Default 404
        self.send_response(404)
        self._headers()
        self.wfile.write(json.dumps({"error": "Endpoint nicht gefunden."}).encode("utf-8"))

def run(server_class=HTTPServer, handler_class=FRSHandler):
    port = 8000
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"\n🔥 FRS ALL-IN-ONE Proxy läuft auf http://localhost:{port}")
    print("   Endpoints:")
    print("    ➤ /programm")
    print("    ➤ /mediathek\n")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
