# Peak_Trade Observability — Stage 2 Decision (Go/No-Go)

Stand: __DATE__
Owner: __NAME__
Stage-1 Report Root: __PATH__  (z.B. reports/obs/stage1/YYYY-MM-DD)

## Ziel
Nach 1–2 Wochen Stage-1 Monitoring entscheiden, ob wir auf **Stage 2** (erweiterte Automation/Signal-Qualität/Integrationen) gehen — ohne die Safety-Defaults zu kompromittieren.

---

## Inputs (was wird ausgewertet)
- Daily Health Snapshots (JSON/JSONL)
- Alert Events (new vs legacy getrennt!)
- Operator Actions (ACK/SNOOZE/NOTES)
- LaunchAgent Health (läuft / Restart-Rate / Log-Output)
- Report Generation (Trend Report + Exit Codes)

---

## Core KPIs (Stage-1 muss stabil sein)
### A) Alert Health (NEW Alerts)
**Hard No-Go (sofort Stage 1 verlängern & fixen):**
- **≥ 1 Critical NEW Alert** (egal wann)
- **Parse Errors / Corrupt JSONL** wiederkehrend (mehr als einmal/Tag oder Trend ↑)
- **Report Generation failed** (fehlende Reports an ≥2 Tagen/Woche)

**Soft No-Go (Stage 1 verlängern, Ursachen prüfen):**
- NEW Alerts **> 3 pro Woche** oder **Trend ↑** (7d rolling avg steigt)
- Gleiche Regel feuert wiederholt ohne Operator Value (Noise)

**Go-Signal:**
- **0 Critical NEW Alerts**
- NEW Alerts **≤ 1 pro Woche** ODER klar erklärbar (z.B. einmalige lokale Aktion)
- Noise niedrig, Events sind interpretierbar

### B) Automation Health (LaunchAgents / Jobs)
**Hard No-Go:**
- LaunchAgent nicht aktiv / startet ständig neu (Restart-Loop)
- Logs fehlen oder sind „stumm" obwohl Jobs laufen sollten

**Go-Signal:**
- LaunchAgents stabil (keine Restart-Spikes)
- Logs plausibel & Reports werden zuverlässig geschrieben

### C) Disk / Growth (falls beobachtet)
**Hard No-Go:**
- Disk Growth Trend nicht kontrolliert (Retention greift nicht, Wachstum beschleunigt)

**Go-Signal:**
- Wachstum linear/klein ODER Retention/Rotation nachweisbar wirksam

---

## Trend-Check (empfohlenes Vorgehen)
1. **7-Tage Rolling Average** für NEW Alerts & Parse Errors
2. Vergleich: **erste 3 Tage** vs **letzte 3 Tage**
   - Wenn last3 > first3 → Trend ↑ (Noise/Instabilität)
3. "Operator Value": Wie oft musste man reagieren?
   - Ziel: **nahe 0**, außer bei echten Incidents

---

## Entscheidungsmatrix
### ✅ GO: Stage 2 starten, wenn ALLE zutreffen
- 0 Critical NEW Alerts
- NEW Alerts ≤ 1/Woche (oder klar erklärbar)
- LaunchAgents stabil (keine Loops)
- Reports zuverlässig (keine Lücken)
- Keine ansteigenden Parse Errors

### 🟡 EXTEND: Stage 1 verlängern (weitere 7 Tage), wenn mind. 1 zutrifft
- NEW Alerts 2–3/Woche oder Trend ↑
- einzelne Report-Lücken / sporadische Parse Errors
- Operator Actions > erwartet (zu viel "Handarbeit")

### 🔴 NO-GO: Stage 1 fixen (sofort), wenn mind. 1 Hard No-Go
- Critical NEW Alerts
- wiederkehrende Parse Errors/Corruption
- LaunchAgent Instabilität / Reports brechen regelmäßig

---

## Stage 2 Scope (wenn GO)
**Stage 2 bedeutet NICHT "mehr Risiko", sondern:**
- bessere Signalqualität / weniger Noise (Rule-Tuning, TTL, grouping)
- Integrationen (z.B. Slack/Webhook), aber weiterhin safe-by-default
- klarere "Operator Playbook" Trigger (wann ack/snooze/escalate)
- optional: Legacy-Alert Brücke (nur observierend, nicht vermischen)

### Stage-2 Deliverables (Minimal)
- 1 neues "Stage2 Trend Summary" Report-Format (1 Page)
- 2–4 Rule-Tuning PRs (Noise runter)
- 1 Integration (Webhook/Slack) im Dry-Run & opt-in

---

## Entscheidung (ausfüllen)
Datum: __DATE__
Entscheidung: GO / EXTEND / NO-GO

Begründung (kurz, faktenbasiert):
- NEW Alerts: ____
- Criticals: ____
- Parse Errors: ____
- LaunchAgents: ____
- Report Lücken: ____
- Operator Actions: ____

Nächste Schritte:
- [ ] ____
- [ ] ____
- [ ] ____
