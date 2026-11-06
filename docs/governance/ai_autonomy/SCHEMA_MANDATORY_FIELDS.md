# AI Autonomy Layer Map – Mandatory Fields Schema

**Status:** Authoritative v1.0  
**Effective Date:** 2026-01-08  
**Owner:** ops  
**Scope:** Mandatory fields for Layer Runs and Evidence Packs

---

## PURPOSE

Dieses Dokument definiert die **verbindlichen Felder**, die bei jedem Layer-Run und in jedem Evidence Pack vorhanden sein **MÜSSEN**.

**Anwendung:**
- Layer-Run Implementations (`src/ai_orchestration/`)
- Evidence Pack Creation (`docs/governance/evidence/`)
- CodeGate Validation
- Audit Trail Compliance

---

## MANDATORY: Layer + Model + Capability Scope

### Required Fields

| Field | Type | Source | Example | Validation Rule |
|---|---|---|---|---|
| `layer_id` | string (enum) | Matrix | `L2` | MUST exist in Matrix (L0-L6) |
| `layer_name` | string | Matrix | `Market Outlook` | MUST match Matrix |
| `autonomy_level` | string (enum) | Matrix | `PROP` | `RO | REC | PROP` (EXEC forbidden) |
| `primary_model_id` | string | Matrix | `gpt-5.2-pro` | MUST match Matrix Layer Mapping |
| `fallback_model_id` | string (optional) | Matrix | `gpt-5.2` | MUST match Matrix Fallback |
| `critic_model_id` | string | Matrix | `deepseek-r1` | MUST differ from `primary_model_id` |
| `capability_scope_id` | string | Config | `L2_market_outlook_v1` | MUST exist in `config/capability_scopes/` |

### Example (Layer Run Metadata)

```python
{
    "layer_id": "L2",
    "layer_name": "Market Outlook",
    "autonomy_level": "PROP",
    "primary_model_id": "gpt-5.2-pro",
    "fallback_model_id": "gpt-5.2",
    "critic_model_id": "deepseek-r1",
    "capability_scope_id": "L2_market_outlook_v1",
    "matrix_version": "v1.0"
}
```

---

## MANDATORY: Capability Scope

### Required Fields

| Field | Type | Source | Validation Rule |
|---|---|---|---|
| `inputs_allowed` | list[string] | Capability Scope Config | Glob patterns (e.g., `docs&#47;**&#47;*.md`) |
| `outputs_allowed` | list[string] | Capability Scope Config | Artefakt-Typen (e.g., `ScenarioReport`) |
| `tooling_allowed` | list[string] (enum) | Capability Scope Config | `none | files | web | code-interpreter` |
| `forbidden` | list[string] | Capability Scope Config | Verbotene Aktionen (e.g., `execution`, `order placement`) |

### Logging (Required per Run)

| Field | Type | Example | Validation Rule |
|---|---|---|---|
| `run_id` | string (UUID) | `run_abc123` | Unique identifier per run |
| `prompt_hash` | string (SHA256) | `a1b2c3d4...` | Hash of prompt inputs |
| `artifact_hash` | string (SHA256) | `e5f6g7h8...` | Hash of output artifact |
| `inputs_manifest` | list[string] | `[""Market Outlook (latest)" (Phase 3+)"]` | List of actual inputs used |
| `outputs_manifest` | list[string] | `["scenario_report_2026-01-08.json"]` | List of outputs generated |
| `timestamp_utc` | string (ISO8601) | `2026-01-08T14:30:00Z` | UTC timestamp |
| `model_id` | string | `gpt-5.2-pro` | Actual model used (Primary or Fallback) |

### Example (Capability Scope Metadata)

```python
{
    "capability_scope_id": "L2_market_outlook_v1",
    "inputs_allowed": [
        "docs/market_outlook/**/*.yaml",
        "config/macro_regimes/**/*.toml",
        "data/market_snapshots/*.json"
    ],
    "outputs_allowed": [
        "ScenarioReport",
        "RegimeClassification",
        "NoTradeTriggers"
    ],
    "tooling_allowed": ["files", "web"],
    "forbidden": [
        "execution",
        "order placement",
        "changing risk limits",
        "live toggles",
        "secrets handling"
    ],
    "logging": {
        "run_id": "run_abc123",
        "prompt_hash": "a1b2c3d4...",
        "artifact_hash": "e5f6g7h8...",
        "inputs_manifest": [""Market Outlook (latest)" (Phase 3+)"],
        "outputs_manifest": ["scenario_report_2026-01-08.json"],
        "timestamp_utc": "2026-01-08T14:30:00Z",
        "model_id": "gpt-5.2-pro"
    }
}
```

---

## MANDATORY: Separation-of-Duties (SoD) Check

### Required Fields

| Field | Type | Example | Validation Rule |
|---|---|---|---|
| `proposer_run_id` | string (UUID) | `run_abc123` | Unique identifier for Proposer run |
| `proposer_model_id` | string | `gpt-5.2-pro` | Primary model used |
| `critic_run_id` | string (UUID) | `run_def456` | Unique identifier for Critic run |
| `critic_model_id` | string | `deepseek-r1` | Critic model used |
| `sod_result` | string (enum) | `PASS` | `PASS | FAIL` |
| `critic_decision` | string (enum) | `APPROVE` | `APPROVE | APPROVE_WITH_CHANGES | REJECT` |
| `critic_rationale` | string | `"Scenario analysis passed SoD; no execution triggers; safe for archival."` | Human-readable explanation |
| `evidence_ids` | list[string] | `["EV-20260107-SEED"]` | Evidence IDs referenced by Critic |

### SoD PASS Criteria (Mandatory)

**SoD Result = PASS**, wenn **alle** Bedingungen erfüllt sind:

1. ✅ `proposer_model_id != critic_model_id`
2. ✅ `critic_decision` in `{APPROVE, APPROVE_WITH_CHANGES, REJECT}`
3. ✅ `critic_rationale` is not empty
4. ✅ `evidence_ids` is not empty (Critic references Evidence IDs and/or run_ids)

**SoD Result = FAIL**, wenn **eine** Bedingung verletzt ist:

- ❌ `proposer_model_id == critic_model_id` → **FAIL** (keine Separation)
- ❌ `critic_decision` not in valid set → **FAIL** (ungültige Entscheidung)
- ❌ `critic_rationale` is empty → **FAIL** (keine Begründung)
- ❌ `evidence_ids` is empty → **FAIL** (keine Referenzen)

### Example (SoD Check Result)

```python
{
    "proposer_run_id": "run_abc123",
    "proposer_model_id": "gpt-5.2-pro",
    "proposer_artifact_hash": "a1b2c3d4...",

    "critic_run_id": "run_def456",
    "critic_model_id": "deepseek-r1",
    "critic_artifact_hash": "e5f6g7h8...",

    "sod_result": "PASS",
    "sod_check_timestamp": "2026-01-08T14:35:00Z",

    "critic_decision": "APPROVE",
    "critic_rationale": "Scenario analysis passed SoD checks. No execution triggers detected. Uncertainty statement present. No-trade triggers listed. Safe for archival.",
    "evidence_ids": ["EV-20260107-SEED", "EV-20260108-L2-PILOT"],
    "related_evidence_packs": ["EVP_20260107_L2_PILOT"]
}
```

---

## FORBIDDEN ACTIONS (Hard Constraints)

**Diese Aktionen sind IMMER verboten** (unabhängig vom Layer):

| Forbidden Action | Reason | Enforcement |
|---|---|---|
| `execution` | L6 EXEC forbidden | Runtime check + GovernanceViolationError |
| `order placement` | L6 EXEC forbidden | Runtime check + GovernanceViolationError |
| `changing risk limits` | Hard Gates sind souverän | Capability Scope enforcement |
| `live toggles` | Safety-First | Capability Scope enforcement |
| `secrets handling` | Security | No secrets in inputs/outputs/logs |
| `bypassing SoD` | Proposer == Critic | SoD Check FAIL → Block |

---

## VALIDATION SCHEMA (Python Dataclass)

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class AutonomyLevel(str, Enum):
    RO = "RO"      # Read-Only
    REC = "REC"    # Recommend
    PROP = "PROP"  # Propose
    EXEC = "EXEC"  # Execute (FORBIDDEN)


class SoDResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class CriticDecision(str, Enum):
    APPROVE = "APPROVE"
    APPROVE_WITH_CHANGES = "APPROVE_WITH_CHANGES"
    REJECT = "REJECT"


@dataclass
class LayerRunMetadata:
    """Mandatory metadata for every Layer Run."""

    # Layer Information (from Matrix)
    layer_id: str  # L0-L6
    layer_name: str
    autonomy_level: AutonomyLevel

    # Model Assignment (from Matrix)
    primary_model_id: str
    critic_model_id: str
    fallback_model_id: Optional[str] = None

    # Capability Scope
    capability_scope_id: str

    # Versioning
    matrix_version: str  # e.g., "v1.0"

    def validate(self):
        """Validate mandatory fields."""
        # Layer ID must be L0-L6
        assert self.layer_id in ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]

        # EXEC is forbidden
        assert self.autonomy_level != AutonomyLevel.EXEC, "EXEC is forbidden"

        # SoD: Primary != Critic
        assert self.primary_model_id != self.critic_model_id, "SoD FAIL: Primary == Critic"


@dataclass
class CapabilityScopeMetadata:
    """Capability Scope enforcement metadata."""

    capability_scope_id: str
    inputs_allowed: List[str]
    outputs_allowed: List[str]
    tooling_allowed: List[str]  # ["none", "files", "web", "code-interpreter"]
    forbidden: List[str]


@dataclass
class RunLogging:
    """Mandatory logging fields per run."""

    run_id: str  # Unique identifier
    prompt_hash: str  # SHA256 of prompt
    artifact_hash: str  # SHA256 of output
    inputs_manifest: List[str]
    outputs_manifest: List[str]
    timestamp_utc: str  # ISO8601
    model_id: str  # Actual model used (Primary or Fallback)


@dataclass
class SoDCheckResult:
    """Separation of Duties check result."""

    # Proposer
    proposer_run_id: str
    proposer_model_id: str
    proposer_artifact_hash: str

    # Critic
    critic_run_id: str
    critic_model_id: str
    critic_artifact_hash: str

    # SoD Result
    sod_result: SoDResult
    sod_check_timestamp: str  # ISO8601

    # Critic Output
    critic_decision: CriticDecision
    critic_rationale: str
    evidence_ids: List[str]
    related_evidence_packs: List[str] = None

    def validate(self):
        """Validate SoD check."""
        # Rule 1: Proposer != Critic
        if self.proposer_model_id == self.critic_model_id:
            self.sod_result = SoDResult.FAIL
            raise ValueError(f"SoD FAIL: Proposer == Critic ({self.proposer_model_id})")

        # Rule 2: Valid Critic Decision
        assert self.critic_decision in [
            CriticDecision.APPROVE,
            CriticDecision.APPROVE_WITH_CHANGES,
            CriticDecision.REJECT
        ]

        # Rule 3: Rationale not empty
        assert self.critic_rationale, "SoD FAIL: Empty rationale"

        # Rule 4: Evidence IDs not empty
        assert self.evidence_ids, "SoD FAIL: No evidence IDs"

        # All checks passed
        self.sod_result = SoDResult.PASS
```

---

## USAGE EXAMPLES

### Example 1: Layer Run Initialization

```python
from src.ai_orchestration.models import LayerRunMetadata, AutonomyLevel

# Initialize Layer Run (L2 Market Outlook)
metadata = LayerRunMetadata(
    layer_id="L2",
    layer_name="Market Outlook",
    autonomy_level=AutonomyLevel.PROP,
    primary_model_id="gpt-5.2-pro",
    fallback_model_id="gpt-5.2",
    critic_model_id="deepseek-r1",
    capability_scope_id="L2_market_outlook_v1",
    matrix_version="v1.0"
)

# Validate
metadata.validate()  # Raises if SoD FAIL or EXEC forbidden
```

---

### Example 2: SoD Check

```python
from src.ai_orchestration.sod_checker import check_sod
from src.ai_orchestration.models import SoDCheckResult, CriticDecision

# After running Proposer + Critic
sod_result = SoDCheckResult(
    proposer_run_id="run_abc123",
    proposer_model_id="gpt-5.2-pro",
    proposer_artifact_hash="a1b2c3d4...",

    critic_run_id="run_def456",
    critic_model_id="deepseek-r1",
    critic_artifact_hash="e5f6g7h8...",

    sod_result=None,  # Will be set by validate()
    sod_check_timestamp="2026-01-08T14:35:00Z",

    critic_decision=CriticDecision.APPROVE,
    critic_rationale="Scenario analysis passed. No execution triggers. Safe.",
    evidence_ids=["EV-20260107-SEED"]
)

# Validate SoD
sod_result.validate()  # Sets sod_result = PASS or raises

assert sod_result.sod_result == "PASS"
```

---

### Example 3: Evidence Pack Validation (CodeGate)

```python
from src.governance.codegate import validate_evidence_pack

# Load Evidence Pack
evidence_pack = load_evidence_pack("docs/governance/evidence/EVP_20260108_L2_OUTLOOK_001.md")

# Validate against Matrix + Schema
validation = validate_evidence_pack(evidence_pack)

# Check mandatory fields
assert validation.has_field("layer_id")
assert validation.has_field("primary_model_id")
assert validation.has_field("critic_model_id")
assert validation.has_field("sod_result")

# Check SoD
assert evidence_pack.sod_result == "PASS"
assert evidence_pack.proposer_model_id != evidence_pack.critic_model_id

# Check Matrix compliance
assert evidence_pack.layer_id in ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
assert evidence_pack.autonomy_level != "EXEC"

# Approve
if validation.status == "VALID":
    print("✅ Evidence Pack APPROVED")
else:
    print(f"❌ Evidence Pack REJECTED: {validation.errors}")
```

---

## INTEGRATION POINTS

| Component | Integration | Schema Fields |
|---|---|---|
| **Layer Runners** (`src/ai_orchestration/`) | Initialize with `LayerRunMetadata` | `layer_id`, `primary_model_id`, `critic_model_id`, `capability_scope_id` |
| **SoD Checker** ("SoD Checker" (Phase 3+)) | Validate with `SoDCheckResult` | `proposer_model_id`, `critic_model_id`, `sod_result`, `critic_decision` |
| **Evidence Packs** (`docs/governance/evidence/`) | Include all mandatory fields | All fields from this schema |
| **CodeGate** (`src&#47;governance&#47;codegate&#47;`) | Validate Evidence Packs against schema | All fields + Matrix compliance |
| **Audit Log** (`logs&#47;ai_model_calls.jsonl`) | Log all runs with `RunLogging` | `run_id`, `prompt_hash`, `artifact_hash`, `inputs_manifest`, `outputs_manifest` |

---

## VERSION HISTORY

| Version | Date | Changes | Author |
|---|---|---|---|
| v1.0 | 2026-01-08 | Initial schema: Mandatory fields for Layer Runs, Capability Scopes, SoD Checks | ops |

---

## REFERENCES

- **Authoritative Matrix:** `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`
- **Evidence Pack Template v2:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`
- **Model Registry:** `config/model_registry.toml`
- **Capability Scopes:** `config&#47;capability_scopes&#47;*.toml`

---

**END OF SCHEMA**

**CRITICAL:** Alle Layer Runs und Evidence Packs MÜSSEN diese Felder enthalten.  
Fehlende oder ungültige Felder führen zu CodeGate REJECTION.
