# Grafana: Time Range Selector (Time Picker) sichtbar machen

## Root cause
- Die provisionierten Peak_Trade Dashboards hatten keinen expliziten `timepicker`-Block (und ein Dashboard keinen `time`-Default).
- In Grafana 12.x kann das dazu führen, dass der Time Range Selector in Dashboard-Views nicht erscheint (insb. bei provisionierten JSONs / UI-State-Defaults).

## Fix
- In allen Dashboard-JSONs unter `docs/webui/observability/grafana/dashboards/**/*.json` wird explizit gesetzt:
  - `timepicker.hidden = false`
  - Falls `time` fehlt oder kein Dict ist: `time = {"from":"now-6h","to":"now"}`
  - Bestehende `time`-Ranges werden **nicht** überschrieben.

## Verify (lokal)
- Stack starten/neu starten: `bash scripts/obs/grafana_local_up.sh` (oder vorher `..._down.sh`)
- Grafana öffnen:
  - `http://127.0.0.1:3000/d/peaktrade-execution-watch-overview`
  - `http://127.0.0.1:3000/d/peaktrade-operator-home`
- Erwartung: oben rechts ist der Time Range Selector sichtbar (z.B. „Last 30 minutes“ / „Last 6 hours“).
