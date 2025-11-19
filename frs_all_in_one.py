import requests,bs4,json
base="https://www.freies-radio.de"
P=bs4.BeautifulSoup(requests.get(base+"/programm/tagesansicht").text,"html.parser")
M=bs4.BeautifulSoup(requests.get(base+"/mediathek").text,"html.parser")

programm=[]
for b in P.select(".calendar-day .broadcast"):
    t=b.select_one("div")
    h=b.select_one("h2 a")
    d=b.select_one("p:not(.font-bold)")
    programm.append({
        "time":t.get_text(strip=True) if t else "",
        "title":h.get_text(strip=True) if h else "",
        "description":d.get_text(strip=True) if d else "",
        "link":base+h["href"] if h and h.get("href","").startswith("/") else (h["href"] if h else "")
    })

mediathek=[]
for b in M.select(".views-row"):
    h=b.select_one("h2 a")
    d=b.select_one(".date")
    p=b.select_one("p")
    a=b.select_one("audio source")
    mediathek.append({
        "title":h.get_text(strip=True) if h else "",
        "date":d.get_text(strip=True) if d else "",
        "teaser":p.get_text(strip=True) if p else "",
        "link":base+h["href"] if h and h.get("href","").startswith("/") else (h["href"] if h else ""),
        "mp3":a.get("src","") if a else ""
    })

print(json.dumps({
    "stream":"https://streaming.fueralle.org/frs-hi.mp3",
    "programm":programm,
    "mediathek":mediathek
},ensure_ascii=False,indent=2))

