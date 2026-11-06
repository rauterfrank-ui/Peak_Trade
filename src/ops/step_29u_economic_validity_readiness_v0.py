"""STEP 29U Economic Validity Readiness v0.

Offline, fail-closed composition over *existing* canonical economic evidence
and ratified gates. Does not invent thresholds, strategies, datasets, samples,
or recompute PF / Net Return / MaxDD outside the canonical economic owners.

Canonical authorities reused:
- config/ops/shadow_preparation_readiness_gate_v0.toml
  (economic_validity_offline_gate_pass)
- docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md
- src/backtest/economic_validity_policy_v1.py (policy identity only)
- config/research/post_pr4940_final_research_fleet_negative_evidence_...
  (terminal fleet FAIL closeout; Master V2 / Double Play research fleet)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_OWNER,
    ECONOMIC_VALIDITY_POLICY_VERSION,
)
from src.ops.shadow_preparation_readiness_gate_v0 import (
    load_shadow_preparation_readiness_gate_config_v0,
)

PACKAGE_MARKER = "STEP_29U_ECONOMIC_VALIDITY_READINESS_V0=true"
PRODUCER_FAMILY = "ops.step_29u_economic_validity_readiness_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_ECONOMIC_VALIDITY_READINESS_V0"

READINESS_CONFIG_RELPATH = "config/ops/shadow_preparation_readiness_gate_v0.toml"
READINESS_CONTRACT_RELPATH = "docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
# Terminal negative fleet closeout — canonical durable FAIL evidence for the
# ratified final research fleet (authorities trading.master_v2 / double_play
# remain non-promoted). Not a Step-29U-specific backtest.
CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH = (
    "config/research/post_pr4940_final_research_fleet_negative_evidence_"
    "terminalization_and_next_material_research_boundary_v0.json"
)

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
STATUS_DEVELOPMENT_ONLY = "DEVELOPMENT_ONLY"
STATUS_HOLDOUT_ONLY = "HOLDOUT_ONLY"
STATUS_SEALED = "SEALED"
STATUS_STALE = "STALE"
STATUS_MISSING = "MISSING"
STATUS_CONTRADICTORY = "CONTRADICTORY"
STATUS_ECONOMIC_GATE_CLOSED = "ECONOMIC_GATE_CLOSED"
STATUS_FUTURE_EVALUATION_REQUIRED = "FUTURE_EVALUATION_REQUIRED"
STATUS_UNVERIFIED = "UNVERIFIED"

VALID_STATUSES = frozenset(
    {
        STATUS_PASS,
        STATUS_FAIL,
        STATUS_INSUFFICIENT_SAMPLE,
        STATUS_DEVELOPMENT_ONLY,
        STATUS_HOLDOUT_ONLY,
        STATUS_SEALED,
        STATUS_STALE,
        STATUS_MISSING,
        STATUS_CONTRADICTORY,
        STATUS_ECONOMIC_GATE_CLOSED,
        STATUS_FUTURE_EVALUATION_REQUIRED,
        STATUS_UNVERIFIED,
    }
)


class Step29UEconomicValidityReadinessError(ValueError):
    """Fail-closed economic readiness evaluator error."""


@dataclass(frozen=True)
class EconomicValidityReadinessResultV0:
    schema_id: str
    schema_version: str
    generated_at: str
    capability_id: str
    status: str
    economic_validity_proven: bool
    evidence_class: str
    gate_closed: bool
    canonical_policy_version: str
    canonical_policy_owner: str
    inputs: Mapping[str, Any]
    reasons: tuple[str, ...]
    blockers: tuple[str, ...]
    provenance: Mapping[str, Any]
    safety_facts: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "capability_id": self.capability_id,
            "status": self.status,
            "economic_validity_proven": self.economic_validity_proven,
            "evidence_class": self.evidence_class,
            "gate_closed": self.gate_closed,
            "canonical_policy_version": self.canonical_policy_version,
            "canonical_policy_owner": self.canonical_policy_owner,
            "inputs": dict(self.inputs),
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "provenance": dict(self.provenance),
            "safety_facts": dict(self.safety_facts),
        }


@dataclass(frozen=True)
class EconomicValidityReadinessOverridesV0:
    readiness_config_path: Optional[Path] = None
    fleet_closeout_path: Optional[Path] = None
    force_status: Optional[str] = None
    overlay_gate_pass: Optional[bool] = None
    overlay_fleet_verdict: Optional[str] = None
    overlay_evidence_class: Optional[str] = None
    claim_thresholds_invented: bool = False


def default_repo_root_v0() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step29UEconomicValidityReadinessError(f"JSON_MALFORMED:{path}:{exc}") from exc
    except OSError as exc:
        raise Step29UEconomicValidityReadinessError(f"JSON_UNREADABLE:{path}:{exc}") from exc


def evaluate_step_29u_economic_validity_readiness_v0(
    *,
    repo_root: Path | None = None,
    overrides: EconomicValidityReadinessOverridesV0 | None = None,
) -> EconomicValidityReadinessResultV0:
    """Compose economic validity readiness from canonical evidence only."""
    root = (repo_root or default_repo_root_v0()).resolve()
    ov = overrides or EconomicValidityReadinessOverridesV0()
    generated_at = _utc_now()

    if ov.claim_thresholds_invented:
        raise Step29UEconomicValidityReadinessError(
            "THRESHOLD_INVENTION_FORBIDDEN:evaluator_does_not_define_pf_net_maxdd"
        )
    if ov.force_status is not None and ov.force_status not in VALID_STATUSES:
        raise Step29UEconomicValidityReadinessError(f"UNKNOWN_ECONOMIC_STATUS:{ov.force_status}")

    readiness_path = (
        ov.readiness_config_path.resolve()
        if ov.readiness_config_path is not None
        else (root / READINESS_CONFIG_RELPATH).resolve()
    )
    fleet_path = (
        ov.fleet_closeout_path.resolve()
        if ov.fleet_closeout_path is not None
        else (root / CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH).resolve()
    )

    reasons: list[str] = []
    blockers: list[str] = []
    inputs: dict[str, Any] = {
        "readiness_config_relpath": READINESS_CONFIG_RELPATH,
        "fleet_closeout_relpath": CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
        "readiness_contract_relpath": READINESS_CONTRACT_RELPATH,
        "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "policy_owner": ECONOMIC_VALIDITY_POLICY_OWNER,
    }

    if ov.force_status is not None:
        status = ov.force_status
        proven = status == STATUS_PASS
        return EconomicValidityReadinessResultV0(
            schema_id=SCHEMA_ID,
            schema_version=SCHEMA_VERSION,
            generated_at=generated_at,
            capability_id=CAPABILITY_ID,
            status=status,
            economic_validity_proven=proven,
            evidence_class=str(ov.overlay_evidence_class or "FORCED"),
            gate_closed=status == STATUS_ECONOMIC_GATE_CLOSED,
            canonical_policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
            canonical_policy_owner=ECONOMIC_VALIDITY_POLICY_OWNER,
            inputs=inputs,
            reasons=(f"FORCED_STATUS:{status}",),
            blockers=() if proven else (f"ECONOMIC_VALIDITY:{status}",),
            provenance={"package_marker": PACKAGE_MARKER, "producer_family": PRODUCER_FAMILY},
            safety_facts={
                "ECONOMIC_VALIDITY_PROVEN": proven,
                "THRESHOLD_INVENTION": False,
                "METRIC_RECOMPUTATION": False,
                "STEP_29U_ACTIVATED": False,
            },
        )

    if not readiness_path.is_file():
        return EconomicValidityReadinessResultV0(
            schema_id=SCHEMA_ID,
            schema_version=SCHEMA_VERSION,
            generated_at=generated_at,
            capability_id=CAPABILITY_ID,
            status=STATUS_MISSING,
            economic_validity_proven=False,
            evidence_class="MISSING",
            gate_closed=True,
            canonical_policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
            canonical_policy_owner=ECONOMIC_VALIDITY_POLICY_OWNER,
            inputs=inputs,
            reasons=("READINESS_CONFIG_ABSENT",),
            blockers=("ECONOMIC_VALIDITY:MISSING",),
            provenance={"package_marker": PACKAGE_MARKER, "producer_family": PRODUCER_FAMILY},
            safety_facts={
                "ECONOMIC_VALIDITY_PROVEN": False,
                "THRESHOLD_INVENTION": False,
                "METRIC_RECOMPUTATION": False,
                "STEP_29U_ACTIVATED": False,
            },
        )

    try:
        cfg = load_shadow_preparation_readiness_gate_config_v0(
            config_path=readiness_path, repo_root=root
        )
    except Exception as exc:  # noqa: BLE001 — fail-closed
        return EconomicValidityReadinessResultV0(
            schema_id=SCHEMA_ID,
            schema_version=SCHEMA_VERSION,
            generated_at=generated_at,
            capability_id=CAPABILITY_ID,
            status=STATUS_UNVERIFIED,
            economic_validity_proven=False,
            evidence_class="UNVERIFIED",
            gate_closed=True,
            canonical_policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
            canonical_policy_owner=ECONOMIC_VALIDITY_POLICY_OWNER,
            inputs=inputs,
            reasons=(f"READINESS_CONFIG_INVALID:{type(exc).__name__}",),
            blockers=("ECONOMIC_VALIDITY:UNVERIFIED",),
            provenance={"package_marker": PACKAGE_MARKER, "producer_family": PRODUCER_FAMILY},
            safety_facts={
                "ECONOMIC_VALIDITY_PROVEN": False,
                "THRESHOLD_INVENTION": False,
                "METRIC_RECOMPUTATION": False,
                "STEP_29U_ACTIVATED": False,
            },
        )

    gate_pass = (
        ov.overlay_gate_pass
        if ov.overlay_gate_pass is not None
        else (cfg.get("economic_validity_offline_gate_pass") is True)
    )
    inputs["economic_validity_offline_gate_pass"] = gate_pass
    inputs["readiness_config_digest"] = _sha256_file(readiness_path)

    fleet_verdict: Optional[str] = None
    fleet_gate_pass: Optional[bool] = None
    evidence_class = "CANONICAL_GATE_AND_FLEET_CLOSEOUT"
    if not fleet_path.is_file():
        reasons.append("FLEET_CLOSEOUT_ABSENT")
        evidence_class = "GATE_ONLY_FLEET_MISSING"
    else:
        fleet = _load_json(fleet_path)
        if not isinstance(fleet, dict):
            raise Step29UEconomicValidityReadinessError("FLEET_CLOSEOUT_NOT_OBJECT")
        fleet_verdict = str(
            ov.overlay_fleet_verdict
            if ov.overlay_fleet_verdict is not None
            else (fleet.get("aggregate_fleet_verdict") or fleet.get("fleet_verdict") or "")
        ).strip()
        raw_gate = fleet.get("economic_validity_offline_gate_pass")
        fleet_gate_pass = bool(raw_gate) if isinstance(raw_gate, bool) else None
        # Keep overlay verdict and gate token coherent for test/composition paths.
        if ov.overlay_fleet_verdict == "FLEET_ECONOMIC_VALIDITY_PASS":
            fleet_gate_pass = True
        elif ov.overlay_fleet_verdict == "FLEET_ECONOMIC_VALIDITY_FAIL":
            fleet_gate_pass = False
        inputs["fleet_closeout_digest"] = _sha256_file(fleet_path)
        inputs["fleet_verdict"] = fleet_verdict
        inputs["fleet_economic_validity_offline_gate_pass"] = fleet_gate_pass
        # Evidence-class hints from durable closeout (no metric recompute).
        if ov.overlay_evidence_class:
            evidence_class = ov.overlay_evidence_class
        else:
            cls_hint = str(
                fleet.get("evidence_class") or fleet.get("admissible_scope_class") or ""
            ).upper()
            if "DEVELOPMENT" in cls_hint:
                evidence_class = STATUS_DEVELOPMENT_ONLY
            elif "HOLDOUT" in cls_hint:
                evidence_class = STATUS_HOLDOUT_ONLY
            elif "SEALED" in cls_hint:
                evidence_class = STATUS_SEALED
            elif "INSUFFICIENT" in cls_hint or "SAMPLE" in cls_hint:
                evidence_class = STATUS_INSUFFICIENT_SAMPLE

    # Contradiction: readiness gate claims PASS while durable fleet FAIL / gate false.
    if gate_pass is True and (
        fleet_verdict == "FLEET_ECONOMIC_VALIDITY_FAIL" or fleet_gate_pass is False
    ):
        status = STATUS_CONTRADICTORY
        reasons.append("GATE_PASS_CONTRADICTS_FLEET_FAIL_CLOSEOUT")
        blockers.append("ECONOMIC_VALIDITY:CONTRADICTORY")
    elif gate_pass is True and fleet_verdict == "FLEET_ECONOMIC_VALIDITY_PASS":
        # Even with aligned PASS tokens, Step-29U still requires separate durable
        # proof under activation sequencing; do not auto-claim proven here without
        # a dedicated Step-29U economic authority artifact (absent by design).
        status = STATUS_FUTURE_EVALUATION_REQUIRED
        reasons.append("ALIGNED_PASS_TOKENS_WITHOUT_STEP29U_ECONOMIC_AUTHORITY_ARTIFACT")
        blockers.append("ECONOMIC_VALIDITY:FUTURE_EVALUATION_REQUIRED")
    elif fleet_verdict == "FLEET_ECONOMIC_VALIDITY_FAIL":
        # Truthful FAIL from canonical fleet closeout; gate remains closed.
        status = STATUS_FAIL
        reasons.append("CANONICAL_FLEET_VERDICT_FAIL")
        reasons.append("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS_FALSE")
        blockers.append("ECONOMIC_VALIDITY:FAIL")
    elif gate_pass is False:
        status = STATUS_ECONOMIC_GATE_CLOSED
        reasons.append("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS_FALSE")
        reasons.append("READINESS_CONTRACT_NOT_PROVEN_BLOCKED")
        blockers.append("ECONOMIC_VALIDITY:ECONOMIC_GATE_CLOSED")
    elif evidence_class in {
        STATUS_DEVELOPMENT_ONLY,
        STATUS_HOLDOUT_ONLY,
        STATUS_SEALED,
        STATUS_INSUFFICIENT_SAMPLE,
        STATUS_STALE,
    }:
        status = evidence_class
        reasons.append(f"EVIDENCE_CLASS_{evidence_class}")
        blockers.append(f"ECONOMIC_VALIDITY:{evidence_class}")
    else:
        status = STATUS_UNVERIFIED
        reasons.append("ECONOMIC_EVIDENCE_UNCLASSIFIED")
        blockers.append("ECONOMIC_VALIDITY:UNVERIFIED")

    if status not in VALID_STATUSES:
        raise Step29UEconomicValidityReadinessError(f"UNKNOWN_ECONOMIC_STATUS:{status}")

    proven = status == STATUS_PASS
    # Hard invariant: FAIL / insufficient / development / holdout / sealed /
    # missing / contradictory / gate-closed must never be relabelled as proven.
    if status != STATUS_PASS:
        proven = False

    return EconomicValidityReadinessResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        capability_id=CAPABILITY_ID,
        status=status,
        economic_validity_proven=proven,
        evidence_class=evidence_class,
        gate_closed=(gate_pass is False) or status == STATUS_ECONOMIC_GATE_CLOSED,
        canonical_policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
        canonical_policy_owner=ECONOMIC_VALIDITY_POLICY_OWNER,
        inputs=inputs,
        reasons=tuple(reasons),
        blockers=tuple(dict.fromkeys(blockers)),
        provenance={
            "package_marker": PACKAGE_MARKER,
            "producer_family": PRODUCER_FAMILY,
            "no_threshold_invention": True,
            "no_metric_recomputation": True,
            "reuses_economic_validity_policy_v1": True,
            "reuses_shadow_preparation_readiness_gate": True,
        },
        safety_facts={
            "ECONOMIC_VALIDITY_PROVEN": proven,
            "THRESHOLD_INVENTION": False,
            "METRIC_RECOMPUTATION": False,
            "STEP_29U_ACTIVATED": False,
            "ACTIVATION_ELIGIBLE": False,
        },
    )


def serialize_economic_result_json_v0(result: EconomicValidityReadinessResultV0) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
