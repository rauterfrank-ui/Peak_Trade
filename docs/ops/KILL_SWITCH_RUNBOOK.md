# Peak_Trade Kill Switch – Operator Runbook

**Version:** 1.0  
**Datum:** 2025-12-28  
**Für:** Operations Team

---

## 🎯 Übersicht

Dieses Runbook beschreibt die operativen Verfahren für den Emergency Kill Switch.

**Was ist der Kill Switch?**
- **Layer 4** der Risk Management Defense-in-Depth Architektur
- **Letzte Verteidigungslinie** gegen unkontrollierte Trading-Verluste
- **Blockt alle Trading-Aktivitäten** sofort bei Aktivierung

**Wann aktivieren?**
- Portfolio Drawdown > 15%
- Unerwartetes Systemverhalten
- Verdächtige Marktbedingungen
- System-Anomalien (Memory/CPU)
- Exchange-Verbindungsprobleme
- Geplante Wartungsarbeiten

---

## 🚨 NOTFALL-VERFAHREN

### 1. MANUELLER KILL SWITCH TRIGGER

**Wann:** Sofortige Notabschaltung erforderlich

**Schritte:**

```bash
# 1. Terminal öffnen
cd ~/Peak_Trade

# 2. Virtual Environment aktivieren
source venv/bin/activate
# oder
source .venv/bin/activate

# 3. Kill Switch triggern
./scripts/ops/kill_switch_ctl.sh trigger "GRUND FÜR NOTABSCHALTUNG"

# Alternative: Direkt via Python CLI
python3 -m src.risk_layer.kill_switch.cli trigger \
  --reason "Grund hier eintragen" \
  --confirm
```

**Bestätigung:**
- System fragt nach Bestätigung: Tippe `yes`
- Ausgabe: `🚨 KILL SWITCH TRIGGERED`
- Trading ist **sofort blockiert**

**Wichtig:**
- Dokumentiere den Grund ausführlich!
- Informiere das Team (Slack/Email)
- Beginne mit Ursachenanalyse

---

### 2. STATUS PRÜFEN

**Zweck:** Aktuellen Zustand des Kill Switch überprüfen

```bash
# Via Operator Script
./scripts/ops/kill_switch_ctl.sh status

# Via Python CLI
python3 -m src.risk_layer.kill_switch.cli status
```

**Ausgabe-Interpretation:**

```
┌────────────────────────────────────────┐
│ KILL SWITCH STATUS                     │
├────────────────────────────────────────┤
│ State:         🟢 ACTIVE               │   ← Trading erlaubt
│ Last Trigger:  Never                   │
│ Events:        0                       │
└────────────────────────────────────────┘
```

**Status-Symbole:**
- 🟢 **ACTIVE**: Normal-Betrieb, Trading erlaubt
- 🔴 **KILLED**: Notfall-Stopp aktiv, Trading blockiert
- 🟡 **RECOVERING**: Recovery-Phase, Trading noch blockiert
- ⚪ **DISABLED**: Deaktiviert (nur Backtest-Mode)

---

### 3. RECOVERY-PROZESS

**Voraussetzungen:**
- ✅ Trigger-Ursache behoben
- ✅ System Health OK
- ✅ Team informiert
- ✅ Approval Code verfügbar

**Schritt 1: Approval Code setzen**

```bash
# Approval Code als Umgebungsvariable setzen
export KILL_SWITCH_APPROVAL_CODE='dein_code_hier'

# Code aus .env Datei laden (falls vorhanden)
source .env
```

**Schritt 2: Health Check durchführen**

```bash
./scripts/ops/kill_switch_ctl.sh health
```

Erwartete Ausgabe bei gesundem System:
```
✅ HEALTH CHECK PASSED
   4 checks passed

Details:
   memory_available_mb: 2048
   cpu_percent: 45.2
   exchange_connected: True
   price_data_age_seconds: 5
```

**Schritt 3: Recovery starten**

```bash
./scripts/ops/kill_switch_ctl.sh recover
```

Das Script fragt nach:
1. **Reason for recovery**: Kurze Beschreibung (z.B. "Issue behoben, System stabil")
2. Verwendet automatisch `KILL_SWITCH_APPROVAL_CODE` aus Environment

**Erwartete Ausgabe:**
```
⏳ RECOVERY STARTED
Reason: Issue behoben, System stabil
Cooldown active. Use 'status' to check progress.

Next steps:
  1. Wait for cooldown period (5 minutes)
  2. Monitor status: kill_switch_ctl.sh status
  3. System will gradually restart with reduced position limits
```

**Schritt 4: Cooldown abwarten**

```bash
# Status regelmäßig prüfen
watch -n 10 './scripts/ops/kill_switch_ctl.sh status'
```

Nach **5 Minuten** wechselt Status automatisch zu ACTIVE.

**Schritt 5: Gradual Restart überwachen**

Nach Recovery startet das System mit **reduzierten Position Limits**:

| Zeit nach Recovery | Position Limit | Beschreibung |
|-------------------|----------------|--------------|
| 0 - 1h | 50% | Vorsichtiger Start |
| 1h - 2h | 75% | Erhöhte Limits |
| 2h+ | 100% | Vollständig recovered |

**Monitoring:**
```bash
# Logs überwachen
tail -f logs/kill_switch.log

# Trading-Aktivität prüfen
./scripts/ops/ops_center.sh monitor
```

---

## 📊 AUDIT TRAIL

### Audit-Events anzeigen

```bash
# Letzte 20 Events
./scripts/ops/kill_switch_ctl.sh audit

# Events der letzten 24 Stunden
./scripts/ops/kill_switch_ctl.sh audit --since 24h

# Events der letzten 7 Tage
./scripts/ops/kill_switch_ctl.sh audit --since 7d

# Spezifisches Datum
python3 -m src.risk_layer.kill_switch.cli audit \
  --since "2025-12-20" \
  --limit 100
```

**Ausgabe-Format:**
```
📋 AUDIT TRAIL (10 events)

Timestamp            Previous     New State    Triggered By    Reason
────────────────────────────────────────────────────────────────────────
2025-12-28 14:32:15  ACTIVE       KILLED       manual_cli      Maintenance required
2025-12-28 14:37:20  KILLED       RECOVERING   manual          Recovery requested by operator
2025-12-28 14:42:25  RECOVERING   ACTIVE       system          Recovery completed
```

### Audit-Dateien

**Speicherort:** `data&#47;kill_switch&#47;audit&#47;`

**Format:** JSONL (JSON Lines) - eine Zeile pro Event

**Rotation:**
- Daily (neue Datei jeden Tag)
- Size-based (max 10 MB pro Datei)

**Retention:** 90 Tage

**Manuelle Analyse:**
```bash
# Alle Events anzeigen
cat data/kill_switch/audit/kill_switch_audit_2025-12-28.jsonl | jq

# Nach State filtern
grep '"new_state":"KILLED"' data/kill_switch/audit/*.jsonl

# Komprimierte Logs lesen
zcat data/kill_switch/audit/kill_switch_audit_2025-12-20.jsonl.gz | jq
```

---

## 🏥 HEALTH CHECKS

### System Health prüfen

```bash
./scripts/ops/kill_switch_ctl.sh health
```

**Geprüfte Komponenten:**

1. **Memory**: Verfügbarer RAM
   - Minimum: 512 MB
   - Kritisch bei: <512 MB

2. **CPU**: CPU-Auslastung
   - Maximum: 80%
   - Kritisch bei: >80%

3. **Exchange Connection**: Verbindung zur Börse
   - Erforderlich: `True`
   - Kritisch bei: `False`

4. **Price Feed**: Aktualität der Kursdaten
   - Maximum Alter: 5 Minuten
   - Kritisch bei: >5 Minuten

**Fehlerbehandlung:**

Wenn Health Check fehlschlägt:
```
❌ HEALTH CHECK FAILED
   2 passed, 2 failed

Issues:
   - Insufficient memory: 384MB < 512MB
   - Exchange not connected
```

**Maßnahmen:**
1. Identifiziere das Problem
2. Behebe die Ursache
3. Wiederhole Health Check
4. Erst danach Recovery starten

---

## 🔧 TROUBLESHOOTING

### Problem: Kill Switch lässt sich nicht triggern

**Symptome:**
```
❌ Failed to trigger (already killed or disabled)
```

**Ursachen & Lösungen:**

1. **Bereits im KILLED State**
   - Prüfen: `./scripts/ops/kill_switch_ctl.sh status`
   - Lösung: Ist bereits getriggert, kein Handlungsbedarf

2. **Kill Switch DISABLED (Backtest Mode)**
   - Prüfen: `config/risk/kill_switch.toml` → `mode = "disabled"`
   - Lösung: Setze `mode = "active"` und restarte System

3. **Keine Permissions**
   - Prüfen: `ls -la scripts/ops/kill_switch_ctl.sh`
   - Lösung: `chmod +x scripts&#47;ops&#47;kill_switch_ctl.sh`

---

### Problem: Recovery funktioniert nicht

**Symptome:**
```
❌ Recovery request failed
Possible reasons:
  - Not in KILLED state
  - Invalid approval code
```

**Ursachen & Lösungen:**

1. **Nicht im KILLED State**
   - Prüfen: Status zeigt ACTIVE oder RECOVERING
   - Lösung: Recovery nur möglich von KILLED → RECOVERING

2. **Falscher Approval Code**
   - Prüfen: `echo $KILL_SWITCH_APPROVAL_CODE`
   - Lösung: Korrekten Code setzen oder aus `.env` laden

3. **Approval Code fehlt**
   ```bash
   export KILL_SWITCH_APPROVAL_CODE='correct_code_here'
   ```

4. **Cooldown noch aktiv**
   - Symptom: Status zeigt "Cooldown: 120s remaining"
   - Lösung: Warten bis Cooldown abgelaufen

---

### Problem: Health Check schlägt fehl

**Symptom:** Recovery blockiert durch fehlgeschlagene Health Checks

**Lösung nach Problem:**

**1. Memory-Problem:**
```bash
# Speicher-Verbrauch prüfen
ps aux --sort=-%mem | head -10

# Unnötige Prozesse beenden
kill <PID>

# System neustarten (falls nötig)
```

**2. CPU-Problem:**
```bash
# CPU-intensive Prozesse finden
top -o %CPU

# Load Average prüfen
uptime
```

**3. Exchange-Verbindung:**
```bash
# Netzwerk-Verbindung testen
ping api.kraken.com

# Exchange-Status prüfen (externe API)
curl https://status.kraken.com/api/v2/status.json
```

**4. Stale Price Data:**
```bash
# Logs prüfen
tail -f logs/data_pipeline.log

# Data Pipeline neustarten
./scripts/data/restart_pipeline.sh
```

---

### Problem: Gradual Restart zu langsam

**Symptom:** Position Limits bleiben bei 50% stecken

**Prüfen:**
```bash
# Aktuellen Status anzeigen
python3 -c "
from src.risk_layer.kill_switch.recovery import RecoveryManager
# ... check position_limit_factor
"
```

**Lösung:**

Option 1: Konfiguration anpassen (für zukünftige Recoveries)
```toml
# config/risk/kill_switch.toml
[kill_switch.recovery]
escalation_intervals = [1800, 3600]  # 30min, 1h statt 1h, 2h
```

Option 2: Manuell erhöhen (nur in Notfällen)
- Erfordert Code-Anpassung
- Kontaktiere Engineering Team

---

## 📞 ESKALATION

### Wann eskalieren?

Eskaliere an Engineering Team wenn:
- Kill Switch lässt sich nicht deaktivieren
- Unerwartetes Verhalten (State Machine hängt)
- Health Checks schlagen dauerhaft fehl
- Audit Trail zeigt ungewöhnliche Muster
- System startet nach Recovery nicht korrekt

### Kontakte

**Emergency Hotline:** [Nummer eintragen]

**Engineering On-Call:** [Nummer eintragen]

**Slack:** `#peak-trade-ops`

### Informationen sammeln vor Eskalation

```bash
# 1. Status exportieren
./scripts/ops/kill_switch_ctl.sh status > /tmp/ks_status.txt

# 2. Audit Trail exportieren
./scripts/ops/kill_switch_ctl.sh audit --since 24h > /tmp/ks_audit.txt

# 3. Logs sammeln
tail -n 1000 logs/kill_switch.log > /tmp/ks_logs.txt

# 4. Health Check
./scripts/ops/kill_switch_ctl.sh health > /tmp/ks_health.txt

# Alle Dateien an Team senden
```

---

## 📋 CHECKLISTEN

### ✅ Tägliche Prüfung

- [ ] Kill Switch Status prüfen: `kill_switch_ctl.sh status`
- [ ] Letzte Events prüfen: `kill_switch_ctl.sh audit --since 24h`
- [ ] Health Check durchführen: `kill_switch_ctl.sh health`
- [ ] Approval Code verfügbar und aktuell

### ✅ Nach Trigger

- [ ] Ursache identifiziert und dokumentiert
- [ ] Team informiert (Slack + Email)
- [ ] Post-Mortem geplant
- [ ] Präventive Maßnahmen identifiziert

### ✅ Nach Recovery

- [ ] System-Stabilität überwacht (erste 2 Stunden)
- [ ] Position Limits prüfen (50% → 75% → 100%)
- [ ] Audit Trail verifiziert
- [ ] Dokumentation aktualisiert

---

**Letzte Aktualisierung:** 2025-12-28  
**Version:** 1.0  
**Maintainer:** Peak_Trade Ops Team
