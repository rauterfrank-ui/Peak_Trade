# Phase 84: Operator Dashboard & Alerts v1.0

## Übersicht

**Status:** ✅ Implementiert
**Phase:** 84
**Ziel:** CLI-Dashboard für Operatoren mit Strategie-/Portfolio-/Eligibility-Übersicht

Phase 84 gibt Operatoren und Gatekeepern ein Tool, um mit einem Blick den "Gesundheitszustand" aller Strategien und Portfolios zu prüfen.

---

## Features

- **Strategien-Übersicht:** Tier, Eligibility, Profil-Status
- **Portfolio-Übersicht:** Eligibility, Compliance-Status
- **Alerts & Warnungen:** Stale Profiles, fehlende Profile, Compliance-Verstöße
- **JSON-Output:** Für Automation und Integration

---

## Verwendung

### Vollständiges Dashboard

```bash
python scripts/operator_dashboard.py
```

**Ausgabe:**
```
======================================================================
  PEAK_TRADE OPERATOR DASHBOARD
  Generated: 2025-12-07T23:45:00
======================================================================

======================================================================
  SUMMARY
======================================================================

  Strategies:
    Total:        12
    Core:         3
    Aux:          6
    Legacy:       3
    Eligible:     9
    With Profile: 5
    Stale:        0

  Portfolios:
    Total:        3
    Eligible:     3
    Compliant:    3

  Alerts:
    Errors:       0
    Warnings:     4
    Info:         0

======================================================================
  STRATEGIES
======================================================================

Strategy                  Tier       Eligible   Profile
----------------------------------------------------------------------
rsi_reversion             [CORE]     OK         OK
ma_crossover              [CORE]     OK         MISSING
bollinger_bands           [CORE]     OK         MISSING
breakout                  [AUX]      OK         OK
macd                      [AUX]      OK         MISSING
...
```

### Einzelne Views

```bash
# Nur Strategien
python scripts/operator_dashboard.py --view strategies

# Nur Portfolios
python scripts/operator_dashboard.py --view portfolios

# Nur Alerts
python scripts/operator_dashboard.py --view alerts

# Nur Summary
python scripts/operator_dashboard.py --view summary
```

### JSON-Output

```bash
# JSON für Automation
python scripts/operator_dashboard.py --format json

# JSON in Datei speichern
python scripts/operator_dashboard.py --format json > dashboard_status.json
```

**JSON-Struktur:**
```json
{
  "timestamp": "2025-12-07T23:45:00",
  "summary": {
    "total_strategies": 12,
    "strategies_by_tier": {"core": 3, "aux": 6, "legacy": 3},
    "strategies_eligible": 9,
    "total_portfolios": 3,
    "portfolios_eligible": 3,
    "alerts_error": 0,
    "alerts_warning": 4
  },
  "strategies": [
    {
      "strategy_id": "rsi_reversion",
      "tier": "core",
      "is_eligible": true,
      "has_profile": true,
      "profile_age_days": 5
    }
  ],
  "portfolios": [...],
  "alerts": [...]
}
```

---

## Alerts

### Alert-Kategorien

| Kategorie | Beschreibung |
|-----------|--------------|
| `profile` | Profil fehlt oder veraltet |
| `eligibility` | Strategy/Portfolio nicht eligible |
| `compliance` | Tiering-Compliance verletzt |
| `config` | Konfigurationsprobleme |

### Alert-Levels

| Level | Beschreibung | Exit-Code |
|-------|--------------|-----------|
| `error` | Kritisches Problem | 1 |
| `warning` | Warnung, aber nicht blockierend | 0 |
| `info` | Informativ | 0 |

### Typische Alerts

```
[!] [ELIGIBILITY] (rsi_reversion)
    Core strategy is NOT eligible: [...]

[?] [PROFILE] (ma_crossover)
    No profile found for core-tier strategy

[?] [PROFILE] (breakout)
    Profile is 45 days old (max: 30)

[!] [COMPLIANCE] (my_portfolio)
    Portfolio not compliant: ['breakout_donchian']

[?] [CONFIG]
    allow_legacy is TRUE in live_policies.toml
```

---

## Integration

### In CI/CD

```yaml
# .github/workflows/operator_checks.yml
- name: Operator Dashboard Check
  run: |
    python scripts/operator_dashboard.py --format json > dashboard.json
    # Prüfe auf Errors
    if python -c "import json; d=json.load(open('dashboard.json')); exit(d['summary']['alerts_error'])"; then
      echo "No critical alerts"
    else
      echo "Critical alerts found!"
      exit 1
    fi
```

### Pre-flight vor Shadow/Testnet

```bash
# Vor Shadow-Start
python scripts/operator_dashboard.py --view alerts
if [ $? -eq 0 ]; then
    echo "OK - starting shadow run"
    python scripts/testnet_orchestrator_cli.py start-shadow ...
else
    echo "Errors detected - aborting"
    exit 1
fi
```

### Regelmäßige Überwachung

```bash
# Cron-Job für täglichen Check
0 8 * * * python scripts/operator_dashboard.py --format json >> /var/log/peak_trade/dashboard.log
```

---

## Tests

```bash
# Alle Dashboard-Tests
pytest tests/test_operator_dashboard.py -v
```

### Testabdeckung

| Testklasse | Tests |
|------------|-------|
| `TestOperatorDashboardCLI` | CLI-Funktionalität |
| `TestOperatorDashboardJSONOutput` | JSON-Validierung |
| `TestOperatorDashboardContent` | Inhalt-Prüfung |
| `TestOperatorDashboardIntegration` | Integration mit Live-Gates |

---

## Verbindung zu anderen Phasen

| Phase | Verbindung |
|-------|------------|
| **Phase 80** | Zeigt Tiered Presets |
| **Phase 83** | Nutzt Live-Gates für Eligibility |
| **Phase 85** | Pre-flight vor Drill |

---

## Definition of Done

- [x] `scripts/operator_dashboard.py` implementiert
- [x] Strategien-View mit Tiering + Eligibility
- [x] Portfolio-View mit Compliance
- [x] Alerts-View mit kategorisierten Warnungen
- [x] JSON-Output für Automation
- [x] Tests (15 Tests)
- [x] Dokumentation

---

## Nächste Schritte

→ **Phase 85:** Dashboard als Pre-flight-Check vor Drill
→ **v1.1:** Web-Dashboard basierend auf JSON-Output
