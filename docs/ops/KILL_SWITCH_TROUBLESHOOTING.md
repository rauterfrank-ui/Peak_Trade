# Peak_Trade Kill Switch – Troubleshooting Guide

**Version:** 1.0  
**Datum:** 2025-12-28  
**Für:** Operations Team & Engineers

---

## 🎯 Übersicht

Dieser Guide hilft bei der Diagnose und Lösung von Problemen mit dem Emergency Kill Switch.

**Bei akuten Problemen:** Siehe [KILL_SWITCH_RUNBOOK.md](KILL_SWITCH_RUNBOOK.md) für Standard-Operationen.

---

## 🔍 Diagnose-Checkliste

### Quick Health Check

```bash
# 1. Kill Switch Status
./scripts/ops/kill_switch_ctl.sh status

# 2. Logs prüfen
tail -f logs/kill_switch.log

# 3. State File prüfen
cat data/kill_switch/state.json

# 4. Audit Trail
./scripts/ops/kill_switch_ctl.sh audit --limit 10
```

---

## ❌ Problem: Kill Switch lässt sich nicht triggern

### Symptom
```
❌ Failed to trigger (already killed or disabled)
```

### Diagnose

**Schritt 1: Status prüfen**
```bash
./scripts/ops/kill_switch_ctl.sh status
```

**Mögliche Ursachen:**

#### A) Bereits im KILLED State
**Erkennung:** Status zeigt 🔴 KILLED

**Lösung:** Bereits getriggert, kein Handlungsbedarf
```bash
# Status bestätigen
./scripts/ops/kill_switch_ctl.sh status

# Falls nötig: Recovery
./scripts/ops/kill_switch_ctl.sh recover
```

#### B) Kill Switch DISABLED (Backtest Mode)
**Erkennung:** Status zeigt ⚪ DISABLED oder Fehlermeldung

**Diagnose:**
```bash
# Config prüfen
grep "mode" config/risk/kill_switch.toml
# Output: mode = "disabled"
```

**Lösung:**
```toml
# config/risk/kill_switch.toml
[kill_switch]
mode = "active"  # Ändern von "disabled" zu "active"
```

**Nach Änderung:** System neustarten

#### C) Permissions-Problem
**Diagnose:**
```bash
ls -la scripts/ops/kill_switch_ctl.sh
# Sollte: -rwxr-xr-x (executable)
```

**Lösung:**
```bash
chmod +x scripts/ops/kill_switch_ctl.sh
```

---

## ❌ Problem: Recovery funktioniert nicht

### Symptom
```
❌ Recovery request failed
Possible reasons:
  - Not in KILLED state
  - Invalid approval code
```

### Diagnose

**Schritt 1: Aktuellen State prüfen**
```bash
./scripts/ops/kill_switch_ctl.sh status
```

### Mögliche Ursachen

#### A) Nicht im KILLED State
**Erkennung:** State ist ACTIVE oder RECOVERING

**Erklärung:** Recovery nur von KILLED → RECOVERING möglich

**Lösung:**
- Falls ACTIVE: Kein Recovery nötig
- Falls RECOVERING: Warten bis Cooldown abgelaufen

#### B) Falscher Approval Code
**Diagnose:**
```bash
# Approval Code in Environment prüfen
echo $KILL_SWITCH_APPROVAL_CODE
# Output: (leer oder falsch)
```

**Lösung:**
```bash
# Korrekten Code setzen
export KILL_SWITCH_APPROVAL_CODE='correct_code_here'

# Aus .env File laden (falls vorhanden)
source .env

# Recovery erneut versuchen
./scripts/ops/kill_switch_ctl.sh recover
```

#### C) Approval Code fehlt komplett
**Erkennung:** `KILL_SWITCH_APPROVAL_CODE` ist nicht gesetzt

**Lösung:**
```bash
# 1. Code vom Team-Lead erhalten
# 2. In Environment setzen
export KILL_SWITCH_APPROVAL_CODE='team_provided_code'

# 3. Oder in .env File speichern (für permanente Verfügbarkeit)
echo "KILL_SWITCH_APPROVAL_CODE='team_provided_code'" >> .env
source .env
```

#### D) Cooldown noch aktiv
**Erkennung:** Status zeigt "Cooldown: XXs remaining"

**Erklärung:** Cooldown von 5 Minuten nach Recovery-Request

**Lösung:** Warten bis Cooldown abgelaufen
```bash
# Cooldown überwachen
watch -n 10 './scripts/ops/kill_switch_ctl.sh status'
```

---

## ❌ Problem: Health Check schlägt fehl

### Symptom
```
❌ HEALTH CHECK FAILED
   2 passed, 2 failed

Issues:
   - Insufficient memory: 384MB < 512MB
   - Exchange not connected
```

### Diagnose nach Problem-Typ

#### A) Memory-Problem
**Symptom:** "Insufficient memory: XXXMB < 512MB"

**Diagnose:**
```bash
# 1. Speicher-Verbrauch prüfen
free -m

# 2. Top Memory-Consumer finden
ps aux --sort=-%mem | head -10

# 3. Kill Switch Schwellwert prüfen
grep "min_memory_available_mb" config/risk/kill_switch.toml
```

**Lösungen:**

**Option 1: Speicher freigeben**
```bash
# Unnötige Prozesse beenden
kill <PID>

# Cache leeren (vorsichtig!)
sync; echo 3 > /proc/sys/vm/drop_caches  # Nur als root
```

**Option 2: Schwellwert anpassen** (temporär für Recovery)
```toml
# config/risk/kill_switch.toml
[kill_switch.recovery]
min_memory_available_mb = 256  # Reduzieren (nur temporär!)
```

**Option 3: System neustarten**
```bash
sudo reboot
```

#### B) CPU-Problem
**Symptom:** "High CPU usage: XX% > 80%"

**Diagnose:**
```bash
# CPU-intensive Prozesse finden
top -o %CPU

# Load Average prüfen
uptime
```

**Lösungen:**

**Option 1: CPU-intensive Prozesse beenden**
```bash
# Identifizieren und beenden
kill <PID>
```

**Option 2: Warten**
- Falls temporäre Spitze: 5-10 Minuten warten
- Dann Health Check erneut

**Option 3: Schwellwert anpassen** (temporär)
```toml
[kill_switch.recovery]
max_cpu_percent = 95  # Erhöhen (nur temporär!)
```

#### C) Exchange-Verbindung
**Symptom:** "Exchange not connected"

**Diagnose:**
```bash
# 1. Netzwerk-Verbindung testen
ping api.kraken.com

# 2. Exchange-Status prüfen (externe API)
curl https://status.kraken.com/api/v2/status.json | jq

# 3. Eigene Exchange-Connection prüfen
python3 scripts/inspect_exchange.py --mode status
```

**Lösungen:**

**Option 1: Verbindung wiederherstellen**
```bash
# Laufende Sessions prüfen und ggf. neu starten (Preisdaten vom Orchestrator)
python3 scripts/testnet_orchestrator_cli.py status --config config/config.toml
python3 scripts/testnet_orchestrator_cli.py stop --all --config config/config.toml
# Neue Session starten – siehe LIVE_OPERATIONAL_RUNBOOKS
```

**Option 2: Exchange-Check deaktivieren** (nur für Recovery!)
```toml
# config/risk/kill_switch.toml
[kill_switch.recovery]
require_exchange_connection = false  # Temporär!
```

**Wichtig:** Nach erfolgreicher Recovery wieder aktivieren!

#### D) Stale Price Data
**Symptom:** "Stale price data (XXXs old)"

**Diagnose:**
```bash
# 1. Laufende Sessions prüfen (Preisdaten vom Live/Testnet-Orchestrator)
python3 scripts/testnet_orchestrator_cli.py status --config config/config.toml

# 2. Execution-Telemetrie prüfen (falls Session läuft)
python3 scripts/view_execution_telemetry.py --path logs/execution --limit 20

# 3. Logs auf Rate-Limit-Hinweise prüfen
grep -r "rate_limit\|rate limit" logs/ 2>/dev/null | tail -5
```

**Lösungen:**

**Option 1: Session neu starten (frische Preisdaten)**
```bash
python3 scripts/testnet_orchestrator_cli.py stop --all --config config/config.toml
# Dann neue Session starten – siehe LIVE_OPERATIONAL_RUNBOOKS
```

**Option 2: Exchange API-Key prüfen**
```bash
# Prüfe ob API-Key noch gültig
echo $KRAKEN_API_KEY  # Sollte gesetzt sein
```

**Option 3: Price Feed Check deaktivieren** (temporär)
```toml
[kill_switch.recovery]
require_price_feed = false  # Temporär!
```

---

## ❌ Problem: Gradual Restart funktioniert nicht

### Symptom
Position Limits bleiben bei 50% stecken

### Diagnose

**Schritt 1: Recovery Status prüfen**
```bash
./scripts/ops/kill_switch_ctl.sh status
```

**Schritt 2: Verstrichene Zeit prüfen**
```python
# Im Python-Interpreter oder Script:
from src.risk_layer.kill_switch.recovery import RecoveryManager
manager = RecoveryManager(config, health_checker)
print(f"Current factor: {manager.position_limit_factor}")
print(f"Stage: {manager.current_stage}")
```

### Lösungen

#### Option 1: Warten
- Initial: 50% Position Limits
- Nach 1h: 75% Position Limits
- Nach 2h: 100% Position Limits

**Monitoring:**
```bash
# Position Limit Factor überwachen
watch -n 300 'echo "Factor: $(date)"'  # Alle 5 Minuten
```

#### Option 2: Config anpassen
**Für zukünftige Recoveries:**
```toml
# config/risk/kill_switch.toml
[kill_switch.recovery]
escalation_intervals = [1800, 3600]  # 30min, 1h statt 1h, 2h
```

#### Option 3: Gradual Restart deaktivieren
**Nur in Notfällen:**
```toml
[kill_switch.recovery]
gradual_restart_enabled = false  # Direkt auf 100%
```

**Wichtig:** System neustarten nach Config-Änderung!

---

## ❌ Problem: State File korrupt

### Symptom
```
ERROR: Corrupt state file
```

### Diagnose

**Schritt 1: State File prüfen**
```bash
# Versuche State File zu lesen
cat data/kill_switch/state.json

# Prüfe auf valides JSON
jq . data/kill_switch/state.json
```

**Schritt 2: Backups prüfen**
```bash
ls -lh data/kill_switch/backups/
```

### Lösungen

#### Option 1: Restore from Backup
```python
from src.risk_layer.kill_switch.persistence import StatePersistence

persistence = StatePersistence("data/kill_switch/state.json")

# Liste Backups
backups = persistence.list_backups()
print(f"Available backups: {len(backups)}")

# Restore from latest
persistence.restore_from_backup()
```

**Oder via Bash:**
```bash
# Manuell neuestes Backup kopieren
cp data/kill_switch/backups/state_*.json data/kill_switch/state.json
```

#### Option 2: State neu initialisieren
```python
from src.risk_layer.kill_switch import KillSwitch, load_config

config = load_config()
kill_switch = KillSwitch(config.get("kill_switch", {}))

# State ist jetzt ACTIVE (initial state)
```

**Oder State File löschen:**
```bash
# Löschen (System startet mit ACTIVE bei nächstem Load)
rm data/kill_switch/state.json

# Laufende Sessions stoppen, damit neuer State sauber übernommen wird
python3 scripts/testnet_orchestrator_cli.py stop --all --config config/config.toml
# Für erneuten Start siehe docs/LIVE_OPERATIONAL_RUNBOOKS.md
```

---

## ❌ Problem: Audit Trail nicht lesbar

### Symptom
- Audit-Befehle liefern keine oder falsche Daten
- Fehler beim Lesen von Audit Files

### Diagnose

**Schritt 1: Audit Dateien prüfen**
```bash
# Liste Audit Files
ls -lh data/kill_switch/audit/

# Prüfe neueste Datei
tail -5 data/kill_switch/audit/kill_switch_audit_*.jsonl

# Versuche JSONL zu parsen
head -1 data/kill_switch/audit/kill_switch_audit_*.jsonl | jq
```

### Lösungen

#### Problem: Permissions
```bash
# Prüfe Permissions
ls -la data/kill_switch/audit/

# Falls nötig: Korrigieren
chmod 644 data/kill_switch/audit/*.jsonl
```

#### Problem: Korrupte Zeilen
**Erklärung:** Einzelne korrupte Zeilen werden automatisch übersprungen

**Manuelle Bereinigung (falls nötig):**
```bash
# Prüfe auf korrupte Zeilen
for file in data/kill_switch/audit/*.jsonl; do
    echo "Checking $file..."
    while IFS= read -r line; do
        echo "$line" | jq . > /dev/null 2>&1 || echo "Corrupt: $line"
    done < "$file"
done
```

#### Problem: Compression-Fehler
```bash
# Test compressed files
for file in data/kill_switch/audit/*.jsonl.gz; do
    echo "Testing $file..."
    zcat "$file" | head -1 | jq
done

# Falls korrupt: Neu komprimieren
gunzip data/kill_switch/audit/corrupt_file.jsonl.gz
gzip data/kill_switch/audit/corrupt_file.jsonl
```

---

## ❌ Problem: CLI funktioniert nicht

### Symptom
```
pyenv: python: command not found
```

### Diagnose

**Python-Version prüfen:**
```bash
# Python verfügbar?
which python
which python3

# Version prüfen
python3 --version
```

### Lösungen

#### Option 1: Python Alias setzen
```bash
alias python=python3
```

#### Option 2: Direkter Python3-Aufruf
```bash
python3 -m src.risk_layer.kill_switch.cli status
```

#### Option 3: Ops Script nutzen (bevorzugt)
```bash
# Script erkennt automatisch python3
./scripts/ops/kill_switch_ctl.sh status
```

---

## 🔄 Problem: System hängt im RECOVERING State

### Symptom
- State ist RECOVERING seit > 10 Minuten
- Cooldown scheint nicht abzulaufen

### Diagnose

```bash
# Status mit Cooldown-Info
./scripts/ops/kill_switch_ctl.sh status

# State File prüfen
cat data/kill_switch/state.json | jq .
```

### Lösungen

#### Option 1: Cooldown-Zeit abwarten
**Standard Cooldown:** 5 Minuten

```bash
# Warten und Status überwachen
watch -n 30 './scripts/ops/kill_switch_ctl.sh status'
```

#### Option 2: Complete Recovery manuell triggern
```python
from src.risk_layer.kill_switch import KillSwitch, load_config

config = load_config()
ks = KillSwitch(config.get("kill_switch", {}))

# Force complete recovery (nach Cooldown)
result = ks.complete_recovery()
print(f"Recovery complete: {result}")
```

#### Option 3: State manuell zurücksetzen (NOTFALL)
**Nur in Extremfällen!**

```bash
# 1. Backup erstellen
cp data/kill_switch/state.json data/kill_switch/state_backup_manual.json

# 2. State löschen
rm data/kill_switch/state.json

# 3. System neustarten
# System startet mit ACTIVE State
```

---

## 📊 Logging & Debugging

### Log-Level erhöhen

```toml
# config/risk/kill_switch.toml
[kill_switch]
log_level = "DEBUG"  # Von INFO auf DEBUG
```

### Logs Analysieren

```bash
# Kill Switch Logs
tail -f logs/kill_switch.log

# Fehler finden
grep "ERROR" logs/kill_switch.log

# Trigger Events
grep "TRIGGERED" logs/kill_switch.log

# State Changes
grep "State:" logs/kill_switch.log
```

### Debug-Modus

```python
# In Python-Console oder Script:
import logging
logging.basicConfig(level=logging.DEBUG)

from src.risk_layer.kill_switch import KillSwitch
# ... debug operations
```

---

## 🆘 Eskalation

### Wann eskalieren?

Eskaliere an Engineering Team wenn:
- ❌ Kill Switch lässt sich nicht aktivieren/deaktivieren
- ❌ State Machine hängt
- ❌ Health Checks schlagen dauerhaft fehl
- ❌ Unerwartetes Verhalten (State Transitions)
- ❌ Data Corruption (State/Audit Files)
- ❌ System startet nicht nach Recovery

### Informationen sammeln

**Vor Eskalation:**
```bash
# 1. Status exportieren
./scripts/ops/kill_switch_ctl.sh status > /tmp/ks_status.txt

# 2. Audit Trail
./scripts/ops/kill_switch_ctl.sh audit --since 24h > /tmp/ks_audit.txt

# 3. Logs
tail -n 1000 logs/kill_switch.log > /tmp/ks_logs.txt

# 4. Health Check
./scripts/ops/kill_switch_ctl.sh health > /tmp/ks_health.txt

# 5. Config
cat config/risk/kill_switch.toml > /tmp/ks_config.toml

# 6. State Files
cat data/kill_switch/state.json > /tmp/ks_state.json

# Alle Dateien archivieren
tar -czf kill_switch_debug_$(date +%Y%m%d_%H%M%S).tar.gz /tmp/ks_*
```

### Kontakte

**Engineering On-Call:** [Nummer eintragen]  
**Slack:** `#peak-trade-ops`  
**Email:** ops@peak-trade.com

---

## 📚 Weitere Ressourcen

- **Runbook:** [KILL_SWITCH_RUNBOOK.md](KILL_SWITCH_RUNBOOK.md)
- **Tech Docs:** [../risk/KILL_SWITCH.md](../risk/KILL_SWITCH.md)
- **Architecture:** [../risk/KILL_SWITCH_ARCHITECTURE.md](../risk/KILL_SWITCH_ARCHITECTURE.md)

---

**Letzte Aktualisierung:** 2025-12-28  
**Version:** 1.0  
**Maintainer:** Peak_Trade Ops Team
