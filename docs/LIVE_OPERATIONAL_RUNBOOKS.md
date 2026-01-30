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
| 10a.10 | Shadow-/Testnet-Session mit Phase-80-Runner | Strategy-to-Execution Bridge (Phase 80) |
| 12a | Live-Track Panel Monitoring | Dashboard-basiertes Session-Monitoring (Phase 82) |
| 12b | Live-Track Session Explorer | Filter, Detail, Stats-API (Phase 85) |

**Demo & Walkthrough:**

| # | Dokument | Anwendungsfall |
|---|----------|----------------|
| – | `PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md` | 10–15 Min Demo (Shadow/Testnet komplett) |

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
# Hinweis: Platzhalter bewusst so gewählt, dass sie nicht wie echte Keys wirken.
export KRAKEN_TESTNET_API_KEY="<KRAKEN_TESTNET_API_KEY>"
export KRAKEN_TESTNET_API_SECRET="<KRAKEN_TESTNET_API_SECRET>"

# Schritt 3: Baseline-Tests prüfen
python3 -m pytest -q --tb=no
# Erwartung: Alle Tests grün (1316+ passed, 4 skipped)

# Schritt 4: Readiness-Check
python3 scripts/check_live_readiness.py --stage testnet
# Erwartung: "Readiness-Check PASSED"

# Schritt 5: Smoke-Test
python3 scripts/smoke_test_testnet_stack.py
# Erwartung: "Smoke-Test PASSED"

# Schritt 6: Testnet-Session starten
python3 scripts/run_testnet_session.py --profile quick_smoke --verbose
# Oder mit DummyExchangeClient (Offline):
# python3 scripts/run_testnet_session.py --use-dummy --verbose

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
python3 -m pytest tests/ -q --tb=short
# Erwartung: Alle Tests grün

# Schritt 4: Readiness-Check für Live
python3 scripts/check_live_readiness.py --stage live
# Erwartung: PASSED

# Schritt 5: Risk-Limits verifizieren
python3 scripts/check_live_risk_limits.py
# Ausgabe prüfen: Limits konservativ?

# Schritt 6: Order-Preview (Dry-Run)
python3 scripts/preview_live_orders.py --strategy <STRATEGIE> --dry-run
# Erwartete Orders prüfen: Sehen sie vernünftig aus?

# Schritt 7: Go-Live (KRITISCHER SCHRITT!)
# Beide Personen bestätigen mündlich: "Ready to go live"
python3 scripts/send_live_orders_dry_run.py --strategy <STRATEGIE> --mode live

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
python3 -m pytest tests/ -q --tb=short
# MUSS grün sein vor Wiederanlauf!

# Schritt 4: Config prüfen
# Wurde die Config geändert?
git diff config/config.toml

# Schritt 5: Readiness-Check
python3 scripts/check_live_readiness.py --stage <STUFE>
# <STUFE> = shadow, testnet, oder live

# Schritt 6: Smoke-Test
python3 scripts/smoke_test_testnet_stack.py

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
python3 scripts/check_open_orders.py

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
python3 -m pytest -q --tb=no
# Erwartung: Alle grün

# Schritt 3: Readiness-Check
python3 scripts/check_live_readiness.py --stage testnet
# Erwartung: PASSED

# Schritt 4: Letzte Runs prüfen
python3 scripts/experiments_explorer.py list --limit 10

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
| Tests grün | `python3 -m pytest -q --tb=no` | Alle passed |
| Readiness | `bash python3 scripts/check_live_readiness.py` | PASSED |
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
grep -A 5 "rate_limit" config/config.toml

# Schritt 4: Rate-Limit erhöhen (falls zu niedrig)
# In config/config.toml:
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
python3 scripts/check_live_readiness.py --stage testnet
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
grep -A 15 "\[live_risk\]" config/config.toml

# Schritt 3: Aktuelle Metriken prüfen
python3 -c "
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
#           → Limits in config/config.toml anpassen, neu starten
#
# Option C: Tagesverlust-Limit erreicht
#           → Trading für heute beenden (System läuft, blockiert aber)

# Schritt 5: Falls Limits angepasst werden
# In config/config.toml:
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
python3 scripts/run_testnet_session.py --skip-live-risk

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
python3 scripts/experiments_explorer.py details --run-id <RUN_ID>

# Schritt 3: Backtest mit gleichem Zeitraum laufen lassen
python3 scripts/run_backtest.py \
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
python3 scripts/testnet_orchestrator_cli.py start-shadow \
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
python3 scripts/testnet_orchestrator_cli.py start-testnet \
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
python3 scripts/testnet_orchestrator_cli.py status --config config/config.toml

# Output:
# Run-ID                                    Mode      Strategy            State     Started
# ----------------------------------------------------------------------------------------------------
# shadow_20251207_120000_abc123             shadow    ma_crossover       running   2025-12-07 12:00:00
# testnet_20251207_130000_def456            testnet   ma_crossover       stopped   2025-12-07 13:00:00
```

**Einzelner Run:**

```bash
python3 scripts/testnet_orchestrator_cli.py status \
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
python3 scripts/testnet_orchestrator_cli.py status --json
```

### 10a.5 Run stoppen

**Einzelner Run:**

```bash
python3 scripts/testnet_orchestrator_cli.py stop \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml

# Output:
# ✅ Run gestoppt: shadow_20251207_120000_abc123
```

**Alle Runs:**

```bash
python3 scripts/testnet_orchestrator_cli.py stop --all --config config/config.toml

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
python3 scripts/testnet_orchestrator_cli.py tail \
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
python3 scripts/testnet_orchestrator_cli.py tail \
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
- Run-Logs werden in `live_runs&#47;{run_id}&#47;` gespeichert
- Metadaten: `live_runs&#47;{run_id}&#47;meta.json`
- Events: `live_runs&#47;{run_id}&#47;events.parquet` (oder `.csv`)

**Log-Struktur:**
- `meta.json`: Run-Metadaten (Run-ID, Mode, Strategy, Symbol, Timeframe, Start/End-Zeit)
- `events.parquet`: Time-Series Events (Step, Timestamp, Signal, Equity, PnL, Risk-Flags, etc.)

**Logs manuell anzeigen:**

```bash
# Metadaten
cat live_runs/shadow_20251207_120000_abc123/meta.json

# Events (mit pandas)
python3 -c "import pandas as pd; df = pd.read_parquet('live_runs/shadow_20251207_120000_abc123/events.parquet'); print(df.tail(10))"
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

## 10a.10 Runbook: Shadow-/Testnet-Session mit Phase-80-Runner

### Übersicht

Der **Phase-80-Runner** (`run_execution_session.py`) bietet eine Strategy-to-Execution Bridge für Single-Strategy-Sessions im Shadow- oder Testnet-Modus.

**Unterschied zum Testnet-Orchestrator (10a):**
- **Orchestrator (10a):** Multi-Run-Management, Run-Registry, Status-Verwaltung
- **Phase-80-Runner:** Single-Strategy-Session mit vollständigem Order-Flow (Strategy → Signals → Orders → ExecutionPipeline)

**Wann nutzen:**
- Nach erfolgreichem Backtest/Sweep einer neuen Strategie
- Um den Order-Flow inkl. Safety-Gates zu validieren
- Vor der Aufnahme einer Strategie ins Tiering (core/aux)

### Shadow-Session starten

**Ziel:** Eine begrenzte Shadow-Session fahren, um Strategy-to-Execution-Flow, Risk-Gates und Logging zu prüfen.

**Voraussetzungen:**
- [ ] Strategie im Backtest/Research-Pipeline getestet
- [ ] `[live_risk]`-Limits in Config definiert
- [ ] Python-Environment aktiviert

**Schritte:**

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Shadow-Session mit Phase-80-Runner
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# Schritt 2: Verfügbare Strategien prüfen
python3 scripts/run_execution_session.py --list-strategies

# Schritt 3: Schneller Smoke-Test (5 Schritte, nur Config validieren)
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --steps 5 \
    --dry-run

# Schritt 4: Shadow-Session starten (30 Minuten)
python3 scripts/run_execution_session.py \
    --strategy ma_crossover \
    --symbol ETH/EUR \
    --timeframe 5m \
    --duration 30

# Schritt 5: Session-Metriken auswerten
# Am Ende der Session werden Metriken ausgegeben:
# - steps: Anzahl verarbeiteter Bars
# - total_orders_generated: Signale → Orders
# - orders_executed: Erfolgreich ausgeführt
# - orders_blocked_risk: Von RiskLimits geblockt

# Schritt 6: Ergebnis dokumentieren
echo "$(date): Shadow-Session ma_crossover ETH/EUR - OK" >> logs/operations.log
```

### Testnet-Session starten

**Ziel:** Order-Flow gegen Exchange-API validieren (validate_only).

**Schritte:**

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK: Testnet-Session mit Phase-80-Runner
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Environment aktivieren
cd ~/Peak_Trade
source .venv/bin/activate

# Schritt 2: API-Credentials setzen (falls nicht in .bashrc/.zshrc)
export KRAKEN_TESTNET_API_KEY="your-testnet-api-key"
export KRAKEN_TESTNET_API_SECRET="your-testnet-api-secret"

# Schritt 3: Testnet-Session starten (20 Schritte)
python3 scripts/run_execution_session.py \
    --mode testnet \
    --strategy trend_following \
    --symbol ETH/EUR \
    --steps 20

# Schritt 4: Session-Metriken auswerten und dokumentieren
```

### Bei Problemen

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `LiveModeNotAllowedError` | Versuch, `--mode live` zu nutzen | Phase 80 blockt LIVE hart – das ist Absicht |
| Keine Signale generiert | Strategie braucht mehr Warmup | `--warmup-candles 300` |
| Alle Orders geblockt | RiskLimits zu eng | `config/config.toml` → `[live_risk]` prüfen |
| Strategy nicht gefunden | Tippfehler oder nicht registriert | `--list-strategies` |

**⚠️ WICHTIG:** Der Phase-80-Runner blockt **LIVE-Mode technisch**. Nur Shadow und Testnet sind erlaubt. Dies ist ein bewusster Safety-First-Ansatz.

**Referenz:** Für detaillierte CLI-Optionen, Metriken-Interpretation und Troubleshooting siehe [`PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md`](PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md), Abschnitt 8.

### Post-Session-Checks – Registry & Reporting (Phase 81)

**Ziel:** Sicherstellen, dass jede Shadow-/Testnet-Session sauber in der Live-Session-Registry erfasst ist und eine Kurz-Summary generiert wurde.

#### 1. Registry-Verfügbarkeit prüfen

- Stelle sicher, dass `reports&#47;experiments&#47;live_sessions&#47;` existiert.
- Falls nicht, wurde ggf. noch keine Session erfolgreich registriert → Ursache prüfen (Logs von `run_execution_session.py`).

```bash
ls -la reports/experiments/live_sessions/
```

#### 2. Reporting-CLI ausführen (Shadow/Testnet)

**Für Shadow-Sessions:**

```bash
python3 scripts/report_live_sessions.py \
  --run-type live_session_shadow \
  --status completed \
  --output-format markdown \
  --summary-only \
  --stdout
```

**Für Testnet-Sessions:**

```bash
python3 scripts/report_live_sessions.py \
  --run-type live_session_testnet \
  --status completed \
  --output-format markdown \
  --summary-only \
  --stdout
```

**Optional: Reports zusätzlich in ein eigenes Verzeichnis schreiben:**

```bash
python3 scripts/report_live_sessions.py \
  --run-type live_session_shadow \
  --status completed \
  --output-format both \
  --output-dir reports/experiments/live_sessions/reports
```

#### 3. Ergebnisse interpretieren

Prüfe insbesondere:

| Metrik | Beschreibung | Warnsignal |
|--------|--------------|------------|
| `num_sessions` | Anzahl Sessions | Weniger als erwartet |
| `by_status` | Status-Verteilung | Viele `failed` |
| `total_realized_pnl` | Gesamt-PnL | Stark negativ |
| `avg_max_drawdown` | Durchschnittlicher Drawdown | > 10% |

Dokumentiere Auffälligkeiten gemäß:
- Incident-Runbook für PnL-Divergenzen (Abschnitt 9)
- Incident-Runbook für Data-Gaps (Abschnitt 10)
- Sonstige relevante Runbooks

#### 4. Dokumentation

Falls eine Session besonders auffällig war (extreme PnL, Drawdown, viele Fehler):

1. Vermerke dies im entsprechenden Betriebsprotokoll (Operator-Log / Notion / internes Log-System)
2. Verweise dabei auf:
   - Session-ID
   - Run-Type (Shadow/Testnet)
   - Timestamp der Session
   - Pfad zum Markdown/HTML-Report

**Beispiel-Eintrag im Operations-Log:**

```bash
echo "$(date): Post-Session-Check – Shadow-Sessions: 5 completed, 0 failed, PnL +123.45 EUR" >> logs/operations.log
```

**Referenz:** Für Details zur Live-Session-Registry und Report-CLI siehe [`PHASE_81_LIVE_SESSION_REGISTRY.md`](PHASE_81_LIVE_SESSION_REGISTRY.md).

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
python3 scripts/live_monitor_cli.py overview --only-active
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
python3 scripts/live_monitor_cli.py overview --only-active

# Übersicht der letzten 24 Stunden
python3 scripts/live_monitor_cli.py overview --max-age-hours 24

# Alle Runs (inkl. inaktive)
python3 scripts/live_monitor_cli.py overview --include-inactive
```

### 10b.3 Run-Details

**Kommando:**

```bash
python3 scripts/live_monitor_cli.py run --run-id shadow_20251207_120000_abc123
```

**Output:**
- Run-Zusammenfassung (Mode, Strategy, Symbol, Timeframe, Active-Status, Start/End-Zeit)
- Aktuelle Metriken (Equity, PnL, Unrealized PnL, Drawdown)
- Letzte Events (Step, Time, Signal, Equity, PnL, Orders)

**Beispiel:**

```bash
# Run-Details anzeigen
python3 scripts/live_monitor_cli.py run \
  --run-id shadow_20251207_120000_abc123 \
  --config config/config.toml

# JSON-Output
python3 scripts/live_monitor_cli.py run \
  --run-id shadow_20251207_120000_abc123 \
  --json
```

### 10b.4 Live-Tailing (Follow-Modus)

**Kommando:**

```bash
python3 scripts/live_monitor_cli.py follow \
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
python3 scripts/live_monitor_cli.py follow \
  --run-id shadow_20251207_120000_abc123 \
  --refresh-interval 2.0 \
  --config config/config.toml
```

### 10b.5 Run-Logs & Verzeichnisstruktur

**Log-Pfad:**
- Run-Logs werden in `live_runs&#47;{run_id}&#47;` gespeichert (konfigurierbar via `shadow_paper_logging.base_dir`)

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
python3 -c "
import pandas as pd
df = pd.read_parquet('live_runs/shadow_20251207_120000_abc123/events.parquet')
print(df.tail(10))
"
```

### 10b.6 Integration mit Testnet-Orchestrator

Das Monitoring-System arbeitet nahtlos mit dem Testnet-Orchestrator zusammen:

1. **Run starten** (via Orchestrator):
   ```bash
   python3 scripts/testnet_orchestrator_cli.py start-shadow \
     --strategy ma_crossover --symbol BTC/EUR --timeframe 1m
   ```

2. **Run überwachen** (via Monitor):
   ```bash
   python3 scripts/live_monitor_cli.py follow --run-id <run_id>
   ```

3. **Run stoppen** (via Orchestrator):
   ```bash
   python3 scripts/testnet_orchestrator_cli.py stop --run-id <run_id>
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
python3 scripts/live_alerts_cli.py run-rules \
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
python3 scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --pnl-drop-threshold-pct 5.0

# Nur No-Events-Check
python3 scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --no-events-max-minutes 10

# Alle Checks
python3 scripts/live_alerts_cli.py run-rules \
  --run-id shadow_20251207_120000_abc123 \
  --pnl-drop-threshold-pct 5.0 \
  --no-events-max-minutes 10 \
  --error-spike-max-errors 5
```

### 10c.4 Integration mit Cron / Scheduler

Das CLI ist so designed, dass es per Cron / Systemd / Scheduler regelmäßig laufen kann:

```bash
# Cron-Beispiel (alle 5 Minuten)
*/5 * * * * cd /path/to/Peak_Trade && python3 scripts/live_alerts_cli.py run-rules \
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
   python3 scripts/testnet_orchestrator_cli.py start-shadow \
     --strategy ma_crossover --symbol BTC/EUR --timeframe 1m
   ```

2. **Run überwachen** (via Monitor):
   ```bash
   python3 scripts/live_monitor_cli.py follow --run-id <run_id>
   ```

3. **Alerts prüfen** (via Alerts CLI):
   ```bash
   python3 scripts/live_alerts_cli.py run-rules \
     --run-id <run_id> \
     --pnl-drop-threshold-pct 5.0 \
     --no-events-max-minutes 10
   ```

**Vorteil:**
- Orchestrator verwaltet den Lifecycle
- Monitor bietet Sichtbarkeit
- Alerts warnen bei Anomalien

---

## 10d. Live Web Dashboard v0 (Phase 67)

### 10d.1 Übersicht

Das **Live Web Dashboard v0** bietet ein einfaches, read-only Web-Interface für das Monitoring von Shadow-/Testnet-Runs.

**Features:**
- REST-API für Run-Listen, Snapshots, Events, Alerts
- HTML-Dashboard mit Auto-Refresh
- Read-only (keine Order-Erzeugung, kein Start/Stop)

**WICHTIG:**
- Dashboard ist **nur** für Shadow-/Testnet-Monitoring gedacht
- Orchestrierung (Start/Stop) bleibt in CLI-Skripten (`testnet_orchestrator_cli.py`)
- Alerts laufen separat über `live_alerts_cli.py` oder Scheduler

### 10d.2 Start

**Option 1: Mit Script (empfohlen)**
```bash
python3 scripts/live_web_server.py
```

**Option 2: Mit uvicorn direkt**
```bash
uvicorn src.live.web.app:app --host 127.0.0.1 --port 8000 --reload
```

**Option 3: Mit Custom-Parametern**
```bash
python3 scripts/live_web_server.py \
  --host 0.0.0.0 \
  --port 9000 \
  --base-runs-dir /path/to/live_runs \
  --auto-refresh-seconds 10
```

### 10d.3 Wichtige URLs

Nach dem Start sind folgende URLs verfügbar:

- **Dashboard:** `http://localhost:8000/` oder `http://localhost:8000/dashboard`
- **Health-Check:** `http://localhost:8000/health`
- **Runs-Liste (JSON):** `http://localhost:8000/runs`
- **Run-Snapshot (JSON):** `http://localhost:8000/runs/{run_id}/snapshot`
- **Run-Events (JSON):** `http://localhost:8000/runs/{run_id}/tail?limit=100`
- **Run-Alerts (JSON):** `http://localhost:8000/runs/{run_id}/alerts?limit=20`

### 10d.4 API-Endpunkte

**GET /health**
- Response: `{"status": "ok"}`
- HTTP 200

**GET /runs**
- Listet alle verfügbaren Runs
- Response: Liste von Run-Metadaten (run_id, mode, strategy_name, symbol, timeframe, ...)

**GET /runs/{run_id}/snapshot**
- Lädt Snapshot eines Runs mit aggregierten Metriken
- Response: Run-Snapshot (total_steps, total_orders, total_blocked_orders, equity, realized_pnl, unrealized_pnl, ...)
- HTTP 404 wenn Run nicht gefunden

**GET /runs/{run_id}/tail?limit=100**
- Lädt die letzten Events eines Runs
- Query-Parameter: `limit` (1-500, default: 50)
- Response: Liste von Events (ts_bar, equity, realized_pnl, unrealized_pnl, position_size, orders_count, risk_allowed, risk_reasons, ...)
- HTTP 404 wenn Run nicht gefunden

**GET /runs/{run_id}/alerts?limit=20**
- Lädt Alerts eines Runs aus `alerts.jsonl`
- Query-Parameter: `limit` (1-100, default: 20)
- Response: Liste von Alerts (rule_id, severity, message, run_id, timestamp)
- HTTP 404 wenn Run nicht gefunden

### 10d.5 Dashboard-Features

Das HTML-Dashboard bietet:

- **Run-Liste:** Übersicht aller verfügbaren Runs (links)
- **Run-Details:** Detaillierte Ansicht des ausgewählten Runs (rechts)
  - Metriken: Equity, Realized PnL, Position, Steps, Orders, Blocked Orders
  - Recent Alerts: Letzte Alerts mit Severity
  - Recent Events: Tabelle der letzten Events
- **Auto-Refresh:** Automatisches Neuladen alle 5 Sekunden (konfigurierbar)

### 10d.6 Integration

**Mit Testnet-Orchestrator:**
```bash
# Terminal 1: Orchestrator starten
python3 scripts/testnet_orchestrator_cli.py start --profile quick_smoke

# Terminal 2: Web-Dashboard starten
python3 scripts/live_web_server.py

# Browser: http://localhost:8000 öffnen
```

**Mit Alerts:**
- Alerts werden automatisch aus `{run_dir}&#47;alerts.jsonl` geladen
- Keine zusätzliche Konfiguration nötig

### 10d.7 Bekannte Limitierungen (v0)

- **Read-only:** Keine Order-Erzeugung, kein Start/Stop aus dem Web UI
- **Kein SSE/WebSocket:** Auto-Refresh via JavaScript (Polling)
- **Einfaches HTML:** Keine komplexe SPA, einfaches Template
- **Keine Authentifizierung:** Nur für lokale/vertrauenswürdige Netzwerke

### 10d.8 Troubleshooting

**Problem: "Run not found"**
- Prüfe ob `base_runs_dir` korrekt gesetzt ist
- Prüfe ob Run-Verzeichnis existiert und `meta.json` enthält

**Problem: "No runs found"**
- Prüfe ob Runs-Verzeichnis existiert
- Prüfe ob Runs vorhanden sind (via `live_monitor_cli.py overview`)

**Problem: "Error loading snapshot"**
- Prüfe ob `events.parquet` existiert und lesbar ist
- Prüfe Logs für detaillierte Fehlermeldungen

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
- Täglicher Health-Check-Eintrag in `logs&#47;operations.log`
- Run-IDs und Ergebnisse in Experiments-Registry

**Bei Incidents:**
- Incident-Report nach Vorlage in `RUNBOOKS_AND_INCIDENT_HANDLING.md`
- Post-Mortem bei High-Severity-Incidents

**Bei Stufen-Übergängen:**
- Ausgefüllte Checklisten in `reports&#47;checklists&#47;`
- Freigabe-Dokumentation

---

## 12. Referenz: Wichtige Befehle

### 12.1 Diagnose

```bash
# Config prüfen
cat config/config.toml | grep -A 10 "\[exchange\]"

# Environment prüfen
env | grep -iE "peak|kraken"

# Prozesse
pgrep -af "python.*run_"

# Logs (letzte 100 Zeilen)
tail -100 logs/*.log

# Experiments-Registry
python3 scripts/experiments_explorer.py list --limit 10
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

## 12a. Runbook: Live-Track Panel Monitoring

### 12a.1 Zweck

Nutzung des Live-Track Panels (Phase 82) für kontinuierliches Session-Monitoring während Shadow-/Testnet-Runs.

### 12a.2 Voraussetzungen

- [ ] Web-Dashboard verfügbar (`src/webui/app.py`)
- [ ] Live-Session-Registry mit Einträgen (`reports&#47;experiments&#47;live_sessions&#47;`)
- [ ] Browser oder curl verfügbar

### 12a.3 Dashboard starten

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 12a: Live-Track Panel Monitoring
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Dashboard starten
cd ~/Peak_Trade
source .venv/bin/activate
uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000 &

# Schritt 2: Health-Check
curl http://127.0.0.1:8000/api/health
# Erwartung: {"status": "ok"}

# Schritt 3: Browser öffnen
open http://127.0.0.1:8000/
```

### 12a.4 Pre-Session-Check im Dashboard

```
VOR EINER SESSION:
□ Dashboard öffnen: http://127.0.0.1:8000/
□ Live-Track Panel sichtbar (Snapshot-Kachel + Tabelle)
□ Keine unbehandelten "failed"-Sessions in der Tabelle
□ Falls "failed" vorhanden: Runbook 12a.7 anwenden
```

### 12a.5 Während der Session

```bash
# Option A: Browser-Tab offen halten und alle 15-30 Min refreshen

# Option B: API-Monitoring im Terminal
watch -n 60 'curl -s http://127.0.0.1:8000/api/live_sessions?limit=1 | jq ".[0] | {session_id, status, realized_pnl, max_drawdown}"'

# Option C: Kombination CLI + Dashboard
# Terminal 1: Dashboard läuft
# Terminal 2: Session läuft
# Terminal 3: API-Monitoring
```

**Prüfpunkte während Monitoring:**

| Element | Normal | Aktion bei Anomalie |
|---------|--------|---------------------|
| Status | started oder completed | Bei "failed": Sofort Runbook 12a.7 |
| Realized PnL | Grün oder leicht rot | Bei > -2%: Risk-Review |
| Max Drawdown | < 5% | Bei > 5%: Risk-Review erwägen |
| Notes | Leer | Bei Fehlermeldung: Untersuchen |

### 12a.6 Post-Session-Check im Dashboard

```
NACH SESSION-ENDE:
□ Dashboard refreshen (F5 oder Browser-Refresh)
□ Session erscheint in Tabelle
□ Status = "completed" (grün)
□ Realized PnL dokumentieren
□ Max Drawdown unter Limit (< 5%)
□ Bei Auffälligkeiten: Notes-Feld prüfen
```

**API-Check für Details:**

```bash
# Letzte Session detailliert
curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq .

# Summary via CLI
python3 scripts/report_live_sessions.py --limit 1 --stdout
```

### 12a.7 Behandlung: Failed-Session im Dashboard

Wenn im Live-Track Panel eine Session mit Status "failed" erscheint:

```bash
# Schritt 1: Fehlerdetails abrufen
curl http://127.0.0.1:8000/api/live_sessions?limit=1 | jq '.[0] | {session_id, status, notes}'

# Schritt 2: Registry-File direkt prüfen
ls -lt reports/experiments/live_sessions/ | head -3
cat reports/experiments/live_sessions/<NEUESTE_DATEI>.json | jq '{error, status, finished_at}'

# Schritt 3: Fehlerursache identifizieren
# Typische Fehler:
# - ConnectionError: Exchange-API nicht erreichbar
# - AuthenticationError: API-Keys ungültig
# - RateLimitExceeded: Zu viele Requests
# - InsufficientFunds: Balance nicht ausreichend

# Schritt 4: Entsprechendes Incident-Runbook anwenden
# - Exchange-Fehler → Runbook 7
# - Risk-Limit → Runbook 8
# - PnL-Divergenz → Runbook 9
# - Data-Gap → Runbook 10

# Schritt 5: Nach Behebung neue Session starten und Dashboard prüfen
```

### 12a.8 Dashboard beenden

```bash
# Option A: Graceful
pkill -f uvicorn

# Option B: Port freigeben
lsof -i :8000
kill <PID>
```

### 12a.9 Wichtige URLs

| URL | Funktion |
|-----|----------|
| http://127.0.0.1:8000/ | Dashboard mit Live-Track Panel |
| http://127.0.0.1:8000/api/live_sessions | Sessions-API (JSON) |
| http://127.0.0.1:8000/api/live_sessions?limit=N | Letzte N Sessions |
| http://127.0.0.1:8000/api/health | Health-Check |
| http://127.0.0.1:8000/docs | OpenAPI/Swagger UI |

---

## 12b. Runbook: Live-Track Session Explorer (Phase 85)

### 12b.1 Zweck

Nutzung des Live-Track Session Explorers für detaillierte Post-Session-Analyse: Filtern, Detailansicht, Statistiken.

### 12b.2 Voraussetzungen

- [ ] Web-Dashboard läuft (`uvicorn src.webui.app:app --reload`)
- [ ] Live-Session-Registry enthält Einträge (Phase 80/81 abgeschlossen)
- [ ] Browser oder curl verfügbar

### 12b.3 Session-Liste filtern

```bash
# ═══════════════════════════════════════════════════════════════════════
# RUNBOOK 12b: Live-Track Session Explorer
# ═══════════════════════════════════════════════════════════════════════

# Schritt 1: Dashboard öffnen
open http://127.0.0.1:8000/

# Schritt 2: Nach Mode filtern
# Shadow-Sessions:
open "http://127.0.0.1:8000/?mode=shadow"

# Testnet-Sessions:
open "http://127.0.0.1:8000/?mode=testnet"

# Schritt 3: Nach Status filtern
# Nur failed:
open "http://127.0.0.1:8000/?status=failed"

# Kombination Mode + Status:
open "http://127.0.0.1:8000/?mode=testnet&status=completed"

# Schritt 4: API für programmatischen Zugriff
curl "http://127.0.0.1:8000/api/live_sessions?mode=shadow&status=completed" | jq .
```

### 12b.4 Session-Detail prüfen

```bash
# Schritt 1: Session-ID aus Liste notieren (z.B. live_session_abc123)

# Schritt 2: Detail-Seite öffnen
open "http://127.0.0.1:8000/session/live_session_abc123"

# Schritt 3: Im Browser prüfen:
# □ Config-Snapshot (Strategy, Presets, Environment)
# □ Kennzahlen (Dauer, Status, PnL, Drawdown)
# □ CLI-Hinweise zum Reproduzieren/Debuggen

# Schritt 4: API für programmatischen Zugriff
curl "http://127.0.0.1:8000/api/live_sessions/live_session_abc123" | jq .
```

### 12b.5 Statistiken abrufen

```bash
# Aggregierte Statistiken aller Sessions
curl "http://127.0.0.1:8000/api/live_sessions/stats" | jq .

# Typische Auswertung:
# - Anzahl Sessions pro Mode (shadow/testnet/live)
# - Anzahl Sessions pro Status (completed/failed/running)
# - Durchschnittlicher PnL, Drawdown

# Für Monitoring-Integration (z.B. Grafana):
# Stats-Endpoint kann regelmäßig gepollt werden
watch -n 60 'curl -s http://127.0.0.1:8000/api/live_sessions/stats | jq .'
```

### 12b.6 Checkliste: Post-Session-Analyse

```
NACH ABGESCHLOSSENER SESSION:
□ Dashboard öffnen: http://127.0.0.1:8000/
□ Nach Mode filtern (shadow/testnet)
□ Session in Liste lokalisieren
□ Detail-Seite öffnen und prüfen:
  □ Status = completed (✅) oder failed (❌)?
  □ Realized PnL plausibel?
  □ Max Drawdown < 5%?
  □ Dauer wie erwartet?
□ Bei Auffälligkeiten:
  □ CLI-Befehle aus Detail-Seite für Re-Run/Debug nutzen
  □ Entsprechendes Incident-Runbook anwenden (7-10)
□ Statistiken prüfen (/api/live_sessions/stats)
□ Ergebnis dokumentieren
```

### 12b.7 Safety-Hinweise

- Sessions im Mode `live` werden im UI mit ⚠️ markiert
- Live-Mode ist in Shadow-/Testnet-Playbooks nicht vorgesehen
- Für Live-Sessions: Zusätzliche Governance-Prüfung erforderlich

### 12b.8 Bei Problemen

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Session nicht in Liste | Filter zu restriktiv | Filter zurücksetzen (`/`) |
| Detail-Seite leer | Session-ID falsch | ID aus Liste kopieren |
| API gibt 404 | Session nicht in Registry | Registry prüfen |
| Stats unvollständig | Zu wenige Sessions | Mehr Sessions fahren |

### 12b.9 Wichtige URLs (Phase 85)

| URL | Funktion |
|-----|----------|
| `http://127.0.0.1:8000/` | Session-Liste (filterbar) |
| `http://127.0.0.1:8000/?mode=shadow` | Nur Shadow-Sessions |
| `http://127.0.0.1:8000/?mode=testnet&status=failed` | Testnet + failed |
| `http://127.0.0.1:8000/session/{session_id}` | Session-Detailseite |
| `http://127.0.0.1:8000/api/live_sessions` | Sessions-API (JSON) |
| `http://127.0.0.1:8000/api/live_sessions/{session_id}` | Session-Detail-API |
| `http://127.0.0.1:8000/api/live_sessions/stats` | Aggregierte Statistiken |

**Referenz:** [`PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md`](PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md)

### 12b.10 Dashboard-Check (Web-Dashboard v1)

**Ziel:** Sicherstellen, dass die zuletzt gelaufene Shadow-/Testnet-Session im Web-Dashboard v1 korrekt sichtbar, geloggt und auswertbar ist.

**Voraussetzung:** Die Session wurde über die CLI gestartet und ist laut Registry abgeschlossen.

**Vorgehen:**

1. **Dashboard öffnen**  
   - Dashboard-URL im Browser öffnen (siehe zentrale Web-Dashboard-Doku / README).
   - Prüfen, ob das Dashboard erreichbar ist und keine Fehlermeldung anzeigt.

2. **System-Status prüfen**  
   - Version, Tag und CI-Status kontrollieren.
   - Verifizieren, dass das Tiering (Research/Beta/Live-ready) zum erwarteten Betriebszustand passt.

3. **Live-Track Panel kontrollieren**  
   - Die zuletzt gelaufene Session (Environment: Shadow/Testnet) identifizieren.
   - Start-/Endzeit, Environment und Ergebnisstatus mit Registry/Report abgleichen.

4. **Session Explorer öffnen**  
   - Session im Explorer öffnen.
   - Prüfen, ob Registry-Metadaten, Laufzeit, Ergebnisstatus und ggf. Error-Felder vollständig sind.
   - Sicherstellen, dass Playbook-/Runbook-Links sichtbar sind.

5. **Abweichungen dokumentieren**  
   - Bei Inkonsistenzen (z.B. Session in Registry, aber nicht im Dashboard sichtbar) einen Incident-Eintrag anlegen.
   - Incident-Referenz in der Session-Notiz ergänzen (falls vorhanden).

**Erwartetes Ergebnis:**  
Die Shadow-/Testnet-Session ist im Web-Dashboard v1 vollständig und konsistent zur Registry dargestellt.
Bei Abweichungen wird ein Incident erfasst und gemäß Incident-Runbook weiterbearbeitet.

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
| `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` | Strategy-to-Execution Bridge & Shadow/Testnet Runner v0 |
| `PHASE_81_LIVE_SESSION_REGISTRY.md` | Live-Session-Registry & Report-CLI |
| `PHASE_82_LIVE_TRACK_DASHBOARD.md` | Live-Track Panel im Web-Dashboard |
| `PHASE_83_LIVE_TRACK_OPERATOR_WORKFLOW.md` | Operator-Workflow für Live-Track Panel |
| `PHASE_84_LIVE_TRACK_DEMO_WALKTHROUGH.md` | Demo Walkthrough & Case Study (10–15 Min) |
| `PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` | Session Explorer: Filter, Detail, Stats-API |

---

## 14. Changelog

- **v1.6** (Phase 85, 2025-12): Live-Track Session Explorer
  - Neues Runbook 12b: Live-Track Session Explorer
  - Filter-, Detail- und Stats-Workflow für Post-Session-Analyse
  - Runbook-Index um 12b ergänzt
  - Referenz zu `PHASE_85_LIVE_TRACK_SESSION_EXPLORER.md` hinzugefügt

- **v1.5** (Phase 84, 2025-12): Live-Track Demo Walkthrough
  - Referenz zu Phase 84 Demo Walkthrough in Referenzen-Tabelle hinzugefügt
  - Runbook-Index um Demo-Walkthrough Verweis ergänzt

- **v1.4** (Phase 82/83, 2025-12): Live-Track Dashboard & Operator-Workflow
  - Neues Runbook 12a: Live-Track Panel Monitoring
  - Pre-Session, Während-Session und Post-Session Checks
  - Failed-Session Behandlung im Dashboard
  - Referenzen zu Phase 82/83 Dokumentation hinzugefügt

- **v1.3** (Phase 81, 2025-12): Live-Session-Registry & Report-CLI ergänzt
  - Neuer Abschnitt "Post-Session-Checks – Registry & Reporting" in Runbook 10a.10 hinzugefügt
  - CLI-Beispiele für `scripts/report_live_sessions.py` (Shadow/Testnet)
  - Interpretations-Tabelle für Registry-Metriken
  - Referenz zu `PHASE_81_LIVE_SESSION_REGISTRY.md` hinzugefügt

- **v1.2** (Phase 80, 2025-12): Phase-80-Runner ergänzt
  - Runbook 10a.10: Shadow-/Testnet-Session mit Phase-80-Runner hinzugefügt
  - Runbook-Index um Phase-80-Runner erweitert
  - Referenz zu `PHASE_80_STRATEGY_TO_EXECUTION_BRIDGE.md` hinzugefügt

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
