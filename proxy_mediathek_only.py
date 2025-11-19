#!/usr/bin/env python3
import requests, json, re
from bs4 import BeautifulSoup
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/mediathek/today':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            r = requests.get("https://www.freies-radio.de/mediathek", timeout=10)
            s = BeautifulSoup(r.content, 'html.parser')
            b = []
            for block in s.find_all('div', class_='views-row'):
                t = block.find_all('time')
                if len(t) < 2: continue
                st = t[0].get('datetime', '')
                m = re.search(r'T(\d{2}):(\d{2})', st)
                hk = m.group(1) + m.group(2) if m else "0000"
                bl = block.find('a', class_='use-ajax')
                bn = bl.text.strip() if bl else "Unbekannt"
                ts = block.find('span', class_='text-base font-bold')
                et = ts.text.strip() if ts else ""
                td = block.find('div', class_='views-field-field-teaser')
                te = td.text.strip() if td else ""
                dk = datetime.now().strftime("%Y%m%d")
                mu = f"https://www.freies-radio.de/systemfiles/mediathek/{dk}-{hk}.mp3"
                b.append({"date": dk, "start_time": st, "end_time": t[1].get('datetime', ''), "broadcast_name": bn, "episode_title": et, "teaser": te, "mp3_url": mu})
            self.wfile.write(json.dumps({"broadcasts": b}).encode())
        else:
            self.send_response(404)
            self.end_headers()

HTTPServer(("", 8000), H).serve_forever()
