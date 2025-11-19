from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json, time, datetime, re

HOST = "localhost"
PORT = 8000

# -----------------------------------------------------------------------------
# Hilfsfunktionen
# -----------------------------------------------------------------------------

def fetch_html(url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = page.content()
        browser.close()
        return html

def extract_mp3_links(html):
    soup = BeautifulSoup(html, "lxml")
    links = []

    # <audio src="">
    for audio in soup.find_all("audio"):
        if audio.get("src"):
            links.append(audio["src"])

    # <a href="...mp3">
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".mp3"):
            links.append(a["href"])

    # m3u playlists
    for a in soup.find_all("a", href=True):
        if ".m3u" in a["href"]:
            links.append(a["href"])

    return list(dict.fromkeys(links))  # Deduplizieren


# -----------------------------------------------------------------------------
# Scraper für Heute / Woche / Mediathek
# -----------------------------------------------------------------------------

def scrape_today():
    url = "https://www.freies-radio.de/programm/tagesansicht"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    results = []
    for block in soup.select(".views-row"):
        title = block.get_text(strip=True)
        results.append({"title": title})

    return results

def scrape_week():
    today = datetime.date.today()
    week = []

    for offset in range(7):
        day = today + datetime.timedelta(days=offset)
        day_str = day.strftime("%Y-%m-%d")

        url = f"https://www.freies-radio.de/programm/tagesansicht?day={day_str}"
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")

        items = []
        for block in soup.select(".views-row"):
            title = block.get_text(strip=True)
            items.append({"title": title})

        week.append({
            "date": day_str,
            "items": items
        })

    return week

def scrape_mediathek():
    url = "https://www.freies-radio.de/mediathek"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    items = []
    for row in soup.select(".views-row"):
        title = row.get_text(strip=True)
        link = row.find("a")["href"] if row.find("a") else None

        if link and not link.startswith("http"):
            link = "https://www.freies-radio.de" + link

        items.append({
            "title": title,
            "url": link
        })

    return items

def scrape_detail(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, "lxml")

    # Beschreibung extrahieren
    desc = soup.get_text(" ", strip=True)

    # MP3-Links
    audios = extract_mp3_links(html)

    return {
        "url": url,
        "description": desc[:2000],
        "audios": audios,
    }


# -----------------------------------------------------------------------------
# HTTP API
# -----------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/schedule/today":
            return self._send_json(scrape_today())

        if parsed.path == "/schedule/week":
            return self._send_json(scrape_week())

        if parsed.path == "/mediathek":
            return self._send_json(scrape_mediathek())

        if parsed.path == "/item":
            qs = parse_qs(parsed.query)
            url = qs.get("url", [""])[0]
            return self._send_json(scrape_detail(url))

        self.send_error(404, "Unknown endpoint")


# -----------------------------------------------------------------------------
# Start Server
# -----------------------------------------------------------------------------

print(f"FRS Proxy läuft auf http://{HOST}:{PORT}")
HTTPServer((HOST, PORT), Handler).serve_forever()
