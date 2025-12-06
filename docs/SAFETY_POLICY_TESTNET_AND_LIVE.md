# Peak_Trade – Safety Policy für Testnet & Live

> **Status:** Phase 25 – Governance & Safety-Dokumentation
> **Scope:** Policy-Dokument für zukünftige Testnet-/Live-Szenarien
> **Hinweis:** Diese Policy beschreibt Anforderungen, die erfüllt sein müssen, bevor Testnet/Live **jemals** aktiviert wird

---

## 1. Scope der Safety-Policy

### Was diese Policy abdeckt

Diese Safety-Policy gilt für alle Aktivitäten, die **nicht** Backtest, Paper oder Shadow sind:

| Modus | Covered by Policy | Beschreibung |
|-------|-------------------|--------------|
| Backtest | Nein | Historische Simulation |
| Paper | Nein | Simulierte Execution ohne API |
| Shadow | Nein | Shadow-Execution (Phase 24), keine echten Calls |
| **Testnet** | **Ja** | Echte API-Calls an Testnet-Endpoints |
| **Live** | **Ja** | Echte API-Calls an Production-Endpoints |

### Aktueller Status

**Peak_Trade befindet sich derzeit in Stufe 0–1 (Research/Shadow).**

- Live-/Testnet-Executors sind Stubs/blockiert
- Keine echten Exchange-Verbindungen implementiert
- Diese Policy ist **vorbereitend**, nicht aktivierend

---

## 2. Risk-Limits & Konfiguration

### 2.1 Übersicht der Limits

Die Risk-Limits werden in `config.toml` unter `[live_risk]` definiert:

```toml
[live_risk]
enabled = true
max_daily_loss_abs = 500.0         # Max. Tagesverlust in EUR
max_daily_loss_pct = 5.0           # Max. Tagesverlust in % des Startkapitals
max_total_exposure_notional = 5000.0   # Max. Gesamt-Exposure
max_symbol_exposure_notional = 2500.0  # Max. Exposure pro Symbol
max_open_positions = 10            # Max. parallele Positionen
max_order_notional = 1000.0        # Max. Notional pro Order
block_on_violation = true          # Bei Verletzung blockieren
use_experiments_for_daily_pnl = true
```

### 2.2 Limit-Definitionen

| Limit | Beschreibung | Empfohlener Wert |
|-------|--------------|------------------|
| `max_daily_loss_abs` | Absoluter maximaler Tagesverlust | 2–5% des Gesamtkapitals |
| `max_daily_loss_pct` | Relativer maximaler Tagesverlust | 5% |
| `max_total_exposure_notional` | Maximale Gesamt-Exposure | 50% des Kapitals |
| `max_symbol_exposure_notional` | Maximale Exposure pro Symbol | 25% des Kapitals |
| `max_open_positions` | Maximale Anzahl offener Positionen | 10 |
| `max_order_notional` | Maximales Volumen pro Order | 10% des Kapitals |

### 2.3 Regeln für Limit-Änderungen

1. **Keine Deaktivierung von `block_on_violation`** ohne expliziten Prozess:
   - Erfordert schriftliche Begründung
   - Zwei-Augen-Prinzip (Review + Owner-Freigabe)
   - Zeitlich begrenzt (z.B. max. 24h für Debug-Zwecke)

2. **Änderungen an Limits erfordern:**
   - Dokumentierte Begründung
   - Risk-Impact-Analyse
   - Review durch Risk Officer oder zweiten Developer
   - Eintrag im Changelog

3. **Erhöhung von Limits (lockern):**
   - Zusätzliche Prüfung: Warum sind aktuelle Limits zu restriktiv?
   - Schrittweise Erhöhung empfohlen (max. 25% pro Änderung)

4. **Senkung von Limits (verschärfen):**
   - Kann ohne Review erfolgen (konservativer = sicherer)
   - Trotzdem dokumentieren

---

## 3. SafetyGuard & Environment

### 3.1 Environment-Modi

```
environment.mode ∈ {paper, testnet, live}
```

| Mode | Beschreibung | API-Calls |
|------|--------------|-----------|
| `paper` | Simulation, kein Exchange-Kontakt | Nein |
| `testnet` | Testnet-APIs (z.B. Kraken Sandbox) | Ja (Testnet) |
| `live` | Production-APIs mit echtem Geld | Ja (Production) |

### 3.2 Bedingungen für Live-Modus

Bevor `environment.mode = "live"` **überhaupt denkbar** ist, müssen folgende Bedingungen erfüllt sein:

1. **Globale Flags:**
   ```toml
   [environment]
   mode = "live"
   enable_live_trading = true
   require_confirm_token = true
   confirm_token = "I_KNOW_WHAT_I_AM_DOING"
   ```

2. **Symbol-Whitelist:**
   - Nur explizit freigegebene Symbole handelbar
   - Definiert in `live_allowed_symbols` oder SafetyGuard

3. **Risk-Limits aktiv:**
   - `[live_risk].enabled = true`
   - Alle Limits konfiguriert und sinnvoll

4. **Logging & Monitoring:**
   - Order-Logging aktiv
   - Experiments-Registry funktionsfähig
   - Monitoring/Alerting eingerichtet

5. **Runbooks vorhanden:**
   - Start/Stop-Runbooks dokumentiert
   - Incident-Response definiert
   - Kill-Switch getestet

6. **Governance-Freigabe:**
   - Checklist abgearbeitet
   - Owner-Freigabe dokumentiert

### 3.3 SafetyGuard-Prüfungen

Der `SafetyGuard` prüft bei jeder Order:

1. **Environment-Check:** Ist der aktuelle Mode erlaubt für diese Operation?
2. **Flag-Check:** Sind alle erforderlichen Flags gesetzt?
3. **Symbol-Check:** Ist das Symbol auf der Whitelist?
4. **Limit-Check:** Sind alle Risk-Limits eingehalten?
5. **Manual-Confirm-Check:** Ist manuelle Bestätigung erforderlich?

Bei Verletzung wird die Order **blockiert**, nicht durchgewunken.

---

## 4. Stufenmodell (Referenz auf Phase 23)

### 4.1 Übersicht der Stufen

| Stufe | Name | Beschreibung | Safety-Requirements |
|-------|------|--------------|---------------------|
| 0 | Research-Only | Backtests, Sweeps, Analyse | Keine besonderen |
| 1 | Shadow | Shadow-Execution, simulierte Orders | Tests grün, Shadow-Config |
| 2 | Testnet | Echte Testnet-API-Calls | Monitoring, Runbooks |
| 3 | Shadow-Live | Live-Daten, simulierte Orders | Erweiterte Limits |
| 4 | Live | Echte Production-Orders | Vollständige Governance |

### 4.2 Safety-Requirements pro Stufe

**Stufe 0 → Stufe 1 (Research → Shadow):**
- Alle Unit-Tests grün
- Shadow-Config in `config.toml` vorhanden
- Strategien haben Backtest-Historie

**Stufe 1 → Stufe 2 (Shadow → Testnet):**
- Shadow-Runs über N Wochen ohne kritische Incidents
- Monitoring/Alerting eingerichtet
- Risk-Limits dokumentiert und reviewed
- Runbooks für Testnet vorhanden

**Stufe 2/3 → Stufe 4 (Testnet → Live):**
- Testnet-Betrieb über N Wochen stabil
- Vollständige Governance-Dokumentation
- Zwei-Personen-Freigabe
- Finanzielle Impact-Analyse
- Kill-Switch getestet
- Runbooks für Live vorhanden

---

## 5. Verbote & Rote Linien

### 5.1 Absolute Verbote

Die folgenden Aktionen sind **unter allen Umständen verboten**:

1. **Live-Trading ohne Runbooks:**
   - Keine Live-Aktivierung ohne dokumentierte Start/Stop/Incident-Prozeduren

2. **API-Keys im Klartext:**
   - Keine API-Keys in Code, Config-Files oder Versionskontrolle
   - Nur über ENV-Variablen, Secret-Manager oder OS Keychain

3. **Unbegrenzte Positionen:**
   - `max_open_positions` muss **immer** gesetzt sein
   - Keine Deaktivierung von Position-Limits

4. **Handel ohne Risk-Limits:**
   - `[live_risk].enabled = false` ist für Live **verboten**
   - `block_on_violation = false` nur temporär für Debug erlaubt

5. **Ungetestete Strategien live:**
   - Keine Strategie ohne mindestens 6 Monate Backtest-Historie
   - Keine Strategie ohne positive Risk-Adjusted-Returns in Backtest

### 5.2 Rote Linien mit Eskalation

Bei folgenden Situationen ist **sofortige Eskalation** erforderlich:

1. **Unexpected Order Execution:**
   - Order wird ausgeführt, die nicht erwartet wurde
   - → Sofort System pausieren, Incident-Analyse

2. **Risk-Limit-Verletzung im Live-Modus:**
   - Trotz `block_on_violation = true` wird Order durchgelassen
   - → Sofort System stoppen, Code-Review

3. **Datenverlust in Registry:**
   - Experiments-Logs fehlen oder sind korrupt
   - → Backup wiederherstellen, Ursache analysieren

4. **Unerwartete API-Responses:**
   - Exchange antwortet mit unbekannten Fehlern
   - → System pausieren, Adapter-Code prüfen

### 5.3 Einschränkungen für spezielle Märkte

| Markttyp | Einschränkung |
|----------|---------------|
| **Leverage-Produkte** | Maximaler Hebel muss explizit begrenzt sein (z.B. max. 2x) |
| **Illiquide Märkte** | Nur mit zusätzlicher Prüfung (Spread-Check, Volume-Check) |
| **Neue Token/Coins** | Nur nach expliziter Whitelist-Freigabe |
| **Derivate** | Separate Risk-Limits, spezielle Runbooks |

---

## 6. Disclaimer

### 6.1 Rechtlicher Hinweis

**Diese Safety-Policy ist ein internes, technisches Governance-Dokument.**

Sie ersetzt **nicht**:
- Rechtliche Beratung
- Aufsichtsrechtliche Compliance-Prüfung
- Professionelle Finanzberatung
- Steuerliche Beratung

### 6.2 Haftungsausschluss

Peak_Trade ist ein experimentelles Research-Framework. Die Verwendung für echtes Trading erfolgt auf eigenes Risiko. Die hier dokumentierten Safety-Maßnahmen sind Best-Practice-Empfehlungen, keine Garantien.

### 6.3 Geltungsbereich

Diese Policy gilt für alle Nutzer und Entwickler von Peak_Trade, die an der Entwicklung oder dem Betrieb des Systems beteiligt sind.

---

## 7. Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `GOVERNANCE_AND_SAFETY_OVERVIEW.md` | Governance-Übersicht, Rollen, Prozesse |
| `RUNBOOKS_AND_INCIDENT_HANDLING.md` | Konkrete Runbooks |
| `LIVE_READINESS_CHECKLISTS.md` | Checklisten für Stufen-Übergänge |
| `PHASE_23_LIVE_TESTNET_BLUEPRINT.md` | Technischer Blueprint |
| `LIVE_RISK_LIMITS.md` | Technische Doku der Risk-Limits |

---

## 8. Changelog

- **Phase 25** (2025-12): Initial erstellt
  - Risk-Limits dokumentiert
  - SafetyGuard-Bedingungen definiert
  - Stufenmodell-Requirements beschrieben
  - Verbote und rote Linien festgelegt
  - Keine Code-Änderungen
