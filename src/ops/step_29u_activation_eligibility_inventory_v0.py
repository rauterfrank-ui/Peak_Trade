"""STEP 29U Activation Eligibility Inventory v0.

Offline, non-activating, fail-closed inventory of prerequisites that would
have to be satisfied before any future, separately authorized Step-29U
activation could even be considered.

This capability is not Activation, not Activation Binding, and not Activation
Readiness approval. It never arms, schedules, connects, submits, promotes, or
mutates runtime state.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.shadow_preparation_readiness_gate_v0 import (
    RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
    load_shadow_preparation_readiness_gate_config_v0,
)
from src.ops.step_29u_canonical_shadow_binding_v0 import (
    BINDING_OWNER,
    observe_canonical_step_29u_bound_v0,
    verify_canonical_step_29u_binding_evidence_v0,
)

PACKAGE_MARKER = "STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0=true"
PRODUCER_FAMILY = "ops.step_29u_activation_eligibility_inventory_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0"
CLI_RELPATH = "scripts/ops/run_step_29u_activation_eligibility_inventory_v0.py"

INVENTORY_RUNBOOK = "docs/ops/runbooks/STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0.md"
BINDING_INVENTORY_RUNBOOK = (
    "docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)
READINESS_CONFIG_RELPATH = "config/ops/shadow_preparation_readiness_gate_v0.toml"
CANONICAL_SOAK_RELPATH = "evidence/ops/step_29u_post_merge_shadow_soak/20260725T222915Z"
EXPECTED_SOAK_TESTED_HEAD_SHA = "cd6d465c83c6c65733e5d85238aa223d4bffd548"

STATE_SATISFIED = "SATISFIED"
STATE_UNSATISFIED = "UNSATISFIED"
STATE_ABSENT = "ABSENT"
STATE_INVALID = "INVALID"
VALID_STATES = frozenset({STATE_SATISFIED, STATE_UNSATISFIED, STATE_ABSENT, STATE_INVALID})

PREREQUISITE_IDS: tuple[str, ...] = (
    "STEP_29U_BINDING_PROVEN",
    "STEP_29U_POST_MERGE_SOAK_PROVEN",
    "STEP_29U_AUDIT_PROVENANCE_COMPLETE",
    "RUNTIME_BRIDGE_BOUND",
    "RUNTIME_REMAINS_NOT_ACTIVATED",
    "SCHEDULER_REMAINS_LOCKED",
    "NETWORK_REMAINS_PROHIBITED",
    "ORDERS_REMAIN_PROHIBITED",
    "ECONOMIC_VALIDITY_PROVEN",
    "SAFETY_AUTHORITY_VALID",
    "RECONCILIATION_PRECONDITIONS_PROVEN",
    "ACTIVATION_AUTHORITY_CONTRACT_PRESENT",
    "EXPLICIT_FUTURE_OPERATOR_GO_PRESENT",
    "BTC_EXCLUDED",
    "SPOT_EXCLUDED",
    "KRAKEN_LEGACY_EXCLUDED",
)

FORBIDDEN_IMPORT_SURFACES = frozenset(
    {
        "src.orders.shadow",
        "scripts.run_shadow_execution",
        "src.live.shadow_session",
        "scripts.run_shadow_paper_session",
        "src.webui",
    }
)


class Step29UActivationEligibilityInventoryError(ValueError):
    """Fail-closed inventory execution error (evaluator health, not eligibility)."""


@dataclass(frozen=True)
class PrerequisiteRecordV0:
    prerequisite_id: str
    description: str
    canonical_owner: str
    source_reference: str
    state: str
    reason_code: str
    evidence_reference: str
    evidence_digest: Optional[str]
    observed_value: str
    expected_condition: str
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "prerequisite_id": self.prerequisite_id,
            "description": self.description,
            "canonical_owner": self.canonical_owner,
            "source_reference": self.source_reference,
            "state": self.state,
            "reason_code": self.reason_code,
            "evidence_reference": self.evidence_reference,
            "evidence_digest": self.evidence_digest,
            "observed_value": self.observed_value,
            "expected_condition": self.expected_condition,
            "evaluated_at": self.evaluated_at,
        }


@dataclass(frozen=True)
class ActivationEligibilityInventoryResultV0:
    schema_id: str
    schema_version: str
    generated_at: str
    evaluated_main_sha: str
    capability_id: str
    evaluator_valid: bool
    status: str
    activation_eligible: bool
    step_29u_activated: bool
    runtime_activated: bool
    scheduler_activated: bool
    network_used: bool
    orders_created: bool
    orders_submitted: bool
    operator_go_present: bool
    btc_excluded: bool
    spot_excluded: bool
    kraken_legacy_excluded: bool
    prerequisites: tuple[PrerequisiteRecordV0, ...]
    blockers: tuple[str, ...]
    summary: Mapping[str, int]
    provenance: Mapping[str, Any]
    safety_facts: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "evaluated_main_sha": self.evaluated_main_sha,
            "capability_id": self.capability_id,
            "evaluator_valid": self.evaluator_valid,
            "status": self.status,
            "activation_eligible": self.activation_eligible,
            "step_29u_activated": self.step_29u_activated,
            "runtime_activated": self.runtime_activated,
            "scheduler_activated": self.scheduler_activated,
            "network_used": self.network_used,
            "orders_created": self.orders_created,
            "orders_submitted": self.orders_submitted,
            "operator_go_present": self.operator_go_present,
            "btc_excluded": self.btc_excluded,
            "spot_excluded": self.spot_excluded,
            "kraken_legacy_excluded": self.kraken_legacy_excluded,
            "prerequisites": [p.to_dict() for p in self.prerequisites],
            "blockers": list(self.blockers),
            "summary": dict(self.summary),
            "provenance": dict(self.provenance),
            "safety_facts": dict(self.safety_facts),
        }


@dataclass(frozen=True)
class EligibilityInventoryOverridesV0:
    """Test-only / explicit path overrides. Never authorizes activation."""

    soak_dir: Optional[Path] = None
    binding_evidence_dir: Optional[Path] = None
    readiness_config_path: Optional[Path] = None
    soak_summary_overlay: Optional[Mapping[str, Any]] = None
    force_unknown_prerequisite: bool = False
    evaluated_main_sha: Optional[str] = None


def default_repo_root_v0() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_sha(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_manifest(manifest_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise Step29UActivationEligibilityInventoryError(
                f"MANIFEST_LINE_INVALID:{manifest_path}"
            )
        digest, rel = parts
        mapping[rel.strip()] = digest.strip().lower()
    return mapping


def _verify_manifest(dir_path: Path, manifest_path: Path) -> tuple[bool, str, Optional[str]]:
    if not manifest_path.is_file():
        return False, "MANIFEST_MISSING", None
    try:
        expected = _read_manifest(manifest_path)
    except (OSError, UnicodeError, Step29UActivationEligibilityInventoryError):
        return False, "MANIFEST_MALFORMED", None
    if not expected:
        return False, "MANIFEST_EMPTY", None
    for rel, digest in sorted(expected.items()):
        target = dir_path / rel
        if not target.is_file():
            return False, f"MANIFEST_FILE_MISSING:{rel}", None
        actual = _sha256_file(target)
        if actual.lower() != digest.lower():
            return False, f"DIGEST_MISMATCH:{rel}", actual
    return True, "MANIFEST_OK", _sha256_file(manifest_path)


def _record(
    *,
    prerequisite_id: str,
    description: str,
    canonical_owner: str,
    source_reference: str,
    state: str,
    reason_code: str,
    evidence_reference: str,
    evidence_digest: Optional[str],
    observed_value: str,
    expected_condition: str,
    evaluated_at: str,
) -> PrerequisiteRecordV0:
    if state not in VALID_STATES:
        raise Step29UActivationEligibilityInventoryError(f"INVALID_STATE:{state}")
    if prerequisite_id not in PREREQUISITE_IDS:
        raise Step29UActivationEligibilityInventoryError(f"UNKNOWN_PREREQUISITE:{prerequisite_id}")
    return PrerequisiteRecordV0(
        prerequisite_id=prerequisite_id,
        description=description,
        canonical_owner=canonical_owner,
        source_reference=source_reference,
        state=state,
        reason_code=reason_code,
        evidence_reference=evidence_reference,
        evidence_digest=evidence_digest,
        observed_value=observed_value,
        expected_condition=expected_condition,
        evaluated_at=evaluated_at,
    )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step29UActivationEligibilityInventoryError(f"JSON_MALFORMED:{path}:{exc}") from exc
    except OSError as exc:
        raise Step29UActivationEligibilityInventoryError(f"JSON_UNREADABLE:{path}:{exc}") from exc


def _boolish(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None


def evaluate_step_29u_activation_eligibility_inventory_v0(
    *,
    repo_root: Path | None = None,
    overrides: EligibilityInventoryOverridesV0 | None = None,
) -> ActivationEligibilityInventoryResultV0:
    """Evaluate canonical eligibility inventory. Always non-activating."""
    root = (repo_root or default_repo_root_v0()).resolve()
    ov = overrides or EligibilityInventoryOverridesV0()
    evaluated_at = _utc_now()
    evaluated_sha = ov.evaluated_main_sha or _git_sha(root)

    if ov.force_unknown_prerequisite:
        raise Step29UActivationEligibilityInventoryError(
            "UNKNOWN_PREREQUISITE:NOT_A_CANONICAL_PREREQUISITE_ID"
        )

    soak_dir = (
        ov.soak_dir.resolve()
        if ov.soak_dir is not None
        else (root / CANONICAL_SOAK_RELPATH).resolve()
    )
    readiness_path = (
        ov.readiness_config_path.resolve()
        if ov.readiness_config_path is not None
        else (root / READINESS_CONFIG_RELPATH).resolve()
    )

    records: list[PrerequisiteRecordV0] = []
    blockers: list[str] = []

    # --- Binding ---
    binding_ok, binding_reasons, _binding_payload = verify_canonical_step_29u_binding_evidence_v0(
        repo_root=root,
        evidence_dir=ov.binding_evidence_dir,
    )
    bound_obs, bound_obs_reasons = observe_canonical_step_29u_bound_v0(
        repo_root=root,
        evidence_dir=ov.binding_evidence_dir,
    )
    if binding_ok and bound_obs:
        records.append(
            _record(
                prerequisite_id="STEP_29U_BINDING_PROVEN",
                description="Canonical Step 29U Shadow no-order binding evidence verified",
                canonical_owner=BINDING_OWNER,
                source_reference="src/ops/step_29u_canonical_shadow_binding_v0.py",
                state=STATE_SATISFIED,
                reason_code="BINDING_EVIDENCE_VERIFIED",
                evidence_reference="evidence/ops/step_29u_offline_capability/2026-07-25_capability_hold_cycle",
                evidence_digest=None,
                observed_value="bound=true verified=true",
                expected_condition="canonical binding evidence verifies and observe_bound=true",
                evaluated_at=evaluated_at,
            )
        )
    elif not (root / "src/ops/step_29u_canonical_shadow_binding_v0.py").is_file():
        records.append(
            _record(
                prerequisite_id="STEP_29U_BINDING_PROVEN",
                description="Canonical Step 29U Shadow no-order binding evidence verified",
                canonical_owner=BINDING_OWNER,
                source_reference="src/ops/step_29u_canonical_shadow_binding_v0.py",
                state=STATE_ABSENT,
                reason_code="BINDING_OWNER_ABSENT",
                evidence_reference="",
                evidence_digest=None,
                observed_value="absent",
                expected_condition="canonical binding evidence verifies and observe_bound=true",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("STEP_29U_BINDING_PROVEN:ABSENT")
    else:
        reason = ",".join(binding_reasons or bound_obs_reasons or ("BINDING_UNSATISFIED",))
        state = (
            STATE_INVALID
            if any(
                "INVALID" in r or "DIGEST" in r or "MALFORMED" in r or "SCHEMA" in r
                for r in (binding_reasons or ())
            )
            else STATE_UNSATISFIED
        )
        records.append(
            _record(
                prerequisite_id="STEP_29U_BINDING_PROVEN",
                description="Canonical Step 29U Shadow no-order binding evidence verified",
                canonical_owner=BINDING_OWNER,
                source_reference="src/ops/step_29u_canonical_shadow_binding_v0.py",
                state=state,
                reason_code=reason[:200],
                evidence_reference="evidence/ops/step_29u_offline_capability/2026-07-25_capability_hold_cycle",
                evidence_digest=None,
                observed_value=f"bound={bound_obs} verified={binding_ok}",
                expected_condition="canonical binding evidence verifies and observe_bound=true",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append(f"STEP_29U_BINDING_PROVEN:{state}")

    # --- Soak ---
    soak_summary_path = soak_dir / "soak_summary.json"
    soak_manifest_path = soak_dir / "evidence_manifest.sha256"
    soak_exact_head_path = soak_dir / "exact_head.txt"
    soak_digest: Optional[str] = None
    soak_payload: dict[str, Any] = {}

    if not soak_dir.is_dir():
        records.append(
            _record(
                prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                description="Post-merge Step 29U bound Shadow soak evidence proven",
                canonical_owner="ops.step_29u_post_merge_shadow_soak",
                source_reference=CANONICAL_SOAK_RELPATH,
                state=STATE_ABSENT,
                reason_code="SOAK_DIR_ABSENT",
                evidence_reference=str(soak_dir.relative_to(root))
                if soak_dir.is_relative_to(root)
                else str(soak_dir),
                evidence_digest=None,
                observed_value="absent",
                expected_condition=f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} manifest digests match",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("STEP_29U_POST_MERGE_SOAK_PROVEN:ABSENT")
        soak_safety = {
            "RUNTIME_ACTIVATED": None,
            "SCHEDULER_ACTIVATED": None,
            "NETWORK_USED": None,
            "ORDERS_CREATED": None,
            "ORDERS_SUBMITTED": None,
            "BTC_OBSERVED": None,
            "SPOT_OBSERVED": None,
            "KRAKEN_LEGACY_OBSERVED": None,
        }
    elif not soak_summary_path.is_file():
        records.append(
            _record(
                prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                description="Post-merge Step 29U bound Shadow soak evidence proven",
                canonical_owner="ops.step_29u_post_merge_shadow_soak",
                source_reference=CANONICAL_SOAK_RELPATH,
                state=STATE_ABSENT,
                reason_code="SOAK_SUMMARY_ABSENT",
                evidence_reference=CANONICAL_SOAK_RELPATH,
                evidence_digest=None,
                observed_value="summary_absent",
                expected_condition=f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} manifest digests match",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("STEP_29U_POST_MERGE_SOAK_PROVEN:ABSENT")
        soak_safety = {
            "RUNTIME_ACTIVATED": None,
            "SCHEDULER_ACTIVATED": None,
            "NETWORK_USED": None,
            "ORDERS_CREATED": None,
            "ORDERS_SUBMITTED": None,
            "BTC_OBSERVED": None,
            "SPOT_OBSERVED": None,
            "KRAKEN_LEGACY_OBSERVED": None,
        }
    else:
        try:
            loaded = _load_json(soak_summary_path)
            if not isinstance(loaded, dict):
                raise Step29UActivationEligibilityInventoryError("SOAK_SUMMARY_NOT_OBJECT")
            soak_payload = dict(loaded)
            if ov.soak_summary_overlay:
                soak_payload.update(dict(ov.soak_summary_overlay))
            manifest_ok, manifest_reason, soak_digest = _verify_manifest(
                soak_dir, soak_manifest_path
            )
            exact_head = (
                soak_exact_head_path.read_text(encoding="utf-8").strip()
                if soak_exact_head_path.is_file()
                else ""
            )
            tested_head = str(soak_payload.get("TESTED_HEAD_SHA") or "").strip()
            status = str(soak_payload.get("STATUS") or "")
            wallclock_ok = soak_payload.get("WALLCLOCK_REQUIREMENT_PASS") is True

            def _int_field(key: str, *, missing: int) -> int:
                if key not in soak_payload or soak_payload[key] is None:
                    return missing
                return int(soak_payload[key])

            verified = _int_field("STEP_29U_VERIFIED_CYCLES", missing=0)
            total = _int_field("TOTAL_CYCLES", missing=0)
            full_chain = _int_field("FULL_CHAIN_CYCLES", missing=0)
            absent_count = _int_field("STEP_29U_ABSENT_COUNT", missing=-1)
            invalid_count = _int_field("STEP_29U_INVALID_COUNT", missing=-1)

            soak_safety = {
                "RUNTIME_ACTIVATED": _boolish(soak_payload.get("RUNTIME_ACTIVATED")),
                "SCHEDULER_ACTIVATED": _boolish(soak_payload.get("SCHEDULER_ACTIVATED")),
                "NETWORK_USED": _boolish(soak_payload.get("NETWORK_USED")),
                "ORDERS_CREATED": _boolish(soak_payload.get("ORDERS_CREATED")),
                "ORDERS_SUBMITTED": _boolish(soak_payload.get("ORDERS_SUBMITTED")),
                "BTC_OBSERVED": _boolish(soak_payload.get("BTC_OBSERVED")),
                "SPOT_OBSERVED": _boolish(soak_payload.get("SPOT_OBSERVED")),
                "KRAKEN_LEGACY_OBSERVED": _boolish(soak_payload.get("KRAKEN_LEGACY_OBSERVED")),
            }

            invalid_reasons: list[str] = []
            if not manifest_ok:
                invalid_reasons.append(manifest_reason)
            if tested_head != EXPECTED_SOAK_TESTED_HEAD_SHA:
                invalid_reasons.append("SOAK_TESTED_HEAD_MISMATCH")
            if exact_head and exact_head != tested_head:
                invalid_reasons.append("SOAK_EXACT_HEAD_MISMATCH")
            if exact_head and exact_head != EXPECTED_SOAK_TESTED_HEAD_SHA:
                invalid_reasons.append("SOAK_EXACT_HEAD_UNEXPECTED")
            for key, expected_false in (
                ("RUNTIME_ACTIVATED", False),
                ("SCHEDULER_ACTIVATED", False),
                ("NETWORK_USED", False),
                ("ORDERS_CREATED", False),
                ("ORDERS_SUBMITTED", False),
            ):
                val = soak_safety[key]
                if val is True:
                    invalid_reasons.append(f"SOAK_{key}_TRUE_INVALID")
                elif val is None:
                    invalid_reasons.append(f"SOAK_{key}_MISSING")

            if invalid_reasons:
                records.append(
                    _record(
                        prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                        description="Post-merge Step 29U bound Shadow soak evidence proven",
                        canonical_owner="ops.step_29u_post_merge_shadow_soak",
                        source_reference=CANONICAL_SOAK_RELPATH,
                        state=STATE_INVALID,
                        reason_code=",".join(invalid_reasons)[:200],
                        evidence_reference=CANONICAL_SOAK_RELPATH,
                        evidence_digest=soak_digest,
                        observed_value=(
                            f"status={status} tested_head={tested_head} manifest_ok={manifest_ok}"
                        ),
                        expected_condition=(
                            f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} "
                            "manifest digests match; safety flags false"
                        ),
                        evaluated_at=evaluated_at,
                    )
                )
                blockers.append("STEP_29U_POST_MERGE_SOAK_PROVEN:INVALID")
            elif (
                status == "PASS"
                and wallclock_ok
                and verified == total == full_chain
                and verified > 0
                and absent_count == 0
                and invalid_count == 0
            ):
                records.append(
                    _record(
                        prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                        description="Post-merge Step 29U bound Shadow soak evidence proven",
                        canonical_owner="ops.step_29u_post_merge_shadow_soak",
                        source_reference=CANONICAL_SOAK_RELPATH,
                        state=STATE_SATISFIED,
                        reason_code="POST_MERGE_SOAK_VERIFIED",
                        evidence_reference=CANONICAL_SOAK_RELPATH,
                        evidence_digest=soak_digest,
                        observed_value=(
                            f"status=PASS cycles={total} verified={verified} "
                            f"tested_head={tested_head}"
                        ),
                        expected_condition=(
                            f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} "
                            "manifest digests match; safety flags false"
                        ),
                        evaluated_at=evaluated_at,
                    )
                )
            else:
                records.append(
                    _record(
                        prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                        description="Post-merge Step 29U bound Shadow soak evidence proven",
                        canonical_owner="ops.step_29u_post_merge_shadow_soak",
                        source_reference=CANONICAL_SOAK_RELPATH,
                        state=STATE_UNSATISFIED,
                        reason_code="SOAK_ASSERTIONS_UNMET",
                        evidence_reference=CANONICAL_SOAK_RELPATH,
                        evidence_digest=soak_digest,
                        observed_value=(
                            f"status={status} verified={verified} total={total} "
                            f"absent={absent_count} invalid={invalid_count}"
                        ),
                        expected_condition=(
                            f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} "
                            "manifest digests match; safety flags false"
                        ),
                        evaluated_at=evaluated_at,
                    )
                )
                blockers.append("STEP_29U_POST_MERGE_SOAK_PROVEN:UNSATISFIED")
        except Step29UActivationEligibilityInventoryError as exc:
            records.append(
                _record(
                    prerequisite_id="STEP_29U_POST_MERGE_SOAK_PROVEN",
                    description="Post-merge Step 29U bound Shadow soak evidence proven",
                    canonical_owner="ops.step_29u_post_merge_shadow_soak",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_INVALID,
                    reason_code=str(exc)[:200],
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=None,
                    observed_value="malformed",
                    expected_condition=(
                        f"STATUS=PASS tested_head={EXPECTED_SOAK_TESTED_HEAD_SHA} "
                        "manifest digests match"
                    ),
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append("STEP_29U_POST_MERGE_SOAK_PROVEN:INVALID")
            soak_safety = {
                "RUNTIME_ACTIVATED": None,
                "SCHEDULER_ACTIVATED": None,
                "NETWORK_USED": None,
                "ORDERS_CREATED": None,
                "ORDERS_SUBMITTED": None,
                "BTC_OBSERVED": None,
                "SPOT_OBSERVED": None,
                "KRAKEN_LEGACY_OBSERVED": None,
            }

    # --- Audit provenance (STEP 29U audit owner still missing per inventory SSOT) ---
    records.append(
        _record(
            prerequisite_id="STEP_29U_AUDIT_PROVENANCE_COMPLETE",
            description="Dedicated STEP 29U activation audit/provenance contract complete",
            canonical_owner="MISSING",
            source_reference=BINDING_INVENTORY_RUNBOOK,
            state=STATE_ABSENT,
            reason_code="STEP_29U_AUDIT_CONTRACT_MISSING",
            evidence_reference=BINDING_INVENTORY_RUNBOOK,
            evidence_digest=None,
            observed_value="audit_owner=MISSING",
            expected_condition="dedicated STEP 29U audit contract owner present and verified",
            evaluated_at=evaluated_at,
        )
    )
    blockers.append("STEP_29U_AUDIT_PROVENANCE_COMPLETE:ABSENT")

    # --- Readiness / runtime bridge / economic / authority ---
    if not readiness_path.is_file():
        runtime_state = None
        econ_pass = None
        activation_flags = {}
        authorities: Sequence[str] = ()
        readiness_state_note = "READINESS_CONFIG_ABSENT"
        readiness_digest = None
    else:
        try:
            cfg = load_shadow_preparation_readiness_gate_config_v0(
                config_path=readiness_path, repo_root=root
            )
            runtime_state = str(
                cfg.get("runtime_bridge_state") or RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED
            )
            econ_pass = cfg.get("economic_validity_offline_gate_pass") is True
            activation_flags = {
                "shadow_activation_authorized": bool(cfg.get("shadow_activation_authorized")),
                "scheduler_activation_authorized": bool(cfg.get("scheduler_activation_authorized")),
                "runtime_activation_authorized": bool(cfg.get("runtime_activation_authorized")),
                "orders_authorized": bool(cfg.get("orders_authorized")),
                "live_authorized": bool(cfg.get("live_authorized")),
            }
            authorities = tuple(cfg.get("known_canonical_authority_identifiers") or ())
            readiness_state_note = "READINESS_CONFIG_LOADED"
            readiness_digest = _sha256_file(readiness_path)
            if any(activation_flags.values()):
                readiness_state_note = "READINESS_ACTIVATION_FLAG_TRUE_INVALID"
        except Exception as exc:  # noqa: BLE001 — fail-closed classification
            runtime_state = None
            econ_pass = None
            activation_flags = {}
            authorities = ()
            readiness_state_note = f"READINESS_CONFIG_INVALID:{type(exc).__name__}"
            readiness_digest = None

    if readiness_state_note == "READINESS_CONFIG_ABSENT":
        records.append(
            _record(
                prerequisite_id="RUNTIME_BRIDGE_BOUND",
                description="Runtime bridge remains BOUND_NOT_ACTIVATED",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_ABSENT,
                reason_code="READINESS_CONFIG_ABSENT",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=None,
                observed_value="absent",
                expected_condition="runtime_bridge_state=BOUND_NOT_ACTIVATED",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("RUNTIME_BRIDGE_BOUND:ABSENT")
    elif readiness_state_note.startswith("READINESS_CONFIG_INVALID") or (
        readiness_state_note == "READINESS_ACTIVATION_FLAG_TRUE_INVALID"
    ):
        records.append(
            _record(
                prerequisite_id="RUNTIME_BRIDGE_BOUND",
                description="Runtime bridge remains BOUND_NOT_ACTIVATED",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_INVALID,
                reason_code=readiness_state_note[:200],
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value=str(runtime_state),
                expected_condition="runtime_bridge_state=BOUND_NOT_ACTIVATED",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("RUNTIME_BRIDGE_BOUND:INVALID")
    elif runtime_state == RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED:
        records.append(
            _record(
                prerequisite_id="RUNTIME_BRIDGE_BOUND",
                description="Runtime bridge remains BOUND_NOT_ACTIVATED",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_SATISFIED,
                reason_code="RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value=runtime_state,
                expected_condition="runtime_bridge_state=BOUND_NOT_ACTIVATED",
                evaluated_at=evaluated_at,
            )
        )
    else:
        records.append(
            _record(
                prerequisite_id="RUNTIME_BRIDGE_BOUND",
                description="Runtime bridge remains BOUND_NOT_ACTIVATED",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_INVALID,
                reason_code="RUNTIME_BRIDGE_STATE_UNEXPECTED",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value=str(runtime_state),
                expected_condition="runtime_bridge_state=BOUND_NOT_ACTIVATED",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("RUNTIME_BRIDGE_BOUND:INVALID")

    def _safety_prereq(
        pid: str,
        *,
        description: str,
        soak_key: str,
        readiness_false_keys: Sequence[str],
        expected: str,
    ) -> None:
        soak_val = soak_safety.get(soak_key)
        readiness_bad = any(activation_flags.get(k) for k in readiness_false_keys)
        if soak_val is True or readiness_bad:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_activation_eligibility_inventory_v0",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_INVALID,
                    reason_code=f"{soak_key}_OR_READINESS_ACTIVATION_TRUE",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value=f"soak={soak_val} readiness_bad={readiness_bad}",
                    expected_condition=expected,
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append(f"{pid}:INVALID")
        elif soak_val is False and not readiness_bad and readiness_path.is_file():
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_activation_eligibility_inventory_v0",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_SATISFIED,
                    reason_code=f"{soak_key}_FALSE_AND_READINESS_LOCKED",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value="false",
                    expected_condition=expected,
                    evaluated_at=evaluated_at,
                )
            )
        elif not soak_dir.is_dir() or soak_val is None:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_activation_eligibility_inventory_v0",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_ABSENT if not soak_dir.is_dir() else STATE_UNSATISFIED,
                    reason_code=f"{soak_key}_NOT_PROVEN",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value=str(soak_val),
                    expected_condition=expected,
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append(f"{pid}:NOT_PROVEN")
        else:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_activation_eligibility_inventory_v0",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_UNSATISFIED,
                    reason_code=f"{soak_key}_UNSATISFIED",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value=str(soak_val),
                    expected_condition=expected,
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append(f"{pid}:UNSATISFIED")

    _safety_prereq(
        "RUNTIME_REMAINS_NOT_ACTIVATED",
        description="Runtime remains not activated",
        soak_key="RUNTIME_ACTIVATED",
        readiness_false_keys=("runtime_activation_authorized",),
        expected="RUNTIME_ACTIVATED=false and runtime_activation_authorized=false",
    )
    _safety_prereq(
        "SCHEDULER_REMAINS_LOCKED",
        description="Scheduler remains locked / not activated",
        soak_key="SCHEDULER_ACTIVATED",
        readiness_false_keys=("scheduler_activation_authorized",),
        expected="SCHEDULER_ACTIVATED=false and scheduler_activation_authorized=false",
    )
    _safety_prereq(
        "NETWORK_REMAINS_PROHIBITED",
        description="Network runtime remains prohibited",
        soak_key="NETWORK_USED",
        readiness_false_keys=(),
        expected="NETWORK_USED=false",
    )
    _safety_prereq(
        "ORDERS_REMAIN_PROHIBITED",
        description="Orders remain prohibited (created/submitted false)",
        soak_key="ORDERS_CREATED",
        readiness_false_keys=("orders_authorized",),
        expected="ORDERS_CREATED=false ORDERS_SUBMITTED=false orders_authorized=false",
    )
    # Tighten orders if submitted true even when created false.
    orders_rec = next(r for r in records if r.prerequisite_id == "ORDERS_REMAIN_PROHIBITED")
    if soak_safety.get("ORDERS_SUBMITTED") is True and orders_rec.state == STATE_SATISFIED:
        records[records.index(orders_rec)] = _record(
            prerequisite_id="ORDERS_REMAIN_PROHIBITED",
            description=orders_rec.description,
            canonical_owner=orders_rec.canonical_owner,
            source_reference=orders_rec.source_reference,
            state=STATE_INVALID,
            reason_code="ORDERS_SUBMITTED_TRUE_INVALID",
            evidence_reference=orders_rec.evidence_reference,
            evidence_digest=orders_rec.evidence_digest,
            observed_value="orders_submitted=true",
            expected_condition=orders_rec.expected_condition,
            evaluated_at=evaluated_at,
        )
        blockers.append("ORDERS_REMAIN_PROHIBITED:INVALID")

    if econ_pass is True:
        # Canonical config currently false; if ever true still require durable proof.
        records.append(
            _record(
                prerequisite_id="ECONOMIC_VALIDITY_PROVEN",
                description="Economic validity offline gate proven",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_UNSATISFIED,
                reason_code="ECONOMIC_VALIDITY_FLAG_TRUE_WITHOUT_DURABLE_PROOF",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value="economic_validity_offline_gate_pass=true",
                expected_condition="durable economic validity proof under separate GO",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("ECONOMIC_VALIDITY_PROVEN:UNSATISFIED")
    elif readiness_path.is_file() and econ_pass is False:
        records.append(
            _record(
                prerequisite_id="ECONOMIC_VALIDITY_PROVEN",
                description="Economic validity offline gate proven",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_UNSATISFIED,
                reason_code="ECONOMIC_VALIDITY_NOT_PROVEN_BLOCKED",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value="economic_validity_offline_gate_pass=false",
                expected_condition="economic_validity_offline_gate_pass proven by durable evidence",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("ECONOMIC_VALIDITY_PROVEN:UNSATISFIED")
    else:
        records.append(
            _record(
                prerequisite_id="ECONOMIC_VALIDITY_PROVEN",
                description="Economic validity offline gate proven",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_ABSENT,
                reason_code="ECONOMIC_VALIDITY_SOURCE_ABSENT",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=None,
                observed_value="absent",
                expected_condition="economic_validity_offline_gate_pass proven by durable evidence",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("ECONOMIC_VALIDITY_PROVEN:ABSENT")

    required_authorities = {
        "trading.master_v2",
        "trading.double_play",
        "safety.independent_veto",
        "runtime_bridge.BOUND_NOT_ACTIVATED",
    }
    if not readiness_path.is_file():
        records.append(
            _record(
                prerequisite_id="SAFETY_AUTHORITY_VALID",
                description="Known safety/trading authorities remain referenced and non-mutated",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_ABSENT,
                reason_code="AUTHORITY_SOURCE_ABSENT",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=None,
                observed_value="absent",
                expected_condition="known_canonical_authority_identifiers contains required set",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("SAFETY_AUTHORITY_VALID:ABSENT")
    elif required_authorities.issubset(set(authorities)) and not any(activation_flags.values()):
        records.append(
            _record(
                prerequisite_id="SAFETY_AUTHORITY_VALID",
                description="Known safety/trading authorities remain referenced and non-mutated",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_SATISFIED,
                reason_code="AUTHORITY_IDENTIFIERS_PRESENT_NON_ACTIVATING",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value=",".join(sorted(required_authorities)),
                expected_condition="known_canonical_authority_identifiers contains required set",
                evaluated_at=evaluated_at,
            )
        )
    else:
        records.append(
            _record(
                prerequisite_id="SAFETY_AUTHORITY_VALID",
                description="Known safety/trading authorities remain referenced and non-mutated",
                canonical_owner="ops.shadow_preparation_readiness_gate_v0",
                source_reference=READINESS_CONFIG_RELPATH,
                state=STATE_UNSATISFIED,
                reason_code="AUTHORITY_SET_INCOMPLETE_OR_ACTIVATION_FLAG",
                evidence_reference=READINESS_CONFIG_RELPATH,
                evidence_digest=readiness_digest,
                observed_value=",".join(sorted(authorities)),
                expected_condition="known_canonical_authority_identifiers contains required set",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("SAFETY_AUTHORITY_VALID:UNSATISFIED")

    soak_proven = any(
        r.prerequisite_id == "STEP_29U_POST_MERGE_SOAK_PROVEN" and r.state == STATE_SATISFIED
        for r in records
    )
    if soak_proven:
        records.append(
            _record(
                prerequisite_id="RECONCILIATION_PRECONDITIONS_PROVEN",
                description="Offline full-chain reconciliation preconditions proven via soak",
                canonical_owner="ops.step_29u_post_merge_shadow_soak",
                source_reference=CANONICAL_SOAK_RELPATH,
                state=STATE_SATISFIED,
                reason_code="SOAK_FULL_CHAIN_HOLD_RECON_OBSERVED",
                evidence_reference=CANONICAL_SOAK_RELPATH,
                evidence_digest=soak_digest,
                observed_value="full_chain_hold_cycles_match_total",
                expected_condition="post-merge soak full-chain HOLD cycles proven",
                evaluated_at=evaluated_at,
            )
        )
    else:
        records.append(
            _record(
                prerequisite_id="RECONCILIATION_PRECONDITIONS_PROVEN",
                description="Offline full-chain reconciliation preconditions proven via soak",
                canonical_owner="ops.step_29u_post_merge_shadow_soak",
                source_reference=CANONICAL_SOAK_RELPATH,
                state=STATE_UNSATISFIED,
                reason_code="SOAK_NOT_PROVEN_FOR_RECON",
                evidence_reference=CANONICAL_SOAK_RELPATH,
                evidence_digest=soak_digest,
                observed_value="soak_not_satisfied",
                expected_condition="post-merge soak full-chain HOLD cycles proven",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("RECONCILIATION_PRECONDITIONS_PROVEN:UNSATISFIED")

    authority_contract_present = (root / BINDING_INVENTORY_RUNBOOK).is_file() and (
        root / "docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
    ).is_file()
    if authority_contract_present:
        records.append(
            _record(
                prerequisite_id="ACTIVATION_AUTHORITY_CONTRACT_PRESENT",
                description="Activation authority contract text present (separate GO required)",
                canonical_owner="runbook.STEP_29U",
                source_reference=BINDING_INVENTORY_RUNBOOK,
                state=STATE_SATISFIED,
                reason_code="ACTIVATION_AUTHORITY_CONTRACT_DOCUMENTED",
                evidence_reference=BINDING_INVENTORY_RUNBOOK,
                evidence_digest=None,
                observed_value="contract_present=true activation_authorized=false",
                expected_condition="authority contract present; does not grant GO",
                evaluated_at=evaluated_at,
            )
        )
    else:
        records.append(
            _record(
                prerequisite_id="ACTIVATION_AUTHORITY_CONTRACT_PRESENT",
                description="Activation authority contract text present (separate GO required)",
                canonical_owner="runbook.STEP_29U",
                source_reference=BINDING_INVENTORY_RUNBOOK,
                state=STATE_ABSENT,
                reason_code="ACTIVATION_AUTHORITY_CONTRACT_ABSENT",
                evidence_reference=BINDING_INVENTORY_RUNBOOK,
                evidence_digest=None,
                observed_value="absent",
                expected_condition="authority contract present; does not grant GO",
                evaluated_at=evaluated_at,
            )
        )
        blockers.append("ACTIVATION_AUTHORITY_CONTRACT_PRESENT:ABSENT")

    # This IMPLEMENTATION_ONLY authorization must never be inferred as future activation GO.
    records.append(
        _record(
            prerequisite_id="EXPLICIT_FUTURE_OPERATOR_GO_PRESENT",
            description="Explicit future Operator-GO for Step 29U activation present",
            canonical_owner="operator.activation_authority",
            source_reference=INVENTORY_RUNBOOK,
            state=STATE_ABSENT,
            reason_code="FUTURE_ACTIVATION_OPERATOR_GO_ABSENT",
            evidence_reference=INVENTORY_RUNBOOK,
            evidence_digest=None,
            observed_value="OPERATOR_GO_PRESENT=false",
            expected_condition="separate explicit future activation Operator-GO artifact",
            evaluated_at=evaluated_at,
        )
    )
    blockers.append("EXPLICIT_FUTURE_OPERATOR_GO_PRESENT:ABSENT")

    def _exclusion(pid: str, soak_key: str, description: str) -> None:
        val = soak_safety.get(soak_key)
        if val is True:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_post_merge_shadow_soak",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_INVALID,
                    reason_code=f"{soak_key}_TRUE_BLOCKS",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value="true",
                    expected_condition=f"{soak_key}=false",
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append(f"{pid}:INVALID")
        elif val is False:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_post_merge_shadow_soak",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_SATISFIED,
                    reason_code=f"{soak_key}_FALSE",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value="false",
                    expected_condition=f"{soak_key}=false",
                    evaluated_at=evaluated_at,
                )
            )
        else:
            records.append(
                _record(
                    prerequisite_id=pid,
                    description=description,
                    canonical_owner="ops.step_29u_post_merge_shadow_soak",
                    source_reference=CANONICAL_SOAK_RELPATH,
                    state=STATE_ABSENT if not soak_dir.is_dir() else STATE_UNSATISFIED,
                    reason_code=f"{soak_key}_NOT_OBSERVED",
                    evidence_reference=CANONICAL_SOAK_RELPATH,
                    evidence_digest=soak_digest,
                    observed_value=str(val),
                    expected_condition=f"{soak_key}=false",
                    evaluated_at=evaluated_at,
                )
            )
            blockers.append(f"{pid}:NOT_PROVEN")

    _exclusion("BTC_EXCLUDED", "BTC_OBSERVED", "BTC instruments excluded")
    _exclusion("SPOT_EXCLUDED", "SPOT_OBSERVED", "Spot instruments excluded")
    _exclusion(
        "KRAKEN_LEGACY_EXCLUDED",
        "KRAKEN_LEGACY_OBSERVED",
        "Kraken legacy surfaces excluded",
    )

    # Deterministic ordering by PREREQUISITE_IDS
    by_id = {r.prerequisite_id: r for r in records}
    missing = [pid for pid in PREREQUISITE_IDS if pid not in by_id]
    if missing:
        raise Step29UActivationEligibilityInventoryError(
            f"INCOMPLETE_PREREQUISITE_SET:{','.join(missing)}"
        )
    ordered = tuple(by_id[pid] for pid in PREREQUISITE_IDS)

    summary = {
        "prerequisite_count": len(ordered),
        "satisfied_count": sum(1 for r in ordered if r.state == STATE_SATISFIED),
        "unsatisfied_count": sum(1 for r in ordered if r.state == STATE_UNSATISFIED),
        "absent_count": sum(1 for r in ordered if r.state == STATE_ABSENT),
        "invalid_count": sum(1 for r in ordered if r.state == STATE_INVALID),
        "blocker_count": len(blockers),
    }

    # Hard terminal defaults for this capability.
    step_29u_activated = False
    operator_go_present = False
    btc_excluded = soak_safety.get("BTC_OBSERVED") is False
    spot_excluded = soak_safety.get("SPOT_OBSERVED") is False
    kraken_legacy_excluded = soak_safety.get("KRAKEN_LEGACY_OBSERVED") is False

    all_satisfied = all(r.state == STATE_SATISFIED for r in ordered)
    dedup_blockers = tuple(dict.fromkeys(blockers))
    # Future activation GO is always absent here; eligibility cannot be true.
    activation_eligible = False
    if all_satisfied and not dedup_blockers:
        # Defensive: even a fully satisfied set cannot authorize activation in v0.
        activation_eligible = False

    return ActivationEligibilityInventoryResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=evaluated_at,
        evaluated_main_sha=evaluated_sha,
        capability_id=CAPABILITY_ID,
        evaluator_valid=True,
        status="PASS",
        activation_eligible=activation_eligible,
        step_29u_activated=step_29u_activated,
        # Terminal defaults for this capability (never report activation truth).
        runtime_activated=False,
        scheduler_activated=False,
        network_used=False,
        orders_created=False,
        orders_submitted=False,
        operator_go_present=operator_go_present,
        btc_excluded=btc_excluded,
        spot_excluded=spot_excluded,
        kraken_legacy_excluded=kraken_legacy_excluded,
        prerequisites=ordered,
        blockers=dedup_blockers,
        summary=summary,
        provenance={
            "package_marker": PACKAGE_MARKER,
            "producer_family": PRODUCER_FAMILY,
            "inventory_runbook": INVENTORY_RUNBOOK,
            "binding_inventory_runbook": BINDING_INVENTORY_RUNBOOK,
            "canonical_soak_relpath": CANONICAL_SOAK_RELPATH,
            "expected_soak_tested_head_sha": EXPECTED_SOAK_TESTED_HEAD_SHA,
            "readiness_config_relpath": READINESS_CONFIG_RELPATH,
            "cli_relpath": CLI_RELPATH,
            "implementation_authorization": "IMPLEMENTATION_ONLY_NOT_ACTIVATION",
            "forbidden_import_surfaces": sorted(FORBIDDEN_IMPORT_SURFACES),
        },
        safety_facts={
            "ACTIVATION_ELIGIBLE": False,
            "STEP_29U_ACTIVATED": False,
            "RUNTIME_ACTIVATED": False,
            "SCHEDULER_ACTIVATED": False,
            "NETWORK_USED": False,
            "ORDERS_CREATED": False,
            "ORDERS_SUBMITTED": False,
            "OPERATOR_GO_PRESENT": False,
            "RUNTIME_BRIDGE_STATE": runtime_state or "UNKNOWN",
            "SOAK_OBSERVED_RUNTIME_ACTIVATED": soak_safety.get("RUNTIME_ACTIVATED"),
            "SOAK_OBSERVED_SCHEDULER_ACTIVATED": soak_safety.get("SCHEDULER_ACTIVATED"),
            "SOAK_OBSERVED_NETWORK_USED": soak_safety.get("NETWORK_USED"),
            "SOAK_OBSERVED_ORDERS_CREATED": soak_safety.get("ORDERS_CREATED"),
            "SOAK_OBSERVED_ORDERS_SUBMITTED": soak_safety.get("ORDERS_SUBMITTED"),
        },
    )


def result_to_machine_lines(
    result: ActivationEligibilityInventoryResultV0,
) -> list[str]:
    return [
        f"STATUS={result.status}",
        f"EVALUATOR_VALID={str(result.evaluator_valid).lower()}",
        f"ACTIVATION_ELIGIBLE={str(result.activation_eligible).lower()}",
        f"STEP_29U_ACTIVATED={str(result.step_29u_activated).lower()}",
        f"PREREQUISITE_COUNT={result.summary['prerequisite_count']}",
        f"SATISFIED_COUNT={result.summary['satisfied_count']}",
        f"UNSATISFIED_COUNT={result.summary['unsatisfied_count']}",
        f"ABSENT_COUNT={result.summary['absent_count']}",
        f"INVALID_COUNT={result.summary['invalid_count']}",
        f"BLOCKERS={list(result.blockers)}",
        f"RUNTIME_ACTIVATED={str(result.runtime_activated).lower()}",
        f"SCHEDULER_ACTIVATED={str(result.scheduler_activated).lower()}",
        f"NETWORK_USED={str(result.network_used).lower()}",
        f"ORDERS_CREATED={str(result.orders_created).lower()}",
        f"ORDERS_SUBMITTED={str(result.orders_submitted).lower()}",
        f"OPERATOR_GO_PRESENT={str(result.operator_go_present).lower()}",
        f"BTC_EXCLUDED={str(result.btc_excluded).lower()}",
        f"SPOT_EXCLUDED={str(result.spot_excluded).lower()}",
        f"KRAKEN_LEGACY_EXCLUDED={str(result.kraken_legacy_excluded).lower()}",
        f"EVALUATED_MAIN_SHA={result.evaluated_main_sha}",
        f"SCHEMA_ID={result.schema_id}",
        f"CAPABILITY_ID={result.capability_id}",
    ]


def serialize_result_json_v0(result: ActivationEligibilityInventoryResultV0) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
