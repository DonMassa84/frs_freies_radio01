# PHASE 5 – Ergebnisbericht: Lokale LLM-Server für die FRS-Metadatenpipeline

**Datum:** 2026-10-07
**Rechner:** „ryzen" – AMD Ryzen 7 5800XT (8C/16T), 32 GiB RAM, kein Swap, Linux Mint 22.3, Kernel 7.0.0-34-generic
**GPU:** NVIDIA RTX 3060, 12288 MiB VRAM, Treiber 595.91.07 (CUDA 12.1 via PyTorch)
**Baseline-VRAM:** ~590–864 MiB (alle Server nach Aufräumen wieder auf Baseline)
**Speicher:** `/` 243 GiB, `/home` 332 GiB, `/mnt/nvme-data` 575 GiB, `/mnt/storage` 391 GiB frei
**Test-Datum:** 2026-10-07 (Einzeltests, je Kandidat ein Server gleichzeitig, nur 127.0.0.1)

---

## 1. Zusammenfassung / Ranking

| Rang | Kandidat | Version | Port | Server-Status | Bench (json_object) | Inferenz (s) | Ladezeit bis „bereit" | Modell |
|---|---|---|---|---|---|---|---|---|
| 1 | **llama.cpp** | b11457 | 8081 | ✅ bestanden | ✅ ok, **0 Fehler** | 4.043 | 3.5 s (Laden) | GGUF 7B q4_0 |
| 2 | **LM Studio** | 0.4.25 | 8082 | ✅ bestanden | ⚠️ `json_object` → HTTP 400, **`json_schema` ok, 0 Fehler** | 2.614 | 2.1 s (Laden) | GGUF 7B q4_0 |
| 3 | **Jan** | 0.8.4 | 8083 | ✅ bestanden (selbst erstelltes Router-Preset, API-Key nötig) | ✅ ok, **0 Fehler** | 4.079 | n.protok. | GGUF 7B q4_0 |
| 4 | **LocalAI** | 4.11.0 | 8084 | ✅ bestanden ( OCI-Backend-Pull nötig) | ✅ ok, **0 Fehler** | 4.03 | 10.245 (Cold Start) | GGUF 7B q4_0 |
| 5 | **vLLM** | 0.31.0 | 8085 | ✅ bestanden (Server) | ⚠️ `schema_errors` – **3 Fehler, modell-bedingt** | 4.137 / 4.637 | ~90 s | Qwen2.5-3B (Option A) |
| 6 | **SGLang** | 0.5.21 | 8086 | ✅ bestanden (CUDA-13-nvcc-JIT) | ⚠️ `schema_errors` – **3–4 Fehler, modell-bedingt** | 4.964 / 5.037 | ~80 s | Qwen2.5-3B (Option A) |

**Wichtiger Vorbehalt (fairer Vergleich):** Kandidaten 1–4 liefen mit dem **7B-GGUF** (0 Validierungsfehler), Kandidaten 5–6 mit dem kleineren **Qwen2.5-3B-Instruct** (Modell-Option A). Die `schema_errors` bei vLLM/SGLang stammen **vom Modell** (liefert Frame-Namen ohne `id3_frames.`-Präfix bzw. `::` statt `.`), nicht vom Server. Beide Server akzeptieren `json_object` **und** `json_schema` (HTTP 200, parsebares JSON, `fenced_output: false`).

**Alle 6 Kandidaten sind grundsätzlich lauffähig** – auch auf einem read-only-System.

### Empfehlung für den FRS-Pilotbetrieb
1. **llama.cpp (b11457)** – empfohlen als Pilot-Backend: schnellster Cold-Start-Lauf mit dem 7B-GGUF, 0 Validierungsfehler, reines CLI, kleinste Installationsfläche (213 MB), volle Schema-Kontrolle über `--jinja`-/Response-Format-Flags.
2. **LM Studio** – schnellste Inferenz (2.61 s), aber **nur `json_schema` nutzbar** (JSON-Object-Modus wird abgelehnt); GUI-basiert, für automatisierte Pipeline ungeeigneter als llama.cpp/Jan.
3. **vLLM/SGLang** – nur empfehlenswert, wenn ein **größeres Modell zur separaten Freigabe** kommt (7B-FP16/BF16 passt in 12 GB VRAM: 7B ≈ 14 GB bf16 → nein; 7B Q5/Q6-GGUF läuft über vLLM nicht, daher bräuchte vLLM ein ~4B-q4-AWQ o.ä.). Bei Option A (3B) liefert das Modell die Validierungsfehler.
4. **LocalAI** – funktional ok, aber höchster Installationsaufwand (OCI-Backend-Pull ~30 min/2.6 GB, Symlinks werden ignoriert, Pfad-Flags zwingend).
5. **Jan** – braucht eigenes Router-Preset + Bearer-API-Key (Key wird vom Server beim Start generiert; nur programmatisch aus `/proc/<pid>/environ` lesen, nie auf CLI/Log).

---

## 2. Rahmenbedingungen (Phase-1- und Phase-2-Befunde)

- **Root-Partition read-only** (`errors=remount-ro,emergency_ro`): `apt install` und Docker sind **unbenutzbar**. Zugelassene Workarounds in dieser Phase:
  - `apt-get download <pkg>` + `dpkg -x <pkg>.deb ~/local/` (ohne Root)
  - pip-Installationen nach Home (`~/vllm-venv`, `~/sglang-venv`)
  - `CPATH` auf extrahierte Python-3.12-Dev-Header (`~/local/python312-dev`)
  - `CUDA_HOME` auf pip-cu13-Toolkit im venv
- `/home` und `/mnt` sind read-write; alle Logs/Artefakte liegen unter `/home/shadowmaker/`.
- Nur lesen: `/mnt/nvme-data/TOSHIBA_Spiegel/03_MEDIA` (21 569 MP3).
- Repo `/home/shadowmaker/frs_freies_radio01` (Branch `feat/archive-normalization`, HEAD `a5e03ed`): **kein Commit, kein Push, `archive_normalization/llm_metadata.py` unverändert.**
- Alle Server ausschließlich an `127.0.0.1`, nur einer gleichzeitig, alle nach Test per PID beendet (Port-Check: **alle Bench-Ports 8081–8086 frei**, VRAM zurück auf Baseline 654 MiB).
- Keine Cloud-Provider, keine curl|bash-Pipes, keine Autostarts, Ollama unberührt erhalten.

---

## 3. Testaufbau

- **Test-Harness:** `/home/shadowmaker/localai-bench/bench_one.py`
  `--base-url --model [--label] [--api {openai,ollama}] [--rf {json_object,json_schema,none}]`
  Fence-Toleranz `fenced_output`; Bearer-Auth nur aus Env `BENCH_API_KEY` (Key nie auf CLI/Log); Ergebnis als JSON auf stdout.
- **Schema/Validierung:** `archive_normalization/llm_metadata.py` (PROMPT_VERSION 2.3, `RESPONSE_SCHEMA`, `validate_proposal`) – nur konsumiert, **nicht verändert**.
- **Synthetischer Test:** `test-uuid-001` (ein Datensatz, identische Eingabe für alle Kandidaten).
- **GGUF-Testmodell:** `/mnt/nvme-data/ollama_gguf/qwen2.5-coder-7b-instruct-q4_0.gguf`
  Größe 4 431 390 720 B, SHA256 `8561411b4705cbf2d105cf8e2084c6d6f1bcaba415249ce65fc5f21230d4961b` (`testmodel.sha256`).
- **HF-Testmodell (Option A):** `Qwen/Qwen2.5-3B-Instruct`, Cache `~/.cache/huggingface/hub/models--Qwen--Qwen2.5-3B-Instruct` (5,8 GB, vollständig).

---

## 4. Kandidaten-Details

### 4.1 llama.cpp b11457 – ✅ bestanden
- **Installationsort:** `~/local/llama-b11457/` (213 MB), Binär `llama-server`
- **Start:** `llama-server -m <GGUF> --host 127.0.0.1 --port 8081 ...`, Log `llama_server.log`
- **Ergebnis:** Laden 3.519 s, Inferenz 4.043 s, **0 Validierungsfehler**, `json_parsable: true`, `fenced_output: false`, `record_id_app_only: true`
- **Schema-Modus:** `json_object` ohne Einschränkung
- **Deinstallation:** `rm -rf ~/local/llama-b11457`

### 4.2 LM Studio 0.4.25 – ✅ bestanden (mit Einschränkung)
- **Installationsort:** `~/Applications/LM-Studio-0.4.25/` (750 MB) + `~/.lmstudio` (Modelle/Config)
- **Ergebnis:** Laden 2.09 s, Inferenz **2.614 s (schnellster Wert)**, 0 Validierungsfehler
- **⚠️ `response_format: json_object` wird abgelehnt (HTTP 400)** – nur `json_schema` nutzbar (`bench_one.py --rf json_schema`)
- **Deinstallation:** `rm -rf ~/Applications/LM-Studio-0.4.25 ~/.lmstudio`

### 4.3 Jan 0.8.4 – ✅ bestanden
- **Binary:** `~/.local/bin/jan`, Daten `~/.jan`, Log `jan_server.log`
- **Besonderheiten:** eigenes Router-Preset `router.preset.ini` (vom Assistenten erstellt); der Router generiert beim Start einen `LLAMA_API_KEY` – nur programmatisch aus `/proc/<pid>/environ`, **nie im Klartext wiedergeben**; Bench-Bearer-Token via `BENCH_API_KEY`.
- **Ergebnis:** Inferenz 4.079 s, 0 Validierungsfehler, `json_object` akzeptiert
- **Deinstallation:** `rm -rf ~/.local/bin/jan ~/.jan`

### 4.4 LocalAI 4.11.0 – ✅ bestanden (höchster Installationsaufwand)
- **Binary:** `~/local/local-ai-v4.11.0-linux-amd64/` (187 MB), Daten unter `~/localai-bench/localai-*`
- **GPU-Backend:** `localai@cuda12-llama-cpp` per Gallery-OCI-Pull (`quay.io/go-skynet/local-ai-backends:latest-gpu-nvidia-cuda-12-llama-cpp`), ~30 min Download, **2.6 GB** (`localai-backends/`, inkl. `libggml-cuda.so`, `libcudart` 12.8)
- **Problem 1 – Symlinks:** LocalAI erkennt Symlinks auf die GGUF **nicht** → echte Datei-Kopie nötig (`localai-models/`, 4.2 GB)
- **Problem 2 – YAML:** Modell braucht Konfiguration daneben (backend `llama-cpp`, `context_size: 8192`, `gpu_layers: 99`, `temperature: 0.0`)
- **Problem 3 – CWD-Abhängigkeit:** Default-Flags zeigen auf das CWD; immer `--models-path/--backends-path/--data-path` setzen (CWD-Müll nach `localai-data/cwd-state/` verschoben)
- **Ergebnis:** Cold-Start-Ladezeit **10.245 s**, VRAM 860 → 5510 MiB (GPU-Backend aktiv), Inferenz 4.03 s, 0 Validierungsfehler, `rf_used: json_object`, `fenced_output: false`
- **Deinstallation:** Binary-Ordner + `rm -rf ~/localai-bench/localai-{backends,models,data}`

### 4.5 vLLM 0.31.0 – ✅ Server bestanden, Modell-Ergebnis mit Fehlern
- **Venv:** `~/vllm-venv/` (8.3 GB), Log `vllm_serve5.log` (erfolgreicher Lauf)
- **Build-/Start-Workarounds (read-only `/`):**
  1. `CPATH=~/local/python312-dev/usr/include/python3.12:~/local/python312-dev/usr/include` (Triton-Build brauchte `Python.h`; via `apt-get download libpython3.12-dev` + `dpkg -x`)
  2. `VLLM_USE_FLASHINFER_SAMPLER=0` (FlashInfer-Sampler wollte nvcc)
  - `--enforce-eager` half dagegen **nicht**
- **Start:** `vllm serve Qwen/Qwen2.5-3B-Instruct --host 127.0.0.1 --port 8085 --served-model-name qwen2.5-3b-instruct --max-model-len 8192 --gpu-memory-utilization 0.75`
- **Ladezeiten:** Model loading 5.79 GiB / 3.571 s, Init engine 45.47 s (Compilation 12.43 s), **bereit ~90 s**, VRAM 9429 MiB
- **Bench:** `json_object`: status `schema_errors`, http 200, Inferenz 4.137 s, `json_parsable: true`, 3 Validierungsfehler; `json_schema`: gleiches Ergebnis (4.637 s) → **modell-bedingt, nicht server-/rf-bedingt**
  - `source_field 'TCON'/'TIT2'` ohne `id3_frames.`-Präfix; `'id3_frames::COMM::eng'` mit `::` statt `.`
- **Aufräumen:** Prozesse per PID gekillt, Port 8085 frei
- **Deinstallation:** `rm -rf ~/vllm-venv ~/local/python312-dev ~/local/debs`

### 4.6 SGLang 0.5.21 – ✅ bestanden (drei Build-Hürden gelöst)
- **Venv:** `~/sglang-venv/` (9.7 GB), Logs `sglang_serve*.log` (endgültiger Lauf: `sglang_serve6.log`)
- **Hürde 1 – `deep_ep`:** braucht `CUDA_HOME` (Env reicht, `find_cuda_home()` prüft Env zuerst)
- **Hürde 2 – nvcc für RoPE-JIT-Build (`sgl_kernel_jit_fused_rope_*`):** kein Disable-Flag vorhanden; **Lösung: komplettes CUDA-13-Toolkit im venv** (`nvidia-cuda-nvcc 13.4.92` → `.../site-packages/nvidia/cu13/`, nvcc 13.4.92 lauffähig)
- **Hürde 3 – Link-Schritt:** Ninja linkt mit `-L .../cu13/lib64` (pip-Paket hat nur `lib/`) und sucht `libcudart.so` (nur `.so.13` vorhanden). **Lösung: zwei Symlinks im eigenen venv:**
  ```
  ln -sfn lib           .../nvidia/cu13/lib64
  ln -sfn libcudart.so.13 .../nvidia/cu13/lib/libcudart.so
  ```
- **Hürde 4 (irrelevant geworden):** `nvidia-cuda-nvcc-cu12 12.9.86` enthält nur `ptxas`, keinen nvcc – cu13-Toolkit ist der richtige Weg
- **Start (erfolgreich):**
  ```
  CUDA_HOME=<venv>/.../nvidia/cu13 LD_LIBRARY_PATH=<venv>/.../nvidia/cu13/lib \
  python -m sglang.launch_server --model Qwen/Qwen2.5-3B-Instruct \
    --host 127.0.0.1 --port 8086 --served-model-name qwen2.5-3b-instruct \
    --context-length 8192 --trust-remote-code --attention-backend triton
  ```
- **Ladezeiten (aus Engine-Timing):** `load_weight=0.86 s`, `kv_cache_allocation=0.26 s`, `scheduler_e2e=40.99 s` (davon `cuda_graph prefill=30.93 s` inkl. JIT-Build), `tokenizer_e2e=47.80 s`, **bereit ~80 s**, VRAM 9462 MiB, `max_total_num_tokens=39864`, Decode-Throughput ~47 tok/s, CUDA-Graph aktiv
- **Bench:** `json_object`: status `schema_errors`, http 200, Inferenz 4.964 s, `json_parsable: true`, 3 Fehler; `json_schema`: identisch (5.037 s) → **modell-bedingt**; beide Male `fenced_output: false`
- **Bekannter Nebenbefund:** Lauf 3 (ohne lib64/libcudart-Symlinks) starb zuerst mit Segfault im HF-Tokenizer-Init; isolierter Test (mit/ohne `LD_LIBRARY_PATH`) war ok → Fork/Race-Konstellation, trat nach Link-Fix nicht mehr auf.
- **Aufräumen:** Parent + Scheduler-/Compile-Worker-Subprozesse per PID gekillt, Port 8086 frei, VRAM 654 MiB
- **Deinstallation:** `rm -rf ~/sglang-venv ~/.cache/sglang`

---

## 5. Ergebnis der Schema-Validierung (test-uuid-001)

| Server | rf-Modus | HTTP | JSON parsebar | Validierungsfehler | `fenced_output` |
|---|---|---|---|---|---|
| llama.cpp | json_object | 200 | ✅ | 0 | false |
| LM Studio | json_object | **400** | – | – | – |
| LM Studio | json_schema | 200 | ✅ | 0 | false |
| Jan | json_object | 200 | ✅ | 0 | false |
| LocalAI | json_object | 200 | ✅ | 0 | false |
| vLLM | json_object | 200 | ✅ | 3 (modell) | false |
| vLLM | json_schema | 200 | ✅ | 3 (modell) | false |
| SGLang | json_object | 200 | ✅ | 3 (modell) | false |
| SGLang | json_schema | 200 | ✅ | 3–4 (modell) | false |

**Fehlerbild Qwen2.5-3B (identisch bei vLLM und SGLang):**
- `source_field 'TCON' not in allowed input fields` (erwartet: mit `id3_frames.`-Präfix)
- `source_field 'id3_frames::COMM::eng' ...` (erwartet: `.` statt `::`)
- `source_field 'TIT2' / 'TALB' not in allowed input fields`

→ Modell-interne Prompt-/Schema-Treue, **nicht** response_format- oder serverbedingt. Behebung nur über Modellwechsel/-training, **nicht** über `llm_metadata.py` (unverändert).

---

## 6. Read-only-System-Befunde (dokumentationspflichtig)

1. Root-Partition read-only → kein `apt install`, kein Docker; Workarounds: `apt-get download`+`dpkg -x`, pip-venvs, Home-Pfade.
2. `CPATH`-Workaround für Triton-C-Builds (Python-3.12-Header extrahiert).
3. CUDA-Toolkit über pip-Pakete rekonstruierbar (`nvidia-cuda-nvcc` 13.4.92 im sglang-venv), inkl. nötiger `lib64`/`libcudart.so`-Symlinks.
4. Alle dauerhaften Prozesse via `setsid nohup ... < /dev/null & disown`; Beendigung per PID (Muster mit `[v]`-Klammer oder `grep -F` + `grep -vF grep`, damit die eigene Shell nicht getroffen wird).

---

## 7. Artefakte

| Datei | Inhalt |
|---|---|
| `~/localai-bench/bench_one.py` | Test-Harness |
| `~/localai-bench/sglang_bench_rfjson.json` | SGLang-Bench `json_object` |
| `~/localai-bench/sglang_bench_rfschema.json` | SGLang-Bench `json_schema` |
| `~/localai-bench/{llama,lms,jan,localai,vllm,sglang}*.log` | Start-/Installations-Logs aller Kandidaten |
| `~/localai-bench/testmodel.sha256` | SHA256 des GGUF-Testmodells |
| `~/localai-bench/localai-models/*.yaml` | LocalAI-Modellkonfiguration |
| `~/frs_freies_radio01/archive_normalization/llm_metadata.py` | Schema/Validierung (unverändert) |

**Gesamtbelegung installierter Kandidaten:** sglang-venv 9.7 G + vllm-venv 8.3 G + LocalAI-Backends 2.6 G + LocalAI-Modelle 4.2 G + LM Studio 0.75 G + llama.cpp 0.21 G + LocalAI-Binary 0.19 G + HF-Qwen2.5-3B 5.8 G ≈ **31.7 GB** (plus GGUF-Testkopie in `localai-models/`).

## 8. Zustand nach Abschluss
- Alle Bench-Ports (8081–8086) **frei**, alle Server per PID beendet.
- VRAM **654 MiB** (Baseline).
- Kein Commit/Push, `llm_metadata.py` unangetastet, MP3-Quelle nur gelesen, keine Autostarts/Timer/Services angelegt.
