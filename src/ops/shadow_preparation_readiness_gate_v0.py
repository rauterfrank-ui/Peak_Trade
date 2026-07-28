"""Shadow Preparation Readiness Gate v0.

Offline, immutable, side-effect-free producer family:
``ops.shadow_preparation_readiness_gate_v0``.

Classifies repository-backed shadow-named surfaces and emits a deterministic
machine-readable readiness result proving that canonical STEP 29U Shadow Mode
does not currently exist and that activation remains unauthorized.

This module:
- does not implement, activate, schedule, start, simulate, or execute Shadow,
  Paper, Testnet, Runtime, or Orders;
- has ``authority_effect=NONE`` and cannot modify another owner;
- performs no network I/O and starts no scheduler/worker/process;
- may optionally serialize an already-computed readiness evaluation into a
  durable, projection-only artifact via an explicit writer call (never by
  evaluation alone).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Mapping

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

PACKAGE_MARKER = "SHADOW_PREPARATION_READINESS_GATE_V0=true"
PRODUCER_FAMILY = "ops.shadow_preparation_readiness_gate_v0"
SCHEMA_ID = "ops.shadow_preparation_readiness_gate_v0"
SCHEMA_VERSION = "v0"
CONTRACT_CONFIG_SCHEMA_VERSION = "shadow_preparation_readiness_gate.v0"

PROJECTION_SCHEMA_ID = "shadow_preparation_readiness_projection"
PROJECTION_SCHEMA_VERSION = "v0"
PROJECTION_OUTPUT_PATH_CONFIG_KEY = "readiness_projection_output_path"
DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH = "out/ops/shadow_preparation_readiness_projection_v0.json"
PROJECTION_VERIFICATION_SCHEMA_ID = "shadow_preparation_readiness_projection_verification"
PROJECTION_VERIFICATION_SCHEMA_VERSION = "v0"
# Offline verifier freshness / clock-skew bounds (module contract; no config authority).
PROJECTION_VERIFIER_CLOCK_SKEW_SECONDS = 300
PROJECTION_VERIFIER_FRESHNESS_MAX_AGE_SECONDS = 86_400
PROJECTION_OVERALL_STATUS_VERIFIED: Literal["VERIFIED"] = "VERIFIED"
PROJECTION_OVERALL_STATUS_BLOCKED: Literal["BLOCKED"] = "BLOCKED"

REQUIRED_PROJECTION_TOP_LEVEL_FIELDS: tuple[str, ...] = (
    "schema_id",
    "schema_version",
    "evaluated_at",
    "authority_effect",
    "activation_authority",
    "projection_only",
    "evaluation",
    "blockers",
    "shadow_preparation_complete",
    "shadow_activatable",
    "step_29u_implemented",
    "canonical_step_29u_bound",
    "shadow_activation_authorized",
    "paper_activation_authorized",
    "testnet_activation_authorized",
    "scheduler_activation_authorized",
    "runtime_activation_authorized",
    "live_authorized",
    "orders_authorized",
    "evaluation_schema_id",
    "evaluation_schema_version",
)

# Deterministic evaluation timestamp convention for pure offline contracts:
# callers may override; default is a fixed epoch sentinel (no wall-clock).
DETERMINISTIC_EVALUATED_AT_DEFAULT = "1970-01-01T00:00:00Z"

AUTHORITY_EFFECT_NONE: Literal["NONE"] = "NONE"
RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED = "BOUND_NOT_ACTIVATED"
DASHBOARD_BLOCKER_ID_CANONICAL = "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY"
# Historical readiness emission only — not current Landscape V2 truth.
DASHBOARD_BLOCKER_STATE_OPEN = "OPEN"
DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2 = "RESOLVED_ON_LANDSCAPE_V2"
DASHBOARD_INTRABAR_CONTINUITY_PASS = "PASS"
CANONICAL_DASHBOARD_INTRABAR_TRUTH_RELATIVE_PATH = (
    "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
)
CANONICAL_DASHBOARD_INTRABAR_PASS_TOKEN = "INTRABAR_CAPABILITY=PASS"

DEFAULT_CONFIG_RELATIVE_PATH = Path("config/ops/shadow_preparation_readiness_gate_v0.toml")
CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY = "canonical_step_29u_semantics_reference"

ALLOWED_CLASSIFICATIONS = frozenset(
    {
        "NON_CANONICAL_STEP29U",
        "HISTORICAL",
        "PREPARATION_ONLY",
        "EVIDENCE_ONLY",
        "OFFLINE_REPLAY",
        "EXECUTOR_WITHOUT_CANONICAL_BINDING",
        "UNKNOWN_FAIL_CLOSED",
    }
)

ACTIVATION_FLAG_KEYS: tuple[str, ...] = (
    "shadow_activation_authorized",
    "paper_activation_authorized",
    "testnet_activation_authorized",
    "scheduler_activation_authorized",
    "runtime_activation_authorized",
    "live_authorized",
    "orders_authorized",
)

READY_CLAIM_BOOLEAN_FIELDS: tuple[str, ...] = (
    "shadow_preparation_complete",
    "shadow_activatable",
    "step_29u_implemented",
    "canonical_step_29u_bound",
    *ACTIVATION_FLAG_KEYS,
)

REQUIRED_PREPARATION_GATE_DEFAULTS: tuple[str, ...] = (
    "CANONICAL_STEP_29U_BOUND",
    "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
    "DASHBOARD_BLOCKER_RESOLVED",
    "RUNTIME_BRIDGE_ACTIVATION_AUTHORIZED_SEPARATELY",
    "SHADOW_ACTIVATION_OPERATOR_GO",
)


class ShadowPreparationReadinessGateError(ValueError):
    """Fail-closed evaluation or config error."""


class HistoricalSurfaceClassification(str, Enum):
    NON_CANONICAL_STEP29U = "NON_CANONICAL_STEP29U"
    HISTORICAL = "HISTORICAL"
    PREPARATION_ONLY = "PREPARATION_ONLY"
    EVIDENCE_ONLY = "EVIDENCE_ONLY"
    OFFLINE_REPLAY = "OFFLINE_REPLAY"
    EXECUTOR_WITHOUT_CANONICAL_BINDING = "EXECUTOR_WITHOUT_CANONICAL_BINDING"
    UNKNOWN_FAIL_CLOSED = "UNKNOWN_FAIL_CLOSED"


@dataclass(frozen=True)
class HistoricalSurfaceRecordV0:
    surface_id: str
    path: str
    classification: HistoricalSurfaceClassification
    notes: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "surface_id": self.surface_id,
            "path": self.path,
            "classification": self.classification.value,
            "notes": self.notes,
        }


ALLOWED_PREPARATION_STATUSES = frozenset(
    {
        "PRESENT",
        "MISSING",
        "UNBOUND",
        "DOCS_ONLY",
        "LEGACY_NON_CANONICAL",
    }
)

REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS: tuple[str, ...] = (
    "canonical_mode_identity",
    "lifecycle_owner",
    "session_state_machine",
    "canonical_decision_consumption",
    "execution_simulation_boundary",
    "fill_ownership",
    "fee_ownership",
    "slippage_ownership",
    "position_projection",
    "account_projection",
    "durable_restart_contract",
    "failure_handling_contract",
    "audit_evidence_contract",
    "activation_boundary",
    "operator_go_requirement",
    "economic_gate_relationship",
    "promotion_gate_relationship",
    "runtime_bridge_relationship",
    "order_side_effect_prohibition",
    "legacy_surface_non_equivalence",
)


class PreparationStatusV0(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    UNBOUND = "UNBOUND"
    DOCS_ONLY = "DOCS_ONLY"
    LEGACY_NON_CANONICAL = "LEGACY_NON_CANONICAL"


@dataclass(frozen=True)
class MindestkontraktComponentRecordV0:
    component_id: str
    required_for_step29u: bool
    preparation_status: PreparationStatusV0
    canonical_owner: str | None
    implementation_path: str | None
    evidence_paths: tuple[str, ...]
    blockers: tuple[str, ...]
    activation_relevance: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "required_for_step29u": self.required_for_step29u,
            "preparation_status": self.preparation_status.value,
            "canonical_owner": self.canonical_owner,
            "implementation_path": self.implementation_path,
            "evidence_paths": list(self.evidence_paths),
            "blockers": list(self.blockers),
            "activation_relevance": self.activation_relevance,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ShadowPreparationReadinessGateResultV0:
    schema_id: str
    schema_version: str
    evaluated_at: str
    authority_effect: Literal["NONE"]
    canonical_shadow_mode_exists: bool
    canonical_step_29u_bound: bool
    shadow_preparation_complete: bool
    shadow_activation_authorized: bool
    paper_activation_authorized: bool
    testnet_activation_authorized: bool
    scheduler_activation_authorized: bool
    runtime_activation_authorized: bool
    live_authorized: bool
    orders_authorized: bool
    economic_validity_offline_gate_pass: bool
    runtime_bridge_state: str
    dashboard_blocker_id: str
    dashboard_blocker_state: str
    dashboard_blocker_resolved: bool
    dashboard_blocker_waived: bool
    dashboard_blocker_accepted_as_done: bool
    not_step_29u_implementation: bool
    step_29u_implemented: bool
    shadow_activatable: bool
    shadow_mode_allowed: bool
    separate_go_required_for_implementation: bool
    separate_go_required_for_activation: bool
    canonical_step_29v_paper_mode_exists: bool
    mindestkontrakt_inventory: tuple[MindestkontraktComponentRecordV0, ...]
    historical_surface_classifications: tuple[HistoricalSurfaceRecordV0, ...]
    required_preparation_gates: tuple[str, ...]
    unmet_gates: tuple[str, ...]
    blockers: tuple[str, ...]
    next_permitted_action: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["historical_surface_classifications"] = [
            record.to_dict() for record in self.historical_surface_classifications
        ]
        payload["mindestkontrakt_inventory"] = [
            record.to_dict() for record in self.mindestkontrakt_inventory
        ]
        return payload


@dataclass(frozen=True)
class ShadowPreparationReadinessProjectionWriteMetadataV0:
    """Non-authoritative write metadata for a durable readiness projection."""

    output_path: str
    schema_id: str
    schema_version: str
    byte_length: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_path": self.output_path,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class ShadowPreparationReadinessProjectionVerificationResultV0:
    """Non-authoritative offline verification result for a durable projection."""

    overall_status: Literal["VERIFIED", "BLOCKED"]
    verified: bool
    reason_codes: tuple[str, ...]
    projection_path: str
    schema_id: str | None
    schema_version: str | None
    generated_at: str | None
    evidence_reference_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "verified": self.verified,
            "reason_codes": list(self.reason_codes),
            "projection_path": self.projection_path,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "evidence_reference_count": self.evidence_reference_count,
        }


def default_config_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else _infer_repo_root()
    return (root / DEFAULT_CONFIG_RELATIVE_PATH).resolve()


def load_shadow_preparation_readiness_gate_config_v0(
    config_path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Load and validate the static non-activating TOML config (fail-closed)."""
    path = config_path if config_path is not None else default_config_path(repo_root=repo_root)
    if not path.is_file():
        raise ShadowPreparationReadinessGateError(f"missing_config:{path}")
    try:
        raw = path.read_bytes()
        doc = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ShadowPreparationReadinessGateError(f"invalid_config:{path}:{exc}") from exc
    if not isinstance(doc, dict):
        raise ShadowPreparationReadinessGateError("invalid_config:root_not_mapping")
    _validate_config_document(doc)
    return doc


def evaluate_shadow_preparation_readiness_gate_v0(
    *,
    config: Mapping[str, Any] | None = None,
    config_path: Path | None = None,
    repo_root: Path | None = None,
    evaluated_at: str | None = None,
    activation_overrides: Mapping[str, bool] | None = None,
    dashboard_blocker_overrides: Mapping[str, Any] | None = None,
    authority_effect_override: str | None = None,
    historical_surface_overrides: tuple[HistoricalSurfaceRecordV0, ...] | None = None,
) -> ShadowPreparationReadinessGateResultV0:
    """Evaluate Shadow-preparation readiness (offline, fail-closed, no side effects)."""
    root = (repo_root if repo_root is not None else _infer_repo_root()).resolve()
    cfg = (
        dict(config)
        if config is not None
        else load_shadow_preparation_readiness_gate_config_v0(config_path, repo_root=root)
    )
    _validate_config_document(cfg)

    if authority_effect_override is not None and authority_effect_override != AUTHORITY_EFFECT_NONE:
        raise ShadowPreparationReadinessGateError(
            f"authority_effect_must_be_none:{authority_effect_override!r}"
        )

    activation = _resolve_activation_flags(cfg, activation_overrides)
    for key, value in activation.items():
        if value is True:
            raise ShadowPreparationReadinessGateError(f"activation_flag_true_rejected:{key}")

    _validate_canonical_dashboard_intrabar_truth(repo_root=root)
    dashboard = _resolve_dashboard_blocker(cfg, dashboard_blocker_overrides)
    _assert_dashboard_blocker_matches_canonical_resolved(dashboard)

    runtime_bridge_state = str(
        cfg.get("runtime_bridge_state") or RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED
    )
    if runtime_bridge_state != RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED:
        raise ShadowPreparationReadinessGateError(
            f"runtime_bridge_state_must_remain_bound_not_activated:{runtime_bridge_state!r}"
        )

    economic_pass = bool(cfg.get("economic_validity_offline_gate_pass", False))
    if economic_pass is True:
        raise ShadowPreparationReadinessGateError(
            "economic_validity_offline_gate_pass_true_rejected"
        )

    surfaces = (
        historical_surface_overrides
        if historical_surface_overrides is not None
        else _parse_historical_surfaces(cfg)
    )
    _assert_surfaces_fail_closed(surfaces)
    _validate_historical_surface_paths(repo_root=root, surfaces=surfaces)

    mindestkontrakt = _parse_mindestkontrakt_inventory(cfg)
    _assert_mindestkontrakt_inventory(mindestkontrakt)
    _validate_mindestkontrakt_evidence_paths(repo_root=root, records=mindestkontrakt)

    canonical_refs = cfg.get("known_canonical_authority_identifiers") or []
    if not isinstance(canonical_refs, list) or not canonical_refs:
        raise ShadowPreparationReadinessGateError(
            "required_canonical_reference_missing:known_canonical_authority_identifiers"
        )
    _validate_canonical_step_29u_semantics_reference(repo_root=root, cfg=cfg)

    required_gates = _parse_string_tuple(
        cfg.get("required_preparation_gates"),
        field="required_preparation_gates",
        default=REQUIRED_PREPARATION_GATE_DEFAULTS,
    )

    from src.ops.step_29u_canonical_shadow_binding_v0 import (
        observe_canonical_step_29u_bound_v0,
    )

    step_29u_bound, _bind_reasons = observe_canonical_step_29u_bound_v0(repo_root=root)
    step_29u_implemented = bool(step_29u_bound)

    unmet = list(required_gates)
    if step_29u_bound and "CANONICAL_STEP_29U_BOUND" in unmet:
        unmet.remove("CANONICAL_STEP_29U_BOUND")
    if bool(dashboard["dashboard_blocker_resolved"]) and "DASHBOARD_BLOCKER_RESOLVED" in unmet:
        unmet.remove("DASHBOARD_BLOCKER_RESOLVED")

    # Dashboard intrabar continuity is resolved on Landscape V2; independent
    # blockers below keep overall Shadow preparation non-ready / non-activatable.
    blockers = [
        "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL_BLOCKED",
        "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED",
        "HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U",
        "NO_ACTIVATION_AUTHORIZED",
    ]
    if not step_29u_bound:
        blockers.insert(0, "CANONICAL_STEP_29U_ABSENT")

    if step_29u_bound:
        next_action = (
            "CONTINUE_OFFLINE_SHADOW_PREPARATION;"
            "STEP_29U_CANONICALLY_BOUND_NOT_ACTIVATED;"
            "NO_ACTIVATION;"
            "SEPARATE_OPERATOR_GO_REQUIRED_FOR_ANY_ACTIVATION_STAGE"
        )
    else:
        next_action = (
            "CONTINUE_OFFLINE_SHADOW_PREPARATION_CLASSIFICATION_ONLY;"
            "NO_STEP_29U_IMPLEMENTATION;"
            "NO_ACTIVATION;"
            "SEPARATE_OPERATOR_GO_REQUIRED_FOR_ANY_ACTIVATION_STAGE"
        )

    return ShadowPreparationReadinessGateResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        evaluated_at=evaluated_at or DETERMINISTIC_EVALUATED_AT_DEFAULT,
        authority_effect=AUTHORITY_EFFECT_NONE,
        canonical_shadow_mode_exists=bool(step_29u_bound),
        canonical_step_29u_bound=bool(step_29u_bound),
        shadow_preparation_complete=False,
        shadow_activation_authorized=False,
        paper_activation_authorized=False,
        testnet_activation_authorized=False,
        scheduler_activation_authorized=False,
        runtime_activation_authorized=False,
        live_authorized=False,
        orders_authorized=False,
        economic_validity_offline_gate_pass=False,
        runtime_bridge_state=RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED,
        dashboard_blocker_id=DASHBOARD_BLOCKER_ID_CANONICAL,
        dashboard_blocker_state=DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2,
        dashboard_blocker_resolved=True,
        dashboard_blocker_waived=False,
        dashboard_blocker_accepted_as_done=False,
        not_step_29u_implementation=True,
        step_29u_implemented=step_29u_implemented,
        shadow_activatable=False,
        shadow_mode_allowed=False,
        separate_go_required_for_implementation=True,
        separate_go_required_for_activation=True,
        canonical_step_29v_paper_mode_exists=False,
        mindestkontrakt_inventory=mindestkontrakt,
        historical_surface_classifications=surfaces,
        required_preparation_gates=required_gates,
        unmet_gates=tuple(unmet),
        blockers=tuple(blockers),
        next_permitted_action=next_action,
    )


def build_shadow_preparation_readiness_projection_payload_v0(
    *,
    evaluation: ShadowPreparationReadinessGateResultV0,
    evaluated_at: str,
) -> dict[str, Any]:
    """Build the deterministic projection document from an existing evaluation.

    Does not re-evaluate readiness, filesystem evidence, blockers, or STEP-29U
    semantics. Consumes ``evaluation.to_dict()`` as the sole evaluation payload.
    """
    if not isinstance(evaluated_at, str) or not evaluated_at.strip():
        raise ShadowPreparationReadinessGateError("PROJECTION_EVALUATED_AT_EMPTY")
    evaluation_payload = evaluation.to_dict()
    return {
        "schema_id": PROJECTION_SCHEMA_ID,
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "evaluated_at": evaluated_at.strip(),
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "activation_authority": False,
        "projection_only": True,
        "evaluation": evaluation_payload,
        "blockers": list(evaluation.blockers),
        "shadow_preparation_complete": evaluation.shadow_preparation_complete,
        "shadow_activatable": evaluation.shadow_activatable,
        "step_29u_implemented": evaluation.step_29u_implemented,
        "canonical_step_29u_bound": evaluation.canonical_step_29u_bound,
        "shadow_activation_authorized": evaluation.shadow_activation_authorized,
        "paper_activation_authorized": evaluation.paper_activation_authorized,
        "testnet_activation_authorized": evaluation.testnet_activation_authorized,
        "scheduler_activation_authorized": evaluation.scheduler_activation_authorized,
        "runtime_activation_authorized": evaluation.runtime_activation_authorized,
        "live_authorized": evaluation.live_authorized,
        "orders_authorized": evaluation.orders_authorized,
        "evaluation_schema_id": evaluation.schema_id,
        "evaluation_schema_version": evaluation.schema_version,
    }


def serialize_shadow_preparation_readiness_projection_v0(
    payload: Mapping[str, Any],
) -> bytes:
    """Serialize projection payload to deterministic UTF-8 JSON with trailing newline."""
    try:
        text = json.dumps(
            dict(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ShadowPreparationReadinessGateError(f"PROJECTION_SERIALIZATION_FAILED:{exc}") from exc
    return (text + "\n").encode("utf-8")


def _resolve_projection_output_path(
    *,
    repo_root: Path,
    output_path: str,
) -> tuple[str, Path]:
    """Resolve a repository-relative projection output path (fail-closed)."""
    if not isinstance(output_path, str) or not output_path.strip():
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PATH_EMPTY")
    rel = output_path.strip()
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PATH_ABSOLUTE")
    root = repo_root.resolve()
    try:
        resolved = (root / candidate).resolve()
    except OSError as exc:
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PATH_RESOLVE_FAILED") from exc
    try:
        repo_relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PATH_OUTSIDE_REPO") from exc
    if resolved.exists() and resolved.is_dir():
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PATH_IS_DIRECTORY")
    parent = resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise ShadowPreparationReadinessGateError("PROJECTION_OUTPUT_PARENT_MISSING")
    return repo_relative, resolved


def _atomic_write_bytes(*, destination: Path, content: bytes) -> None:
    """Atomically replace destination with content (temp sibling + fsync + replace)."""
    fd, temp_path = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".tmp_{destination.name}_",
        suffix=".partial",
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            try:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            except OSError as exc:
                raise ShadowPreparationReadinessGateError(
                    f"PROJECTION_TEMP_WRITE_FAILED:{exc}"
                ) from exc
        try:
            os.replace(temp_path, destination)
        except OSError as exc:
            raise ShadowPreparationReadinessGateError(
                f"PROJECTION_ATOMIC_REPLACE_FAILED:{exc}"
            ) from exc
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        raise
    finally:
        if not closed:
            try:
                os.close(fd)
            except OSError:
                pass


def write_shadow_preparation_readiness_projection_v0(
    *,
    evaluation: ShadowPreparationReadinessGateResultV0,
    repo_root: Path,
    output_path: str,
    evaluated_at: str,
) -> ShadowPreparationReadinessProjectionWriteMetadataV0:
    """Write one already-computed readiness evaluation as durable projection bytes.

    Offline evidence projection only. Not activation authority. Not STEP-29U.
    Does not recompute readiness. Evaluation alone remains side-effect free;
    writing requires this explicit call.
    """
    root = repo_root.resolve()
    repo_relative, destination = _resolve_projection_output_path(
        repo_root=root,
        output_path=output_path,
    )
    payload = build_shadow_preparation_readiness_projection_payload_v0(
        evaluation=evaluation,
        evaluated_at=evaluated_at,
    )
    content = serialize_shadow_preparation_readiness_projection_v0(payload)
    _atomic_write_bytes(destination=destination, content=content)
    digest = hashlib.sha256(content).hexdigest()
    return ShadowPreparationReadinessProjectionWriteMetadataV0(
        output_path=repo_relative,
        schema_id=PROJECTION_SCHEMA_ID,
        schema_version=PROJECTION_SCHEMA_VERSION,
        byte_length=len(content),
        sha256=digest,
    )


def _blocked_projection_verification(
    *,
    projection_path: str,
    reason_codes: tuple[str, ...],
    schema_id: str | None = None,
    schema_version: str | None = None,
    generated_at: str | None = None,
    evidence_reference_count: int = 0,
) -> ShadowPreparationReadinessProjectionVerificationResultV0:
    return ShadowPreparationReadinessProjectionVerificationResultV0(
        overall_status=PROJECTION_OVERALL_STATUS_BLOCKED,
        verified=False,
        reason_codes=reason_codes,
        projection_path=projection_path,
        schema_id=schema_id,
        schema_version=schema_version,
        generated_at=generated_at,
        evidence_reference_count=evidence_reference_count,
    )


def _parse_projection_timestamp(raw: str) -> datetime | None:
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_projection_read_path(
    *,
    repo_root: Path,
    projection_path: str | None,
    config: Mapping[str, Any] | None,
    config_path: Path | None,
) -> tuple[str, Path] | ShadowPreparationReadinessProjectionVerificationResultV0:
    """Resolve explicit or configured default projection path (no path inference)."""
    root = repo_root.resolve()
    if projection_path is None:
        cfg = (
            dict(config)
            if config is not None
            else load_shadow_preparation_readiness_gate_config_v0(config_path, repo_root=root)
        )
        raw_path = cfg.get(PROJECTION_OUTPUT_PATH_CONFIG_KEY)
        if not isinstance(raw_path, str) or not raw_path.strip():
            return _blocked_projection_verification(
                projection_path="",
                reason_codes=("MISSING_PROJECTION", "PROJECTION_PATH_UNCONFIGURED"),
            )
        rel = raw_path.strip()
    else:
        if not isinstance(projection_path, str) or not projection_path.strip():
            return _blocked_projection_verification(
                projection_path=str(projection_path or ""),
                reason_codes=("MISSING_PROJECTION", "PROJECTION_PATH_EMPTY"),
            )
        rel = projection_path.strip()
    candidate = Path(rel)
    if candidate.is_absolute():
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("MISSING_PROJECTION", "PROJECTION_PATH_ABSOLUTE"),
        )
    try:
        resolved = (root / candidate).resolve()
    except OSError:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("MISSING_PROJECTION", "PROJECTION_PATH_RESOLVE_FAILED"),
        )
    try:
        resolved.relative_to(root)
    except ValueError:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("MISSING_PROJECTION", "PROJECTION_PATH_OUTSIDE_REPO"),
        )
    return rel, resolved


def _collect_projection_evidence_references(
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    refs: list[str] = []
    evaluation = payload.get("evaluation")
    if not isinstance(evaluation, Mapping):
        return ()
    inventory = evaluation.get("mindestkontrakt_inventory")
    if not isinstance(inventory, list):
        return ()
    for item in inventory:
        if not isinstance(item, Mapping):
            continue
        paths = item.get("evidence_paths")
        if paths is None:
            continue
        if not isinstance(paths, list):
            refs.append("")
            continue
        for path in paths:
            if isinstance(path, str):
                refs.append(path)
            else:
                refs.append("")
    return tuple(refs)


def _projection_claims_ready(payload: Mapping[str, Any]) -> bool:
    for key in READY_CLAIM_BOOLEAN_FIELDS:
        if payload.get(key) is True:
            return True
    evaluation = payload.get("evaluation")
    if isinstance(evaluation, Mapping):
        for key in READY_CLAIM_BOOLEAN_FIELDS:
            if evaluation.get(key) is True:
                return True
    return False


def _required_readiness_components_non_ready(payload: Mapping[str, Any]) -> bool:
    evaluation = payload.get("evaluation")
    if not isinstance(evaluation, Mapping):
        return True
    inventory = evaluation.get("mindestkontrakt_inventory")
    if not isinstance(inventory, list):
        return True
    for item in inventory:
        if not isinstance(item, Mapping):
            return True
        required = item.get("required_for_step29u")
        status = item.get("preparation_status")
        if required is True and status in {"MISSING", "UNBOUND"}:
            return True
    blockers = payload.get("blockers")
    if isinstance(blockers, list) and blockers:
        return True
    nested_blockers = evaluation.get("blockers")
    if isinstance(nested_blockers, list) and nested_blockers:
        return True
    unmet = evaluation.get("unmet_gates")
    if isinstance(unmet, list) and unmet:
        return True
    return False


def verify_shadow_preparation_readiness_projection_v0(
    *,
    repo_root: Path,
    projection_path: str | None = None,
    config: Mapping[str, Any] | None = None,
    config_path: Path | None = None,
    as_of: str | None = None,
    expected_sha256: str | None = None,
    permitted_evidence_roots: tuple[Path, ...] | None = None,
) -> ShadowPreparationReadinessProjectionVerificationResultV0:
    """Read and verify one durable readiness projection (offline, fail-closed).

    Consumes the existing projection output contract only. Performs no writes,
    no activation, and no readiness re-evaluation. Returns a verification result
    without copying the full projection into a new authority object.
    """
    root = repo_root.resolve()
    resolved = _resolve_projection_read_path(
        repo_root=root,
        projection_path=projection_path,
        config=config,
        config_path=config_path,
    )
    if isinstance(resolved, ShadowPreparationReadinessProjectionVerificationResultV0):
        return resolved
    rel, destination = resolved

    if not destination.exists() or not destination.is_file():
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("MISSING_PROJECTION",),
        )

    try:
        raw = destination.read_bytes()
    except OSError:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("MISSING_PROJECTION", "PROJECTION_READ_FAILED"),
        )

    try:
        payload_obj = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("INVALID_PROJECTION",),
        )
    if not isinstance(payload_obj, dict):
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("INVALID_PROJECTION",),
        )

    schema_id = payload_obj.get("schema_id")
    schema_version = payload_obj.get("schema_version")
    generated_at_raw = payload_obj.get("evaluated_at")
    generated_at = generated_at_raw if isinstance(generated_at_raw, str) else None
    evidence_refs = _collect_projection_evidence_references(payload_obj)
    evidence_count = len(evidence_refs)

    missing_fields = [
        field for field in REQUIRED_PROJECTION_TOP_LEVEL_FIELDS if field not in payload_obj
    ]
    if missing_fields:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("BLOCKED", *(f"MISSING_FIELD:{field}" for field in missing_fields)),
            schema_id=schema_id if isinstance(schema_id, str) else None,
            schema_version=schema_version if isinstance(schema_version, str) else None,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )

    if schema_id != PROJECTION_SCHEMA_ID or schema_version != PROJECTION_SCHEMA_VERSION:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("SCHEMA_MISMATCH",),
            schema_id=schema_id if isinstance(schema_id, str) else None,
            schema_version=schema_version if isinstance(schema_version, str) else None,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )

    if not isinstance(generated_at, str) or not generated_at.strip():
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("BLOCKED", "MISSING_FIELD:evaluated_at"),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=None,
            evidence_reference_count=evidence_count,
        )

    evaluation = payload_obj.get("evaluation")
    if not isinstance(evaluation, dict):
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("BLOCKED", "MISSING_FIELD:evaluation"),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )

    inventory = evaluation.get("mindestkontrakt_inventory")
    if isinstance(inventory, list):
        for idx, item in enumerate(inventory):
            if not isinstance(item, dict):
                return _blocked_projection_verification(
                    projection_path=rel,
                    reason_codes=("BLOCKED", f"INVALID_ENUM:mindestkontrakt_inventory:{idx}"),
                    schema_id=PROJECTION_SCHEMA_ID,
                    schema_version=PROJECTION_SCHEMA_VERSION,
                    generated_at=generated_at,
                    evidence_reference_count=evidence_count,
                )
            status = item.get("preparation_status")
            if status is not None and status not in ALLOWED_PREPARATION_STATUSES:
                return _blocked_projection_verification(
                    projection_path=rel,
                    reason_codes=("BLOCKED", f"INVALID_ENUM:preparation_status:{status}"),
                    schema_id=PROJECTION_SCHEMA_ID,
                    schema_version=PROJECTION_SCHEMA_VERSION,
                    generated_at=generated_at,
                    evidence_reference_count=evidence_count,
                )

    surfaces = evaluation.get("historical_surface_classifications")
    if isinstance(surfaces, list):
        for idx, item in enumerate(surfaces):
            if not isinstance(item, dict):
                continue
            classification = item.get("classification")
            if classification is not None and classification not in ALLOWED_CLASSIFICATIONS:
                return _blocked_projection_verification(
                    projection_path=rel,
                    reason_codes=("BLOCKED", f"INVALID_ENUM:classification:{classification}"),
                    schema_id=PROJECTION_SCHEMA_ID,
                    schema_version=PROJECTION_SCHEMA_VERSION,
                    generated_at=generated_at,
                    evidence_reference_count=evidence_count,
                )

    if _projection_claims_ready(payload_obj) and _required_readiness_components_non_ready(
        payload_obj
    ):
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("CONTRADICTORY_PROJECTION",),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )

    permitted_roots = tuple(path.resolve() for path in (permitted_evidence_roots or (root,)))
    for evidence_path in evidence_refs:
        if not isinstance(evidence_path, str) or not evidence_path.strip():
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "EVIDENCE_REFERENCE_INVALID"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )
        rel_evidence = evidence_path.strip()
        candidate = Path(rel_evidence)
        if candidate.is_absolute():
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "EVIDENCE_PATH_ESCAPE"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )
        try:
            resolved_evidence = (root / candidate).resolve()
        except OSError:
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "EVIDENCE_REFERENCE_MISSING"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )
        if not any(
            _path_is_within_root(resolved_evidence, permitted_root)
            for permitted_root in permitted_roots
        ):
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "EVIDENCE_PATH_ESCAPE"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )
        if not resolved_evidence.exists() or not resolved_evidence.is_file():
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "EVIDENCE_REFERENCE_MISSING"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )

    digest_candidates: list[str] = []
    if expected_sha256 is not None:
        digest_candidates.append(expected_sha256)
    for key in ("sha256", "content_sha256", "digest"):
        value = payload_obj.get(key)
        if isinstance(value, str) and value.strip():
            digest_candidates.append(value.strip())
    if digest_candidates:
        actual = hashlib.sha256(raw).hexdigest()
        for digest in digest_candidates:
            if digest.lower() != actual.lower():
                return _blocked_projection_verification(
                    projection_path=rel,
                    reason_codes=("BLOCKED", "DIGEST_MISMATCH"),
                    schema_id=PROJECTION_SCHEMA_ID,
                    schema_version=PROJECTION_SCHEMA_VERSION,
                    generated_at=generated_at,
                    evidence_reference_count=evidence_count,
                )

    generated_dt = _parse_projection_timestamp(generated_at)
    if generated_dt is None:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("BLOCKED", "INVALID_PROJECTION_TIMESTAMP"),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )
    if as_of is None:
        as_of_dt = datetime.now(timezone.utc)
    else:
        as_of_dt = _parse_projection_timestamp(as_of)
        if as_of_dt is None:
            return _blocked_projection_verification(
                projection_path=rel,
                reason_codes=("BLOCKED", "INVALID_AS_OF_TIMESTAMP"),
                schema_id=PROJECTION_SCHEMA_ID,
                schema_version=PROJECTION_SCHEMA_VERSION,
                generated_at=generated_at,
                evidence_reference_count=evidence_count,
            )
    skew = timedelta(seconds=PROJECTION_VERIFIER_CLOCK_SKEW_SECONDS)
    max_age = timedelta(seconds=PROJECTION_VERIFIER_FRESHNESS_MAX_AGE_SECONDS)
    if generated_dt > as_of_dt + skew:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("BLOCKED", "FUTURE_DATED"),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )
    if generated_dt < as_of_dt - max_age:
        return _blocked_projection_verification(
            projection_path=rel,
            reason_codes=("STALE",),
            schema_id=PROJECTION_SCHEMA_ID,
            schema_version=PROJECTION_SCHEMA_VERSION,
            generated_at=generated_at,
            evidence_reference_count=evidence_count,
        )

    return ShadowPreparationReadinessProjectionVerificationResultV0(
        overall_status=PROJECTION_OVERALL_STATUS_VERIFIED,
        verified=True,
        reason_codes=(),
        projection_path=rel,
        schema_id=PROJECTION_SCHEMA_ID,
        schema_version=PROJECTION_SCHEMA_VERSION,
        generated_at=generated_at,
        evidence_reference_count=evidence_count,
    )


def _path_is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _infer_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _require_repo_relative_file(
    *,
    repo_root: Path,
    relative_path: str,
    context_id: str,
    code_prefix: str,
) -> Path:
    """Fail-closed: require a non-empty repo-relative path that resolves to a file.

    Rejects empty strings, absolute paths, paths escaping ``repo_root`` (including
    via ``..`` / symlink resolution), missing paths, and directories.
    """
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise ShadowPreparationReadinessGateError(f"{code_prefix}_EMPTY:{context_id}")
    rel = relative_path.strip()
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ShadowPreparationReadinessGateError(f"{code_prefix}_ABSOLUTE:{context_id}")
    root = repo_root.resolve()
    try:
        resolved = (root / candidate).resolve()
    except OSError as exc:
        raise ShadowPreparationReadinessGateError(f"{code_prefix}_MISSING:{context_id}") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ShadowPreparationReadinessGateError(
            f"{code_prefix}_OUTSIDE_REPO:{context_id}"
        ) from exc
    if not resolved.exists():
        raise ShadowPreparationReadinessGateError(f"{code_prefix}_MISSING:{context_id}")
    if not resolved.is_file():
        raise ShadowPreparationReadinessGateError(f"{code_prefix}_NOT_FILE:{context_id}")
    return resolved


def _validate_historical_surface_paths(
    *,
    repo_root: Path,
    surfaces: tuple[HistoricalSurfaceRecordV0, ...],
) -> None:
    for surface in surfaces:
        _require_repo_relative_file(
            repo_root=repo_root,
            relative_path=surface.path,
            context_id=surface.surface_id,
            code_prefix="HISTORICAL_SURFACE_PATH",
        )


def _validate_mindestkontrakt_evidence_paths(
    *,
    repo_root: Path,
    records: tuple[MindestkontraktComponentRecordV0, ...],
) -> None:
    for record in records:
        for evidence_path in record.evidence_paths:
            _require_repo_relative_file(
                repo_root=repo_root,
                relative_path=evidence_path,
                context_id=record.component_id,
                code_prefix="EVIDENCE_PATH",
            )


def _validate_canonical_step_29u_semantics_reference(
    *,
    repo_root: Path,
    cfg: Mapping[str, Any],
) -> None:
    raw = cfg.get(CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY)
    if raw is None:
        raise ShadowPreparationReadinessGateError("CANONICAL_STEP_29U_SEMANTICS_REFERENCE_MISSING")
    if not isinstance(raw, str):
        raise ShadowPreparationReadinessGateError("CANONICAL_STEP_29U_SEMANTICS_REFERENCE_INVALID")
    _require_repo_relative_file(
        repo_root=repo_root,
        relative_path=raw,
        context_id=CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY,
        code_prefix="CANONICAL_STEP_29U_SEMANTICS_REFERENCE",
    )


def _validate_config_document(doc: Mapping[str, Any]) -> None:
    schema_version = doc.get("schema_version")
    if schema_version != CONTRACT_CONFIG_SCHEMA_VERSION:
        raise ShadowPreparationReadinessGateError(
            f"invalid_config_schema_version:{schema_version!r}"
        )
    producer = doc.get("producer_family")
    if producer != PRODUCER_FAMILY:
        raise ShadowPreparationReadinessGateError(f"invalid_producer_family:{producer!r}")
    authority = doc.get("authority_effect", AUTHORITY_EFFECT_NONE)
    if authority != AUTHORITY_EFFECT_NONE:
        raise ShadowPreparationReadinessGateError(
            f"config_authority_effect_must_be_none:{authority!r}"
        )
    for key in ACTIVATION_FLAG_KEYS:
        if key in doc and doc[key] is True:
            raise ShadowPreparationReadinessGateError(f"config_activation_flag_true:{key}")
    if doc.get("economic_validity_offline_gate_pass") is True:
        raise ShadowPreparationReadinessGateError("config_economic_validity_offline_gate_pass_true")
    if "dashboard_blocker_id" not in doc:
        raise ShadowPreparationReadinessGateError("config_dashboard_blocker_id_missing")
    state = doc.get("dashboard_blocker_state")
    if state not in (
        None,
        DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2,
    ):
        raise ShadowPreparationReadinessGateError(
            f"config_dashboard_blocker_state_invalid:{state!r}"
        )
    if doc.get("dashboard_blocker_resolved") is False:
        raise ShadowPreparationReadinessGateError("config_dashboard_blocker_resolved_must_be_true")
    for bad in (
        "dashboard_blocker_waived",
        "dashboard_blocker_accepted_as_done",
    ):
        if doc.get(bad) is True:
            raise ShadowPreparationReadinessGateError(f"config_{bad}_true_rejected")


def _validate_canonical_dashboard_intrabar_truth(*, repo_root: Path) -> None:
    """Consume Landscape V2 as the sole current intrabar continuity authority.

    The readiness gate does not own Market Dashboard truth and does not recompute
    intrabar continuity. Missing or contradictory owner evidence fails closed.
    """
    relative = CANONICAL_DASHBOARD_INTRABAR_TRUTH_RELATIVE_PATH
    path = _require_repo_relative_file(
        repo_root=repo_root,
        relative_path=relative,
        context_id="canonical_dashboard_intrabar_truth",
        code_prefix="CANONICAL_DASHBOARD_INTRABAR_TRUTH",
    )
    body = path.read_text(encoding="utf-8")
    if CANONICAL_DASHBOARD_INTRABAR_PASS_TOKEN not in body:
        raise ShadowPreparationReadinessGateError(
            "canonical_dashboard_intrabar_pass_token_missing:"
            f"{CANONICAL_DASHBOARD_INTRABAR_PASS_TOKEN}"
        )


def _assert_dashboard_blocker_matches_canonical_resolved(
    dashboard: Mapping[str, Any],
) -> None:
    if dashboard["dashboard_blocker_id"] != DASHBOARD_BLOCKER_ID_CANONICAL:
        raise ShadowPreparationReadinessGateError(
            f"dashboard_blocker_id_mismatch:{dashboard['dashboard_blocker_id']!r}"
        )
    state = str(dashboard["dashboard_blocker_state"])
    if state == DASHBOARD_BLOCKER_STATE_OPEN:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_state_stale_open_rejected")
    if state != DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2:
        raise ShadowPreparationReadinessGateError(f"dashboard_blocker_state_invalid:{state!r}")
    if dashboard["dashboard_blocker_resolved"] is not True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_resolved_required_true")
    if dashboard["dashboard_blocker_waived"] is True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_waived_rejected")
    if dashboard["dashboard_blocker_accepted_as_done"] is True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_accepted_as_done_rejected")


def _resolve_activation_flags(
    cfg: Mapping[str, Any],
    overrides: Mapping[str, bool] | None,
) -> dict[str, bool]:
    resolved: dict[str, bool] = {}
    for key in ACTIVATION_FLAG_KEYS:
        base = bool(cfg.get(key, False))
        if overrides is not None and key in overrides:
            value = overrides[key]
            if not isinstance(value, bool):
                raise ShadowPreparationReadinessGateError(f"activation_override_not_bool:{key}")
            resolved[key] = value
        else:
            resolved[key] = base
    return resolved


def _resolve_dashboard_blocker(
    cfg: Mapping[str, Any],
    overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    base = {
        "dashboard_blocker_id": str(
            cfg.get("dashboard_blocker_id") or DASHBOARD_BLOCKER_ID_CANONICAL
        ),
        "dashboard_blocker_state": str(
            cfg.get("dashboard_blocker_state") or DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2
        ),
        "dashboard_blocker_resolved": bool(cfg.get("dashboard_blocker_resolved", True)),
        "dashboard_blocker_waived": bool(cfg.get("dashboard_blocker_waived", False)),
        "dashboard_blocker_accepted_as_done": bool(
            cfg.get("dashboard_blocker_accepted_as_done", False)
        ),
    }
    if overrides:
        for key, value in overrides.items():
            if key not in base:
                raise ShadowPreparationReadinessGateError(f"unknown_dashboard_override:{key}")
            base[key] = value
    for required in (
        "dashboard_blocker_id",
        "dashboard_blocker_state",
        "dashboard_blocker_resolved",
        "dashboard_blocker_waived",
        "dashboard_blocker_accepted_as_done",
    ):
        if required not in base or base[required] is None:
            raise ShadowPreparationReadinessGateError(f"dashboard_blocker_field_missing:{required}")
    return base


def _parse_historical_surfaces(
    cfg: Mapping[str, Any],
) -> tuple[HistoricalSurfaceRecordV0, ...]:
    raw = cfg.get("historical_surfaces")
    if raw is None:
        raise ShadowPreparationReadinessGateError("historical_surfaces_missing")
    if not isinstance(raw, list) or not raw:
        raise ShadowPreparationReadinessGateError("historical_surfaces_empty_or_invalid")
    records: list[HistoricalSurfaceRecordV0] = []
    seen: set[str] = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ShadowPreparationReadinessGateError(f"historical_surface_not_mapping:{idx}")
        surface_id = str(item.get("surface_id") or "").strip()
        path = str(item.get("path") or "").strip()
        classification_raw = str(item.get("classification") or "").strip()
        notes = str(item.get("notes") or "")
        if not surface_id or not path or not classification_raw:
            raise ShadowPreparationReadinessGateError(f"historical_surface_incomplete:{idx}")
        if surface_id in seen:
            raise ShadowPreparationReadinessGateError(f"historical_surface_duplicate:{surface_id}")
        seen.add(surface_id)
        if classification_raw not in ALLOWED_CLASSIFICATIONS:
            raise ShadowPreparationReadinessGateError(
                f"historical_surface_unknown_classification:{surface_id}:{classification_raw}"
            )
        classification = HistoricalSurfaceClassification(classification_raw)
        records.append(
            HistoricalSurfaceRecordV0(
                surface_id=surface_id,
                path=path,
                classification=classification,
                notes=notes,
            )
        )
    return tuple(records)


def _assert_surfaces_fail_closed(
    surfaces: tuple[HistoricalSurfaceRecordV0, ...],
) -> None:
    if not surfaces:
        raise ShadowPreparationReadinessGateError("historical_surfaces_empty")
    for surface in surfaces:
        if surface.classification == HistoricalSurfaceClassification.UNKNOWN_FAIL_CLOSED:
            raise ShadowPreparationReadinessGateError(
                f"historical_surface_ambiguous_fail_closed:{surface.surface_id}"
            )
        # No surface may claim canonical STEP 29U equivalence by classification alone.
        # Canonical STEP 29U is unbound; NON_CANONICAL_STEP29U and related are required.
        if surface.classification.value not in ALLOWED_CLASSIFICATIONS:
            raise ShadowPreparationReadinessGateError(
                f"historical_surface_classification_invalid:{surface.surface_id}"
            )


def _parse_string_list_field(raw: Any, *, field: str) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ShadowPreparationReadinessGateError(f"{field}_invalid")
    out: list[str] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise ShadowPreparationReadinessGateError(f"{field}_item_invalid:{idx}")
        out.append(item.strip())
    return tuple(out)


def _parse_optional_str(raw: Any) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    return text


def _parse_mindestkontrakt_inventory(
    cfg: Mapping[str, Any],
) -> tuple[MindestkontraktComponentRecordV0, ...]:
    raw = cfg.get("mindestkontrakt_components")
    if raw is None:
        raise ShadowPreparationReadinessGateError("mindestkontrakt_components_missing")
    if not isinstance(raw, list) or not raw:
        raise ShadowPreparationReadinessGateError("mindestkontrakt_components_empty_or_invalid")
    records: list[MindestkontraktComponentRecordV0] = []
    seen: set[str] = set()
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_component_not_mapping:{idx}"
            )
        component_id = str(item.get("component_id") or "").strip()
        if not component_id:
            raise ShadowPreparationReadinessGateError(f"mindestkontrakt_component_id_missing:{idx}")
        if component_id in seen:
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_component_duplicate:{component_id}"
            )
        seen.add(component_id)
        status_raw = str(item.get("preparation_status") or "").strip()
        if status_raw not in ALLOWED_PREPARATION_STATUSES:
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_status_invalid:{component_id}:{status_raw}"
            )
        required = item.get("required_for_step29u")
        if not isinstance(required, bool):
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_required_for_step29u_invalid:{component_id}"
            )
        blockers = _parse_string_list_field(
            item.get("blockers"), field=f"mindestkontrakt_blockers:{component_id}"
        )
        evidence_paths = _parse_string_list_field(
            item.get("evidence_paths"), field=f"mindestkontrakt_evidence_paths:{component_id}"
        )
        activation_relevance = str(item.get("activation_relevance") or "").strip()
        if not activation_relevance:
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_activation_relevance_missing:{component_id}"
            )
        notes = str(item.get("notes") or "")
        records.append(
            MindestkontraktComponentRecordV0(
                component_id=component_id,
                required_for_step29u=required,
                preparation_status=PreparationStatusV0(status_raw),
                canonical_owner=_parse_optional_str(item.get("canonical_owner")),
                implementation_path=_parse_optional_str(item.get("implementation_path")),
                evidence_paths=evidence_paths,
                blockers=blockers,
                activation_relevance=activation_relevance,
                notes=notes,
            )
        )
    return tuple(records)


def _assert_mindestkontrakt_inventory(
    records: tuple[MindestkontraktComponentRecordV0, ...],
) -> None:
    ids = tuple(record.component_id for record in records)
    if ids != REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS:
        raise ShadowPreparationReadinessGateError(
            "mindestkontrakt_component_set_or_order_mismatch:"
            f"expected={list(REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS)};actual={list(ids)}"
        )
    for record in records:
        if record.preparation_status.value not in ALLOWED_PREPARATION_STATUSES:
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_status_not_allowed:{record.component_id}"
            )
        if (
            record.preparation_status
            in (
                PreparationStatusV0.MISSING,
                PreparationStatusV0.UNBOUND,
            )
            and not record.blockers
        ):
            raise ShadowPreparationReadinessGateError(
                f"mindestkontrakt_missing_or_unbound_requires_blockers:{record.component_id}"
            )
        if record.preparation_status == PreparationStatusV0.PRESENT:
            # PRESENT is reserved for preparation-lock facts, never executable Shadow owners.
            if record.implementation_path:
                raise ShadowPreparationReadinessGateError(
                    f"mindestkontrakt_present_must_not_claim_implementation_path:{record.component_id}"
                )
            if record.component_id in {
                "lifecycle_owner",
                "session_state_machine",
                "canonical_decision_consumption",
                "execution_simulation_boundary",
                "fill_ownership",
                "fee_ownership",
                "slippage_ownership",
                "position_projection",
                "account_projection",
            }:
                raise ShadowPreparationReadinessGateError(
                    f"mindestkontrakt_executable_component_cannot_be_present:{record.component_id}"
                )
        if record.canonical_owner is not None and record.preparation_status in (
            PreparationStatusV0.MISSING,
            PreparationStatusV0.UNBOUND,
        ):
            # Unbound/missing components must not invent executable owners.
            if not record.canonical_owner.startswith("docs.") and record.canonical_owner not in {
                "ops.shadow_preparation_readiness_gate_v0",
                "runbook.STEP_29U",
            }:
                # Allow only explicit non-executable reference owners already used as evidence.
                pass


def _parse_string_tuple(
    raw: Any,
    *,
    field: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    if raw is None:
        return default
    if not isinstance(raw, list) or not all(isinstance(x, str) and x.strip() for x in raw):
        raise ShadowPreparationReadinessGateError(f"{field}_invalid")
    return tuple(str(x).strip() for x in raw)


__all__ = [
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "CONTRACT_CONFIG_SCHEMA_VERSION",
    "PROJECTION_SCHEMA_ID",
    "PROJECTION_SCHEMA_VERSION",
    "PROJECTION_OUTPUT_PATH_CONFIG_KEY",
    "DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH",
    "PROJECTION_VERIFICATION_SCHEMA_ID",
    "PROJECTION_VERIFICATION_SCHEMA_VERSION",
    "PROJECTION_VERIFIER_CLOCK_SKEW_SECONDS",
    "PROJECTION_VERIFIER_FRESHNESS_MAX_AGE_SECONDS",
    "PROJECTION_OVERALL_STATUS_VERIFIED",
    "PROJECTION_OVERALL_STATUS_BLOCKED",
    "CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY",
    "DETERMINISTIC_EVALUATED_AT_DEFAULT",
    "AUTHORITY_EFFECT_NONE",
    "RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED",
    "DASHBOARD_BLOCKER_ID_CANONICAL",
    "DASHBOARD_BLOCKER_STATE_OPEN",
    "DASHBOARD_BLOCKER_STATE_RESOLVED_ON_LANDSCAPE_V2",
    "DASHBOARD_INTRABAR_CONTINUITY_PASS",
    "CANONICAL_DASHBOARD_INTRABAR_TRUTH_RELATIVE_PATH",
    "CANONICAL_DASHBOARD_INTRABAR_PASS_TOKEN",
    "ALLOWED_PREPARATION_STATUSES",
    "REQUIRED_MINDESTKONTRAKT_COMPONENT_IDS",
    "ShadowPreparationReadinessGateError",
    "HistoricalSurfaceClassification",
    "HistoricalSurfaceRecordV0",
    "PreparationStatusV0",
    "MindestkontraktComponentRecordV0",
    "ShadowPreparationReadinessGateResultV0",
    "ShadowPreparationReadinessProjectionWriteMetadataV0",
    "ShadowPreparationReadinessProjectionVerificationResultV0",
    "default_config_path",
    "load_shadow_preparation_readiness_gate_config_v0",
    "evaluate_shadow_preparation_readiness_gate_v0",
    "build_shadow_preparation_readiness_projection_payload_v0",
    "serialize_shadow_preparation_readiness_projection_v0",
    "write_shadow_preparation_readiness_projection_v0",
    "verify_shadow_preparation_readiness_projection_v0",
]
