# Phase 3 Mission Brief – Runtime Orchestrator v0

**Stand:** 2026-01-08  
**Phase:** 3 (Runtime Orchestrator Core)  
**Status:** IN PROGRESS

---

## 1. Mission Brief (Architect Role)

### Goal (1 Satz)
Implementierung eines runtime-fähigen, fail-closed Orchestrators, der Model Selection und Scope Enforcement deterministisch umsetzt.

### In Scope
- **Orchestrator Core** (`src/ai_orchestration/orchestrator.py`):
  - API: `select_model(layer_id, autonomy_level, task_type, constraints, context) -> ModelSelection`
  - Enforcement: Registry + Scope + Layer Map prüfen
  - Fail-closed: Unknown/forbidden → deny/raise
  - Explainability: Begründungsdaten (rule_id, scope_id, registry_version)

- **Tests**:
  - Positive cases: erlaubte Kombinationen (L0/L2/L4)
  - Negative cases: verbotene Kombinationen müssen blocken
  - SoD validation: Proposer ≠ Critic
  - Unknown layer/model → Exception

- **CLI Entry** (optional):
  - `scripts/orchestrator_dryrun.py` für Operator
  - Dry-run selection ohne Side-Effects

### Out of Scope
- Live-Enablement (muss governance-locked bleiben)
- Auto-Switching / Auto-Promotion
- Telemetry (Phase 5)
- Evidence Pack Validator (Phase 4)

### Safety Posture (fail-closed)
- **Unknown layer_id** → Exception
- **Unknown model_id** → Exception
- **Forbidden autonomy level (EXEC)** → Exception
- **SoD violation (Proposer == Critic)** → Exception
- **Default:** deny, kein „best effort"

### Acceptance Criteria (messbar)
1. ✅ Unknown/forbidden inputs → fail-closed (block)
2. ✅ Deterministische Fehlermeldungen (keine Drift)
3. ✅ Testabdeckung für kritische Pfade (≥95%)
4. ✅ Konsistenz mit Validator (keine Divergenz)
5. ✅ Rollback-Mechanismus (Feature Flag / Guard)

### Evidence Required
- Validator output: `python3 scripts/validate_layer_map_config.py` (OK)
- Test results: `python3 -m pytest tests/ai_orchestration/ -v` (OK)
- CI run IDs/links (nach PR)
- Merge log + evidence index update plan

---

## 2. Design Decisions

### 2.1 API Design

```python
@dataclass
class ModelSelection:
    """Result of orchestrator model selection."""
    layer_id: str
    autonomy_level: AutonomyLevel
    primary_model_id: str
    fallback_model_ids: List[str]
    critic_model_id: str
    capability_scope_id: str
    registry_version: str
    selection_reason: str  # Explainability
    selection_timestamp: str

@dataclass
class SelectionConstraints:
    """Constraints for model selection."""
    max_cost_per_1k_tokens: Optional[float] = None
    max_latency_ms: Optional[int] = None
    required_capabilities: List[str] = field(default_factory=list)

class Orchestrator:
    def __init__(self, config_dir: Path):
        """Load registry, scopes, layer mappings."""
        ...

    def select_model(
        self,
        layer_id: str,
        autonomy_level: AutonomyLevel,
        task_type: str,
        constraints: Optional[SelectionConstraints] = None,
        context: Optional[dict] = None,
    ) -> ModelSelection:
        """
        Select model based on layer, autonomy, constraints.

        Raises:
            ValueError: Invalid layer/model/autonomy
            RuntimeError: SoD violation
        """
        ...
```

### 2.2 Enforcement Rules

1. **Layer Map Lookup**: `layer_id` → registry mapping
2. **Model Validation**: model_id in registry
3. **SoD Check**: primary != critic
4. **EXEC Block**: autonomy_level != EXEC
5. **Capability Scope**: Laden aus TOML, später enforcement

### 2.3 Rollback Plan

**Feature Flag:**
```python
ORCHESTRATOR_ENABLED = os.getenv("ORCHESTRATOR_ENABLED", "false").lower() == "true"

if not ORCHESTRATOR_ENABLED:
    raise RuntimeError("Orchestrator disabled (safety default)")
```

**Fallback:** Ohne Flag ist alles deny-all.

---

## 3. Implementation Plan (Implementer)

### 3.1 Orchestrator Core

**File:** `src/ai_orchestration/orchestrator.py`

**Steps:**
1. Load registry, scopes, layer mappings (TOML)
2. Validate layer_id (L0-L6)
3. Validate autonomy_level (not EXEC)
4. Lookup primary/fallback/critic from registry
5. Validate SoD (primary != critic)
6. Return ModelSelection with explainability

### 3.2 Tests

**File:** `tests/ai_orchestration/test_orchestrator.py`

**Test Cases:**
- `test_select_model_L0_valid`: L0 REC → gpt-5.2 + deepseek-r1
- `test_select_model_L2_valid`: L2 PROP → gpt-5.2-pro + deepseek-r1
- `test_select_model_L4_valid`: L4 RO → o3-pro + gpt-5.2-pro
- `test_select_model_unknown_layer`: unknown layer → ValueError
- `test_select_model_exec_forbidden`: EXEC → ValueError
- `test_select_model_sod_violation`: primary == critic → RuntimeError
- `test_select_model_unknown_model`: model not in registry → ValueError

### 3.3 CLI Dry-Run (optional)

**File:** `scripts/orchestrator_dryrun.py`

```bash
python3 scripts/orchestrator_dryrun.py --layer L2 --autonomy PROP
```

Output:
```
Selected Model: gpt-5.2-pro
Critic Model: deepseek-r1
Capability Scope: L2_market_outlook
Registry Version: 1.0
Reason: Layer L2 PROP → primary model per registry
```

---

## 4. Verification Plan (QA + Docs)

### 4.1 Operator Quick Pack

```bash
# Validator
python3 scripts/validate_layer_map_config.py

# Tests
python3 -m pytest tests/ai_orchestration/ -v

# Dry-Run
python3 scripts/orchestrator_dryrun.py --layer L0 --autonomy REC
```

### 4.2 Expected Outputs

- Validator: ✅ VALIDATION PASSED
- Tests: ≥95% coverage, all green
- Dry-Run: deterministische Model Selection

### 4.3 Docs Updates

- Update `docs/architecture/ai_autonomy_layer_map_v1.md` (Runtime Orchestrator Abschnitt)
- Create `docs/ops/PHASE3_ORCHESTRATOR_QUICKSTART.md`

---

## 5. Critic Checklist (SoD)

**Proposer:** AI Agent (Architect + Implementer)  
**Critic:** AI Agent (Critic Role) oder Human Reviewer

- [ ] Fail-closed defaults verified?
- [ ] Scope enforcement verified?
- [ ] Any path to live enablement? (must be blocked)
- [ ] New risks introduced? Enumerate.
- [ ] Rollback plan explicit + tested?
- [ ] Docs gates stable?
- [ ] Evidence complete?

**Decision:** [APPROVE / REQUEST CHANGES]

---

## 6. PR Body Template (Release Manager)

```text
Summary: Phase 3 – Runtime Orchestrator v0 (Core)

Why:
- Baseline (Phase 1/2) ist gemerged
- Runtime-fähiger Orchestrator fehlt noch
- Deterministisches Model Selection + Scope Enforcement benötigt

Changes:
- src/ai_orchestration/orchestrator.py (Core)
- tests/ai_orchestration/test_orchestrator.py (≥95% coverage)
- scripts/orchestrator_dryrun.py (Operator CLI)
- docs/ops/PHASE3_ORCHESTRATOR_QUICKSTART.md

Verification:
- Validator: python3 scripts/validate_layer_map_config.py (OK)
- Tests: python3 -m pytest tests/ai_orchestration/ -v (OK)
- Dry-Run: python3 scripts/orchestrator_dryrun.py --layer L0 --autonomy REC (OK)

Risk:
- New runtime component (aber fail-closed default)
- Kein Live-Enablement (governance-locked)

Rollback:
- Feature Flag: ORCHESTRATOR_ENABLED=false (default off)
- Bei Problemen: revert PR

Evidence:
- CI Run ID: [TBD]
- Validator Output: ✅
- Test Coverage: ≥95%

SoD:
- Proposer: AI Agent (Architect + Implementer)
- Critic: [TBD – Human Reviewer oder AI Critic]
```

---

## 7. Next Steps

1. ✅ Baseline verifiziert (Validator + Tests)
2. 🚧 Orchestrator implementieren
3. 🚧 Tests schreiben
4. ⏳ Critic Review
5. ⏳ PR erstellen
6. ⏳ Merge + Evidence Index Update

---

**Status:** Mission Brief erstellt. Starte Implementierung.
