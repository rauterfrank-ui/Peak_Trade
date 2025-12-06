# Peak_Trade – Live Operational Runbooks

> **Phase:** 39 – Live-Deployment-Playbook & Ops-Runbooks
> **Version:** v1.1
> **Zweck:** Konkrete Step-by-Step-Anleitungen für Operations
> **Zielgruppe:** Entwickler, Operatoren

---

## 1. Einleitung

### 1.1 Was ist ein Runbook?

Ein **Runbook** ist eine dokumentierte Schritt-für-Schritt-Anleitung für wiederkehrende oder kritische Operationen. Runbooks stellen sicher, dass:

- Operationen konsistent durchgeführt werden
- Im Notfall keine Zeit mit Nachdenken verloren geht
- Wissen nicht nur in einzelnen Köpfen steckt
- Fehler durch vergessene Schritte vermieden werden

### 1.2 Verwendung dieses Dokuments

- **Standard-Runbooks** (Abschnitte 2-6): Für normale, wiederkehrende Operationen
- **Incident-Runbooks** (Abschnitte 7-10): Für Problembehebung und Incidents
- **Kommunikation & Verantwortung** (Abschnitt 11): Rollen und Entscheidungswege

### 1.3 Runbook-Index

**Standard-Runbooks:**

| # | Runbook | Anwendungsfall |
|---|---------|----------------|
| 2 | Testnet-Run starten | Testnet-Session hochfahren |
| 3 | Live-Run (Small Size) starten | Erster echter Live-Betrieb |
| 4 | Systemstart nach Wartung | Wiederanlauf nach Pause/Update |
| 5 | Sicheres Beenden laufender Sessions | Normales Herunterfahren |
| 6 | System-Health-Check | Tägliche Prüfung |

**Incident-Runbooks:**

| # | Runbook | Anwendungsfall |
|---|---------|----------------|
| 7 | Exchange-Fehler behandeln | API-Fehler, Timeouts, Rate-Limits |
| 8 | Risk-Limit-Verletzung | Umgang mit blockierten Orders |
| 9 | Auffällige PnL-Divergenzen | Performance weicht stark ab |
| 10 | Unvollständige Daten / Data-Gaps | Fehlende Marktdaten |

---

## 2. Runbook: Testnet-Run starten

### 2.1 Voraussetzungen

- [ ] Python-Environment aktiviert
- [ ] API-Credentials gesetzt (Environment-Variablen)
- [ ] `[exchange].default_type` korrekt konfiguriert
- [ ] Readiness-Check bestanden

### 2.2 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 1: Testnet-Run starten
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# Schritt 2: API-Credentials setzen (falls nicht in .bashrc/.zshrc)
export KRAKEN_TESTNET_API_KEY="your-testnet-api-key"
export KRAKEN_TESTNET_API_SECRET="your-testnet-api-secret"

# Schritt 3: Baseline-Tests prüfen
pytest -q --tb=no
# Erwartung: Alle Tests grün (1316+ passed, 4 skipped)

# Schritt 4: Readiness-Check
python scripts/check_live_readiness.py --stage testnet
# Erwartung: "Readiness-Check PASSED"

# Schritt 5: Smoke-Test
python scripts/smoke_test_testnet_stack.py
# Erwartung: "Smoke-Test PASSED"

# Schritt 6: Testnet-Session starten
python scripts/run_testnet_session.py --profile quick_smoke --verbose
# Oder mit DummyExchangeClient (Offline):
# python scripts/run_testnet_session.py --use-dummy --verbose

# Schritt 7: Logs beobachten (in zweitem Terminal)
tail -f logs/*.log
```

### 2.3 Erwartetes Verhalten

- Session startet ohne Fehler
- Erste Signale/Orders werden geloggt
- Risk-Limits werden geprüft
- Bei `validate_only=true`: Orders werden validiert, nicht ausgeführt

### 2.4 Bei Problemen

| Problem | Aktion |
|---------|--------|
| "API-Key not set" | Environment-Variablen prüfen |
| "Readiness-Check failed" | Output lesen, Voraussetzungen erfüllen |
| "Connection error" | Netzwerk/Exchange-Status prüfen |
| Unerwartete Fehler | → Runbook 4 (Pausieren), dann analysieren |

---

## 3. Runbook: Live-Run (Small Size) starten

### 3.1 Zweck

Erster echter Live-Handel mit stark begrenztem Kapital. **Nur nach vollständiger Testnet-Phase!**

### 3.2 Voraussetzungen

```
╔══════════════════════════════════════════════════════════════════════════╗
║  WARNUNG: Dieser Runbook betrifft ECHTES GELD!                           ║
║  Alle Schritte mit erhöhter Sorgfalt ausführen.                          ║
║  Two-Man-Rule beachten!                                                   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

- [ ] Checklist "Testnet → Live" vollständig abgehakt
- [ ] Two-Man-Rule-Freigabe dokumentiert
- [ ] Live-API-Credentials sicher hinterlegt
- [ ] Risk-Limits konservativ konfiguriert
- [ ] Kill-Switch getestet
- [ ] Notfall-Kontakte aktuell

### 3.3 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Live-Run (Small Size) starten
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Environment aktivieren (beide Personen anwesend!)
cd ~/Peak_Trade
source .venv/bin/activate

# Schritt 2: Live-Credentials setzen
# NIEMALS in Logs oder Terminals mit History speichern!
export KRAKEN_API_KEY="..."
export KRAKEN_API_SECRET="..."

# Schritt 3: Finaler Test-Run
pytest tests/ -q --tb=short
# Erwartung: Alle Tests grün

# Schritt 4: Readiness-Check für Live
python scripts/check_live_readiness.py --stage live
# Erwartung: PASSED

# Schritt 5: Risk-Limits verifizieren
python scripts/check_live_risk_limits.py
# Ausgabe prüfen: Limits konservativ?

# Schritt 6: Order-Preview (Dry-Run)
python scripts/preview_live_orders.py --strategy <STRATEGIE> --dry-run
# Erwartete Orders prüfen: Sehen sie vernünftig aus?

# Schritt 7: Go-Live (KRITISCHER SCHRITT!)
# Beide Personen bestätigen mündlich: "Ready to go live"
python scripts/send_live_orders_dry_run.py --strategy <STRATEGIE> --mode live

# Schritt 8: Erste Order überwachen
# Terminal 1: Live-Run läuft
# Terminal 2: Logs beobachten
tail -f logs/*.log

# Schritt 9: Nach erstem erfolgreichen Trade
# - Trade dokumentieren
# - Screenshots/Logs archivieren
# - Monitoring-Alerts bestätigen
```

### 3.4 Erwartete Outputs

- Erste Order wird an Exchange gesendet
- Bestätigung von Exchange empfangen
- Risk-Limits werden geprüft (keine Blockierung)
- PnL-Tracking beginnt

### 3.5 Bei Problemen

| Problem | Sofortmaßnahme |
|---------|----------------|
| Order rejected | Pausieren, Logs prüfen, Ursache finden |
| Risk-Limit blockiert | Pausieren, Limits prüfen |
| API-Fehler | Pausieren, Exchange-Status prüfen |
| Unerwartetes Verhalten | SOFORT Kill-Switch, dann analysieren |

---

## 4. Runbook: Systemstart nach Wartung

### 4.1 Zweck

Sicherer Wiederanlauf nach geplanter Wartung, Update oder nach einer Pause.

### 4.2 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Systemstart nach Wartung
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Änderungen prüfen (falls Update)
cd ~/Peak_Trade
git log --oneline -5
git status

# Schritt 2: Dependencies aktualisieren (falls nötig)
source .venv/bin/activate
pip install -e ".[dev]"

# Schritt 3: Tests ausführen
pytest tests/ -q --tb=short
# MUSS grün sein vor Wiederanlauf!

# Schritt 4: Config prüfen
# Wurde die Config geändert?
git diff config/config.toml

# Schritt 5: Readiness-Check
python scripts/check_live_readiness.py --stage <STUFE>
# <STUFE> = shadow, testnet, oder live

# Schritt 6: Smoke-Test
python scripts/smoke_test_testnet_stack.py

# Schritt 7: Wiederanlauf
# Je nach Stufe das entsprechende Start-Runbook ausführen

# Schritt 8: Erhöhtes Monitoring
# Erste 2 Stunden nach Wiederanlauf: Logs aktiv beobachten
tail -f logs/*.log
```

### 4.3 Checkliste nach Wiederanlauf

- [ ] Prozesse laufen (`pgrep -af python.*run_`)
- [ ] Keine Fehler in Logs
- [ ] Erste Signale/Orders werden generiert
- [ ] Risk-Limits aktiv
- [ ] Monitoring funktioniert

---

## 5. Runbook: Sicheres Beenden laufender Sessions

### 5.1 Zweck

Sauberes, kontrolliertes Herunterfahren des Systems ohne Datenverlust.

### 5.2 Schritt-für-Schritt: Normales Beenden

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Sicheres Beenden (Normal)
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Laufende Prozesse identifizieren
pgrep -af "python.*run_"

# Schritt 2: Graceful Shutdown
# Option A: Im Terminal Ctrl+C
# Option B: SIGTERM senden
kill <PID>

# Schritt 3: Warten auf Cleanup (max. 30 Sekunden)
sleep 5
pgrep -af "python.*run_"
# Sollte leer sein

# Schritt 4: Verifizieren
# - Keine Prozesse mehr laufen
# - Logs zeigen "Shutdown complete" oder ähnlich

# Schritt 5: Bei Testnet/Live - Offene Orders prüfen
# Manuell auf Exchange oder via Script
python scripts/check_open_orders.py

# Schritt 6: Logs sichern (optional)
cp -r logs/ logs_shutdown_$(date +%Y%m%d_%H%M%S)/

# Schritt 7: Dokumentieren
echo "$(date): System ordnungsgemäß beendet - Grund: [GRUND]" >> logs/operations.log
```

### 5.3 Schritt-für-Schritt: Notfall-Beenden

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Sicheres Beenden (Notfall)
# ═══════════════════════════════════════════════════════════════════════

# NUR wenn Graceful Shutdown nicht funktioniert!

# Schritt 1: Force-Kill aller Prozesse
pkill -9 -f "python.*run_"
pkill -9 -f "python.*testnet"
pkill -9 -f "python.*shadow"
pkill -9 -f "python.*live"

# Schritt 2: Verifizieren
pgrep -af "python.*peak"

# Schritt 3: Bei Live - Offene Orders MANUELL prüfen!
# Auf Exchange-Website einloggen und offene Orders checken

# Schritt 4: Logs sofort sichern
cp -r logs/ logs_emergency_$(date +%Y%m%d_%H%M%S)/
cp -r reports/ reports_emergency_$(date +%Y%m%d_%H%M%S)/

# Schritt 5: Incident-Report starten
# → Siehe RUNBOOKS_AND_INCIDENT_HANDLING.md
```

---

## 6. Runbook: System-Health-Check

### 6.1 Zweck

Tägliche Prüfung der Systemgesundheit. Am besten morgens vor Trading-Start.

### 6.2 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Täglicher Health-Check
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# Schritt 2: Tests laufen lassen
pytest -q --tb=no
# Erwartung: Alle grün

# Schritt 3: Readiness-Check
python scripts/check_live_readiness.py --stage testnet
# Erwartung: PASSED

# Schritt 4: Letzte Runs prüfen
python scripts/experiments_explorer.py --limit 10

# Schritt 5: Logs auf Fehler prüfen
grep -i "error\|critical\|exception" logs/*.log | tail -20

# Schritt 6: Disk-Space prüfen
df -h ~/Peak_Trade
# Erwartung: > 10% frei

# Schritt 7: Dokumentieren
echo "$(date): Health-Check OK" >> logs/operations.log
```

### 6.3 Health-Check Checkliste

| Check | Befehl | Erwartung |
|-------|--------|-----------|
| Tests grün | `pytest -q --tb=no` | Alle passed |
| Readiness | `python scripts/check_live_readiness.py` | PASSED |
| Keine Fehler in Logs | `grep -i error logs/*.log` | Leer oder bekannt |
| Disk-Space | `df -h` | > 10% frei |
| Prozesse laufen | `pgrep -af python.*run_` | Je nach Erwartung |

---

## 7. Incident-Runbook: Exchange-Fehler behandeln

### 7.1 Fehlertypen

| Fehler | Ursache | Schweregrad |
|--------|---------|-------------|
| `ExchangeNetworkError` | Netzwerk/Exchange down | Medium |
| `ExchangeRateLimitError` | Zu viele Requests | Low |
| `ExchangeAuthenticationError` | API-Keys ungültig | High |
| `ExchangeOrderError` | Order abgelehnt | Medium |
| `ExchangeAPIError` | Allgemeiner API-Fehler | Medium |

### 7.2 Schritt-für-Schritt: Netzwerk-/Timeout-Fehler

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 2a: Netzwerk-Fehler behandeln
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Fehler identifizieren
# Typische Log-Nachricht:
# "[EXCHANGE] ExchangeNetworkError: Request timeout"

# Schritt 2: Exchange-Status prüfen
# Kraken: https://status.kraken.com/
curl -s https://api.kraken.com/0/public/Time | jq .

# Schritt 3: Eigene Netzwerkverbindung prüfen
ping -c 3 api.kraken.com

# Schritt 4: Entscheidung
# - Exchange down → Warten, System läuft weiter (Retries)
# - Eigenes Netzwerk → Netzwerk fixen
# - Dauerhaft → Pausieren (Runbook 4)

# Schritt 5: Nach Behebung
# System sollte automatisch wiederaufnehmen (Retry-Logik)
# Bei Testnet: Keine offenen Positionen zu schließen
```

### 7.3 Schritt-für-Schritt: Rate-Limit-Fehler

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 2b: Rate-Limit-Fehler behandeln
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Fehler identifizieren
# Typische Log-Nachricht:
# "[EXCHANGE] ExchangeRateLimitError: Rate limit exceeded"

# Schritt 2: Abwarten
# System sollte automatisch pausieren und Retry versuchen
# Typische Wartezeit: 60-120 Sekunden

# Schritt 3: Falls persistent
# Config prüfen:
grep -A 5 "rate_limit" config.toml

# Schritt 4: Rate-Limit erhöhen (falls zu niedrig)
# In config.toml:
# [exchange.kraken_testnet]
# rate_limit_ms = 2000  # Erhöhen von 1000 auf 2000

# Schritt 5: System neu starten (falls Config geändert)
```

### 7.4 Schritt-für-Schritt: Authentication-Fehler

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 2c: Authentication-Fehler behandeln
# ═══════════════════════════════════════════════════════════════════════

# ACHTUNG: Dieser Fehler ist KRITISCH!

# Schritt 1: Sofort pausieren
# Ctrl+C oder kill <PID>

# Schritt 2: API-Keys prüfen
echo "API-Key gesetzt: ${KRAKEN_TESTNET_API_KEY:+Ja}"
echo "API-Secret gesetzt: ${KRAKEN_TESTNET_API_SECRET:+Ja}"

# Schritt 3: Keys validieren
# - Auf Exchange-Website einloggen
# - API-Key-Status prüfen (aktiv? Berechtigungen?)
# - Bei Kompromittierung: SOFORT KEY ROTIEREN!

# Schritt 4: Neue Keys setzen (falls rotiert)
export KRAKEN_TESTNET_API_KEY="new-key"
export KRAKEN_TESTNET_API_SECRET="new-secret"

# Schritt 5: Neu starten
python scripts/check_live_readiness.py --stage testnet
```

---

## 8. Incident-Runbook: Risk-Limit-Verletzung

### 8.1 Symptome

- Log-Nachricht: `[RISK] Order blocked: ...`
- Orders werden nicht ausgeführt
- System läuft weiter, aber handelt nicht

### 8.2 Risk-Limit-Typen

| Limit | Beschreibung | Reaktion |
|-------|--------------|----------|
| `max_order_notional` | Einzelorder zu groß | Order blockiert |
| `max_daily_loss_abs` | Tagesverlust erreicht | Alle Orders blockiert |
| `max_daily_loss_pct` | % Tagesverlust erreicht | Alle Orders blockiert |
| `max_symbol_exposure` | Position in Symbol zu groß | Neue Orders blockiert |
| `max_total_exposure` | Gesamt-Exposure zu hoch | Neue Orders blockiert |

### 8.3 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 3: Risk-Limit-Verletzung behandeln
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Verletzung identifizieren
# Typische Log-Nachricht:
# "[RISK] Order blocked: max_order_notional exceeded (500 > 100)"

# Schritt 2: Aktuelle Risk-Limits prüfen
grep -A 15 "\[live_risk\]" config.toml

# Schritt 3: Aktuelle Metriken prüfen
python -c "
from src.core.peak_config import load_config
from src.live.risk_limits import LiveRiskLimits

cfg = load_config()
limits = LiveRiskLimits.from_config(cfg, starting_cash=10000)
print('Max Order Notional:', limits.config.max_order_notional)
print('Max Daily Loss Abs:', limits.config.max_daily_loss_abs)
"

# Schritt 4: Entscheidung
# Option A: Limits sind korrekt, Order war zu groß
#           → Order-Größe reduzieren, System läuft weiter
#
# Option B: Limits sind zu streng
#           → Limits in config.toml anpassen, neu starten
#
# Option C: Tagesverlust-Limit erreicht
#           → Trading für heute beenden (System läuft, blockiert aber)

# Schritt 5: Falls Limits angepasst werden
# In config.toml:
# [live_risk]
# max_order_notional = 2000.0  # Von 1000 auf 2000 erhöht

# Schritt 6: Bei Tagesverlust-Limit
# NICHT umgehen! Das Limit existiert aus gutem Grund.
# Morgen wird der Counter zurückgesetzt.
```

### 8.4 Risk-Limits temporär lockern (NUR FÜR TESTS!)

```bash
# ⚠️ NUR FÜR TESTNET/SHADOW - NIEMALS FÜR LIVE!

# Option 1: In Config anpassen
# [live_risk]
# max_order_notional = 10000.0  # Temporär erhöht

# Option 2: Via CLI-Flag (falls unterstützt)
python scripts/run_testnet_session.py --skip-live-risk

# WICHTIG: Nach dem Test wieder zurücksetzen!
```

---

## 9. Incident-Runbook: Auffällige PnL-Divergenzen

### 9.1 Symptome

- Shadow-PnL weicht stark (>30%) von Backtest-Erwartung ab
- Live-PnL entspricht nicht der Simulation
- Unerwartete Verluste ohne erkennbare Marktbewegung

### 9.2 Ursachen

| Ursache | Häufigkeit | Diagnose |
|---------|------------|----------|
| Slippage höher als erwartet | Häufig | Fills vs. Signal-Preis vergleichen |
| Fee-Modell falsch | Mittel | Fee-Abzüge in Logs prüfen |
| Datenqualitätsprobleme | Mittel | Bid/Ask-Spreads, Gaps prüfen |
| Bug in Strategie-Logik | Selten | Code-Review |
| Market-Regime-Wechsel | Häufig | Backtest mit aktuellem Zeitraum |

### 9.3 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: PnL-Divergenz analysieren
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: System pausieren (bei Live/Testnet)
# Nicht bei Shadow - dort weiterlaufen lassen für Daten

# Schritt 2: PnL-Daten exportieren
python scripts/experiments_explorer.py --run-id <RUN_ID> --export-csv

# Schritt 3: Backtest mit gleichem Zeitraum laufen lassen
python scripts/run_backtest.py \
    --strategy <STRATEGIE> \
    --start <START_DATUM> \
    --end <END_DATUM>

# Schritt 4: Vergleich
# - PnL-Kurven überlagern
# - Trade-für-Trade-Vergleich wenn möglich

# Schritt 5: Slippage analysieren
# In Logs: Signal-Preis vs. Fill-Preis
grep "fill\|signal" logs/*.log | tail -50

# Schritt 6: Entscheidung
# - Slippage-Problem → Slippage-Parameter in Config erhöhen
# - Fee-Problem → Fee-Rate prüfen
# - Daten-Problem → Datenquelle prüfen
# - Strategie-Problem → Strategie aus Rotation nehmen
```

### 9.4 Wiederanlaufbedingungen

- [ ] Ursache identifiziert
- [ ] Fix implementiert oder Parameter angepasst
- [ ] Erneuter Backtest zeigt realistische Werte
- [ ] Bei Live: Owner-Freigabe vor Wiederanlauf

---

## 10. Incident-Runbook: Unvollständige Daten / Data-Gaps

### 10.1 Symptome

- Log-Nachricht: `[DATA] Gap detected: ...`
- Fehlende Candles in OHLCV-Daten
- Strategie generiert keine Signale

### 10.2 Ursachen

| Ursache | Diagnose |
|---------|----------|
| Exchange-API-Problem | Exchange-Status prüfen |
| Netzwerkproblem | Lokale Konnektivität testen |
| Rate-Limiting | Request-Frequenz in Logs prüfen |
| Markt geschlossen | Handelszeiten prüfen (bei traditionellen Märkten) |
| Bug im Data-Loader | Code/Logs prüfen |

### 10.3 Schritt-für-Schritt

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Data-Gap behandeln
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Gap identifizieren
# In Logs suchen:
grep -i "gap\|missing\|incomplete" logs/*.log | tail -20

# Schritt 2: Zeitraum bestimmen
# Wann hat der Gap begonnen?
# Wie lange dauert er?

# Schritt 3: Exchange-Status prüfen
# Kraken: https://status.kraken.com/
curl -s https://api.kraken.com/0/public/Time | jq .

# Schritt 4: Lokale Daten prüfen
# Letzte gespeicherte Candle
ls -la data/*.csv | tail -5

# Schritt 5: Entscheidung
# - Exchange down → Warten, System läuft weiter (ohne neue Signale)
# - Rate-Limit → Request-Frequenz reduzieren
# - Dauerhaft → Pausieren und analysieren

# Schritt 6: Bei Behebung
# System sollte automatisch aufholen (je nach Implementation)
# Ggf. Manuelles Nachfüllen der Daten nötig
```

### 10.4 Wiederanlaufbedingungen

- [ ] Datenquelle wieder verfügbar
- [ ] Gap gefüllt oder als akzeptabel markiert
- [ ] System zeigt wieder normale Signalgenerierung

---

## 11. Kommunikation & Verantwortung

### 11.1 Rollen und Entscheidungswege

| Rolle | Verantwortung | Entscheidungsbefugnis |
|-------|---------------|----------------------|
| **Owner** | Gesamtverantwortung, Live-Freigabe | Stufen-Übergänge, Live-Start/Stopp |
| **Operator** | Täglicher Betrieb, Monitoring | Pause bei Anomalien, Routine-Starts |
| **Risk Officer** | Risk-Limit-Prüfung, Governance | Limit-Änderungen, Rollback-Empfehlung |

### 11.2 Entscheidungsmatrix

| Situation | Entscheider | Dokumentation |
|-----------|-------------|---------------|
| Normaler Start/Stopp | Operator | operations.log |
| Pause wegen Anomalie | Operator, dann Owner informieren | Incident-Report |
| Risk-Limit-Änderung | Risk Officer + Owner | Config-Commit + Begründung |
| Live-Aktivierung | Owner + 2. Person | Freigabe-Dokument |
| Notfall-Liquidation | Jeder (dann Owner informieren) | Incident-Report (High) |

### 11.3 Dokumentationspflichten

**Laufender Betrieb:**
- Täglicher Health-Check-Eintrag in `logs/operations.log`
- Run-IDs und Ergebnisse in Experiments-Registry

**Bei Incidents:**
- Incident-Report nach Vorlage in `RUNBOOKS_AND_INCIDENT_HANDLING.md`
- Post-Mortem bei High-Severity-Incidents

**Bei Stufen-Übergängen:**
- Ausgefüllte Checklisten in `reports/checklists/`
- Freigabe-Dokumentation

---

## 12. Referenz: Wichtige Befehle

### 12.1 Diagnose

```bash
# Config prüfen
cat config.toml | grep -A 10 "\[exchange\]"

# Environment prüfen
env | grep -iE "peak|kraken"

# Prozesse
pgrep -af "python.*run_"

# Logs (letzte 100 Zeilen)
tail -100 logs/*.log

# Experiments-Registry
python scripts/experiments_explorer.py --limit 10
```

### 12.2 Kontrolle

```bash
# Graceful Stop
kill <PID>

# Force Stop
kill -9 <PID>

# Alle stoppen
pkill -f "python.*run_"

# Logs sichern
cp -r logs/ logs_backup_$(date +%Y%m%d_%H%M%S)/
```

### 12.3 Monitoring

```bash
# Live-Logs
tail -f logs/*.log

# Alerts
tail -f logs/alerts.log

# System-Last
top -l 1 | head -10
```

---

## 13. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `LIVE_DEPLOYMENT_PLAYBOOK.md` | Stufenplan, Hochfahren/Runterfahren |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Incident-Response, Post-Mortem |
| `LIVE_READINESS_CHECKLISTS.md` | Detaillierte Checklisten |
| `SAFETY_POLICY_TESTNET_AND_LIVE.md` | Safety-Policies |
| `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Governance-Übersicht, Rollen |
| `PHASE_37_TESTNET_ORCHESTRATION_AND_LIMITS.md` | Testnet-Orchestrierung |

---

## 14. Changelog

- **v1.1** (Phase 39, 2025-12): Erweitert
  - Runbook: Live-Run (Small Size) starten hinzugefügt
  - Runbook: Systemstart nach Wartung hinzugefügt
  - Runbook: Sicheres Beenden laufender Sessions hinzugefügt
  - Incident-Runbook: PnL-Divergenzen hinzugefügt
  - Incident-Runbook: Data-Gaps hinzugefügt
  - Abschnitt Kommunikation & Verantwortung hinzugefügt
  - Nummerierung korrigiert

- **v1.0** (Phase 39, 2024-12): Initial erstellt
  - Runbook: Testnet-Run starten
  - Runbook: Exchange-Fehler behandeln
  - Runbook: Risk-Limit-Verletzung
  - System-Health-Check
  - Wichtige Befehle

---

*Diese Runbooks sind lebende Dokumente. Bei Änderungen an Prozessen oder Architektur sollten sie aktualisiert werden.*




