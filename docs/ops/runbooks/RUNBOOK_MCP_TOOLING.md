# RUNBOOK — MCP Tooling (Cursor)

**Status:** READY  
**Scope:** Cursor MCP Setup für Playwright (Browser) und Grafana (read-only)  
**Risk:** LOW (keine mutierenden Ops; Grafana MCP default read-only)

## Zweck

Dieses Runbook beschreibt die Einrichtung und Nutzung von **MCP (Model Context Protocol)** in Cursor für:
- **Playwright MCP**: Browser-Automatisierung, Snapshots, Screenshots
- **Grafana MCP**: Read-only Zugriff auf Grafana-APIs (Dashboards, Datasources, Queries)

## Voraussetzungen

### Node.js / npx (Playwright MCP)

```bash
node --version   # empfohlen: >= 18
npx --version
```

### Docker (Grafana MCP)

```bash
docker --version
docker ps
```

## Operator Quickstart

### One-liner (Preflight)

```bash
bash scripts/ops/mcp_smoke_preflight.sh
```

### Exit-Codes (Preflight)

- **Exit 0**: Alles ok (JSON parse + Help-Smokes)
- **Exit 2**: Smoke/Config fehlgeschlagen (JSON parse oder `--help`/`-h` Command)
- **Exit 3**: Dependency fehlt (`python3`, `npx` oder `docker`)

## Setup (Projekt-Konfiguration)

Die MCP-Server werden projekt-lokal über `.cursor/mcp.json` konfiguriert.

- **Playwright MCP** läuft via `npx`.
- **Grafana MCP** läuft via Docker und ist standardmäßig **read-only** (`--disable-write`).

## Secret-Handling (KRITISCH)

### Prinzip

- **Keine Secrets ins Repo committen.**
- `.cursor/mcp.json` enthält **keine Tokens**.
- Secrets werden ausschließlich über **Environment Variables** bereitgestellt.

### Lokale Env-Datei (Template + lokale Kopie)

Im Repo liegt ein Template: `.cursor/.env.example`.

```bash
# Einmalig lokal:
cp .cursor/.env.example .cursor/.env
# Dann Token eintragen in .cursor/.env (lokal, gitignored via .gitignore-Regel für .env)
```

> Hinweis: Dieses Repo ignoriert `.env`-Dateien per `.gitignore`. Die lokale Datei `.cursor/.env` wird daher nicht committed.

### Cursor übernimmt Env Vars nur beim Start

Cursor lädt `.env` nicht automatisch. Du musst die Env Vars **in dem Prozess setzen, der Cursor startet**.

Beispiel (Shell-Session):

```bash
set -a
source .cursor/.env
set +a

# Danach Cursor aus dieser Shell starten (Variante A: Cursor CLI, falls installiert)
cursor .
```

Wenn du keine Cursor-CLI nutzt, stelle sicher, dass Cursor aus einer Umgebung startet, die diese Variablen hat (z.B. Terminal-Start).

### DO / DON'T (max 15 bullets)

- **DO**: `.cursor/mcp.json` ohne Secrets lassen (nur `-e VAR` Pass-through).
- **DO**: Tokens über `GRAFANA_SERVICE_ACCOUNT_TOKEN` setzen (Service Account, least-privilege).
- **DO**: Grafana MCP read-only lassen (`--disable-write`), außer explizit und kontrolliert.
- **DO**: Vor Commits kurz prüfen, dass keine Secrets in `.cursor/` liegen.
- **DO**: Tokens rotieren (z.B. 60–90 Tage) und sofort bei Verdacht invalidieren.
- **DON'T**: Tokens/Passwords in JSON/YAML/Markdown committen.
- **DON'T**: `REPLACE_ME` durch echte Tokens in committed Dateien ersetzen.
- **DON'T**: Write-Tools in Production aktivieren (Dashboards/Alerts mutieren).

## Reproducible Smoke-Flows (offline-freundlich)

Es gibt ein Smoke-Check Script:
- `scripts/ops/mcp_smoke_check.py`
- `scripts/ops/mcp_smoke_preflight.sh` (Operator-Preflight, führt Help-Checks aus)

### Struktur-Check (offline, ohne Downloads)

```bash
python3 scripts/ops/mcp_smoke_check.py
```

### Optional: Help-Checks (können Erst-Download triggern)

```bash
python3 scripts/ops/mcp_smoke_check.py --check-all
```

### Operator-Preflight (Copy/Paste)

```bash
bash scripts/ops/mcp_smoke_preflight.sh
```

## Playwright MCP Quickstart

### Ziel

- Eine lokale Grafana-URL öffnen
- Einen Screenshot speichern
- Einen Panel-Titel im Snapshot verifizieren

### Usecase A (Copy/Paste Prompt)

```markdown
Nutze Playwright MCP und führe aus:

1) Öffne `http://localhost:3000/d/<DASHBOARD_UID>` (falls du nur die Startseite kennst: erst `http://localhost:3000`, dann navigieren).
2) Warte bis das Dashboard geladen ist (max 30s).
3) Erstelle einen Vollseiten-Screenshot und speichere als `grafana_dashboard_<DASHBOARD_UID>.png`.
4) Erzeuge einen Snapshot der Seite und prüfe, ob ein Panel mit Titel `<PANEL_TITLE>` enthalten ist.
5) Gib eine kurze Summary: Screenshot-Dateiname, Panel gefunden ja/nein (inkl. Panel-Reihenfolge/ID wenn sichtbar).
```

## Grafana MCP Quickstart (read-only)

### Vorbereitung (Token)

1) In Grafana einen **Service Account** erstellen und ein Token generieren.  
2) Token als Env Var setzen (siehe Secret-Handling).

### Usecase B (Copy/Paste Prompt)

```markdown
Nutze Grafana MCP (read-only) und führe aus:

1) Liste Dashboards (UID, Title, Folder).
2) Liste Folders (UID, Title).
3) Für Dashboard UID `<DASHBOARD_UID>`:
   - Hole eine kompakte Summary (bevorzugt) und/oder gezielt Properties.
   - Hole Panel-Queries + Datasource-Infos.
4) Prüfe, ob Datasource `<EXPECTED_DATASOURCE_NAME>` oder UID `<EXPECTED_DATASOURCE_UID>` verwendet wird.
5) Gib eine Summary: Counts (Dashboards/Folders), Dashboard-Titel+UID, Datasources (UID+Name+Type), Erwartung erfüllt ja/nein.
```

## Troubleshooting

### Preflight schlägt fehl (Exit-Code 2 vs 3)

- **Exit 2** (Smoke/Config failure):
  - JSON ungültig: prüfe `.cursor/mcp.json` (Parse-Check im Output)
  - `npx … --help` oder `docker … -h` fehlgeschlagen: wiederhole mit funktionierendem Netzwerk/Docker-Daemon
- **Exit 3** (Dependency fehlt):
  - `python3`, `npx` oder `docker` sind nicht im PATH oder nicht installiert

### MCP Server erscheint nicht in Cursor

- Cursor komplett beenden und neu starten (Env Vars + MCP werden beim Start geladen).
- JSON prüfen:

```bash
python3 -c "import json; json.load(open('.cursor/mcp.json')); print('OK')"
```

### `npx` / `docker` fehlt

```bash
which npx && npx --version
which docker && docker --version
```

### Env Vars werden nicht übernommen

- Prüfe in der Shell, die Cursor startet:

```bash
echo "$GRAFANA_URL"
echo "${GRAFANA_SERVICE_ACCOUNT_TOKEN:+SET}"
```

## Stop-Rules

- MCP Tools **niemals** für Live-Trading / Order Placement / Execution verwenden.
- Keine Secrets (Tokens/Creds) in Repo-Dateien schreiben oder committen.
- Grafana MCP bleibt **read-only** (`--disable-write`) für produktionsnahe Umgebungen.
- Keine untrusted externen URLs automatisiert ansteuern ohne explizite Operator-Freigabe.

## Referenzen

- MCP: `https://modelcontextprotocol.io/`
- Playwright MCP: `https://github.com/microsoft/playwright-mcp`
- Grafana MCP: `https://github.com/grafana/mcp-grafana`
