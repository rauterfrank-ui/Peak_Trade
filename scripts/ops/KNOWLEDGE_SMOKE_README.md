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

1. `GET &#47;api&#47;knowledge&#47;snippets?limit=1`
2. `GET &#47;api&#47;knowledge&#47;strategies?limit=1`
3. `GET &#47;api&#47;knowledge&#47;search?q=test&k=3` (200 oder 501 ok, nie 500)

### POST Endpoints (gated)

1. `POST &#47;api&#47;knowledge&#47;snippets`
   ```json
   {
     "category": "insight",
     "title": "smoke",
     "content": "c",
     "tags": ["x"]
   }
   ```

2. `POST &#47;api&#47;knowledge&#47;strategies`
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

## 🌐 Variante 3: Remote/Production Smoke (knowledge_prod_smoke.sh)

**Verwendung:** Remote smoke tests gegen eine live deployment (Prod/Staging) ohne Server-Restart.

### Wann verwenden?

- ✅ Post-Deployment-Verifikation in Staging/Production
- ✅ Health-Checks gegen laufende Systeme
- ✅ CI/CD-Pipeline-Integration (Pre/Post-Deploy-Gates)
- ✅ Scheduled monitoring (cron/GitHub Actions)

### Voraussetzungen

```bash
# Zugriff auf Target-URL
curl -I https://prod.example.com/api/health

# Optional: Bearer Token (falls API Auth erfordert)
export PROD_API_TOKEN="your-token-here"
```

### Ausführung

#### Basic (ohne Auth)

```bash
# Via Argument
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com

# Via ENV
BASE_URL=https://prod.example.com ./scripts/ops/knowledge_prod_smoke.sh
```

#### Mit Authentication

```bash
# Token als Flag
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --token "${PROD_API_TOKEN}"

# Token via ENV
export TOKEN="${PROD_API_TOKEN}"
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com
```

#### Advanced

```bash
# Custom API prefix
./scripts/ops/knowledge_prod_smoke.sh https://staging.example.com \
  --prefix /v1/knowledge

# Strict mode (501 = FAIL statt DEGRADED)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --strict

# Verbose output
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --verbose

# Custom timeout (default 10s)
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --timeout 30

# Insecure SSL (dev/staging nur!)
./scripts/ops/knowledge_prod_smoke.sh https://staging.example.com \
  --insecure

# Custom headers
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --header "X-Request-ID: drill-$(date +%s)" \
  --header "X-Environment: production"

# Alle Optionen kombiniert
./scripts/ops/knowledge_prod_smoke.sh https://staging.example.com \
  --prefix /v1/knowledge \
  --token "${STAGING_TOKEN}" \
  --timeout 15 \
  --verbose \
  --header "X-Environment: staging"
```

### Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧪 Knowledge DB Production Smoke Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BASE_URL:   https://prod.example.com
PREFIX:     /api/knowledge
TIMEOUT:    10s
INSECURE:   0
STRICT:     0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PASS: Stats endpoint (200)
✅ PASS: Snippets list (200)
✅ PASS: Strategies list (200)
✅ PASS: Search (GET) (200)
✅ PASS: Write gating probe (403 - correctly blocked)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ PASS:     5
🟡 DEGRADED: 0
❌ FAIL:     0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 All checks passed
```

### Exit Codes

- **0** = All checks passed (or degraded in non-strict mode)
- **1** = One or more checks failed
- **2** = Degraded in strict mode (501 errors)

### Graceful Degradation

Wenn ChromaDB-Backend nicht verfügbar ist:

```
🟡 DEGRADED: Stats endpoint (501 - backend unavailable)
🟡 DEGRADED: Snippets list (501 - backend unavailable)
🟡 DEGRADED: Strategies list (501 - backend unavailable)
🟡 DEGRADED: Search (GET) (501 - backend unavailable)
✅ PASS: Write gating probe (403 - correctly blocked)

📊 Summary
✅ PASS:     1
🟡 DEGRADED: 4
❌ FAIL:     0

🎉 All checks passed
```

**Non-Strict:** Exit Code 0 (degraded akzeptiert)  
**Strict:** Exit Code 2 (degraded = fail)

### Getestete Checks (5)

1. **Stats Endpoint** — `GET &#47;api&#47;knowledge&#47;stats` → 200 (oder 501)
2. **Snippets List** — `GET &#47;api&#47;knowledge&#47;snippets?limit=1` → 200 (oder 501)
3. **Strategies List** — `GET &#47;api&#47;knowledge&#47;strategies?limit=1` → 200 (oder 501)
4. **Search Probe** — `GET &#47;api&#47;knowledge&#47;search?q=smoke&limit=1` → 200 (oder 501)
   - Falls 404/405: versucht POST-Variante
5. **Write Gating Probe** — `POST &#47;api&#47;knowledge&#47;snippets` → 403 (erwartet!)
   - 401 = auth missing (degraded ok)
   - 200/201 = **CRITICAL** (writes nicht geblockt!)

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
- name: Production Smoke Test
  run: |
    ./scripts/ops/knowledge_prod_smoke.sh ${{ secrets.PROD_URL }} \
      --token ${{ secrets.PROD_TOKEN }}
```

### Troubleshooting

#### Script meldet 401 (Unauthorized)

```bash
# Token prüfen
echo $PROD_API_TOKEN

# Manuell testen
curl -H "Authorization: Bearer $PROD_API_TOKEN" \
  https://prod.example.com/api/knowledge/stats
```

#### Script meldet 404 (Not Found)

```bash
# Korrekten Prefix finden
curl -I https://prod.example.com/api/knowledge/stats
curl -I https://prod.example.com/v1/knowledge/stats

# Richtigen Prefix verwenden
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --prefix /v1/knowledge
```

#### Write Probe gibt 200/201 zurück

⚠️ **CRITICAL** — Writes sind NICHT geblockt in Production!

**Sofort-Maßnahmen:**
1. Deployment stoppen (falls neu)
2. Config prüfen:
   ```bash
   kubectl exec -it <pod> -- env | grep KNOWLEDGE
   # Expected: READONLY=true, WEB_WRITE=false
   ```
3. Logs prüfen
4. **Rollback** falls fehlkonfiguriert

#### Timeout (000 status code)

```bash
# Timeout erhöhen
./scripts/ops/knowledge_prod_smoke.sh https://prod.example.com \
  --timeout 30

# Netzwerk prüfen
ping prod.example.com
```

### Help

```bash
./scripts/ops/knowledge_prod_smoke.sh --help
```

---

## 📋 Vergleich der 3 Varianten

| Feature | Manual | Auto | **Production/Remote** |
|---------|--------|------|----------------------|
| **Server-Restart** | Manuell | Automatisch | ❌ Nicht benötigt |
| **Alle 3 Modi** | ✅ Ja | ✅ Ja | ❌ Nein (testet aktuellen Mode) |
| **Remote-Einsatz** | ❌ Nein | ❌ Nein | ✅ Ja |
| **Auth-Support** | ❌ Nein | ❌ Nein | ✅ Bearer Token |
| **CI/CD-Ready** | ❌ Nein | ⚠️  Eingeschränkt | ✅ Ja |
| **Staging/Prod** | ❌ Nein | ❌ Nein | ✅ Ja |
| **Custom Headers** | ❌ Nein | ❌ Nein | ✅ Ja |
| **SSL Options** | ❌ Nein | ❌ Nein | ✅ --insecure |
| **Exit Codes** | Basic | Basic | ✅ Detailliert (0/1/2) |

**Empfehlung:**
- **Lokale Entwicklung:** `knowledge_smoke_runner_auto.sh` (testet alle 3 Modi)
- **Production/Staging:** `knowledge_prod_smoke.sh` (remote, auth, CI/CD)

---

**Empfehlung:** Verwende `knowledge_smoke_runner_auto.sh` für schnelle, vollständige Tests aller 3 Modi. Verwende `knowledge_prod_smoke.sh` für Post-Deployment-Checks und Production-Monitoring.
