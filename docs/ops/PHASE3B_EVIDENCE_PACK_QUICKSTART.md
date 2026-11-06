# Phase 3B: Evidence Pack Validator – Quickstart

**Phase:** 3B (Evidence Pack Validator)  
**Status:** Implemented  
**Date:** 2026-01-08

---

## Overview

The Evidence Pack Validator provides structured, auditable records for AI Autonomy Layer Runs.

**Key Features:**
- Mandatory field validation (Evidence Pack ID, Phase ID, Layer ID, Autonomy Level)
- SoD (Separation of Duties) enforcement
- Run log tracking
- Test result validation
- File I/O (JSON format)
- CLI tool for operator validation

---

## Quick Start

### 1. Create Evidence Pack

```python
from src.ai_orchestration.evidence_pack import create_evidence_pack
from src.ai_orchestration.models import AutonomyLevel

pack = create_evidence_pack(
    evidence_pack_id="EVP-PHASE3B-001",
    phase_id="Phase3B-Demo",
    layer_id="L0",
    autonomy_level=AutonomyLevel.REC,
    registry_version="1.0",
    description="Demo Evidence Pack"
)
```

### 2. Add Layer Run Metadata

```python
from src.ai_orchestration.models import LayerRunMetadata

pack.layer_run_metadata = LayerRunMetadata(
    layer_id="L0",
    layer_name="Ops/Docs Tooling",
    autonomy_level=AutonomyLevel.REC,
    primary_model_id="gpt-5-2",
    critic_model_id="deepseek-r1",
    capability_scope_id="L0_RO_REC_PROP",
    matrix_version="v1.0"
)
```

### 3. Add Run Logs

```python
from src.ai_orchestration.models import RunLogging
from datetime import datetime, timezone

run_log = RunLogging(
    run_id="run-001",
    prompt_hash="abc123",
    artifact_hash="def456",
    inputs_manifest=["input1.txt"],
    outputs_manifest=["output1.txt"],
    timestamp_utc=datetime.now(timezone.utc).isoformat(),
    model_id="gpt-5-2"
)

pack.run_logs = [run_log]
```

### 4. Validate Evidence Pack

```python
# Validate in code
pack.validate()  # Raises ValueError if validation fails

# Or use validator
from src.ai_orchestration.evidence_pack import EvidencePackValidator

validator = EvidencePackValidator(strict=True)
result = validator.validate_pack(pack)
```

### 5. Save Evidence Pack

```python
from src.ai_orchestration.evidence_pack import save_evidence_pack
from pathlib import Path

save_evidence_pack(pack, Path("data/evidence_packs/EVP-001.json"))
```

### 6. Validate from CLI

```bash
# Strict validation (default)
python3 scripts/validate_evidence_pack.py data/evidence_packs/EVP-001.json

# Lenient validation (warnings only)
python3 scripts/validate_evidence_pack.py --lenient data/evidence_packs/EVP-001.json

# Verbose output
python3 scripts/validate_evidence_pack.py --verbose data/evidence_packs/EVP-001.json
```

---

## Integration with Orchestrator

### End-to-End Workflow

```python
from src.ai_orchestration.orchestrator import Orchestrator
from src.ai_orchestration.evidence_pack import create_evidence_pack
from src.ai_orchestration.models import AutonomyLevel, LayerRunMetadata
import os

# Enable orchestrator
os.environ["ORCHESTRATOR_ENABLED"] = "true"

# Step 1: Select models
orch = Orchestrator()
selection = orch.select_model(layer_id="L0", autonomy_level=AutonomyLevel.REC)

# Step 2: Create Evidence Pack
pack = create_evidence_pack(
    evidence_pack_id="EVP-WORKFLOW-001",
    phase_id="Workflow-Demo",
    layer_id=selection.layer_id,
    autonomy_level=selection.autonomy_level,
    registry_version=selection.registry_version
)

# Step 3: Add metadata from selection
pack.layer_run_metadata = LayerRunMetadata(
    layer_id=selection.layer_id,
    layer_name="Ops/Docs Tooling",
    autonomy_level=selection.autonomy_level,
    primary_model_id=selection.primary_model_id,
    critic_model_id=selection.critic_model_id,
    capability_scope_id=selection.capability_scope_id,
    matrix_version=selection.registry_version
)

# Step 4: Validate
pack.validate()
print(f"✅ Evidence Pack validated: {pack.evidence_pack_id}")
```

---

## Validation Rules

### Mandatory Fields

Evidence Packs MUST include:
- **evidence_pack_id** (non-empty string)
- **phase_id** (non-empty string)
- **creation_timestamp** (valid ISO8601)
- **registry_version** (non-empty string)
- **layer_id** (L0-L6)
- **autonomy_level** (RO, REC, PROP; EXEC forbidden)

### SoD Enforcement

If LayerRunMetadata is present:
- **primary_model_id ≠ critic_model_id** (enforced)

If SoDCheckResult is present:
- **proposer_model_id ≠ critic_model_id** (enforced)
- **critic_decision** must be APPROVE, APPROVE_WITH_CHANGES, or REJECT
- **critic_rationale** must be non-empty
- **evidence_ids** must be non-empty

### Warnings (Non-Blocking)

Validator will warn if:
- No run logs present
- No SoD checks present
- Not all tests passed (tests_passed < tests_total)

---

## File Format

Evidence Packs are saved as JSON:

```json
{
  "evidence_pack_id": "EVP-PHASE3B-001",
  "phase_id": "Phase3B",
  "creation_timestamp": "2026-01-08T18:30:00Z",
  "registry_version": "1.0",
  "layer_id": "L0",
  "autonomy_level": "REC",
  "validator_run": true,
  "tests_passed": 10,
  "tests_total": 10,
  "description": "Demo Evidence Pack",
  "related_prs": ["#611", "#613"],
  "related_evidence_packs": [],
  "layer_run_metadata": {
    "layer_id": "L0",
    "layer_name": "Ops/Docs Tooling",
    "autonomy_level": "REC",
    "primary_model_id": "gpt-5-2",
    "critic_model_id": "deepseek-r1",
    "capability_scope_id": "L0_RO_REC_PROP",
    "matrix_version": "v1.0"
  },
  "run_logs": [...],
  "sod_checks": [...]
}
```

---

## Troubleshooting

### Error: "evidence_pack_id is required"

**Cause:** Evidence Pack ID is empty or missing.

**Fix:**
```python
pack = create_evidence_pack(
    evidence_pack_id="EVP-YOUR-ID-HERE",  # Must be non-empty
    ...
)
```

### Error: "EXEC is forbidden"

**Cause:** Autonomy level is set to EXEC.

**Fix:** Use RO, REC, or PROP instead:
```python
autonomy_level=AutonomyLevel.REC  # Not EXEC
```

### Error: "SoD FAIL: Proposer == Critic"

**Cause:** Primary model and Critic model are the same.

**Fix:** Ensure models are different:
```python
primary_model_id="gpt-5-2",
critic_model_id="deepseek-r1",  # Must be different
```

### Warning: "No run logs present"

**Cause:** Evidence Pack has no run logs.

**Fix:** Add run logs for audit trail:
```python
pack.run_logs = [run_log]
```

---

## API Reference

### Core Functions

**create_evidence_pack()**
- Creates new Evidence Pack with minimal required fields
- Validates immediately on creation
- Returns: `EvidencePackMetadata`

**save_evidence_pack(pack, filepath)**
- Saves Evidence Pack to JSON file
- Validates before saving
- Raises: `ValueError` if validation fails

### Classes

**EvidencePackMetadata**
- Main Evidence Pack data structure
- Methods: `validate()`, `to_dict()`

**EvidencePackValidator**
- Validator for Evidence Packs
- Modes: strict (fail on error) or lenient (collect warnings)
- Methods: `validate_pack(pack)`, `validate_file(filepath)`

---

## Next Steps

**Phase 4:** CI Integration
- Add Evidence Pack validation gate to CI
- Enforce Evidence Pack creation for all Layer Runs
- Automate Evidence Pack archival

**Phase 5:** Telemetry & Audit Trail
- Integrate Evidence Packs with audit logging
- Add Evidence Pack search/query API
- Build Evidence Pack dashboard

---

## References

**Implementation:**
- Evidence Pack module (Phase 3B implementation)
- Orchestrator module (Phase 3A, PR #611)
- Data models (Phase 2, PR #610)

**Documentation:**
- Layer Map reference (architecture documentation)
- Mandatory Fields Schema (governance documentation)
- Model Registry (configuration file)

**Workflow:**
- AI Autonomy Audit Workflow (Phase 3B section)
