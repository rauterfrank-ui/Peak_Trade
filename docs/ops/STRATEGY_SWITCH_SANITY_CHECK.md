# Strategy-Switch Sanity Check — Governance Documentation

**Stand**: Januar 2026  
**Status**: ✅ Produktiv (in TestHealthAutomation integriert)  
**Version**: v1.0

---

## Überblick

Der **Strategy-Switch Sanity Check** ist eine Governance-Prüfung für die `[live_profile.strategy_switch]`-Konfiguration in `config/config.toml`. Er validiert, dass nur sichere, live-ready Strategien für Live-Trading freigegeben sind.

### Zweck

- **Governance-Gate**: Verhindert versehentliche Freigabe von R&D-Strategien für Live-Trading
- **Konsistenz-Check**: Validiert, dass `active_strategy_id` in der `allowed`-Liste enthalten ist
- **Registry-Validierung**: Prüft, dass alle Strategien in `allowed` in der Strategy-Registry existieren
- **Read-Only**: Führt KEINE Änderungen durch, nur Validierung und Reporting

### Guardrails (nicht verhandelbar)

- ❌ **Kein automatisches Switching** — nur Validierung
- ❌ **Keine Config-Änderungen** — read-only
- ❌ **Keine Live-Execution** — reine Offline-Prüfung
- ✅ **Deterministisch** — gleiche Inputs → gleiche Outputs
- ✅ **Maschinenlesbar** — JSON/MD/HTML Reports

---

## Governance-Regeln

Der Check validiert folgende Regeln:

### 1. `allowed`-Liste darf nicht leer sein

```toml
[live_profile.strategy_switch]
allowed = []  # ❌ FAIL
```

**Rationale**: Ohne erlaubte Strategien ist kein Strategy-Switch möglich.

### 2. `active_strategy_id` muss in `allowed` enthalten sein

```toml
[live_profile.strategy_switch]
active_strategy_id = "unknown_strategy"
allowed = ["ma_crossover", "rsi_reversion"]  # ❌ FAIL
```

**Rationale**: Die aktive Strategie muss explizit freigegeben sein.

### 3. Keine R&D-Strategien in `allowed`

```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "armstrong_cycle"]  # ❌ FAIL (armstrong_cycle ist R&D)
```

**Rationale**: R&D-Strategien (`tier=r_and_d` oder `is_live_ready=False`) sind nicht für Live-Trading geeignet.

**Bekannte R&D-Strategien** (Stand Januar 2026):
- `armstrong_cycle`
- `el_karoui_vol_model`
- `ehlers_cycle_filter`
- `meta_labeling`
- `bouchaud_microstructure`
- `vol_regime_overlay`

### 4. Alle Strategien in `allowed` müssen in der Registry existieren

```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "nonexistent_strategy"]  # ❌ FAIL
```

**Rationale**: Unbekannte Strategy-IDs können nicht validiert werden.

### 5. Warnung bei zu vielen Strategien in `allowed`

```toml
[live_profile.strategy_switch]
allowed = ["s1", "s2", "s3", "s4", "s5", "s6"]  # ⚠️ WARN (> 5 Strategien)
```

**Rationale**: Viele Strategien erhöhen die Komplexität — bewusste Überprüfung erforderlich.

---

## Usage

### 1. Standalone CLI

```bash
# Einfacher Check
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml

# JSON-Output (maschinenlesbar)
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --json

# Quiet-Mode (nur Exit-Code)
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --quiet
```

**Exit-Codes**:
- `0` = OK (alles gesund)
- `1` = FAIL (kritische Violations)
- `2` = WARN (Warnungen, aber nicht kritisch)

### 2. TestHealthAutomation Integration

```bash
# Governance-Profil ausführen (inkl. Switch-Sanity)
python3 scripts/run_test_health_profile.py --profile governance_strategy_switch_sanity

# Weekly-Core-Profil (mit Switch-Sanity)
python3 scripts/run_test_health_profile.py --profile weekly_core

# Switch-Sanity überspringen (für spezielle Szenarien)
python3 scripts/run_test_health_profile.py --profile weekly_core --no-switch-sanity
```

### 3. Python-API

```python
from src.governance.strategy_switch_sanity_check import run_strategy_switch_sanity_check

# Check ausführen
result = run_strategy_switch_sanity_check(
    config_path="config/config.toml",
    section_path="live_profile.strategy_switch",
)

# Ergebnis prüfen
if result.ok:
    print("✅ Alles OK")
else:
    print(f"❌ Status: {result.status}")
    for msg in result.messages:
        print(f"  - {msg}")

# Violations prüfen
if result.r_and_d_strategies:
    print(f"R&D-Strategien gefunden: {result.r_and_d_strategies}")

if result.invalid_strategies:
    print(f"Unbekannte Strategien: {result.invalid_strategies}")
```

---

## Report-Artefakte

Der Check erzeugt folgende Artefakte (wenn über TestHealthAutomation ausgeführt):

### 1. JSON-Report (`summary.json`)

```json
{
  "switch_sanity": {
    "enabled": true,
    "is_ok": true,
    "violations": [],
    "active_strategy_id": "ma_crossover",
    "allowed": ["ma_crossover", "rsi_reversion", "breakout"],
    "config_path": "config/config.toml"
  }
}
```

**Felder**:
- `enabled`: Ob der Check aktiviert ist
- `is_ok`: `true` wenn keine Violations, sonst `false`
- `violations`: Liste von Violation-Messages (leer wenn OK)
- `active_strategy_id`: Aktuell konfigurierte aktive Strategie
- `allowed`: Liste der erlaubten Strategien
- `config_path`: Verwendete Config-Datei

### 2. Markdown-Report (`summary.md`)

```markdown
## 🔒 Strategy-Switch Sanity (v1)

**Status**: ✅ OK
**Active Strategy**: `ma_crossover`
**Allowed Strategies**: `ma_crossover`, `rsi_reversion`, `breakout`
**Config Path**: `config/config.toml`
```

### 3. HTML-Report (`summary.html`)

Visuell aufbereiteter Report mit Ampel-System (🟢 Grün / 🟡 Gelb / 🔴 Rot).

---

## Failure-Szenarien & Operator-Actions

### Szenario 1: R&D-Strategie in `allowed`

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
R&D- oder nicht-live-ready-Strategien in allowed: armstrong_cycle
```

**Operator-Action**:
1. Öffne `config/config.toml`
2. Entferne R&D-Strategie aus `[live_profile.strategy_switch].allowed`
3. Re-run Check: `python3 scripts&#47;run_strategy_switch_sanity_check.py --config config&#47;config.toml`

**Beispiel-Fix**:
```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "rsi_reversion"]  # armstrong_cycle entfernt
```

### Szenario 2: `active_strategy_id` nicht in `allowed`

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
active_strategy_id 'unknown_strategy' ist NICHT in der allowed-Liste.
```

**Operator-Action**:
1. Prüfe ob `active_strategy_id` korrekt ist
2. Falls korrekt: Füge zu `allowed` hinzu
3. Falls falsch: Korrigiere `active_strategy_id`

**Beispiel-Fix**:
```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"  # Korrigiert
allowed = ["ma_crossover", "rsi_reversion"]
```

### Szenario 3: Leere `allowed`-Liste

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
allowed-Liste ist leer – kein Strategy-Switch möglich.
```

**Operator-Action**:
1. Füge mindestens eine live-ready Strategie zu `allowed` hinzu
2. Setze `active_strategy_id` auf eine der erlaubten Strategien

**Beispiel-Fix**:
```toml
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover"]
```

### Szenario 4: Unbekannte Strategy-ID

**Symptom**:
```
❌ Strategy-Switch Sanity Check: FAIL
Unbekannte Strategy-IDs in allowed (nicht in Registry): nonexistent_strategy
```

**Operator-Action**:
1. Prüfe Schreibweise der Strategy-ID (Tippfehler?)
2. Prüfe ob Strategie in `src/strategies/registry.py` registriert ist
3. Falls nicht registriert: Entferne aus `allowed` oder registriere Strategie

**Beispiel-Fix**:
```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "rsi_reversion"]  # nonexistent_strategy entfernt
```

---

## CI/CD-Integration

### GitHub Actions Workflow

Der Check ist in `.github/workflows/test-health-automation.yml` integriert:

```yaml
- name: Run Governance Strategy-Switch Sanity
  run: |
    python3 scripts/run_test_health_profile.py \
      --profile governance_strategy_switch_sanity
```

**Verhalten**:
- ✅ **Exit 0**: Workflow continues
- ❌ **Exit 1**: Workflow fails (kritische Violations)

### Pre-Commit Hook (optional)

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check Strategy-Switch Sanity vor Commit
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --quiet

if [ $? -ne 0 ]; then
    echo "❌ Strategy-Switch Sanity Check failed!"
    echo "Fix violations in config/config.toml before committing."
    exit 1
fi
```

---

## Konfiguration

### TestHealthAutomation Config (`config/test_health_profiles.toml`)

```toml
[switch_sanity]
enabled = true
config_path = "config/config.toml"
section_path = "live_profile.strategy_switch"
allow_r_and_d_in_allowed = false
require_active_in_allowed = true
require_non_empty_allowed = true

r_and_d_strategy_keys = [
    "armstrong_cycle",
    "el_karoui_vol_model",
    "ehlers_cycle_filter",
    "meta_labeling",
    "bouchaud_microstructure",
    "vol_regime_overlay",
]
```

**Konfigurationsoptionen**:
- `enabled`: Check aktivieren/deaktivieren
- `config_path`: Pfad zur Haupt-Config
- `section_path`: TOML-Pfad zur strategy_switch Sektion
- `allow_r_and_d_in_allowed`: Wenn `false`, R&D-Strategien nicht erlaubt
- `require_active_in_allowed`: `active_strategy_id` muss in `allowed` sein
- `require_non_empty_allowed`: `allowed` darf nicht leer sein
- `r_and_d_strategy_keys`: Liste bekannter R&D-Strategien

---

## Testing

### Unit-Tests

```bash
# Alle Strategy-Switch-Sanity-Tests
python3 -m pytest tests/governance/test_strategy_switch_sanity_check.py -v

# Einzelne Test-Klasse
python3 -m pytest tests/governance/test_strategy_switch_sanity_check.py::TestHealthyConfig -v

# Integration-Tests
python3 -m pytest tests/ops/test_test_health_v1.py::TestRunSwitchSanityCheck -v
```

**Test-Coverage**:
- ✅ Healthy Config (OK)
- ✅ Active not in allowed (FAIL)
- ✅ R&D in allowed (FAIL)
- ✅ Empty allowed (FAIL)
- ✅ Config errors (FAIL)
- ✅ Too many strategies (WARN)
- ✅ Integration mit echter Config

### Manual Testing

```bash
# Test gegen echte Config
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml

# Test gegen Test-Config
cat > /tmp/test_config.toml << 'EOF'
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "armstrong_cycle"]
EOF

python3 scripts/run_strategy_switch_sanity_check.py --config /tmp/test_config.toml
# Erwartung: FAIL (armstrong_cycle ist R&D)
```

---

## Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'src'`

**Ursache**: PYTHONPATH nicht gesetzt

**Lösung**:
```bash
# Option 1: PYTHONPATH setzen
PYTHONPATH=/Users/frnkhrz/Peak_Trade python3 scripts/run_strategy_switch_sanity_check.py

# Option 2: Script wurde bereits gefixt (sys.path.insert in Script)
# Sollte nicht mehr auftreten
```

### Problem: Check schlägt fehl, aber Config sieht korrekt aus

**Debugging**:
```bash
# JSON-Output für Details
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --json

# Prüfe Registry
python3 -c "from src.strategies.registry import get_available_strategy_keys; print(get_available_strategy_keys())"

# Prüfe Config-Parsing
python3 -c "import tomllib; print(tomllib.load(open('config/config.toml', 'rb'))['live_profile']['strategy_switch'])"
```

### Problem: Check ist zu streng / zu viele Warnings

**Anpassung**:
```bash
# Max-Allowed-Threshold erhöhen (default: 5)
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml --max-allowed 10
```

---

## Maintenance

### Neue R&D-Strategie hinzufügen

1. Füge Strategy-Key zu `config/test_health_profiles.toml` hinzu:

```toml
[switch_sanity]
r_and_d_strategy_keys = [
    "armstrong_cycle",
    "el_karoui_vol_model",
    # ... bestehende ...
    "new_r_and_d_strategy",  # NEU
]
```

2. Füge Test-Case hinzu in `tests/governance/test_strategy_switch_sanity_check.py`:

```python
def test_new_r_and_d_strategy_blocked(self, temp_config_dir: Path):
    """Test: Neue R&D-Strategie wird blockiert."""
    config = """
[live_profile.strategy_switch]
active_strategy_id = "ma_crossover"
allowed = ["ma_crossover", "new_r_and_d_strategy"]
"""
    config_path = write_temp_config(temp_config_dir, config)
    result = run_strategy_switch_sanity_check(
        config_path=str(config_path),
        r_and_d_strategy_keys=["new_r_and_d_strategy"],
    )
    assert result.status == "FAIL"
    assert "new_r_and_d_strategy" in result.r_and_d_strategies
```

3. Run Tests:

```bash
python3 -m pytest tests/governance/test_strategy_switch_sanity_check.py -v
```

---

## FAQ

### Q: Kann ich den Check deaktivieren?

**A**: Ja, in `config/test_health_profiles.toml`:

```toml
[switch_sanity]
enabled = false
```

**WARNUNG**: Nicht empfohlen für Production-Umgebungen!

### Q: Wie füge ich eine neue Strategie zu `allowed` hinzu?

**A**:
1. Stelle sicher, dass Strategie in `src/strategies/registry.py` registriert ist
2. Stelle sicher, dass Strategie **nicht** R&D ist (`tier != "r_and_d"`, `is_live_ready = true`)
3. Füge zu `config/config.toml` hinzu:

```toml
[live_profile.strategy_switch]
allowed = ["ma_crossover", "rsi_reversion", "new_strategy"]  # NEU
```

4. Run Check:

```bash
python3 scripts/run_strategy_switch_sanity_check.py --config config/config.toml
```

### Q: Was ist der Unterschied zwischen `allowed` und `strategies.active`?

**A**:
- `strategies.active`: Strategien für **Backtests/Portfolio** (Research/Offline)
- `live_profile.strategy_switch.allowed`: Strategien für **Live-Trading** (Production)

**Rationale**: Live-Trading hat strengere Governance-Anforderungen.

### Q: Kann ich den Check für spezielle Configs anpassen?

**A**: Ja, über CLI-Argumente:

```bash
# Custom Section-Path
python3 scripts/run_strategy_switch_sanity_check.py \
    --config config/custom.toml \
    --section "custom_profile.strategy_switch"

# Custom Max-Allowed-Threshold
python3 scripts/run_strategy_switch_sanity_check.py \
    --config config/config.toml \
    --max-allowed 10
```

---

## Changelog

### v1.0 (Januar 2026)
- ✅ Initial implementation
- ✅ Integration in TestHealthAutomation
- ✅ CLI-Entry-Point mit JSON-Output
- ✅ 16 Unit-Tests + 7 Integration-Tests
- ✅ Governance-Regeln: R&D-Blocker, Active-in-Allowed, Registry-Validierung
- ✅ Report-Artefakte: JSON/MD/HTML
- ✅ CI/CD-Integration (GitHub Actions)
- ✅ Dokumentation (diese Datei)

---

## Kontakt & Support

- **Dokumentation**: `docs/ops/STRATEGY_SWITCH_SANITY_CHECK.md` (diese Datei)
- **Source Code**: `src/governance/strategy_switch_sanity_check.py`
- **CLI-Script**: `scripts/run_strategy_switch_sanity_check.py`
- **Tests**: `tests/governance/test_strategy_switch_sanity_check.py`
- **Config**: `config/test_health_profiles.toml` (Sektion `[switch_sanity]`)

Bei Fragen oder Problemen: Siehe **Troubleshooting**-Sektion oben.
