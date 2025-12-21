# Peak_Trade – Incident Simulation & Drills

> **Phase 56** – Praktisches Drill-Playbook für kontrollierte Incident-Übungen
>
> **Ziel:** Runbooks, Alerts, Live-Ops-CLI und Governance-Prozesse praktisch validieren

---

## 1. Einleitung

### Was ist dieses Dokument?

Dieses Dokument ist ein **praktisches Drill-Playbook**, um kritische Incidents kontrolliert zu üben. Es beschreibt konkrete, reproduzierbare Szenarien, mit denen du dein Incident-Handling trainieren kannst.

### Warum Incident-Drills?

Du hast bereits:
- ✅ Runbooks (`RUNBOOKS_AND_INCIDENT_HANDLING.md`)
- ✅ Alerts & Notifications (Phase 49/50)
- ✅ Live-Ops-CLI (Phase 51)
- ✅ Governance & Safety-Prozesse (Phase 25)
- ✅ Research → Live Playbook (Phase 54)

**Jetzt geht es darum, zu prüfen, ob diese Tools und Prozesse in der Praxis funktionieren.**

### Abgrenzung

- **Keine echten Produktionsorders**: Alle Drills laufen in Shadow/Testnet/Paper-Modi
- **Fokus auf drei Aspekte**:
  1. **Erkennen**: Wird das Problem erkannt? (Alerts, Logs, Monitoring)
  2. **Reagieren**: Funktionieren die Runbooks? (Schritt-für-Schritt-Anleitungen)
  3. **Dokumentieren**: Wird alles protokolliert? (Drill-Log, Post-Mortem)

### Verwandte Dokumente

- [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Governance-Rahmen
- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Incident-Runbooks
- [`LIVE_TESTNET_TRACK_STATUS.md`](LIVE_TESTNET_TRACK_STATUS.md) – Live-/Testnet-Status
- [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Research → Live Prozess
- [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md) – Drill-Log für Dokumentation

---

## 2. Rollen & Scope

### Rollen

| Rolle | Verantwortung im Drill |
|-------|------------------------|
| **Research/Quant** | Liefert erwartete PnL/Verhaltens-Referenz, validiert Research-Ergebnisse |
| **Operator** | Führt Drills aus, beobachtet Alerts & Live-Ops, dokumentiert Ergebnisse |
| **Risk/Governance** | Definiert Schwellen, bewertet Drill-Ergebnisse, entscheidet über Follow-Ups |

### Scope

- **Umgebungen**: Drills laufen in **Shadow-/Paper-/Testnet-Umgebungen**
- **Ziel**: Reaktionsketten testen, nicht maximalen Schaden simulieren
- **Sicherheit**: Niemals echtes Live-Kapital verwenden
- **Dokumentation**: Alle Drills werden in `INCIDENT_DRILL_LOG.md` protokolliert

---

## 3. Incident-Kategorien

Dieses Playbook fokussiert auf vier Hauptkategorien:

1. **Datenprobleme**
   - Data-Gap (fehlende Zeitintervalle)
   - Korrupte Candle/Outlier

2. **PnL-Divergenzen**
   - Research-/Backtest-PnL vs. Shadow-/Testnet-PnL driftet auseinander

3. **Risk-Limit-Verletzungen**
   - Order-Level Limits
   - Portfolio-Level Limits

4. **Alert-/Webhook-/Slack-Failures**
   - Alerts werden nicht oder nur teilweise zugestellt

Jede Kategorie bekommt ein konkretes Drill-Szenario.

---

## 4. Szenario 1 – Data-Gap / korrupte Candle

**Ziel:** Testen, ob das System Datenprobleme erkennt / damit umgeht und ob Runbooks & Alerts funktionieren.

### 4.1 Vorbereitung

1. **Umgebung wählen**: Shadow-/Research-Umgebung (kein Testnet nötig)
2. **Daten identifizieren**: Wähle einen kleinen Datenabschnitt (z.B. 1–2 Tage BTC/ETH 1h oder 15m Daten)
3. **Backup erstellen**: Stelle sicher, dass du das Original-File/Parquet wiederherstellen kannst:
   ```bash
   # Backup erstellen
   cp data/raw/btc_eur_1h.parquet data/raw/btc_eur_1h.backup.parquet
   ```

### 4.2 Drill-Variante A – Data-Gap simulieren

**Schritte:**

1. **Erzeuge bewusst eine Lücke**:
   - In einem CSV/Parquet-Bereich ein Zeitfenster entfernen (1–3 Stunden)
   - Oder: In einem Test-Dataset einzelne Zeilen rauslöschen

2. **Starte einen Backtest-/Research-Run** mit diesem fehlerhaften Dataset:
   ```bash
   python scripts/research_cli.py portfolio \
     --config config/config.toml \
     --portfolio-preset rsi_reversion_conservative \
     --format both
   ```

3. **Beobachte**:
   - Kommt eine Warnung/Exception vom Data-Layer?
   - Brechen Scripts hart ab oder gibt es "silent failure"?
   - Werden Lücken in Reports/Plots sichtbar?

### 4.3 Drill-Variante B – Outlier / korrupte Candle

**Schritte:**

1. **Manipuliere eine Candle**:
   - Setze `close` auf 10x Preis für genau einen Timestamp
   - Oder: Setze `high` auf unrealistisch hoch

2. **Wiederhole einen Research-/Backtest-Run**:
   ```bash
   python scripts/run_backtest.py \
     --strategy ma_crossover \
     --symbol BTC/EUR \
     --bars 500
   ```

3. **Beobachte**:
   - Wird der Outlier erkannt?
   - Werden Plots/Reports auffällig?
   - Gibt es Warnungen im Log?

### 4.4 Erfolgskriterien

**Mindestens eines der folgenden ist wahr:**

- ✅ Data-Layer meldet auffällige Lücken/Outlier
- ✅ Reports/Plots machen Unsauberkeit sichtbar
- ✅ Du kannst das Problem **manuell** erkennen (z.B. mit Plot-Inspection) und den zugehörigen Runbook-Eintrag anwenden

**Dokumentation:**

- Trage das Ergebnis in `INCIDENT_DRILL_LOG.md` ein
- Notiere, welche Erkennungsmechanismen funktioniert haben
- Dokumentiere Verbesserungsvorschläge

### 4.5 Cleanup

```bash
# Original-Daten wiederherstellen
mv data/raw/btc_eur_1h.backup.parquet data/raw/btc_eur_1h.parquet
```

### 4.6 Referenz-Runbook

- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Abschnitt "Data-Gaps & Data-Quality Incidents"

---

## 5. Szenario 2 – PnL-Divergenz Research vs. Shadow/Testnet

**Ziel:** Testen, ob du merkst, wenn der Live-/Shadow-PnL **nicht dem Research-PnL** entspricht, und ob du dein Playbook & Runbooks konsequent nutzt.

### 5.1 Vorbereitung

1. **Portfolio-Preset wählen**, z.B.:
   - `multi_style_moderate`
   - `rsi_reversion_conservative`

2. **Research-Referenz erstellen**:
   ```bash
   # Aktuelle Research-Reports generieren
   python scripts/run_portfolio_robustness.py \
     --config config/config.toml \
     --portfolio-preset multi_style_moderate \
     --format both
   ```
   - Notiere die erwarteten Metriken (Sharpe, MaxDD, CAGR)

3. **Shadow-/Paper-Run vorbereiten**:
   - Stelle sicher, dass du Shadow-/Paper-Runs für dieses Portfolio simulieren kannst

### 5.2 Drill-Idee

**Variante ohne Code-Hack (nur konzeptuell/drill-artig):**

1. **Nimm an, der Shadow-/Testnet-PnL verläuft über ein paar Tage sichtbar anders** als erwartet (z.B. aufgrund:
   - Slippage/Fees
   - Leicht anderer Daten-Feed
   - Implementation Drift)

2. **Simuliere diese Situation**:
   - Erzeuge ein fiktives Shadow-PnL-Log (z.B. kleine CSV/JSON-Datei) **oder**
   - Fahre einen Teil der Shadow-Runs bewusst mit anderem Setup (siehe Playbook für Mapping)

3. **Vergleiche Research vs. Shadow-PnL**:
   ```bash
   # Portfolio-Snapshot aus Shadow-Run
   python scripts/live_ops.py portfolio --config config/config.toml --json > shadow_pnl.json

   # Vergleich mit Research-Ergebnissen
   # (manuell oder mit kleinem Vergleichs-Script)
   ```

4. **Geh deinen Playbook-Schritt "PnL-Divergenz" durch**:
   - Was sind potenzielle Ursachen?
   - Welche Log-/Run-Layer prüfst du (z.B. `run_logging`, Order-Logs, Data-Layer)?
   - Wann wird es zu einem Incident im Sinne des Runbooks?

### 5.3 Erfolgskriterien

**Du kannst:**

- ✅ Eine Checkliste/Sequenz definieren (oder in der Doku ergänzen), wie du PnL-Divergenzen untersuchst
- ✅ Eindeutig erkennen, ob der Unterschied "erklärbar" (Fees, Slippage) oder "kritisch" (Daten-/Bugs) ist
- ✅ Das entsprechende Runbook anwenden

**Dokumentation:**

- Notiere das Ergebnis & Erkenntnisse im Drill-Log
- Dokumentiere, welche Untersuchungsschritte hilfreich waren

### 5.4 Referenzen

- [`PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md`](PLAYBOOK_RESEARCH_TO_LIVE_PORTFOLIOS.md) – Schritte Re-Kalibrierung & Monitoring
- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – PnL-Divergenz-Abschnitt

---

## 6. Szenario 3 – Risk-Limit-Verletzung (Order-/Portfolio-Level)

**Ziel:** Praktisch üben, was passiert, wenn ein **Live-Risk-Limit** greift:
→ Wird blockiert?
→ Wird ein Alert generiert (inkl. Webhook/Slack)?
→ Weißt du, was als Nächstes zu tun ist?

### 6.1 Vorbereitung

1. **Umgebung wählen**: Testnet oder isolierter Modus (niemals echtes Live-Kapital)
2. **Setup prüfen**:
   - Orders können generiert werden (z.B. mit vorhandenen Preview-/Paper-Runs)
   - `LiveRiskLimits` verwendet (`[live_risk]` in `config/config.toml`)
   - Alerts sind konfiguriert (`[live_alerts]` in `config/config.toml`)

### 6.2 Konfig-basierte Simulation

**Anstatt Code zu hacken, senkst du bewusst Limits**, um einen Verstoß zu erzwingen:

**Schritt 1: Config sichern (Backup)**
```bash
cp config/config.toml config/config.before_risk_drill.toml
```

**Schritt 2: live_risk im config anpassen (temporär)**
```toml
# In config/config.toml:
[live_risk]
enabled = true
max_total_exposure_notional = 10.0  # Sehr niedrig, um Verstoß zu erzwingen
max_order_notional = 5.0            # Noch niedriger
max_daily_loss_abs = 1.0            # Sehr eng
```

**Schritt 3: Drill auslösen über Live-Ops / Preview-CLI**
```bash
# Orders-Preview mit Risk-Check
python scripts/live_ops.py orders \
  --signals reports/forward/forward_*_signals.csv \
  --config config/config.toml \
  --enforce-live-risk

# Oder Portfolio-Snapshot (Portfolio-Level Risk)
python scripts/live_ops.py portfolio \
  --config config/config.toml
```

**Erwartung:**

- ✅ `LiveRiskLimits.check_orders()` schlägt an
- ✅ Alerts-System erzeugt mindestens einen WARNING/CRITICAL-Alert
- ✅ Webhook/Slack-Sinks (sofern konfiguriert) feuern
- ✅ Orders werden blockiert oder klar als "nicht erlaubt" markiert

### 6.3 Erfolgskriterien

**Das System:**

- ✅ Blockiert Orders oder markiert sie klar als "nicht erlaubt" (je nach Config)
- ✅ Ein Alert wird ausgelöst:
  - Im Log
  - Auf stderr
  - Ggf. via Webhook/Slack

**Du kannst:**

- ✅ Das entsprechende **Risk-/Incident-Runbook** anwenden:
  - Trade-/Strategy-Pause?
  - Config zurücksetzen?
  - Post-Mortem-Eintrag?

**Dokumentation:**

- Drill im `INCIDENT_DRILL_LOG.md` dokumentiert
- Notiere, welche Alerts gefeuert haben und ob sie korrekt zugestellt wurden

### 6.4 Cleanup

```bash
# Config aus Backup wiederherstellen
mv config/config.before_risk_drill.toml config/config.toml
```

### 6.5 Referenzen

- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Risk-Limit-Verletzungen
- [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](GOVERNANCE_AND_SAFETY_OVERVIEW.md) – Risk-Policies

---

## 7. Szenario 4 – Alert-/Webhook-/Slack-Failure

**Ziel:** Sicherstellen, dass du merkst, wenn das **Alert-System selbst** Probleme hat (z.B. Slack-Webhook kaputt), und weißt, wie du dann reagierst.

### 7.1 Vorbereitung

1. **Alerts-Konfiguration prüfen**:
   ```bash
   # Prüfe live_alerts in config.toml
   cat config/config.toml | grep -A 10 "\[live_alerts\]"
   ```

2. **Mindestens ein Webhook/Slack-Sink aktiv**:
   - Stelle sicher, dass `[live_alerts]` konfiguriert ist
   - Falls Webhook/Slack aktiv: Notiere die URLs (für späteres Wiederherstellen)

### 7.2 Drill-Idee

**Schritt 1: Config sichern**
```bash
cp config/config.toml config/config.before_alert_drill.toml
```

**Schritt 2: Alert-Failure simulieren**

**Variante A – Ungültige Webhook-URL:**
```toml
# In config/config.toml:
[live_alerts]
enabled = true
sinks = ["log", "webhook"]  # Webhook aktiv
webhook_urls = ["https://invalid-url-that-does-not-exist.com/webhook"]  # Ungültig
```

**Variante B – Ungültige Slack-Webhook-URL:**
```toml
[live_alerts]
enabled = true
sinks = ["log", "slack_webhook"]
slack_webhook_urls = ["https://hooks.slack.com/services/INVALID/INVALID/INVALID"]
```

**Schritt 3: Risk-Alert auslösen**

Nutze das Risk-Limit-Drill-Szenario (Szenario 3), um einen Alert zu triggern:
```bash
# Risk-Limit-Verletzung erzeugen (siehe Szenario 3)
python scripts/live_ops.py portfolio --config config/config.toml
```

**Schritt 4: Beobachte Alert-Verhalten**

- Werden Fehler beim Alert-Senden geloggt (ohne zu crashen)?
- Werden Fallback-Sinks (Logging, stderr) verwendet?
- Bekommst du trotzdem mit, dass etwas nicht stimmt?

### 7.3 Erfolgskriterien

**Das System:**

- ✅ Loggt Fehler beim Alert-Senden, ohne zu crashen
- ✅ Verwendet Fallback-Sinks (Logging, stderr)
- ✅ Risk-/Ops-seitig bekommst du trotzdem mit, dass etwas **nicht stimmt**

**Du kannst:**

- ✅ Erkennen, dass Alerts nicht/teilweise zugestellt werden
- ✅ Welche **Notfall-Kommunikationswege** du in diesem Fall nutzt (z.B. andere Kanäle, manuelles Monitoring)

**Dokumentation:**

- Notiere im Drill-Log, wie du Alert-Failures erkennst
- Dokumentiere deine Notfall-Kommunikationswege

### 7.4 Cleanup

```bash
# Config aus Backup wiederherstellen
mv config/config.before_alert_drill.toml config/config.toml
```

### 7.5 Referenzen

- [`RUNBOOKS_AND_INCIDENT_HANDLING.md`](RUNBOOKS_AND_INCIDENT_HANDLING.md) – Alert-Failures
- [`PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md`](PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md) – Alert-System-Doku
- [`PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md`](PHASE_50_LIVE_ALERT_WEBHOOKS_AND_SLACK.md) – Webhook/Slack-Doku

---

## 8. Drill-Frequenz & Organisation

### Empfohlene Frequenz

- **Monatlich**: Mindestens 1 Drill (abwechselnd Szenarien)
- **Quartalsweise**: Kompletter Zyklus durch alle Szenarien

### Drill-Planung

**Vorschlag für monatliche Rotation:**

| Monat | Szenario | Fokus |
|-------|----------|-------|
| Monat 1 | Data-Gap / korrupte Candle | Datenqualität |
| Monat 2 | PnL-Divergenz | Research vs. Live |
| Monat 3 | Risk-Limit-Verletzung | Risk-Management |
| Monat 4 | Alert-Failure | Alert-System |

**Quartalsweise:**
- Alle 4 Szenarien durchführen
- Review der Drill-Ergebnisse
- Runbooks & Prozesse anpassen (falls nötig)

### Dokumentation

- **Alle Drills** werden in [`INCIDENT_DRILL_LOG.md`](INCIDENT_DRILL_LOG.md) protokolliert
- **Erkenntnisse** werden in Runbooks & Governance-Doku eingearbeitet
- **Follow-Ups** werden als TODOs oder Phase-Items dokumentiert

---

## 9. Best Practices

### Vor jedem Drill

1. ✅ **Backup erstellen**: Configs, Daten, kritische Dateien
2. ✅ **Umgebung prüfen**: Shadow/Testnet, nicht Live
3. ✅ **Ziel definieren**: Was willst du testen?
4. ✅ **Erfolgskriterien festlegen**: Wann ist der Drill erfolgreich?

### Während des Drills

1. ✅ **Schritt-für-Schritt dokumentieren**: Was passiert wann?
2. ✅ **Alerts & Logs beobachten**: Werden sie erwartungsgemäß ausgelöst?
3. ✅ **Runbooks befolgen**: Nutze die dokumentierten Prozesse

### Nach jedem Drill

1. ✅ **Ergebnis dokumentieren**: In `INCIDENT_DRILL_LOG.md`
2. ✅ **Erkenntnisse notieren**: Was hat funktioniert? Was nicht?
3. ✅ **Follow-Ups definieren**: Was muss verbessert werden?
4. ✅ **Cleanup durchführen**: Configs & Daten wiederherstellen

---

## 10. Erweiterte Szenarien (Optional)

### Szenario 5 – Exchange-API-Failure

**Ziel:** Testen, wie das System reagiert, wenn die Exchange-API nicht erreichbar ist.

**Drill-Idee:**
- Simuliere API-Failures (z.B. durch Netzwerk-Blockade oder ungültige API-URLs)
- Beobachte, ob das System graceful degradiert oder hart abbricht

### Szenario 6 – Portfolio-Korrelation-Drift

**Ziel:** Testen, ob du merkst, wenn Portfolio-Korrelationen sich unerwartet ändern.

**Drill-Idee:**
- Vergleiche historische vs. aktuelle Korrelationen zwischen Strategien
- Prüfe, ob Alerts/Reports auf Korrelations-Drift hinweisen

---

## 11. Integration mit bestehenden Tools

### Live-Ops-CLI

```bash
# Health-Check vor/nach Drill
python scripts/live_ops.py health --config config/config.toml

# Portfolio-Snapshot für PnL-Vergleich
python scripts/live_ops.py portfolio --config config/config.toml --json
```

### Research-CLI

```bash
# Research-Referenz für PnL-Vergleich
python scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset multi_style_moderate \
  --format both
```

### Alerts & Logs

- **Logs prüfen**: `logs/` Verzeichnis
- **Alerts beobachten**: stderr, Logging, Webhook/Slack

---

## 12. Zusammenfassung

Dieses Drill-Playbook bietet:

- ✅ **Konkrete, reproduzierbare Szenarien** für Incident-Übungen
- ✅ **Klare Erfolgskriterien** für jeden Drill
- ✅ **Integration** mit bestehenden Runbooks & Tools
- ✅ **Dokumentations-Framework** für Drill-Ergebnisse

**Nächste Schritte:**

1. Führe deinen ersten Drill durch (z.B. Szenario 3 – Risk-Limit-Verletzung)
2. Dokumentiere das Ergebnis in `INCIDENT_DRILL_LOG.md`
3. Passe Runbooks & Prozesse basierend auf Erkenntnissen an
4. Plane regelmäßige Drills (monatlich/quartalsweise)

---

**Built with ❤️ and safety-first architecture**
