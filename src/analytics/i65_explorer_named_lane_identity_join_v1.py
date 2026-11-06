"""EG-I82-JOIN U-I82-R23 — I65 named-lane IDENTITY join on explorer.

Attaches Package-N SHA256 IDENTITY onto the named I65 live contract
surfaces without rewriting ExperimentSummary, explorer lookups, or the
UUID run_id generator, without Cap 7.2 / src.execution, and without
persistence, migration, or backfill. Live experiment_id/run_id remain
RUN provenance and cannot fill IDENTITY. Historical rows stay readable.
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

CONTRACT_ID = "i65_explorer_named_lane_identity_join_v1"
I65_NAMED_LANE_IDENTITY_JOIN_REGISTERED = True

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
_FORBIDDEN_LIVE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "campaign_id",
        "session_id",
        "registry_run_id",
        "mlflow_run_id",
        "orders",
        "credentials",
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
    }
)
_FORBIDDEN_LIVE_CONTENT_KEYS = frozenset(
    {
        "payload",
        "raw",
        "raw_payload",
        "transcript",
        "secrets",
        "orders",
        "credentials",
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
_CROSS_LANE_KEYS = frozenset({"I16", "I17", "I52", "I56", "I61"})
_CROSS_PLANE_KEYS = frozenset(
    {
        "plane_presence",
        "join_key",
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


class I65ExplorerNamedLaneIdentityJoinError(ValueError):
    """Fail-closed I65 named-lane IDENTITY join error."""


def _reject(message: str) -> None:
    raise I65ExplorerNamedLaneIdentityJoinError(message)


def is_i65_named_lane_identity_join_registered() -> bool:
    """True iff the I65 named-lane IDENTITY join is registered on live I65 surfaces."""
    return I65_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def _optional_live_str(payload: Mapping[str, Any], key: str) -> str | None:
    if key not in payload:
        return None
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: I65 {key} is invalid")
    return value


def _require_identity(identity: object) -> str:
    if identity is None:
        _reject("implicit absence rejected: I65 named-lane IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _reject_sha256_as_legacy_id(value: str, *, label: str) -> None:
    if is_package_n_sha256_canonical_id(value):
        _reject(
            "noncanonical ID substitution rejected: "
            f"{label} must not be treated as Package-N SHA256"
        )


def _reject_forbidden_keys(payload: Mapping[str, Any], *, surface: str) -> None:
    keys = {str(key) for key in payload.keys()}
    forbidden = sorted(keys & _FORBIDDEN_LIVE_KEYS)
    if forbidden:
        if forbidden[0] in _CROSS_LANE_KEYS:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in _CROSS_PLANE_KEYS:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    content = sorted(keys & _FORBIDDEN_LIVE_CONTENT_KEYS)
    if content:
        if content[0] in _CROSS_PLANE_KEYS:
            _reject(f"cross-plane substitution rejected: {content[0]}")
        _reject(f"malformed plane data rejected: I65 live surface {surface} carries {content[0]}")
    allowed = (
        _REQUIRED_SUMMARY_KEYS | _OPTIONAL_SUMMARY_KEYS
        if surface == "summary"
        else _ROW_IDENTITY_KEYS | _OPTIONAL_ROW_RECORD_KEYS
    )
    extra = sorted(keys - allowed - _FORBIDDEN_LIVE_KEYS - _FORBIDDEN_LIVE_CONTENT_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I65 {surface} field: {extra[0]}")


def _extract_summary(live: Mapping[str, Any]) -> dict[str, Any]:
    missing = sorted(key for key in _REQUIRED_SUMMARY_KEYS if key not in live)
    if missing:
        _reject(f"malformed plane data rejected: I65 summary missing {missing[0]}")
    experiment_id = live["experiment_id"]
    if not isinstance(experiment_id, str) or not experiment_id.strip():
        _reject("malformed plane data rejected: I65 summary experiment_id is invalid")
    if experiment_id != experiment_id.strip():
        _reject("malformed plane data rejected: I65 summary experiment_id is invalid")
    _reject_sha256_as_legacy_id(experiment_id, label="summary.experiment_id")
    for required in ("run_type", "run_name"):
        value = live[required]
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            _reject(f"malformed plane data rejected: I65 summary {required} is invalid")
    if "tags" in live and live["tags"] is not None and not isinstance(live["tags"], list):
        _reject("malformed plane data rejected: I65 summary tags is not a list")
    if (
        "metrics" in live
        and live["metrics"] is not None
        and not isinstance(live["metrics"], Mapping)
    ):
        _reject("malformed plane data rejected: I65 summary metrics is not an object")
    if "params" in live and live["params"] is not None and not isinstance(live["params"], Mapping):
        _reject("malformed plane data rejected: I65 summary params is not an object")
    return {"run_id": experiment_id, "experiment_id": experiment_id}


def _extract_row(live: Mapping[str, Any]) -> dict[str, Any]:
    run_id = _optional_live_str(live, "run_id")
    experiment_id = _optional_live_str(live, "experiment_id")
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
    alias = _optional_live_str(live, "legacy_alias_md5_12")
    secondary = _optional_live_str(live, "legacy_experiment_id_md5_12")
    if alias is not None and secondary is not None and alias != secondary:
        _reject("conflicting identity rejected: MD5 alias fields disagree")
    if alias is not None:
        out["legacy_alias_md5_12"] = alias
    elif secondary is not None:
        out["legacy_alias_md5_12"] = secondary
    return out


def join_i65_named_lane_identity_v1(
    live: object,
    *,
    surface: str,
    experiment_identity_id: str | None = None,
    run_id: str | None = None,
    campaign_id: str | None = None,
    session_id: str | None = None,
    legacy_alias_md5_12: str | None = None,
    content_sha256: str | None = None,
    evidence_ref: str | None = None,
    historical_provenance: Mapping[str, Any] | None = None,
) -> CrossLaneIdentityJoinV1:
    """Join Package-N SHA256 IDENTITY onto a named I65 live contract payload.

    Does not mutate inputs and does not rewrite persisted I65 rows or ExperimentSummary.
    """
    if surface not in LIVE_CONTRACT_SURFACES:
        _reject(f"malformed plane data rejected: unknown I65 live surface {surface}")
    if isinstance(live, (list, tuple)):
        _reject("ambiguous join rejected: I65 live surface has multiple Package-N assignments")
    if not isinstance(live, Mapping):
        _reject("malformed plane data rejected: I65 live payload is not an object")
    snapshot = copy.deepcopy(dict(live))
    _reject_forbidden_keys(live, surface=surface)

    identity = _require_identity(experiment_identity_id)
    if run_id is not None:
        _reject("noncanonical ID substitution rejected: run_id")
    extracted = _extract_summary(live) if surface == "summary" else _extract_row(live)
    sidecar_campaign = _optional_sidecar(campaign_id, field="campaign_id")
    sidecar_session = _optional_sidecar(session_id, field="session_id")
    sidecar_alias = _optional_sidecar(legacy_alias_md5_12, field="legacy_alias_md5_12")
    sidecar_hash = _optional_sidecar(content_sha256, field="content_sha256")
    sidecar_evidence = _optional_sidecar(evidence_ref, field="evidence_ref")

    live_alias = extracted.get("legacy_alias_md5_12")
    if sidecar_alias is not None and live_alias and sidecar_alias != live_alias:
        _reject("conflicting identity rejected: ALIAS values disagree")

    payload: dict[str, Any] = {"experiment_identity_id": identity}
    if extracted.get("run_id") is not None:
        payload["run_id"] = extracted["run_id"]
    if extracted.get("experiment_id") is not None:
        payload["experiment_id"] = extracted["experiment_id"]
    if live_alias:
        payload["legacy_alias_md5_12"] = live_alias
    elif sidecar_alias is not None:
        payload["legacy_alias_md5_12"] = sidecar_alias
    if sidecar_campaign is not None:
        payload["campaign_id"] = sidecar_campaign
    if sidecar_session is not None:
        payload["session_id"] = sidecar_session
    if sidecar_hash is not None:
        payload["content_sha256"] = sidecar_hash
    if sidecar_evidence is not None:
        payload["evidence_ref"] = sidecar_evidence
    if historical_provenance is not None:
        if not isinstance(historical_provenance, Mapping):
            _reject("malformed plane data rejected: historical_provenance must be an object")
        provenance_copy = copy.deepcopy(dict(historical_provenance))
        nested = provenance_copy.get("experiment_identity_id")
        if nested is not None and nested != identity:
            _reject("conflicting identity rejected: historical_provenance.experiment_identity_id")
        payload["historical_provenance"] = provenance_copy

    try:
        record = attach_i65_explorer_join_v1(payload)
    except I65ExplorerJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I65ExplorerNamedLaneIdentityJoinError(
            f"I65 named-lane IDENTITY join rejected by R9 attachment: {exc}"
        ) from exc

    if dict(live) != snapshot:
        _reject("I65 live payload input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I65ExplorerNamedLaneIdentityJoinError",
    "I65_NAMED_LANE_IDENTITY_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i65_named_lane_identity_join_registered",
    "join_i65_named_lane_identity_v1",
]
