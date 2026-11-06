"""EG-I82-JOIN U-I82-R16 — dormant I65 live-contract join registration.

Binds Package-N SHA256 IDENTITY onto validated I65 ExperimentSummary /
historical registry-row payloads without rewriting explorer.py,
ExperimentSummary, or the UUID run_id generator, without hooking
Cap 7.2 / src.execution, and without persistence, migration, or backfill.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from src.analytics.i65_explorer_join_attachment_v1 import (
    I65ExplorerJoinAttachmentError,
    attach_i65_explorer_join_v1,
)
from src.experiments.cross_lane_identity_join_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)

CONTRACT_ID = "i65_explorer_live_contract_join_v1"
I65_LIVE_CONTRACT_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "summary",
    "row",
)

_REQUIRED_SUMMARY_KEYS = frozenset({"experiment_id", "run_type", "run_name"})
_OPTIONAL_SUMMARY_KEYS = frozenset(
    {
        "strategy_name",
        "sweep_name",
        "scan_name",
        "portfolio_name",
        "symbol",
        "tags",
        "created_at",
        "metrics",
        "params",
    }
)
_ROW_IDENTITY_KEYS = frozenset(
    {
        "run_id",
        "experiment_id",
        "legacy_alias_md5_12",
        "legacy_experiment_id_md5_12",
    }
)
_OPTIONAL_ROW_RECORD_KEYS = frozenset(
    {
        "run_type",
        "run_name",
        "timestamp",
        "strategy_key",
        "symbol",
        "portfolio_name",
        "sweep_name",
        "scan_name",
        "total_return",
        "cagr",
        "max_drawdown",
        "sharpe",
        "report_dir",
        "report_prefix",
        "params_json",
        "stats_json",
        "metadata_json",
        "tags",
    }
)
_KNOWN_ENVELOPE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "summary",
        "row",
        "experiment_id",
        "run_id",
        "campaign_id",
        "session_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
        "historical_provenance",
    }
)
_FORBIDDEN_ENVELOPE_KEYS = frozenset(
    {
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "registry_run_id",
        "mlflow_run_id",
        "orders",
        "credentials",
        "secrets",
        "payload",
        "raw",
        "raw_payload",
        "transcript",
        "promotion_authority",
        "apply_authority",
        "live_arming",
        "I16",
        "I17",
        "I52",
        "I56",
        "I61",
        "I65",
        "plane_presence",
        "join_key",
        "fills",
        "ts",
        "side",
        "qty",
        "fill_price",
    }
)
_LIVE_IDENTITY_SUBSTITUTE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "plane_presence",
        "join_key",
        "I16",
        "I17",
        "I52",
        "I56",
        "I61",
    }
)
_CROSS_PLANE_LIVE_KEYS = frozenset(
    {
        "fills",
        "ts",
        "side",
        "qty",
        "fill_price",
        "capsule_id",
        "total_fills",
        "session_dir",
    }
)


class I65ExplorerLiveContractJoinError(ValueError):
    """Fail-closed I65 live-contract join registration error."""


def _reject(message: str) -> None:
    raise I65ExplorerLiveContractJoinError(message)


def is_i65_live_contract_registered() -> bool:
    """True iff the dormant I65 live-contract join surface is registered."""
    return I65_LIVE_CONTRACT_REGISTERED is True


def _optional_str(payload: Mapping[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str):
        _reject(f"{key} must be a string when present")
    if not value.strip() or value != value.strip():
        _reject(f"{key} is present but empty or whitespace-padded")
    return value


def _require_identity(envelope: Mapping[str, Any]) -> str:
    if "experiment_identity_id" not in envelope:
        _reject("implicit absence rejected: I65 live-contract IDENTITY is missing")
    identity = envelope.get("experiment_identity_id")
    if identity is None:
        _reject("implicit absence rejected: I65 live-contract IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _snapshot_live_payload(raw: object, *, surface: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: I65 live surface {surface} is missing")
    if isinstance(raw, (list, tuple)):
        if not raw:
            _reject(f"implicit absence rejected: I65 live surface {surface} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: I65 live surface {surface} has multiple Package-N assignments"
            )
        return _snapshot_live_payload(raw[0], surface=surface)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: I65 live surface {surface} is not an object")
    return copy.deepcopy(dict(raw))


def _reject_live_identity_substitution(payload: Mapping[str, Any], *, surface: str) -> None:
    substitutes = sorted(
        str(key) for key in payload.keys() if str(key) in _LIVE_IDENTITY_SUBSTITUTE_KEYS
    )
    if substitutes:
        _reject(
            f"noncanonical ID substitution rejected: live surface {surface} uses {substitutes[0]} "
            "as Package-N identity"
        )
    cross_plane = sorted(str(key) for key in payload.keys() if str(key) in _CROSS_PLANE_LIVE_KEYS)
    if cross_plane:
        _reject(
            f"cross-plane substitution rejected: I65 live surface {surface} carries {cross_plane[0]}"
        )


def _select_live_surface(envelope: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    present = [name for name in LIVE_CONTRACT_SURFACES if name in envelope]
    if not present:
        _reject("implicit absence rejected: I65 live contract surface is missing")
    if len(present) != 1:
        _reject("ambiguous join rejected: I65 live contract has multiple Package-N assignments")
    surface = present[0]
    return surface, _snapshot_live_payload(envelope[surface], surface=surface)


def _reject_sha256_as_legacy_id(value: str, *, label: str) -> None:
    if is_package_n_sha256_canonical_id(value):
        _reject(
            f"noncanonical ID substitution rejected: {label} must not be treated as Package-N SHA256"
        )


def _validate_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    extra = sorted(
        str(key)
        for key in payload.keys()
        if str(key) not in _REQUIRED_SUMMARY_KEYS | _OPTIONAL_SUMMARY_KEYS
    )
    if extra:
        _reject(f"malformed plane data rejected: unknown I65 summary field: {extra[0]}")
    missing = sorted(key for key in _REQUIRED_SUMMARY_KEYS if key not in payload)
    if missing:
        _reject(f"malformed plane data rejected: I65 summary missing {missing[0]}")
    experiment_id = payload["experiment_id"]
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        _reject("malformed plane data rejected: I65 summary experiment_id is invalid")
    if experiment_id != experiment_id.strip():
        _reject("malformed plane data rejected: I65 summary experiment_id is invalid")
    _reject_sha256_as_legacy_id(experiment_id, label="summary.experiment_id")
    for required in ("run_type", "run_name"):
        value = payload[required]
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            _reject(f"malformed plane data rejected: I65 summary {required} is invalid")
    if "tags" in payload and payload["tags"] is not None and not isinstance(payload["tags"], list):
        _reject("malformed plane data rejected: I65 summary tags is not a list")
    if (
        "metrics" in payload
        and payload["metrics"] is not None
        and not isinstance(payload["metrics"], Mapping)
    ):
        _reject("malformed plane data rejected: I65 summary metrics is not an object")
    if (
        "params" in payload
        and payload["params"] is not None
        and not isinstance(payload["params"], Mapping)
    ):
        _reject("malformed plane data rejected: I65 summary params is not an object")
    return {"run_id": experiment_id, "experiment_id": experiment_id}


def _validate_row(payload: Mapping[str, Any]) -> dict[str, Any]:
    extra = sorted(
        str(key)
        for key in payload.keys()
        if str(key) not in _ROW_IDENTITY_KEYS | _OPTIONAL_ROW_RECORD_KEYS
    )
    if extra:
        _reject(f"malformed plane data rejected: unknown I65 row field: {extra[0]}")
    run_id = _optional_str(payload, "run_id")
    experiment_id = _optional_str(payload, "experiment_id")
    if run_id is None and experiment_id is None:
        _reject("implicit absence rejected: I65 row has no run_id or experiment_id")
    if run_id is not None:
        _reject_sha256_as_legacy_id(run_id, label="row.run_id")
    if experiment_id is not None:
        _reject_sha256_as_legacy_id(experiment_id, label="row.experiment_id")
    if run_id is not None and experiment_id is not None and run_id != experiment_id:
        _reject("conflicting identity rejected: row.experiment_id disagrees with row.run_id")
    out: dict[str, Any] = {}
    if run_id is not None:
        out["run_id"] = run_id
    if experiment_id is not None:
        out["experiment_id"] = experiment_id
    alias = _optional_str(payload, "legacy_alias_md5_12")
    secondary = _optional_str(payload, "legacy_experiment_id_md5_12")
    if alias is not None and secondary is not None and alias != secondary:
        _reject("conflicting identity rejected: MD5 alias fields disagree")
    if alias is not None:
        out["legacy_alias_md5_12"] = alias
    elif secondary is not None:
        out["legacy_alias_md5_12"] = secondary
    return out


_SURFACE_VALIDATORS = {
    "summary": _validate_summary,
    "row": _validate_row,
}


def _agree_optional(left: str | None, right: str | None, *, label: str) -> str | None:
    if left is not None and right is not None and left != right:
        _reject(f"conflicting identity rejected: {label} values disagree")
    return left if left is not None else right


def _join_payload(
    *,
    identity_id: str,
    live: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"experiment_identity_id": identity_id}
    run_id = _agree_optional(
        live.get("run_id") if isinstance(live.get("run_id"), str) else None,
        _optional_str(envelope, "run_id"),
        label="run_id",
    )
    experiment_id = _agree_optional(
        live.get("experiment_id") if isinstance(live.get("experiment_id"), str) else None,
        _optional_str(envelope, "experiment_id"),
        label="experiment_id",
    )
    alias = _agree_optional(
        live.get("legacy_alias_md5_12")
        if isinstance(live.get("legacy_alias_md5_12"), str)
        else None,
        _optional_str(envelope, "legacy_alias_md5_12"),
        label="legacy_alias_md5_12",
    )
    if run_id is not None:
        payload["run_id"] = run_id
    if experiment_id is not None:
        payload["experiment_id"] = experiment_id
    if alias is not None:
        payload["legacy_alias_md5_12"] = alias
    for key in ("campaign_id", "session_id", "evidence_ref", "content_sha256"):
        value = _optional_str(envelope, key)
        if value is not None:
            payload[key] = value
    provenance = envelope.get("historical_provenance")
    if provenance is not None:
        payload["historical_provenance"] = copy.deepcopy(provenance)
    return payload


def register_i65_live_contract_join_v1(
    live_join: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Register an I65 live-contract payload onto the Package-N SHA256 join path."""
    if not isinstance(live_join, Mapping):
        _reject("malformed plane data rejected: I65 live-contract envelope is not an object")
    snapshot = copy.deepcopy(dict(live_join))
    forbidden = sorted(str(key) for key in live_join.keys() if str(key) in _FORBIDDEN_ENVELOPE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I17", "I52", "I56", "I61"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"} | _CROSS_PLANE_LIVE_KEYS:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    extra = sorted(str(key) for key in live_join.keys() if str(key) not in _KNOWN_ENVELOPE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I65 live-contract field: {extra[0]}")

    identity_id = _require_identity(live_join)
    surface, live_payload = _select_live_surface(live_join)
    _reject_live_identity_substitution(live_payload, surface=surface)
    validated = _SURFACE_VALIDATORS[surface](live_payload)
    attachment = _join_payload(identity_id=identity_id, live=validated, envelope=live_join)
    try:
        record = attach_i65_explorer_join_v1(attachment)
    except I65ExplorerJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "field separation rejected" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I65ExplorerLiveContractJoinError(
            f"I65 live-contract join rejected by R9 attachment: {exc}"
        ) from exc

    if dict(live_join) != snapshot:
        _reject("I65 live-contract envelope input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I65ExplorerLiveContractJoinError",
    "I65_LIVE_CONTRACT_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i65_live_contract_registered",
    "register_i65_live_contract_join_v1",
]
