# Phase 3 Orchestrator Quickstart

**Datum:** 2026-01-08  
**Phase:** 3 (Runtime Orchestrator v0)

---

## Quick Reference

### Operator Commands

```bash
# 1. Validate Config (Baseline)
python3 scripts/validate_layer_map_config.py

# 2. Run Tests
python3 -m pytest tests/ai_orchestration/ -v

# 3. Dry-Run (Test Model Selection)
python3 scripts/orchestrator_dryrun.py --layer L0 --autonomy REC --enable-orchestrator
python3 scripts/orchestrator_dryrun.py --layer L2 --autonomy PROP --enable-orchestrator
```

---

## Orchestrator API

### Python Usage

```python
import os
from pathlib import Path
from src.ai_orchestration.orchestrator import Orchestrator
from src.ai_orchestration.models import AutonomyLevel

# Enable orchestrator (required)
os.environ["ORCHESTRATOR_ENABLED"] = "true"

# Initialize
config_dir = Path("config")
orch = Orchestrator(config_dir=config_dir)

# Select model
selection = orch.select_model(
    layer_id="L2",
    autonomy_level=AutonomyLevel.PROP,
    task_type="market_analysis"
)

print(f"Primary Model: {selection.primary_model_id}")
print(f"Critic Model: {selection.critic_model_id}")
print(f"SoD Validated: {selection.sod_validated}")
```

### CLI Usage

```bash
# Basic usage
python3 scripts/orchestrator_dryrun.py \
  --layer L2 \
  --autonomy PROP \
  --enable-orchestrator

# Verbose output
python3 scripts/orchestrator_dryrun.py \
  --layer L0 \
  --autonomy REC \
  --enable-orchestrator \
  --verbose
```

---

## Supported Layers

| Layer | Description | Autonomy | Primary Model | Critic Model |
|-------|-------------|----------|---------------|--------------|
| L0 | Ops/Docs | REC | gpt-5-2 | deepseek-r1 |
| L1 | Deep Research | PROP | o3-deep-research | o3-pro |
| L2 | Market Outlook | PROP | gpt-5-2-pro | deepseek-r1 |
| L3 | Trade Plan Advisory | REC/PROP | gpt-5-2-pro | o3 |
| L4 | Governance Critic | RO/REC | o3-pro | gpt-5-2-pro |
| L5 | Risk Gate | RO | none | none |
| L6 | Execution | EXEC (forbidden) | none | none |

---

## Fail-Closed Behavior

**Orchestrator is disabled by default.** Set `ORCHESTRATOR_ENABLED=true` to enable.

### Forbidden Operations

- ❌ EXEC autonomy level (any layer)
- ❌ Unknown layer_id
- ❌ Unknown model_id
- ❌ SoD violation (primary == critic)
- ❌ L5 (Risk Gate) – no LLM support
- ❌ L6 (Execution) – no LLM support

**All forbidden operations raise Exceptions (fail-closed).**

---

## Troubleshooting

### Error: "Orchestrator is disabled"

```bash
export ORCHESTRATOR_ENABLED=true
```

### Error: "Invalid layer_id: LX"

Valid layers: L0, L1, L2, L3, L4, L5, L6

### Error: "EXEC is forbidden"

EXEC autonomy level is hard-blocked. Use RO, REC, or PROP.

### Error: "Model X not found in registry"

Check `config/model_registry.toml` for available models.

---

## Health Check

```python
health = orch.health_check()
print(health)
```

**Expected Output:**
```json
{
  "enabled": true,
  "registry_version": "1.0",
  "models_count": 8,
  "layers_mapped": 7,
  "scopes_loaded": 4,
  "status": "healthy"
}
```

---

## Files & Locations

| Component | Path |
|-----------|------|
| Orchestrator Core | `src/ai_orchestration/orchestrator.py` |
| Tests | `tests/ai_orchestration/test_orchestrator.py` |
| CLI Dry-Run | `scripts/orchestrator_dryrun.py` |
| Model Registry | `config/model_registry.toml` |
| Capability Scopes | `config&#47;capability_scopes&#47;*.toml` |
| Validator | `scripts/validate_layer_map_config.py` |

---

## Next Steps

- **Phase 4:** Evidence Pack Validator v1 + SoD Enforcement
- **Phase 5:** Telemetry & Audit Trail
- **Phase 6:** Governance Enablement Gates

---

**For full details, see:**
- `docs/ops/PHASE3_MISSION_BRIEF.md`
- `docs/ops/PHASE3_VERIFICATION_EVIDENCE_PACK.md`
