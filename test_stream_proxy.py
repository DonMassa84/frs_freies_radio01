#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

AUDIO_URL = "https://stream.freies-radio.de/live/mp3"

class Handler(BaseHTTPRequestHandler):
    def _stream_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Accept-Ranges", "bytes")

    def do_HEAD(self):
        if self.path == "/stream":
            self.send_response(200)
            self._stream_headers()
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self._stream_headers()
            self.end_headers()
            with requests.get(AUDIO_URL, stream=True) as r:
                for chunk in r.iter_content(chunk_size=4096):
                    if chunk:
                        self.wfile.write(chunk)
            return

        self.send_response(404)
        self.end_headers()

print("TEST STREAM PROXY läuft: http://localhost:8001/stream")
HTTPServer(("", 8001), Handler).serve_forever()
