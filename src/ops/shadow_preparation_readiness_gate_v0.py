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
- performs no network I/O and starts no scheduler/worker/process.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
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

# Deterministic evaluation timestamp convention for pure offline contracts:
# callers may override; default is a fixed epoch sentinel (no wall-clock).
DETERMINISTIC_EVALUATED_AT_DEFAULT = "1970-01-01T00:00:00Z"

AUTHORITY_EFFECT_NONE: Literal["NONE"] = "NONE"
RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED = "BOUND_NOT_ACTIVATED"
DASHBOARD_BLOCKER_ID_CANONICAL = "MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY"
DASHBOARD_BLOCKER_STATE_OPEN = "OPEN"

DEFAULT_CONFIG_RELATIVE_PATH = Path("config/ops/shadow_preparation_readiness_gate_v0.toml")

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
        return payload


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
    root = repo_root if repo_root is not None else _infer_repo_root()
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

    dashboard = _resolve_dashboard_blocker(cfg, dashboard_blocker_overrides)
    if dashboard["dashboard_blocker_id"] != DASHBOARD_BLOCKER_ID_CANONICAL:
        raise ShadowPreparationReadinessGateError(
            f"dashboard_blocker_id_mismatch:{dashboard['dashboard_blocker_id']!r}"
        )
    if dashboard["dashboard_blocker_state"] != DASHBOARD_BLOCKER_STATE_OPEN:
        raise ShadowPreparationReadinessGateError(
            f"dashboard_blocker_state_must_be_open:{dashboard['dashboard_blocker_state']!r}"
        )
    if dashboard["dashboard_blocker_resolved"] is True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_resolved_rejected")
    if dashboard["dashboard_blocker_waived"] is True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_waived_rejected")
    if dashboard["dashboard_blocker_accepted_as_done"] is True:
        raise ShadowPreparationReadinessGateError("dashboard_blocker_accepted_as_done_rejected")

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

    canonical_refs = cfg.get("known_canonical_authority_identifiers") or []
    if not isinstance(canonical_refs, list) or not canonical_refs:
        raise ShadowPreparationReadinessGateError(
            "required_canonical_reference_missing:known_canonical_authority_identifiers"
        )

    required_gates = _parse_string_tuple(
        cfg.get("required_preparation_gates"),
        field="required_preparation_gates",
        default=REQUIRED_PREPARATION_GATE_DEFAULTS,
    )

    unmet = list(required_gates)
    blockers = [
        "CANONICAL_STEP_29U_ABSENT",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL_BLOCKED",
        "DASHBOARD_BLOCKER_OPEN:MARKET_DASHBOARD_VISIBLE_INTRABAR_CONTINUITY",
        "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED",
        "HISTORICAL_SHADOW_SURFACES_NON_EQUIVALENT_TO_STEP_29U",
        "NO_ACTIVATION_AUTHORIZED",
    ]

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
        canonical_shadow_mode_exists=False,
        canonical_step_29u_bound=False,
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
        dashboard_blocker_state=DASHBOARD_BLOCKER_STATE_OPEN,
        dashboard_blocker_resolved=False,
        dashboard_blocker_waived=False,
        dashboard_blocker_accepted_as_done=False,
        historical_surface_classifications=surfaces,
        required_preparation_gates=required_gates,
        unmet_gates=tuple(unmet),
        blockers=tuple(blockers),
        next_permitted_action=next_action,
    )


def _infer_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


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
    if doc.get("dashboard_blocker_state") not in (None, DASHBOARD_BLOCKER_STATE_OPEN):
        if doc.get("dashboard_blocker_state") != DASHBOARD_BLOCKER_STATE_OPEN:
            raise ShadowPreparationReadinessGateError(
                f"config_dashboard_blocker_state_invalid:{doc.get('dashboard_blocker_state')!r}"
            )
    for bad in (
        "dashboard_blocker_resolved",
        "dashboard_blocker_waived",
        "dashboard_blocker_accepted_as_done",
    ):
        if doc.get(bad) is True:
            raise ShadowPreparationReadinessGateError(f"config_{bad}_true_rejected")


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
            cfg.get("dashboard_blocker_state") or DASHBOARD_BLOCKER_STATE_OPEN
        ),
        "dashboard_blocker_resolved": bool(cfg.get("dashboard_blocker_resolved", False)),
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
    "DETERMINISTIC_EVALUATED_AT_DEFAULT",
    "AUTHORITY_EFFECT_NONE",
    "RUNTIME_BRIDGE_STATE_BOUND_NOT_ACTIVATED",
    "DASHBOARD_BLOCKER_ID_CANONICAL",
    "DASHBOARD_BLOCKER_STATE_OPEN",
    "ShadowPreparationReadinessGateError",
    "HistoricalSurfaceClassification",
    "HistoricalSurfaceRecordV0",
    "ShadowPreparationReadinessGateResultV0",
    "default_config_path",
    "load_shadow_preparation_readiness_gate_config_v0",
    "evaluate_shadow_preparation_readiness_gate_v0",
]
