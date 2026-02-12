# PR 994 — Merge Log

## Summary
MCP Tooling ist jetzt „first-class“ im Repo: projekt-lokale Cursor MCP Konfiguration für Playwright (via npx) und Grafana (via Docker, default read-only), plus reproduzierbares Preflight-Smoke-Script, Runbook-Quickstart/Troubleshooting und ein optionaler, path-gefilterter CI Smoke-Check (signal-only).

## Why
- Reproduzierbare, sichere MCP-Nutzung im Projekt ohne globale Cursor-Config.
- Frühes, günstiges Feedback (Smoke) bei Änderungen an MCP-Tooling/Docs, ohne always-run CI Noise.
- Klare Operator-UX (Quickstart + Exit-Code Semantik) und Repo-Discoverability (Runbook-Navigation).

## Changes
- **Cursor MCP Config / Tooling:**
  - `.cursor&#47;mcp.json` (projekt-lokale MCP-Server-Definitionen)
  - `.cursor&#47;.env.example` (Beispiel-Env ohne Secrets; Operator setzt z.B. `GRAFANA_URL` und `GRAFANA_SERVICE_ACCOUNT_TOKEN`)
  - `scripts&#47;ops&#47;mcp_smoke_check.py` (JSON-/Smoke-Validation Helper; ergänzt/unterstützt das Shell-Preflight)
- **CI (signal-only, path-filtered):**
  - Neu: `.github&#47;workflows&#47;mcp_smoke_preflight.yml` (triggert nur bei Änderungen an `.cursor&#47;**`, `scripts&#47;ops&#47;mcp_*`, `docs&#47;ops&#47;runbooks&#47;RUNBOOK_MCP_TOOLING.md`)
  - Führt `bash scripts&#47;ops&#47;mcp_smoke_preflight.sh` aus (inkl. best-effort ShellCheck)
- **Ops Script:**
  - `scripts&#47;ops&#47;mcp_smoke_preflight.sh` (executable, Header + `--help&#47;--version`, stabile Exit-Codes: `2` = JSON/Smoke fail, `3` = missing dep)
  - Smoke umfasst: JSON parse + `npx -y @playwright&#47;mcp@latest --help` + `docker run --rm grafana&#47;mcp-grafana -h`
- **Docs / Navigation / UX:**
  - `docs&#47;ops&#47;runbooks&#47;RUNBOOK_MCP_TOOLING.md` erweitert um Operator Quickstart + Troubleshooting (Exit-Code 2 vs 3) + Preflight Copy/Paste
  - Token-Policy: Inline-Pfade sind token-policy-konform (Slash-Encoding `&#47;`) für den wiederkehrenden `docs-token-policy-gate`
  - `docs&#47;ops&#47;runbooks&#47;README.md` verlinkt das MCP-Runbook

## Verification
### Tests executed (local)
- `bash scripts&#47;ops&#47;mcp_smoke_preflight.sh --version`
- `bash scripts&#47;ops&#47;mcp_smoke_preflight.sh --help`
- `bash scripts&#47;ops&#47;mcp_smoke_preflight.sh`
- `shellcheck scripts&#47;ops&#47;mcp_smoke_preflight.sh` (lokal, falls installiert)

### Result
- PASS: Preflight läuft lokal sauber durch (JSON parse + npx … --help + `docker run --rm grafana/mcp-grafana -h`)
- PASS: Workflow ist sauber path-gefiltert und damit nicht „always-run“
- PASS: Script ist executable und ShellCheck-kompatibel (best-effort)

## Risk
LOW — betrifft nur `.github&#47;workflows&#47;`, `.cursor&#47;`, `docs&#47;`, `scripts&#47;ops&#47;`; keine Secrets im Repo, keine Live/Execution/Risk-Pfade, keine Netz-Calls außer expliziten `--help&#47;-h` Smokes.

## Operator How-To
- MCP Preflight (lokal):
  - `bash scripts&#47;ops&#47;mcp_smoke_preflight.sh`
- Exit-Codes:
  - `0` = OK
  - `2` = JSON/Smoke fail
  - `3` = python3/npx/docker fehlt

## References
- PR: #994
- Runbook: `docs&#47;ops&#47;runbooks&#47;RUNBOOK_MCP_TOOLING.md`
- Config: `.cursor&#47;mcp.json`, `.cursor&#47;.env.example`
- Script: `scripts&#47;ops&#47;mcp_smoke_preflight.sh`, `scripts&#47;ops&#47;mcp_smoke_check.py`
- Workflow: `.github&#47;workflows&#47;mcp_smoke_preflight.yml`
