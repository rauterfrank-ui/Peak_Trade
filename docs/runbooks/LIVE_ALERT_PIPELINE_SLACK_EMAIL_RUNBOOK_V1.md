# Live Alert-Pipeline – Operator Runbook v1

## Übersicht

Dieses Runbook beschreibt die Handlungsempfehlungen für Operatoren beim Empfang von Alerts aus der Peak_Trade Alert-Pipeline (Phase 82).

**Alert-Kanäle:**
- 🔔 **Slack** (primär) – `#peak-trade-alerts`
- 📧 **E-Mail** (Backup) – nur bei `CRITICAL`

---

## Alert-Kategorien

| Kategorie | Beschreibung | Typische Quellen |
|-----------|--------------|------------------|
| `RISK` | Risk-Management-Events | Severity-Transitions, Limit-Breaches |
| `EXECUTION` | Order-Pipeline-Events | Fill-Fehler, Timeouts (v1.1) |
| `SYSTEM` | System-Health-Events | Heartbeat-Fails, API-Fehler (v1.1) |

---

## Severity-Levels

### ℹ️ INFO
**Bedeutung:** Informativ, keine sofortige Aktion erforderlich.

**Typische Events:**
- Recovery: `RED → GREEN`
- System-Status-Updates

**Aktion:**
- Zur Kenntnis nehmen
- Kein Handlungsbedarf

---

### ⚠️ WARN
**Bedeutung:** Erhöhte Aufmerksamkeit erforderlich. System funktioniert noch normal.

**Typische Events:**
- Risk Severity: `GREEN → YELLOW`
- Recovery: `RED → YELLOW`
- Limits im Warnbereich (80-99% ausgeschöpft)

**Sofortige Aktionen:**
1. Alert-Details im Slack-Block prüfen
2. Dashboard öffnen und Metriken validieren
3. Offene Positionen und Orders prüfen

**Empfohlene Maßnahmen:**
- [ ] Exposure-Verteilung analysieren
- [ ] Trading-Intensität ggf. reduzieren
- [ ] Daily-PnL engmaschig überwachen
- [ ] Position-Sizing anpassen (falls nötig)

**Monitoring-Intervall:** 1-5 Minuten

---

### 🚨 CRITICAL
**Bedeutung:** Sofortige Aktion erforderlich. Systemverhalten möglicherweise eingeschränkt.

**Typische Events:**
- Risk Severity: `YELLOW → RED` oder `GREEN → RED`
- Hard-Limit-Breach (MaxDailyLoss, Drawdown, Exposure)
- Orders werden automatisch blockiert

**Sofortige Aktionen:**
1. ⛔ **STOP** – Keine neuen Trades manuell initiieren
2. Dashboard sofort öffnen und Status verifizieren
3. Betroffene Limits und aktuelle Werte prüfen

**Eskalation:**
- [ ] Team/On-Call-Kontakt informieren (falls konfiguriert)
- [ ] Incident-Log anlegen (Zeitpunkt, Limit, Context)

**Empfohlene Maßnahmen:**
- [ ] Offene Orders prüfen und ggf. stornieren
- [ ] Bestehende Positionen evaluieren
- [ ] Kontrollierter Positions-Abbau erwägen
- [ ] Ursache identifizieren (Gap? Akkumulation? Over-Exposure?)
- [ ] Screenshots/Charts für Postmortem sichern

**Monitoring-Intervall:** Kontinuierlich (Live-Watch)

---

## Risk Severity Transitions

### GREEN → YELLOW

```
⚠️ [WARN] Risk Severity changed: GREEN → YELLOW
```

**Bedeutung:** Mindestens ein Limit im Warnbereich (80-99%).

**Checkliste:**
- [ ] Welche(s) Limit(s) sind betroffen?
- [ ] Wie schnell nähern wir uns dem Breach?
- [ ] Gibt es eine bekannte Ursache (News, Volatilität)?

**Nächste Schritte:**
1. Situation 5 Minuten beobachten
2. Bei Annäherung an BREACH: Defensive Maßnahmen einleiten
3. Bei Stabilisierung: Normale Überwachung fortsetzen

---

### YELLOW → RED

```
🚨 [CRITICAL] Risk Severity changed: YELLOW → RED
```

**Bedeutung:** Mindestens ein Limit wurde verletzt. **Neue Orders werden blockiert.**

**Sofort-Checkliste:**
- [ ] Welches Limit wurde verletzt?
- [ ] Wie weit über dem Limit liegen wir?
- [ ] Gibt es offene Orders, die storniert werden sollten?

**Nächste Schritte:**
1. Keine neuen Trades
2. Offene Orders evaluieren
3. Exit-Strategie für bestehende Positionen prüfen
4. Warten auf Recovery oder manuelle Intervention

---

### RED → YELLOW (Recovery)

```
⚠️ [WARN] Risk Severity changed: RED → YELLOW
```

**Bedeutung:** Limit-Verletzung behoben, aber weiterhin im Warnbereich.

**Checkliste:**
- [ ] Was hat zur Recovery geführt?
- [ ] Ist die Situation stabil?
- [ ] Sollten defensive Maßnahmen beibehalten werden?

---

### RED → GREEN (Full Recovery)

```
ℹ️ [INFO] Risk Severity changed: RED → GREEN
```

**Bedeutung:** Alle Limits wieder komfortabel eingehalten.

**Aktion:**
- Normalbetrieb kann fortgesetzt werden
- Postmortem für den Incident dokumentieren

---

## Hard-Limit-Breaches

### MaxDailyLoss Breach

```
🚨 [CRITICAL] max_daily_loss limit breached
```

**Bedeutung:** Tagesverlust hat das konfigurierte Maximum überschritten.

**Sofortige Aktionen:**
1. Alle Trading-Aktivitäten stoppen
2. Keine neuen Positionen eröffnen
3. Bestehende Positionen evaluieren

**Fragen:**
- Was war die Ursache? (einzelner Trade, Marktbewegung?)
- Waren Stop-Losses aktiv?
- Gibt es Positionen, die weiter Risiko bergen?

---

### Max Exposure Breach

```
🚨 [CRITICAL] max_total_exposure limit breached
```

**Bedeutung:** Gesamt-Exposure überschreitet das Limit.

**Sofortige Aktionen:**
1. Offene Orders prüfen (könnten Exposure erhöht haben)
2. Positions-Reduktion erwägen
3. Keine neuen Positionen

---

### Max Position Count Breach

```
🚨 [CRITICAL] max_open_positions limit breached
```

**Bedeutung:** Zu viele offene Positionen.

**Sofortige Aktionen:**
1. Positions-Liste prüfen
2. Älteste/kleinste Positionen für Exit evaluieren
3. Diversifikation überprüfen

---

## Troubleshooting

### Alert kommt nicht an

1. **Slack:**
   - Webhook-URL in `config.toml` prüfen
   - Slack-Channel-Berechtigungen prüfen
   - `alerts.slack.enabled = true` prüfen

2. **E-Mail:**
   - SMTP-Konfiguration prüfen
   - Environment-Variable für Passwort gesetzt?
   - `alerts.email.enabled = true` prüfen

3. **Generell:**
   - `alerts.enabled = true` in Config?
   - `min_severity` zu hoch eingestellt?
   - Logs auf Fehler prüfen: `peak_trade.live.alert_pipeline`

### Zu viele Alerts

1. Alert-Debouncing aktivieren (`debounce_seconds`)
2. `min_severity` erhöhen (z.B. von `WARN` auf `CRITICAL`)
3. Recovery-Alerts deaktivieren (`send_recovery_alerts = false`)

---

## Kontakte & Eskalation

| Rolle | Kontakt | Erreichbarkeit |
|-------|---------|----------------|
| On-Call Operator | [TBD] | 24/7 |
| Risk Manager | [TBD] | Business Hours |
| Tech Lead | [TBD] | Business Hours |

---

## Referenzen

- [Phase 82 Dokumentation](../phase82_alert_pipeline.md)
- [Live Risk Limits](../../src/live/risk_limits.py)
- [Alert Pipeline Code](../../src/live/alert_pipeline.py)
- [Config.toml](../../config/config.toml)

---

### Siehe auch

- [`INCIDENT_RUNBOOK_INTEGRATION_V1`](INCIDENT_RUNBOOK_INTEGRATION_V1.md) – Beschreibung der Runbook-Verknüpfung in der Alert-Pipeline (Phase 84)
- [`LIVE_RISK_SEVERITY_INTEGRATION`](LIVE_RISK_SEVERITY_INTEGRATION.md) – Details zum Live Risk Severity System, das viele Alerts triggert

---

*Version: v1.0 | Phase 82 | Dezember 2025*
