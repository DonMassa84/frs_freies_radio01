import re
import json
import os

SRC_FILE = 'mediathek.md'
OUT_DIR = 'data'
OUT_FILE = os.path.join(OUT_DIR, 'mediathek.json')

def parse_mediathek_md(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    blocks = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    for block in blocks:
        lines = [l for l in block.strip().split('\n') if l.strip()]
        if not lines:
            continue

        title = lines[0].strip()
        date = ""
        url = ""
        desc_list = []

        for line in lines[1:]:
            line = line.strip()
            if line.startswith("http"):
                url = line
            elif any(ch.isdigit() for ch in line) and "." in line:
                # sehr einfache Datums-Heuristik, z.B. "12.11.2025"
                date = line
            else:
                desc_list.append(line)

        description = ' '.join(desc_list).strip()

        entries.append({
            "title": title,
            "date": date,
            "url": url,
            "description": description
        })

    return entries

def main():
    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"{SRC_FILE} nicht gefunden – bitte anlegen.")

    os.makedirs(OUT_DIR, exist_ok=True)
    entries = parse_mediathek_md(SRC_FILE)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Mediathek: {len(entries)} Einträge gefunden.")
    print(f"Gespeichert in: {OUT_FILE}")

if __name__ == "__main__":
    main()
