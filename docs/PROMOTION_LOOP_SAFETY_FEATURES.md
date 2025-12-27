# Promotion Loop Safety Features (P0/P1)

**Version:** v1.1  
**Datum:** 2025-12-11  
**Status:** ✅ Implementiert & Getestet (33/33 Tests grün)

---

## 🎯 Übersicht

Das Learning & Promotion Loop System verfügt über zwei Ebenen von Sicherheitsfeatures:

- **P0 (Critical):** Harte Sicherheitssperren, die Auto-Promotion verhindern
- **P1 (Important):** Governance-Layer und Audit-Mechanismen

Diese Features schützen das System vor ungewollten oder gefährlichen Änderungen im bounded_auto-Modus.

---

## 🔒 P0: Critical Safety Features

### 1. Blacklist (Promotion-Sperre)

**Zweck:** Verhindert Auto-Promotion von kritischen/sensiblen Config-Targets

**Implementierung:**
- Prefix-Matching auf `target` (z.B., `live.api_keys` blockt auch `live.api_keys.binance`)
- Tag-basierte Blacklist (z.B., `r_and_d`, `experimental`)

**Konfiguration:**

```toml
# config/promotion_loop_config.toml

[promotion_loop.safety]
# Target-basierte Blacklist
auto_apply_blacklist = [
    "live.api_keys",           # Alle API-Keys
    "risk.stop_loss",          # Kritische Risk-Parameter
    "live.max_order_size",     # Order-Size-Limits
    "strategy.name",           # Verhindert Strategy-Wechsel
]

# Tag-basierte Blacklist
blacklist_tags = [
    "r_and_d",                 # R&D-Strategien
    "experimental",            # Experimentelle Features
    "untested",                # Nicht getestete Patches
]
```

**Verhalten:**
- **manual_only:** Kandidat bleibt sichtbar mit P0_BLACKLIST Flag, aber wird rejected
- **bounded_auto:** Kandidat wird hart rejected, keine Auto-Promotion möglich

**Beispiel:**

```python
# Dieser Patch wird rejected, egal wie hoch die Confidence ist
patch = ConfigPatch(
    target="live.api_keys.binance",
    old_value="old_key",
    new_value="new_key",
    confidence_score=0.99,  # Selbst 99% reicht nicht!
)
# → P0_BLACKLIST: Target 'live.api_keys.binance' matches blacklisted pattern 'live.api_keys'
```

---

### 2. Bounds (Harte Grenzen)

**Zweck:** Verhindert zu extreme Änderungen (min/max Werte, max_step)

**Implementierung:**
- Tag-basierte Bounds-Zuordnung (leverage, trigger, macro)
- Numerische Patches werden gegen min/max/max_step geprüft

**Konfiguration:**

```toml
# config/promotion_loop_config.toml

[promotion_loop.bounds]
# Leverage-Bounds
leverage_min = 1.0
leverage_max = 2.0
leverage_max_step = 0.25

# Trigger-Delay-Bounds
trigger_delay_min = 3.0
trigger_delay_max = 15.0
trigger_delay_max_step = 2.0

# Macro-Weight-Bounds
macro_weight_min = 0.0
macro_weight_max = 0.8
macro_weight_max_step = 0.1
```

**Verhalten:**
- Prüft `new_value` gegen min/max range
- Prüft `abs(new_value - old_value)` gegen max_step
- Nicht-numerische Werte werden übersprungen

**Beispiel:**

```python
# Zu aggressive Leverage-Erhöhung
patch = ConfigPatch(
    target="portfolio.leverage",
    old_value=1.0,
    new_value=2.5,  # > max_value (2.0) UND step 1.5 > max_step (0.25)
    confidence_score=0.85,
)
# → P0_BOUNDS: New value 2.5 > max_value 2.0 (tag: leverage)
# → P0_BOUNDS: Step 1.500 > max_step 0.25 (tag: leverage)
```

---

### 3. bounded_auto Guardrails

**Zweck:** Zusätzliche Sicherheitsschicht für Auto-Promotion

**Checks:**
1. **Global Promotion Lock:** Wenn aktiv, kein bounded_auto
2. **Keine P0 Violations:** Kandidat darf keine P0-Flags haben
3. **Confidence-Threshold:** Mindest-Confidence für Auto-Apply (Standard: 0.80)
4. **R&D Tier:** Keine R&D- oder experimentelle Patches
5. **Live-Ready Status:** `is_live_ready` Flag muss `True` sein

**Konfiguration:**

```toml
[promotion_loop.safety]
min_confidence_for_auto_apply = 0.80

[promotion_loop.governance]
global_promotion_lock = false
```

**Verhalten:**
- Guardrails werden NUR für `bounded_auto` mode enforced
- `manual_only` mode erlaubt Review, auch wenn Guardrails verletzt wären

**Beispiel:**

```python
# Zu niedrige Confidence für bounded_auto
patch = ConfigPatch(
    target="portfolio.leverage",
    old_value=1.0,
    new_value=1.2,
    confidence_score=0.75,  # < 0.80 threshold
)
# manual_only: ✅ OK (Operator kann reviewen)
# bounded_auto: ❌ REJECTED (P0_GUARDRAIL: Confidence 0.750 < min_threshold 0.800)
```

---

## 📊 P1: Important Safety Features

### 1. Audit Logging

**Zweck:** Vollständige Nachverfolgbarkeit aller Promotion-Entscheidungen

**Implementierung:**
- JSONL-Format (ein JSON-Objekt pro Zeile)
- Wird für ALLE Entscheidungen geschrieben (accepted + rejected)
- Fehler im Logging crashen das System nicht (graceful degradation)

**Konfiguration:**

```toml
[promotion_loop.governance]
audit_log_path = "reports/promotion_audit/promotion_audit.jsonl"
```

**Audit-Entry Format:**

```json
{
  "timestamp": "2025-12-11T23:45:00.123456",
  "mode": "manual_only",
  "patch_id": "patch_001",
  "target": "portfolio.leverage",
  "old_value": 1.0,
  "new_value": 1.25,
  "confidence_score": 0.85,
  "source_experiment_id": "test_health_2025_12_11",
  "decision_status": "ACCEPTED_FOR_PROPOSAL",
  "decision_reasons": [],
  "safety_flags": [],
  "tags": ["leverage"],
  "eligible_for_live": true,
  "meta": {...}
}
```

**Verwendung:**

```bash
# Alle akzeptierten Patches anzeigen
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.decision_status == "ACCEPTED_FOR_PROPOSAL")'

# Alle Patches mit P0 Violations
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.safety_flags | length > 0)'

# Statistik nach Mode
cat reports/promotion_audit/promotion_audit.jsonl | jq -r '.mode' | sort | uniq -c
```

---

### 2. Global Promotion Lock

**Zweck:** Notfall-Killswitch für bounded_auto

**Implementierung:**
- Wenn aktiv: bounded_auto wird zu manual_only degradiert
- manual_only bleibt erlaubt (mit deutlichem Warning)
- P0 Guardrail prüft den Lock-Status

**Konfiguration:**

```toml
[promotion_loop.governance]
global_promotion_lock = false  # true = Lock aktiv
```

**Verwendung:**

```bash
# Notfall: bounded_auto deaktivieren
# Edit config/promotion_loop_config.toml:
# global_promotion_lock = true

# Danach:
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
# → Wird automatisch zu manual_only degradiert mit Warning
```

**Verhalten:**

```
[promotion_loop] WARNING: Global promotion lock is active.
                 bounded_auto is disabled. Only manual changes are allowed.
[promotion_loop] Forcing mode to manual_only due to global lock.
```

---

## 🔄 Workflow & Integration

### 1. Promotion Cycle mit Safety Features

```python
from src.governance.promotion_loop import (
    build_promotion_candidates_from_patches,
    filter_candidates_for_live,
    load_safety_config_from_toml,
)

# 1. Load safety config
safety_config = load_safety_config_from_toml(Path("config/promotion_loop_config.toml"))

# 2. Build candidates
candidates = build_promotion_candidates_from_patches(patches)

# 3. Mark eligible
for candidate in candidates:
    if candidate.patch.confidence_score >= 0.75:
        candidate.eligible_for_live = True

# 4. Apply safety filters (P0 + P1)
decisions = filter_candidates_for_live(
    candidates,
    safety_config=safety_config,
    mode="bounded_auto",  # or "manual_only"
)

# 5. Check results
for decision in decisions:
    if decision.candidate.safety_flags:
        print(f"Safety flags: {decision.candidate.safety_flags}")
```

### 2. Safety Flags im Operator Report

Reports unter `reports/live_promotion/<run_id>/OPERATOR_CHECKLIST.md` zeigen Safety Flags:

```markdown
## Patches

### Patch 1: patch_demo_001
- Target: `live.api_keys.binance`
- Old value: `old_key`
- New value: `new_key`
- Confidence: `0.990`
- Tags: api_keys
- **Safety Flags:** P0_BLACKLIST: Target 'live.api_keys.binance' matches blacklisted pattern 'live.api_keys'
- Decision notes: candidate has P0 safety violations
```

---

## 🧪 Testing

### Unit Tests (26 Tests)

```bash
pytest tests/governance/test_promotion_loop_safety.py -v
```

**Test-Coverage:**
- P0: Blacklist (4 tests)
- P0: Bounds (6 tests)
- P0: Guardrails (6 tests)
- P0: Integration (3 tests)
- P1: Audit Logging (3 tests)
- P1: Global Lock (2 tests)
- Edge Cases (2 tests)

### Integration Tests (7 Tests)

```bash
pytest tests/governance/test_promotion_loop_safety_integration.py -v
```

**Szenarien:**
- Full cycle mit valid candidate
- Full cycle mit blacklisted candidate
- Full cycle mit out-of-bounds candidate
- Mixed candidates (valid + invalid)
- bounded_auto mode enforces stricter rules
- Global lock prevents bounded_auto
- Audit log records all decisions

### Alle Tests ausführen

```bash
pytest tests/governance/test_promotion_loop_safety*.py -v
# ✅ 33 passed in 0.09s
```

---

## 🛡️ bounded_auto Safety Guarantees

Mit den P0/P1-Features garantiert bounded_auto:

### ✅ Garantien

1. **Keine Blacklist-Violations:**
   - Keine API-Keys, Stop-Loss, oder kritische Parameter
   - Keine R&D- oder experimentelle Patches

2. **Keine Bounds-Violations:**
   - Alle Werte innerhalb [min, max] Range
   - Alle Schritte <= max_step

3. **Hohe Confidence:**
   - Nur Patches mit confidence >= 0.80 (konfigurierbar)

4. **Kill-Switch:**
   - Global Lock kann bounded_auto sofort deaktivieren

5. **Vollständige Audit-Trail:**
   - Jede Entscheidung wird geloggt
   - Nachvollziehbar für Compliance & Debugging

### ⚠️ Was bounded_auto NICHT macht

- ❌ Keine Änderungen ohne explizite Bounds
- ❌ Keine Patches mit P0-Flags
- ❌ Keine R&D- oder Experimental-Tier Patches
- ❌ Keine Änderungen während Global Lock aktiv ist

---

## 📊 Troubleshooting

### Problem: Patch wird rejected, aber Confidence ist hoch

**Diagnose:**

```bash
# Check operator report für safety_flags
cat reports/live_promotion/<run_id>/OPERATOR_CHECKLIST.md | grep "Safety Flags"

# Check audit log
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.patch_id == "patch_001")'
```

**Häufige Ursachen:**
1. Target ist blacklisted → Check `auto_apply_blacklist`
2. Wert außerhalb Bounds → Check `promotion_loop.bounds`
3. Step zu groß → Check `max_step` settings
4. Global Lock aktiv → Check `global_promotion_lock`

### Problem: bounded_auto promotet nichts

**Diagnose:**

```bash
# Check ob Candidates überhaupt generiert wurden
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto 2>&1 | grep "candidate"

# Check safety flags
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto 2>&1 | grep "P0"
```

**Häufige Ursachen:**
1. Alle Patches haben P0-Violations
2. Global Lock ist aktiv
3. Confidence < min_threshold (0.80)
4. Keine Tags passen zu konfigurierten Bounds

### Problem: Audit Log wird nicht geschrieben

**Diagnose:**

```bash
# Check permissions
ls -la reports/promotion_audit/

# Check if directory exists
mkdir -p reports/promotion_audit

# Run mit debug output
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only 2>&1 | grep audit
```

**Lösung:**
- Audit-Logging-Fehler crashen das System nicht (by design)
- Check stderr für Warnings: `[safety] WARNING: Failed to write audit log entry`

---

## 🔄 Migration & Rollout

### Phase 1: Testing (aktuell)

```bash
# Run in manual_only mit Safety-Features
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only
```

**Status:** ✅ **DONE** - 33 Tests grün, System validiert

### Phase 2: Dry-Run bounded_auto

```toml
# config/promotion_loop_config.toml
[promotion_loop]
mode = "bounded_auto"

[promotion_loop.governance]
global_promotion_lock = false  # Aber: Start mit Test-Environment
```

```bash
# Test in isolierter Umgebung
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
```

**Prüfen:**
- Werden nur valide Patches promoted?
- Werden P0-Violations korrekt rejected?
- Wird Audit-Log korrekt geschrieben?

### Phase 3: Production

```bash
# Nach erfolgreicher Dry-Run Phase
# Aktiviere bounded_auto in Production (mit konservativen Bounds)
```

**Empfehlung:**
- Start mit sehr kleinen max_step Werten
- Überwache Audit-Log eng
- Halte Global Lock als Notfall-Option bereit

---

## 📚 Weiterführende Dokumentation

- **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](./LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)** - Gesamtarchitektur
- **[PROMOTION_LOOP_V0.md](./PROMOTION_LOOP_V0.md)** - Technische Details
- **[CYCLES_6_10_LAB_FAST_FORWARD_REPORT.md](../CYCLES_6_10_LAB_FAST_FORWARD_REPORT.md)** - Findings & Gap-Analysis
- **[STABILIZATION_PHASE_COMPLETE.md](./learning_promotion/STABILIZATION_PHASE_COMPLETE.md)** - Stabilisierungsphase

---

**Version:** 1.1  
**Letztes Update:** 2025-12-11  
**Status:** ✅ Implementiert & Produktionsbereit

