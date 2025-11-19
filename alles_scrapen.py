import requests
from bs4 import BeautifulSoup
import json

def scrape_tagesprogramm():
    url = "https://www.freies-radio.de/programm/tagesansicht"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    entries = []
    # Struktur für ein schönes App- und Website-ähnliches Listing
    for h2 in soup.find_all("h2"):
        if "Programm" in h2.get_text(strip=True):
            block = h2.find_next_sibling()
            while block and block.name in ["h3", "p"]:
                if block.name == "h3":
                    title = block.get_text(strip=True)
                    time, desc = "", ""
                    nxt = block.find_next_sibling()
                    if nxt and nxt.name == "p":
                        desc = nxt.get_text(strip=True)
                        time_split = title.split("–")
                        if len(time_split) == 2:
                            time = time_split[1].strip()
                            title = time_split[0].strip()
                    entries.append({
                        "title": title,
                        "time": time,
                        "description": desc
                    })
                block = block.find_next_sibling()
    with open("data/tagesprogramm.json", "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print("Tagesprogramm:", len(entries), "Sendungen gefunden.")

def scrape_mediathek():
    url = "https://www.freies-radio.de/mediathek"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    entries = []
    for div in soup.find_all("div", class_="view-content"):
        for h3 in div.find_all("h3"):
            title = h3.get_text(strip=True)
            next_p = h3.find_next_sibling("p")
            desc = next_p.get_text(strip=True) if next_p else ""
            url_a = h3.find("a")
            url_sendung = "https://www.freies-radio.de" + url_a["href"] if url_a and url_a.get("href","").startswith("/") else ""
            entries.append({
                "title": title,
                "description": desc,
                "url": url_sendung
            })
    with open("data/mediathek.json", "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print("Mediathek:", len(entries), "Sendungen gefunden.")

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    scrape_tagesprogramm()
    scrape_mediathek()
    print("Alles gescrapt!")
