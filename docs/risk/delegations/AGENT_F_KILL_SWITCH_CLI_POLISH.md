# Agent F: Kill Switch CLI Polish & Operator UX

**Agent:** F (Emergency Controls Specialist)  
**Phase:** 5 (Finalisierung)  
**Priorität:** 🟡 MITTEL  
**Aufwand:** 1 Tag  
**Status:** 📋 BEREIT ZU STARTEN

---

## 🎯 Ziel

Finalisierung des Kill Switch CLI für Production-Ready Operator Experience.

**Kontext:** Kill Switch ist zu 97% fertig. Diese Task poliert die letzten 3% für optimale Operator-Experience.

---

## 📋 Aufgaben

### 1. CLI Error Messages verbessern

**Aktuell:** Generische Fehlermeldungen  
**Ziel:** Hilfreiche, actionable Error Messages mit Kontext

**Dateien:**
- `src/risk_layer/kill_switch/cli.py`

**Beispiel-Verbesserungen:**

```python
# VORHER
if not kill_switch.is_killed:
    print("Error: Kill switch not in KILLED state")
    sys.exit(1)

# NACHHER
if not kill_switch.is_killed:
    print("❌ ERROR: Recovery nicht möglich")
    print(f"   Aktueller State: {kill_switch.state.name}")
    print(f"   Erwarteter State: KILLED")
    print()
    print("💡 TIPP: Trigger den Kill Switch zuerst:")
    print("   python -m peak_trade.risk.kill_switch trigger --reason 'Test'")
    sys.exit(1)
```

**Acceptance Criteria:**
- [ ] Alle Error Messages haben Emoji-Prefix (❌, ⚠️, 💡)
- [ ] Jeder Error zeigt aktuellen State
- [ ] Jeder Error hat einen "TIPP" mit nächstem Schritt
- [ ] Exit Codes sind dokumentiert (0=OK, 1=Error, 2=Invalid State)

---

### 2. Operator Runbook Hilfe-Texte

**Ziel:** Inline-Hilfe für häufige Operator-Tasks

**Dateien:**
- `src/risk_layer/kill_switch/cli.py`

**Neue Commands:**

```bash
# Hilfe für Recovery-Workflow
python -m peak_trade.risk.kill_switch help recovery

# Hilfe für Troubleshooting
python -m peak_trade.risk.kill_switch help troubleshoot

# Quick Reference
python -m peak_trade.risk.kill_switch help quick-ref
```

**Implementierung:**

```python
def cmd_help(subcommand: str):
    """Zeigt Hilfe für spezifische Workflows."""

    if subcommand == "recovery":
        print("""
╔════════════════════════════════════════════════════════════════╗
║                   KILL SWITCH RECOVERY WORKFLOW                ║
╚════════════════════════════════════════════════════════════════╝

📋 VORAUSSETZUNGEN:
   1. Kill Switch ist im KILLED State
   2. Trigger-Grund wurde behoben
   3. System Health ist OK

🔄 SCHRITTE:

   1️⃣  Health Check durchführen
       $ python -m peak_trade.risk.kill_switch health

   2️⃣  Recovery starten (mit Approval Code)
       $ python -m peak_trade.risk.kill_switch recover \\
           --code "EMERGENCY_RECOVERY_2025" \\
           --reason "Wartung abgeschlossen"

   3️⃣  Cooldown abwarten (5 Minuten)
       Status prüfen:
       $ python -m peak_trade.risk.kill_switch status

   4️⃣  Position Limits überwachen
       - Nach Recovery: 50% der normalen Limits
       - Nach 1h: 75% der normalen Limits
       - Nach 2h: 100% der normalen Limits

⚠️  WICHTIG:
   - Approval Code aus Umgebungsvariable: KILL_SWITCH_APPROVAL_CODE
   - Bei Problemen: docs/ops/KILL_SWITCH_TROUBLESHOOTING.md

📞 SUPPORT:
   - Dokumentation: docs/ops/KILL_SWITCH_RUNBOOK.md
   - Logs: logs/kill_switch_audit_*.jsonl
        """)

    elif subcommand == "troubleshoot":
        # ... ähnlich strukturiert
        pass

    elif subcommand == "quick-ref":
        print("""
╔════════════════════════════════════════════════════════════════╗
║                   KILL SWITCH QUICK REFERENCE                  ║
╚════════════════════════════════════════════════════════════════╝

📊 STATUS ABFRAGEN:
   $ python -m peak_trade.risk.kill_switch status

🚨 MANUELLER TRIGGER:
   $ python -m peak_trade.risk.kill_switch trigger \\
       --reason "Wartung" --confirm

🔄 RECOVERY STARTEN:
   $ python -m peak_trade.risk.kill_switch recover \\
       --code "CODE" --reason "Grund"

📜 AUDIT TRAIL:
   $ python -m peak_trade.risk.kill_switch audit --limit 50

🏥 HEALTH CHECK:
   $ python -m peak_trade.risk.kill_switch health

📚 HILFE:
   $ python -m peak_trade.risk.kill_switch help recovery
   $ python -m peak_trade.risk.kill_switch help troubleshoot
        """)
```

**Acceptance Criteria:**
- [ ] `help recovery` Command implementiert
- [ ] `help troubleshoot` Command implementiert
- [ ] `help quick-ref` Command implementiert
- [ ] Alle Hilfe-Texte sind Box-formatiert (╔═╗ Style)
- [ ] Emoji-Icons für visuelle Struktur

---

### 3. Health Check Output formatieren

**Aktuell:** Plain Text Output  
**Ziel:** Strukturierter, farbiger Output mit klaren Status-Indikatoren

**Dateien:**
- `src/risk_layer/kill_switch/cli.py`
- `src/risk_layer/kill_switch/health_check.py`

**Beispiel-Output:**

```
╔════════════════════════════════════════════════════════════════╗
║                   KILL SWITCH HEALTH CHECK                     ║
╚════════════════════════════════════════════════════════════════╝

🔍 SYSTEM CHECKS:

   ✅ Memory Available:     2.4 GB / 16.0 GB (15%)
   ✅ CPU Usage:            12% (Threshold: 80%)
   ✅ Disk Space:           45.2 GB free
   ✅ Process Running:      PID 12345 (Uptime: 3d 14h)

🔌 CONNECTIVITY:

   ✅ Exchange Connection:  Kraken (Latency: 45ms)
   ✅ Price Feed:           BTC-EUR: €42,350.00 (Age: 2s)
   ⚠️  Network Quality:     Packet Loss: 0.5% (Acceptable)

📊 RISK METRICS:

   ✅ Portfolio Drawdown:   -8.2% (Threshold: -15%)
   ✅ Daily P&L:            +2.1% (Threshold: -5%)
   ✅ VaR (95%):            €850 (Limit: €2,000)

🎯 OVERALL STATUS:

   ✅ HEALTHY - System ready for recovery

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 NEXT STEPS:
   System ist bereit für Recovery. Starte Recovery mit:
   $ python -m peak_trade.risk.kill_switch recover --code "CODE"
```

**Bei Problemen:**

```
╔════════════════════════════════════════════════════════════════╗
║                   KILL SWITCH HEALTH CHECK                     ║
╚════════════════════════════════════════════════════════════════╝

🔍 SYSTEM CHECKS:

   ❌ Memory Available:     14.8 GB / 16.0 GB (92%)
      ⚠️  KRITISCH: Memory-Threshold überschritten (90%)

   ✅ CPU Usage:            12% (Threshold: 80%)
   ✅ Disk Space:           45.2 GB free

🔌 CONNECTIVITY:

   ❌ Exchange Connection:  FAILED (Timeout after 10s)
      ⚠️  KRITISCH: Keine Verbindung zu Kraken

🎯 OVERALL STATUS:

   ❌ UNHEALTHY - 2 kritische Probleme gefunden

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  WARNUNG:
   Recovery NICHT empfohlen. Behebe zuerst folgende Probleme:

   1. Memory-Usage reduzieren (aktuell 92%, Limit 90%)
      → Andere Prozesse beenden oder System neustarten

   2. Exchange-Verbindung wiederherstellen
      → Netzwerk prüfen, Kraken-Status prüfen

📚 TROUBLESHOOTING:
   docs/ops/KILL_SWITCH_TROUBLESHOOTING.md
```

**Implementierung:**

```python
def format_health_check(result: HealthCheckResult) -> str:
    """Formatiert Health Check für CLI-Output."""

    lines = []
    lines.append("╔" + "═" * 64 + "╗")
    lines.append("║" + "KILL SWITCH HEALTH CHECK".center(64) + "║")
    lines.append("╚" + "═" * 64 + "╝")
    lines.append("")

    # System Checks
    lines.append("🔍 SYSTEM CHECKS:")
    lines.append("")

    for check in result.system_checks:
        icon = "✅" if check.passed else "❌"
        lines.append(f"   {icon} {check.name:20s} {check.status}")
        if not check.passed and check.details:
            lines.append(f"      ⚠️  {check.details}")

    # ... weitere Sections

    # Overall Status
    lines.append("")
    lines.append("🎯 OVERALL STATUS:")
    lines.append("")

    if result.is_healthy:
        lines.append("   ✅ HEALTHY - System ready for recovery")
    else:
        lines.append(f"   ❌ UNHEALTHY - {len(result.issues)} kritische Probleme gefunden")

    return "\n".join(lines)
```

**Acceptance Criteria:**
- [ ] Box-formatierter Output mit Unicode-Zeichen
- [ ] Emoji-Icons für Status (✅ ❌ ⚠️)
- [ ] Farbige Ausgabe (optional, via `colorama` oder ANSI codes)
- [ ] Klare "NEXT STEPS" Section
- [ ] Bei Problemen: Konkrete Troubleshooting-Hinweise

---

### 4. Status Command erweitern

**Aktuell:** Basis-Status  
**Ziel:** Detaillierter Status mit Trigger-History

**Beispiel-Output:**

```
╔════════════════════════════════════════════════════════════════╗
║                     KILL SWITCH STATUS                         ║
╚════════════════════════════════════════════════════════════════╝

🔴 STATE:            KILLED
⏰ TRIGGERED AT:     2025-12-28 14:32:15 UTC (2h 15m ago)
👤 TRIGGERED BY:     threshold (portfolio_drawdown)
📝 REASON:           Drawdown=-16.2% exceeded threshold=-15.0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TRIGGER CONFIGURATION:

   ✅ Drawdown Trigger:      Enabled (Threshold: -15%)
   ✅ Daily Loss Trigger:    Enabled (Threshold: -5%)
   ⚠️  Volatility Trigger:   Disabled
   ✅ System Health Watchdog: Enabled

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📜 RECENT EVENTS (Last 5):

   2025-12-28 14:32:15  🚨 ACTIVE → KILLED
                        Reason: Drawdown=-16.2% exceeded threshold

   2025-12-28 10:15:42  ✅ RECOVERING → ACTIVE
                        Reason: Recovery completed

   2025-12-28 10:10:30  ⏳ KILLED → RECOVERING
                        Reason: Recovery requested by operator_frank

   2025-12-28 09:45:12  🚨 ACTIVE → KILLED
                        Reason: Manual trigger for maintenance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 NEXT STEPS:
   Kill Switch ist aktiv. Trading ist blockiert.

   Um Recovery zu starten:
   1. Behebe den Trigger-Grund (Drawdown reduzieren)
   2. Führe Health Check durch: kill_switch health
   3. Starte Recovery: kill_switch recover --code "CODE"
```

**Acceptance Criteria:**
- [ ] Detaillierter State mit Timestamps
- [ ] Trigger-Configuration Overview
- [ ] Recent Events (letzte 5)
- [ ] Context-sensitive "NEXT STEPS"

---

## 📁 Dateien

### Zu modifizieren:
- `src/risk_layer/kill_switch/cli.py` – Hauptarbeit hier
- `src/risk_layer/kill_switch/health_check.py` – Health Check Formatting

### Zu erstellen:
- Keine neuen Dateien nötig

---

## 🧪 Tests

### Unit Tests (erweitern):
- `tests/risk_layer/kill_switch/test_cli.py`

**Neue Test-Cases:**
```python
def test_help_recovery_command():
    """Test help recovery command output."""
    result = subprocess.run(
        ["python", "-m", "peak_trade.risk.kill_switch", "help", "recovery"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "RECOVERY WORKFLOW" in result.stdout
    assert "VORAUSSETZUNGEN" in result.stdout

def test_health_check_formatting():
    """Test health check output formatting."""
    # Mock health check result
    result = HealthCheckResult(is_healthy=True, checks=[...])

    output = format_health_check(result)

    assert "╔" in output  # Box formatting
    assert "✅" in output  # Status icons
    assert "HEALTHY" in output

def test_status_with_trigger_history():
    """Test status command includes trigger history."""
    # Setup: Trigger kill switch
    kill_switch.trigger("Test trigger")

    result = subprocess.run(
        ["python", "-m", "peak_trade.risk.kill_switch", "status"],
        capture_output=True,
        text=True,
    )

    assert "RECENT EVENTS" in result.stdout
    assert "Test trigger" in result.stdout
```

**Acceptance Criteria:**
- [ ] Alle neuen Commands haben Tests
- [ ] Formatting-Funktionen haben Tests
- [ ] Exit Codes werden getestet

---

## 🎨 Design-Prinzipien

### 1. Operator-First
- Klare, actionable Fehlermeldungen
- Keine technischen Details ohne Kontext
- Immer "NEXT STEPS" anzeigen

### 2. Visual Hierarchy
- Emoji-Icons für schnelle Orientierung
- Box-Formatting für wichtige Sections
- Konsistente Farben (optional)

### 3. Defensive UX
- Bestätigungen für kritische Actions
- Dry-Run Mode für Testing
- Verbose Mode für Debugging

---

## 📊 Acceptance Criteria (Gesamt)

- [ ] Alle Error Messages haben hilfreichen Kontext
- [ ] `help` Commands implementiert (recovery, troubleshoot, quick-ref)
- [ ] Health Check Output ist strukturiert und visuell klar
- [ ] Status Command zeigt Trigger-History
- [ ] Alle neuen Features haben Tests (>90% Coverage)
- [ ] CLI ist dokumentiert in `docs/ops/KILL_SWITCH_RUNBOOK.md`
- [ ] Exit Codes sind konsistent (0=OK, 1=Error, 2=Invalid State)

---

## 🚀 Deliverables

### Code
- Modifizierte `src/risk_layer/kill_switch/cli.py`
- Modifizierte `src/risk_layer/kill_switch/health_check.py` (optional)

### Tests
- Erweiterte `tests/risk_layer/kill_switch/test_cli.py`

### Dokumentation
- Update `docs/ops/KILL_SWITCH_RUNBOOK.md` mit neuen Commands

---

## 📝 PR-Beschreibung

**Titel:** `feat(risk): polish kill-switch CLI and operator UX`

**Beschreibung:**
```markdown
## 🎯 Ziel

Finalisierung des Kill Switch CLI für Production-Ready Operator Experience.

## ✨ Änderungen

### 1. Verbesserte Error Messages
- Alle Errors haben Emoji-Prefix und Kontext
- "NEXT STEPS" für jeden Error
- Konsistente Exit Codes

### 2. Neue Help Commands
- `help recovery` – Recovery-Workflow
- `help troubleshoot` – Troubleshooting-Guide
- `help quick-ref` – Quick Reference

### 3. Formatierter Health Check
- Box-formatierter Output
- Emoji-Icons für Status
- Klare "NEXT STEPS" Section

### 4. Erweiterter Status Command
- Trigger-Configuration Overview
- Recent Events (letzte 5)
- Context-sensitive "NEXT STEPS"

## 🧪 Tests

- ✅ Alle neuen Commands haben Tests
- ✅ Formatting-Funktionen getestet
- ✅ Exit Codes validiert

## 📚 Dokumentation

- ✅ Runbook aktualisiert mit neuen Commands

## 🎨 Screenshots

[Optional: Screenshots von CLI-Output]
```

---

## ⏱️ Timeline

**Geschätzter Aufwand:** 1 Tag (8 Stunden)

| Task | Aufwand |
|------|---------|
| Error Messages verbessern | 2h |
| Help Commands implementieren | 2h |
| Health Check formatieren | 2h |
| Status Command erweitern | 1h |
| Tests schreiben | 1h |

---

## 📞 Support

**Bei Fragen:**
- Alignment Doc: `docs/risk/RISK_LAYER_ROADMAP_ALIGNMENT.md`
- Kill Switch Architecture: `docs/risk/KILL_SWITCH_ARCHITECTURE.md`
- Operator Runbook: `docs/ops/KILL_SWITCH_RUNBOOK.md`

**Agent A (Lead):** Verfügbar für Architektur-Fragen

---

**Erstellt von:** Agent A (Lead Orchestrator)  
**Delegiert an:** Agent F (Emergency Controls Specialist)  
**Status:** 📋 BEREIT ZU STARTEN

**Viel Erfolg! 🚀**
