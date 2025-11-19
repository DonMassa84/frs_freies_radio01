import re
import json
import os

SRC_FILE = 'programm.md'
OUT_DIR = 'data'
OUT_FILE = os.path.join(OUT_DIR, 'programm.json')

def parse_programm_md(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    # Blöcke nach "## " trennen
    blocks = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    for block in blocks:
        lines = [l for l in block.strip().split('\n') if l.strip()]
        if not lines:
            continue

        title = lines[0].strip()
        time = ""
        desc_list = []

        for line in lines[1:]:
            line = line.strip()
            # Zeile beginnt mit Uhrzeit, z.B. "10:00" oder "10:00–12:00"
            if re.match(r'^\d{2}:\d{2}', line):
                time = line
            else:
                desc_list.append(line)

        description = ' '.join(desc_list).strip()

        entries.append({
            "title": title,
            "time": time,
            "description": description
        })

    return entries

def main():
    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"{SRC_FILE} nicht gefunden – bitte anlegen.")

    os.makedirs(OUT_DIR, exist_ok=True)
    entries = parse_programm_md(SRC_FILE)

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"Tagesprogramm: {len(entries)} Einträge gefunden.")
    print(f"Gespeichert in: {OUT_FILE}")

if __name__ == "__main__":
    main()
