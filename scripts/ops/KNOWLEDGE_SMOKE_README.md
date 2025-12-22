# Knowledge DB Smoke Test Scripts

Zwei Varianten für umfassende Smoke Tests der Knowledge DB API.

## 📋 Übersicht

Beide Scripts testen **3 offizielle Konfigurationsmodi**:

| Mode | READONLY | WEB_WRITE | GET | POST | Verwendung |
|------|----------|-----------|-----|------|------------|
| **Production** | true | false | ✅ 200 | ❌ 403 | Live-Systeme (sicher) |
| **Development** | false | true | ✅ 200 | ✅ 201 | Lokale Entwicklung |
| **Research** | false | false | ✅ 200 | ❌ 403 | Nur Scripts, WebUI read-only |

## 🚀 Variante 1: Manual (knowledge_smoke_runner.sh)

**Verwendung:** Server muss manuell für jeden Mode neu gestartet werden.

### Voraussetzungen

```bash
# Terminal 1: Server ist bereits gestartet mit gewünschten ENV Flags
cd /Users/frnkhrz/Peak_Trade
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=true
uv run uvicorn src.webui.app:app --reload --port 8000
```

### Ausführung

```bash
# Terminal 2: Script ausführen (testet nur einen Mode)
cd /Users/frnkhrz/Peak_Trade
./scripts/ops/knowledge_smoke_runner.sh
```

**⚠️ Hinweis:** Dieses Script setzt ENV-Variablen intern, aber diese wirken nicht auf den bereits laufenden Server. Du musst den Server **manuell für jeden Mode neu starten**:

```bash
# Mode 1: Production
pkill -f uvicorn
export KNOWLEDGE_READONLY=true KNOWLEDGE_WEB_WRITE_ENABLED=false
uv run uvicorn src.webui.app:app --port 8000 &
sleep 3
./scripts/ops/knowledge_smoke_runner.sh

# Mode 2: Development
pkill -f uvicorn
export KNOWLEDGE_READONLY=false KNOWLEDGE_WEB_WRITE_ENABLED=true
uv run uvicorn src.webui.app:app --port 8000 &
sleep 3
./scripts/ops/knowledge_smoke_runner.sh

# Mode 3: Research
pkill -f uvicorn
export KNOWLEDGE_READONLY=false KNOWLEDGE_WEB_WRITE_ENABLED=false
uv run uvicorn src.webui.app:app --port 8000 &
sleep 3
./scripts/ops/knowledge_smoke_runner.sh
```

## 🤖 Variante 2: Auto (knowledge_smoke_runner_auto.sh) - **EMPFOHLEN**

**Verwendung:** Startet/stoppt Server automatisch für jeden Mode.

### Ausführung

```bash
cd /Users/frnkhrz/Peak_Trade
./scripts/ops/knowledge_smoke_runner_auto.sh
```

**Vorteile:**
- ✅ Startet Server automatisch für jeden Mode
- ✅ Stoppt Server nach jedem Test
- ✅ Ein Befehl, alle 3 Modi getestet
- ✅ Cleanup bei Abbruch (trap)

### Optional: Anderer Port

```bash
PORT=9000 BASE_URL=http://127.0.0.1:9000 ./scripts/ops/knowledge_smoke_runner_auto.sh
```

## 📊 Output

Beide Scripts zeigen detaillierte Ergebnisse:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Knowledge DB Smoke Runner
BASE_URL: http://127.0.0.1:8000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

───────────────────────────────────────────────────────
▶ MODE: Production
   KNOWLEDGE_READONLY=true
   KNOWLEDGE_WEB_WRITE_ENABLED=false
───────────────────────────────────────────────────────
   🚀 Starting server with READONLY=true, WEB_WRITE=false...
   Server PID: 12345
   ✓ Server ready after 3s
✅ OK:   Production: GET snippets (200)
✅ OK:   Production: GET strategies (200)
✅ OK:   Production: GET search (200)
✅ OK:   Production: POST snippets (403)
✅ OK:   Production: POST strategies (403)
   🛑 Stopping server (PID 12345)...

───────────────────────────────────────────────────────
▶ MODE: Development
   KNOWLEDGE_READONLY=false
   KNOWLEDGE_WEB_WRITE_ENABLED=true
───────────────────────────────────────────────────────
   🚀 Starting server...
✅ OK:   Development: GET snippets (200)
✅ OK:   Development: GET strategies (200)
✅ OK:   Development: GET search (200)
✅ OK:   Development: POST snippets (201)
✅ OK:   Development: POST strategies (201)
   🛑 Stopping server...

───────────────────────────────────────────────────────
▶ MODE: Research
   KNOWLEDGE_READONLY=false
   KNOWLEDGE_WEB_WRITE_ENABLED=false
───────────────────────────────────────────────────────
   🚀 Starting server...
✅ OK:   Research: GET snippets (200)
✅ OK:   Research: GET strategies (200)
✅ OK:   Research: GET search (200)
✅ OK:   Research: POST snippets (403)
✅ OK:   Research: POST strategies (403)
   🛑 Stopping server...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 All smoke checks passed.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🧪 Getestete Endpoints

### GET Endpoints (immer 200)

1. `GET /api/knowledge/snippets?limit=1`
2. `GET /api/knowledge/strategies?limit=1`
3. `GET /api/knowledge/search?q=test&k=3` (200 oder 501 ok, nie 500)

### POST Endpoints (gated)

1. `POST /api/knowledge/snippets`
   ```json
   {
     "category": "insight",
     "title": "smoke",
     "content": "c",
     "tags": ["x"]
   }
   ```

2. `POST /api/knowledge/strategies`
   ```json
   {
     "name": "smoke_strat",
     "description": "Smoke test strategy",
     "status": "rd",
     "tier": "experimental"
   }
   ```

## ✅ Erwartete Ergebnisse

### Production Mode (READONLY=true, WEB_WRITE=false)
- ✅ GET → 200
- ❌ POST → 403 (readonly blockiert)

### Development Mode (READONLY=false, WEB_WRITE=true)
- ✅ GET → 200
- ✅ POST → 201 (beide Flags enabled)

### Research Mode (READONLY=false, WEB_WRITE=false)
- ✅ GET → 200
- ❌ POST → 403 (web write disabled)

## 🐛 Troubleshooting

### Script findet Server nicht

```bash
# Prüfe ob Server läuft
curl http://127.0.0.1:8000/api/health

# Prüfe Port
lsof -i :8000
```

### Auto-Version startet nicht

```bash
# Prüfe Log
cat /tmp/knowledge_smoke_server.log

# Manuell testen
cd /Users/frnkhrz/Peak_Trade
uv run uvicorn src.webui.app:app --port 8000
```

### Tests schlagen fehl

```bash
# Einzelnen Endpoint testen
curl -v http://127.0.0.1:8000/api/knowledge/snippets

# Mit Flags testen
export KNOWLEDGE_READONLY=false
export KNOWLEDGE_WEB_WRITE_ENABLED=true
uv run uvicorn src.webui.app:app --port 8000
# In anderem Terminal:
curl -X POST http://127.0.0.1:8000/api/knowledge/snippets \
  -H "Content-Type: application/json" \
  -d '{"category":"test","title":"t","content":"c","tags":["x"]}'
```

## 📝 Integration in CI/CD

```yaml
# .github/workflows/knowledge-smoke.yml
name: Knowledge DB Smoke Tests

on: [push, pull_request]

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt
      - name: Run smoke tests
        run: ./scripts/ops/knowledge_smoke_runner_auto.sh
```

## 🎯 Verwendung in anderen Projekten

Das Script ist portabel und kann leicht angepasst werden:

```bash
# Andere Endpoints hinzufügen
get_custom() {
  http_code "${BASE_URL}/api/custom/endpoint"
}

# In run_mode() einfügen:
expect "${mode}: GET custom" "$(get_custom)" "200"
```

---

**Empfehlung:** Verwende `knowledge_smoke_runner_auto.sh` für schnelle, vollständige Tests aller 3 Modi.
