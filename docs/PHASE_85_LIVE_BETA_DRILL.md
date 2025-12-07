# Phase 85: Live-Beta Drill (Shadow/Testnet) v1.0

## Übersicht

**Status:** ✅ Implementiert
**Phase:** 85
**Ziel:** Simulierter "Alles zusammen"-Durchlauf als Live-Beta Drill, ohne echtes Geld

Phase 85 vereint alle bisherigen Komponenten (Tiering, Live-Gates, Operator-Dashboard, Incident-Simulation) zu einem umfassenden Pre-Live-Drill.

---

## Motivation

**Problem:** Vor dem Live-Track-Start fehlt ein systematischer "Generalprobe"-Prozess:
- Wie wissen wir, dass alle Systeme korrekt interagieren?
- Wie prüfen wir, dass Safety-Gates wirklich greifen?
- Wie validieren wir, dass Incident-Handling funktioniert?

**Lösung:** Ein Live-Beta-Drill, das:
- Alle Subsysteme prüft (Pre-flight, Eligibility, Gates, Incidents)
- Klare Pass/Fail-Kriterien liefert
- Lessons Learned und Recommendations generiert
- Ohne echtes Kapital auskommt

---

## Neue Komponenten

### 1. Script: `scripts/run_live_beta_drill.py`

#### Drill-Kategorien

| Kategorie | Beschreibung |
|-----------|--------------|
| `preflight` | Pre-flight Check: Tiering, Policies, Presets |
| `eligibility` | Eligibility-Checks: Core/Legacy/Portfolio |
| `gates` | Shadow-Readiness: Live-Dry-Run-Drills (Phase 73) |
| `incident` | Incident-Simulation: Data-Gap, Risk-Limit, Alerts |

#### Datenmodelle

```python
@dataclass
class DrillCheckResult:
    check_name: str
    passed: bool
    details: str
    category: str  # preflight, eligibility, gates, incident
    severity: str  # info, warning, error

@dataclass
class LiveBetaDrillResult:
    timestamp: str
    drill_type: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: List[DrillCheckResult]
    lessons_learned: List[str]
    recommendations: List[str]
```

---

## Verwendung

### Vollständiger Drill

```bash
python scripts/run_live_beta_drill.py
```

**Ausgabe:**
```
======================================================================
  PEAK_TRADE LIVE-BETA DRILL (Phase 85)
======================================================================
  Timestamp: 2025-12-07T23:45:00
  Drill Type: live_beta_drill

======================================================================
  SUMMARY
======================================================================
  Status:         ✅ ALL PASSED
  Total Checks:   24
  Passed:         24
  Failed:         0

======================================================================
  PREFLIGHT
======================================================================
  ✅ Tiering-System Active
     Tiering: 3 core, 3 aux, 3 legacy (total: 9)
  ✅ Live-Policies Loaded
     Policies: min_sharpe_core=1.5, allow_legacy=False
  ✅ Eligibility-Summary Available
     Eligible: 6, Ineligible: 3
  ✅ Tiered Presets Available
     Tiered Presets: 3 available (core_balanced, ...)

======================================================================
  ELIGIBILITY
======================================================================
  ✅ Core Strategies Eligible
     All 3 core strategies are eligible
  ✅ Legacy Strategies Blocked
     All 3 legacy strategies are correctly blocked
  ...

======================================================================
  LESSONS LEARNED
======================================================================
  • All systems operational - Ready for Shadow/Testnet runs

======================================================================
  RECOMMENDATIONS
======================================================================
  → System is ready for Phase 86 (Research v1.0 Freeze)
```

### Einzelne Szenarien

```bash
# Nur Pre-flight
python scripts/run_live_beta_drill.py --scenario preflight

# Nur Eligibility
python scripts/run_live_beta_drill.py --scenario eligibility

# Nur Shadow-Gates
python scripts/run_live_beta_drill.py --scenario shadow-gates

# Nur Incident-Simulation
python scripts/run_live_beta_drill.py --scenario incident-sim
```

### JSON-Output

```bash
# JSON für Automation
python scripts/run_live_beta_drill.py --format json

# JSON in Datei speichern
python scripts/run_live_beta_drill.py --format json > drill_result.json
```

**JSON-Struktur:**
```json
{
  "phase": "85",
  "description": "Live-Beta Drill (Shadow/Testnet)",
  "timestamp": "2025-12-07T23:45:00",
  "summary": {
    "all_passed": true,
    "total_checks": 24,
    "passed_checks": 24,
    "failed_checks": 0
  },
  "checks": [...],
  "lessons_learned": [...],
  "recommendations": [...]
}
```

---

## Drill-Checks im Detail

### Pre-flight (4 Checks)

| Check | Prüft |
|-------|-------|
| Tiering-System Active | Sind Strategien nach Tier klassifiziert? |
| Live-Policies Loaded | Können live_policies.toml geladen werden? |
| Eligibility-Summary | Gibt es eligible Strategien? |
| Tiered Presets Available | Sind ≥3 Presets vorhanden? |

### Eligibility (4 Checks)

| Check | Prüft |
|-------|-------|
| Core Strategies Eligible | Sind alle Core-Strategien live-eligible? |
| Legacy Strategies Blocked | Sind Legacy-Strategien korrekt blockiert? |
| Presets Tiering-Compliant | Sind alle Presets tiering-compliant? |
| Portfolio core_balanced Eligible | Ist core_balanced eligible? |

### Gates (8 Checks)

Führt die Standard-Live-Dry-Run-Drills aus Phase 73 aus:

| Drill | Prüft |
|-------|-------|
| A - Voll gebremst | enable_live_trading=False blockiert |
| B - Gate 1 ok, Gate 2 fehlt | live_mode_armed=False blockiert |
| C - Dry-Run aktiv | live_dry_run_mode=True blockiert |
| D - Confirm-Token fehlt | Falsches Token blockiert |
| E - Risk-Limits | Risk-Limit-Konzept |
| F - Testnet-Modus | Testnet blockiert |
| G - Paper-Modus | Paper blockiert |
| Summary | Alle Gates bestanden? |

### Incident Simulation (4 Checks)

| Check | Prüft |
|-------|-------|
| Data-Gap Detection | Würde Data-Layer Lücken erkennen? |
| Risk-Limit Enforcement | Würde LiveRiskLimits blockieren? |
| Alert-System Fallback | Würden Alerts auf Log fallen? |
| PnL-Divergenz Detection | Würde Monitoring PnL vergleichen? |

---

## Integration in CI/CD

```yaml
# .github/workflows/live_beta_drill.yml
- name: Live-Beta Drill
  run: |
    python scripts/run_live_beta_drill.py --format json > drill.json
    if python -c "import json; d=json.load(open('drill.json')); exit(0 if d['summary']['all_passed'] else 1)"; then
      echo "All checks passed"
    else
      echo "Drill failed!"
      exit 1
    fi
```

---

## Pre-Live Checklist

Vor einem Shadow-/Testnet-Run sollte der Drill bestanden sein:

```bash
# 1. Drill ausführen
python scripts/run_live_beta_drill.py

# 2. Bei ALL PASSED → Shadow-Run starten
if [ $? -eq 0 ]; then
    echo "Drill passed - starting shadow run"
    python scripts/testnet_orchestrator_cli.py start-shadow \
      --strategy ma_crossover \
      --symbol BTC/EUR \
      --timeframe 1m
else
    echo "Drill failed - review issues first"
fi
```

---

## Tests

```bash
# Alle Live-Beta Drill Tests
pytest tests/test_live_beta_drill.py -v
```

### Testabdeckung

| Testklasse | Tests |
|------------|-------|
| `TestDrillCheckResult` | Datamodel-Tests |
| `TestLiveBetaDrillResult` | Datamodel-Tests |
| `TestPreflightDrill` | Pre-flight Checks |
| `TestEligibilityDrill` | Eligibility Checks |
| `TestShadowGatesDrill` | Gate Checks |
| `TestIncidentSimulationDrill` | Incident Checks |
| `TestRunAllDrills` | Gesamtdrill |
| `TestFormatters` | Text/JSON Formatter |
| `TestLiveBetaDrillCLI` | CLI-Tests |
| `TestLiveBetaDrillIntegration` | Integration |

---

## Verbindung zu anderen Phasen

| Phase | Verbindung |
|-------|------------|
| **Phase 73** | Nutzt Live-Dry-Run-Drills |
| **Phase 80** | Prüft Tiered Presets |
| **Phase 83** | Nutzt Live-Gates für Eligibility |
| **Phase 84** | Ergänzt Operator-Dashboard |
| **Phase 86** | Pre-Condition für Research Freeze |

---

## Lessons Learned System

Das Drill generiert automatisch:

### Bei Erfolg
```
• All systems operational - Ready for Shadow/Testnet runs
→ System is ready for Phase 86 (Research v1.0 Freeze)
```

### Bei Fehlern
```
• X checks failed - Review required before Shadow/Testnet
→ Review Gate-Drills - some safety gates may not be correctly configured
→ Review Eligibility - some strategies/portfolios may not be live-ready
```

---

## Definition of Done

- [x] `scripts/run_live_beta_drill.py` implementiert
- [x] Pre-flight, Eligibility, Gates, Incident-Szenarien
- [x] Text- und JSON-Output
- [x] CLI mit --scenario und --format
- [x] Tests (40 Tests)
- [x] Dokumentation

---

## Nächste Schritte

→ **Phase 86:** Research v1.0 Freeze & Live-Beta Label
  - Release Notes finalisieren
  - Git-Tags setzen
  - Scope-Freeze dokumentieren
