# Phase 4A: Quick Reference Commands

## Local Testing

### 1. Create Evidence Pack (Smoke Run)

```bash
# Default: L0, REC
python3 scripts/run_layer_smoke_with_evidence_pack.py --verbose

# Specify layer and autonomy
python3 scripts/run_layer_smoke_with_evidence_pack.py --layer L1 --autonomy PROP --verbose
```

### 2. Validate Evidence Packs

```bash
# Validate all packs (strict mode)
python3 scripts/validate_evidence_pack_ci.py --root .artifacts/evidence_packs --verbose

# Generate JSON report
python3 scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --output validation_report.json \
  --verbose
```

### 3. Run Tests

```bash
# CI gate tests only (17 tests)
python3 -m pytest tests/ai_orchestration/test_evidence_pack_ci_gate.py -v

# All Evidence Pack tests (41 tests)
python3 -m pytest tests/ai_orchestration/test_evidence_pack*.py -v
```

---

## Usage Examples

### Minimal Integration (Python)

```python
from src.ai_orchestration.evidence_pack_runtime import create_minimal_evidence_pack_for_run
from src.ai_orchestration.models import AutonomyLevel

# Quick one-liner
pack_path = create_minimal_evidence_pack_for_run(
    run_id="run-001",
    layer_id="L0",
    autonomy_level=AutonomyLevel.REC,
    description="Test run",
)
print(f"Evidence Pack saved: {pack_path}")
```

### Full Integration (Python)

```python
from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime
from src.ai_orchestration.models import AutonomyLevel
import uuid

runtime = EvidencePackRuntime()
run_id = f"run-{uuid.uuid4().hex[:8]}"

# Start run
runtime.start_run(
    run_id=run_id,
    layer_id="L0",
    autonomy_level=AutonomyLevel.REC,
    description="Example layer run",
)

# Add layer run metadata (optional)
runtime.add_layer_run_metadata(
    run_id=run_id,
    layer_name="Ops/Docs Tooling",
    primary_model_id="gpt-5-2-pro",
    critic_model_id="deepseek-r1",
    capability_scope_id="L0_RO_REC_PROP",
    matrix_version="v1.0",
)

# YOUR LAYER RUN LOGIC HERE

# Finish run
runtime.finish_run(run_id=run_id, status="success", tests_passed=5, tests_total=5)

# Save pack
pack_path = runtime.save_pack(run_id=run_id)
print(f"Evidence Pack saved: {pack_path}")
```

---

## CI Workflow

### Workflow Name
`Evidence Pack Validation Gate`

### Required Check Name
`evidence-pack-validation-gate`

### Local CI Simulation

```bash
# Step 1: Create Evidence Pack (smoke run)
python3 scripts/run_layer_smoke_with_evidence_pack.py --verbose

# Step 2: Validate Evidence Packs (CI gate)
python3 scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --output .artifacts/validation_report.json \
  --strict \
  --verbose

# Step 3: Check exit code
echo "Exit code: $?"
# 0 = success, 1 = failure
```

---

## Troubleshooting

### No Evidence Packs Found

```bash
# Check if smoke run created pack
ls -la .artifacts/evidence_packs/

# Create pack manually
python3 scripts/run_layer_smoke_with_evidence_pack.py --verbose
```

### Invalid Evidence Pack

```bash
# Validate specific pack with verbose output
python3 scripts/validate_evidence_pack_ci.py \
  --root .artifacts/evidence_packs \
  --verbose

# Check JSON report for details
cat .artifacts/validation_report.json | python3 -m json.tool
```

---

## File Locations

```
.artifacts/evidence_packs/         # Evidence Pack root (gitignored)
├── <run_id>/
│   ├── evidence_pack.json         # Evidence Pack (validated)
│   └── run_metadata.json          # Runtime metadata
└── ...

.artifacts/validation_report.json  # CI validation report (JSON)
```

---

## Documentation

- **Phase 4A Implementation:** `PHASE4A_IMPLEMENTATION_REPORT.md`
- **CI Gate Guide:** `docs/ai/EVIDENCE_PACK_CI_GATE.md`
- **Phase 3B Quickstart:** `docs/ops/PHASE3B_EVIDENCE_PACK_QUICKSTART.md`
