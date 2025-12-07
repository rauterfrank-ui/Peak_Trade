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

## 10a. Testnet-Orchestrator v1 (Phase 64)

### 10a.1 Übersicht

Der **Testnet-Orchestrator** ist ein v1-Tool für die Orchestrierung von Shadow- und Testnet-Runs. Er bietet:

- **Start/Stop** von Shadow- und Testnet-Runs
- **Status-Abfrage** für laufende Runs
- **Event-Tailing** aus Run-Logging
- **Automatische Readiness-Checks** vor dem Start
- **Integration** mit LiveRunLogger, LiveRiskLimits, ShadowPaperSession

**WICHTIG:** Der Orchestrator sendet **NIEMALS echte Orders**. Nur Shadow- und Testnet-Modi sind erlaubt.

### 10a.2 Shadow-Run starten

**Voraussetzungen:**
- [ ] `environment.mode = "paper"` in `config/config.toml`
- [ ] Strategie in Config definiert (z.B. `[strategy.ma_crossover]`)
- [ ] Live-Risk-Limits konfiguriert

**Schritt-für-Schritt:**

```bash
# Shadow-Run starten
python scripts/testnet_orchestrator_cli.py start-shadow \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m \
  --config config/config.toml \
  --notes "Daily test run"

# Output:
# ✅ Shadow-Run gestartet: shadow_20251207_120000_abc123
#    Strategie: ma_crossover
#    Symbol: BTC/EUR
#    Timeframe: 1m
```

**Was passiert automatisch:**
1. Readiness-Checks (Environment-Mode, Config, Risk-Limits)
2. Run-Logger wird erstellt
3. ShadowPaperSession wird initialisiert
4. Run wird in separatem Thread gestartet
5. Run-ID wird zurückgegeben

### 10a.3 Testnet-Run starten

**Voraussetzungen:**
- [ ] `environment.mode = "testnet"` in `config/config.toml`
- [ ] Strategie in Config definiert
- [ ] Live-Risk-Limits konfiguriert

**Schritt-für-Schritt:**

```bash
# Testnet-Run starten
python scripts/testnet_orchestrator_cli.py start-testnet \
  --strategy ma_crossover \
  --symbol BTC/EUR \
  --timeframe 1m \
  --config config/config.toml \
  --notes "Testnet validation run"

# Output:
# ✅ Testnet-Run gestartet: testnet_20251207_120000_def456
#    Strategie: ma_crossover
#    Symbol: BTC/EUR
#    Timeframe: 1m
```

**Hinweis:** In v1 werden Testnet-Runs ähnlich wie Shadow-Runs behandelt (Dry-Run). Später kann hier echte Testnet-Integration erfolgen.

### 10a.4 Run-Status abfragen

**Alle Runs:**

```bash
python scripts/testnet_orchestrator_cli.py status --config config/config.toml

# Output:
# Run-ID                                    Mode      Strategy            State     Started
# ----------------------------------------------------------------------------------------------------
# shadow_20251207_120000_abc123             shadow    ma_crossover       running   2025-12-07 12:00:00
# testnet_20251207_130000_def456            testnet   ma_crossover       stopped   2025-12-07 13:00:00
```

**Einzelner Run:**

```bash
python scripts/testnet_orchestrator_cli.py status \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml

# Output:
# Run-ID: shadow_20251207_120000_abc123
# Mode: shadow
# Strategy: ma_crossover
# Symbol: BTC/EUR
# Timeframe: 1m
# State: running
# Started: 2025-12-07T12:00:00+00:00
```

**JSON-Output:**

```bash
python scripts/testnet_orchestrator_cli.py status --json
```

### 10a.5 Run stoppen

**Einzelner Run:**

```bash
python scripts/testnet_orchestrator_cli.py stop \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml

# Output:
# ✅ Run gestoppt: shadow_20251207_120000_abc123
```

**Alle Runs:**

```bash
python scripts/testnet_orchestrator_cli.py stop --all --config config/config.toml

# Output:
# ✅ 2 Run(s) gestoppt
```

**Was passiert beim Stoppen:**
1. Session wird sauber beendet (Shutdown-Signal)
2. Run-Logger wird finalisiert
3. Run-Status wird auf `stopped` gesetzt
4. Stop-Zeit wird gespeichert

### 10a.6 Events tailen

**Letzte Events anzeigen:**

```bash
python scripts/testnet_orchestrator_cli.py tail \
  --run-id shadow_20251207_120000_abc123 \
  --limit 50 \
  --config config/config.toml

# Output:
# Letzte 50 Events für Run: shadow_20251207_120000_abc123
# ----------------------------------------------------------------------------------------------------
# Step 1 | 2025-12-07T12:00:00 | Signal: 1 | Equity: 10000.0
# Step 2 | 2025-12-07T12:01:00 | Signal: 0 | Equity: 10050.0
# ...
```

**JSON-Output:**

```bash
python scripts/testnet_orchestrator_cli.py tail \
  --run-id shadow_20251207_120000_abc123 \
  --limit 10 \
  --json
```

### 10a.7 Readiness-Checks

Der Orchestrator führt automatisch folgende Checks durch:

1. **Config-Validierung:**
   - Config kann geladen werden
   - Alle erforderlichen Sektionen vorhanden

2. **Environment-Validierung:**
   - Shadow-Runs erfordern `environment.mode = "paper"`
   - Testnet-Runs erfordern `environment.mode = "testnet"`
   - Live-Mode wird blockiert

3. **Safety-Checks:**
   - SafetyGuard prüft, dass kein Live-Mode aktiv ist
   - Risk-Limits sind konfiguriert (optional, aber empfohlen)

**Bei Fehlern:**
- Klare Fehlermeldungen mit Exit-Code ≠ 0
- Run wird nicht gestartet

### 10a.8 Logs & Events

**Log-Pfad:**
- Run-Logs werden in `live_runs/{run_id}/` gespeichert
- Metadaten: `live_runs/{run_id}/meta.json`
- Events: `live_runs/{run_id}/events.parquet` (oder `.csv`)

**Log-Struktur:**
- `meta.json`: Run-Metadaten (Run-ID, Mode, Strategy, Symbol, Timeframe, Start/End-Zeit)
- `events.parquet`: Time-Series Events (Step, Timestamp, Signal, Equity, PnL, Risk-Flags, etc.)

**Logs manuell anzeigen:**

```bash
# Metadaten
cat live_runs/shadow_20251207_120000_abc123/meta.json

# Events (mit pandas)
python -c "import pandas as pd; df = pd.read_parquet('live_runs/shadow_20251207_120000_abc123/events.parquet'); print(df.tail(10))"
```

### 10a.9 Bekannte Limitierungen (v1)

- **Threading:** Runs laufen in separaten Threads (kein Multi-Process)
- **Testnet:** Testnet-Runs nutzen aktuell ShadowPaperSession (später echte Testnet-Integration)
- **Persistence:** Run-Status ist nur im Memory (bei Neustart verloren)
- **Monitoring:** Kein automatisches Health-Checking (manuell via `status`)

**Zukünftige Verbesserungen:**
- Persistente Run-Registry (z.B. JSON-Datei)
- Automatisches Health-Checking
- Echte Testnet-Session-Integration
- Multi-Process-Support für bessere Isolation

---

## 10b. Monitoring & CLI-Dashboards v1 (Phase 65)

### 10b.1 Übersicht

Das **Live-Monitoring-System** bietet Operatoren eine einfache Möglichkeit, Shadow- und Testnet-Runs zu überwachen, ohne Code ändern zu müssen.

**Zweck:**
- Übersicht über alle relevanten Runs
- Details zu einem Run einsehen
- Echtzeit-Monitoring in einem "tail"-Mode

**Features:**
- Run-Übersicht mit aggregierten Metriken (Equity, PnL, Drawdown)
- Run-Details mit letzten Events
- Live-Tailing-Modus für Echtzeit-Überwachung
- Wiederverwendbare Library-Schicht für zukünftige Web-Dashboards

### 10b.2 Run-Übersicht

**Kommando:**

```bash
python scripts/live_monitor_cli.py overview --only-active
```

**Output:**
- Tabelle mit allen aktiven Runs
- Spalten: Run-ID, Mode, Strategy, Symbol, Timeframe, Active, Last Event, Equity, PnL, Drawdown

**Optionen:**
- `--only-active`: Nur aktive Runs (Default)
- `--include-inactive`: Auch inaktive Runs anzeigen
- `--max-age-hours 24`: Nur Runs der letzten 24 Stunden
- `--json`: JSON-Output für maschinelle Verarbeitung

**Beispiel:**

```bash
# Übersicht aller aktiven Runs
python scripts/live_monitor_cli.py overview --only-active

# Übersicht der letzten 24 Stunden
python scripts/live_monitor_cli.py overview --max-age-hours 24

# Alle Runs (inkl. inaktive)
python scripts/live_monitor_cli.py overview --include-inactive
```

### 10b.3 Run-Details

**Kommando:**

```bash
python scripts/live_monitor_cli.py run --run-id shadow_20251207_120000_abc123
```

**Output:**
- Run-Zusammenfassung (Mode, Strategy, Symbol, Timeframe, Active-Status, Start/End-Zeit)
- Aktuelle Metriken (Equity, PnL, Unrealized PnL, Drawdown)
- Letzte Events (Step, Time, Signal, Equity, PnL, Orders)

**Beispiel:**

```bash
# Run-Details anzeigen
python scripts/live_monitor_cli.py run \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml

# JSON-Output
python scripts/live_monitor_cli.py run \
  --run-id shadow_20251207_120000_abc123 \
  --json
```

### 10b.4 Live-Tailing (Follow-Modus)

**Kommando:**

```bash
python scripts/live_monitor_cli.py follow \
  --run-id shadow_20251207_120000_abc123 \
  --refresh-interval 2.0
```

**Verhalten:**
- Aktualisiert sich alle `refresh-interval` Sekunden
- Zeigt aktuellen Status (Active, Events, Equity, PnL, Drawdown)
- Zeigt neue Events in Echtzeit
- Beenden mit Ctrl+C

**Empfehlung:**
- Während eines Testnet-Runs parallel ein "follow"-Fenster offen haben
- Refresh-Intervall: 2-5 Sekunden für Live-Monitoring, 10-30 Sekunden für weniger häufige Updates

**Beispiel:**

```bash
# Live-Tailing mit 2 Sekunden Refresh
python scripts/live_monitor_cli.py follow \
  --run-id shadow_20251207_120000_abc123 \
  --refresh-interval 2.0 \
  --config config/config.toml
```

### 10b.5 Run-Logs & Verzeichnisstruktur

**Log-Pfad:**
- Run-Logs werden in `live_runs/{run_id}/` gespeichert (konfigurierbar via `shadow_paper_logging.base_dir`)

**Verzeichnisstruktur:**
```
live_runs/
  {run_id}/
    meta.json          # Run-Metadaten
    events.parquet     # Time-Series Events (oder events.csv)
```

**Metadaten (`meta.json`):**
- Run-ID, Mode, Strategy, Symbol, Timeframe
- Start/End-Zeit
- Config-Snapshot, Notizen

**Events (`events.parquet`):**
- Step, Timestamp (ts_event, ts_bar)
- Equity, PnL, Unrealized PnL
- Signal, Orders (generated, filled, rejected, blocked)
- Risk-Info (risk_allowed, risk_reasons)
- Preis-Daten (price, open, high, low, close, volume)

**Logs manuell anzeigen:**

```bash
# Metadaten
cat live_runs/shadow_20251207_120000_abc123/meta.json | jq

# Events (mit pandas)
python -c "
import pandas as pd
df = pd.read_parquet('live_runs/shadow_20251207_120000_abc123/events.parquet')
print(df.tail(10))
"
```

### 10b.6 Integration mit Testnet-Orchestrator

Das Monitoring-System arbeitet nahtlos mit dem Testnet-Orchestrator zusammen:

1. **Run starten** (via Orchestrator):
   ```bash
   python scripts/testnet_orchestrator_cli.py start-shadow \
     --strategy ma_crossover --symbol BTC/EUR --timeframe 1m
   ```

2. **Run überwachen** (via Monitor):
   ```bash
   python scripts/live_monitor_cli.py follow --run-id <run_id>
   ```

3. **Run stoppen** (via Orchestrator):
   ```bash
   python scripts/testnet_orchestrator_cli.py stop --run-id <run_id>
   ```

**Vorteil:**
- Orchestrator verwaltet den Lifecycle
- Monitor bietet Sichtbarkeit ohne Lifecycle-Änderungen

---

## 10c. Alerts & Incident Notifications v1 (Phase 66)

### 10c.1 Übersicht

Das **Alerting & Incident-Notification-System** ermöglicht es Operatoren, automatisch auf kritische Situationen in Shadow- und Testnet-Runs aufmerksam gemacht zu werden.

**Zweck:**
- Automatische Erkennung von Anomalien (PnL-Drops, Data-Gaps, Fehler-Spikes)
- Sofortige Benachrichtigung bei kritischen Ereignissen
- Vorbereitung für externe Integrationen (E-Mail, Telegram)

**Features:**
- Regel-Engine mit konfigurierbaren Schwellenwerten
- Multi-Notifier-Support (Logging, Console, E-Mail-Stub, Telegram-Stub)
- Robuste Fehlerbehandlung (ein Notifier-Fehler crasht nicht die anderen)

### 10c.2 Verfügbare Regeln

**1. PnL-Drop-Rule**
- **Zweck:** Erkennt starke Intraday-PnL-Drops
- **Parameter:**
  - `threshold_pct`: Schwellenwert in Prozent (z.B. 5.0 für 5%)
  - `window`: Zeitfenster (z.B. 1 Stunde)
- **Alert-Level:** CRITICAL

**2. No-Events-Rule**
- **Zweck:** Erkennt ausbleibende Events (Data-Gaps)
- **Parameter:**
  - `max_silence`: Maximale Stille-Zeit (z.B. 10 Minuten)
- **Alert-Level:** WARNING (bei Überschreitung), CRITICAL (bei doppelter Überschreitung)

**3. Error-Spike-Rule**
- **Zweck:** Erkennt gehäufte Fehler/Order-Rejects
- **Parameter:**
  - `max_errors`: Maximale Anzahl Fehler im Zeitfenster
  - `window`: Zeitfenster (z.B. 10 Minuten)
- **Alert-Level:** WARNING (bei Überschreitung), CRITICAL (bei doppelter Überschreitung)

### 10c.3 CLI-Verwendung

**Kommando:**

```bash
python scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml \
  --pnl-drop-threshold-pct 5.0 \
  --pnl-drop-window-hours 1 \
  --no-events-max-minutes 10 \
  --error-spike-max-errors 5 \
  --error-spike-window-minutes 10
```

**Optionen:**
- `--run-id`: Run-ID (erforderlich)
- `--pnl-drop-threshold-pct`: PnL-Drop-Schwellenwert in Prozent (optional)
- `--pnl-drop-window-hours`: Zeitfenster für PnL-Drop-Check in Stunden (Default: 1.0)
- `--no-events-max-minutes`: Maximale Stille-Zeit in Minuten (optional)
- `--error-spike-max-errors`: Maximale Anzahl Fehler im Zeitfenster (optional)
- `--error-spike-window-minutes`: Zeitfenster für Error-Spike-Check in Minuten (Default: 10.0)

**Exit-Codes:**
- `0`: Keine kritischen Alerts
- `1`: Mindestens ein CRITICAL-Alert wurde ausgelöst

**Beispiele:**

```bash
# Nur PnL-Drop-Check
python scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --pnl-drop-threshold-pct 5.0

# Nur No-Events-Check
python scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --no-events-max-minutes 10

# Alle Checks
python scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10 \
  --error-spike-max-errors 5
```

### 10c.4 Integration mit Cron / Scheduler

Das CLI ist so designed, dass es per Cron / Systemd / Scheduler regelmäßig laufen kann:

```bash
# Cron-Beispiel (alle 5 Minuten)
*/5 * * * * cd /path/to/Peak_Trade && python scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10 \
  >> /var/log/peak_trade_alerts.log 2>&1
```

**Exit-Code-Interpretation:**
- Exit-Code `0` = keine kritischen Alerts → keine Aktion nötig
- Exit-Code `1` = kritischer Alert → kann an externe Tools weitergeleitet werden (z.B. Alertmanager, PagerDuty)

### 10c.5 Notifier & Integrationen

**Aktuell verfügbar:**
- **LoggingAlertSink**: Alerts werden über Python-Logging ausgegeben
- **ConsoleAlertNotifier**: Alerts werden auf stdout/stderr ausgegeben
- **EmailAlertNotifier**: Stub für E-Mail-Integration (Phase 66)
- **TelegramAlertNotifier**: Stub für Telegram-Integration (Phase 66)

**Hinweis:**
- E-Mail- und Telegram-Notifier sind in Phase 66 als **Stubs** implementiert
- Das Interface ist bewusst so gestaltet, dass später echte Integrationen einfach nachgeschoben werden können
- Stubs loggen aktuell nur, dass sie einen Alert erhalten hätten

**Zukünftige Integrationen (spätere Phasen):**
- Echte SMTP-Integration für E-Mail
- Echte Telegram-Bot-API-Integration
- Weitere Notifier (Slack, Discord, etc.)

### 10c.6 Integration mit Monitoring & Orchestrator

Das Alerting-System arbeitet nahtlos mit Monitoring und Orchestrator zusammen:

1. **Run starten** (via Orchestrator):
   ```bash
   python scripts/testnet_orchestrator_cli.py start-shadow \
     --strategy ma_crossover --symbol BTC/EUR --timeframe 1m
   ```

2. **Run überwachen** (via Monitor):
   ```bash
   python scripts/live_monitor_cli.py follow --run-id <run_id>
   ```

3. **Alerts prüfen** (via Alerts CLI):
   ```bash
   python scripts/live_alerts_cli.py run-rules \
     --run-id <run_id> \
     --pnl-drop-threshold-pct 5.0 \
     --no-events-max-minutes 10
   ```

**Vorteil:**
- Orchestrator verwaltet den Lifecycle
- Monitor bietet Sichtbarkeit
- Alerts warnen bei Anomalien

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




