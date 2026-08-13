"""EG-I82-JOIN U-I82-R22 — I61 named-lane IDENTITY join on live session eval.

Attaches Package-N SHA256 IDENTITY onto the named I61 live contract
surfaces without rewriting Fill / CSV IO / eval CLI, without Cap 7.2 /
src.execution, and without persistence, migration, or backfill.
session_dir remains a filesystem hint and never fills SESSION or IDENTITY.
Fill trade fields stay off the join surface.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from src.experiments.cross_lane_identity_join_v1 import (
    CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SECOND_EXECUTION_AUTHORITY_AUTHORIZED,
    CrossLaneIdentityJoinV1,
    is_package_n_sha256_canonical_id,
)
from src.live_eval.i61_live_eval_join_attachment_v1 import (
    I61LiveEvalJoinAttachmentError,
    attach_i61_live_eval_join_v1,
)

CONTRACT_ID = "i61_live_eval_named_lane_identity_join_v1"
I61_NAMED_LANE_IDENTITY_JOIN_REGISTERED = True

LIVE_CONTRACT_SURFACES: tuple[str, ...] = (
    "metrics",
    "session",
)

_REQUIRED_METRICS_KEYS = frozenset(
    {
        "total_fills",
        "symbols",
        "start_ts",
        "end_ts",
        "total_notional",
        "total_qty",
        "vwap_overall",
        "side_breakdown",
        "realized_pnl_total",
        "realized_pnl_per_symbol",
    }
)
_OPTIONAL_METRICS_KEYS = frozenset({"vwap_per_symbol"})
_SESSION_KEYS = frozenset({"session_dir"})
_FORBIDDEN_LIVE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "experiment_id",
        "identity_id",
        "ref_id",
        "canonical_id",
        "canonical_identity_id",
        "package_n_sha256",
        "campaign_id",
        "run_id",
        "session_id",
        "legacy_alias_md5_12",
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
        "symbol",
        "side",
        "qty",
        "fill_price",
    }
)
_CROSS_LANE_KEYS = frozenset({"I16", "I17", "I52", "I56", "I65"})
_CROSS_PLANE_KEYS = frozenset(
    {
        "plane_presence",
        "join_key",
        "fills",
        "ts",
        "symbol",
        "side",
        "qty",
        "fill_price",
    }
)


class I61LiveEvalNamedLaneIdentityJoinError(ValueError):
    """Fail-closed I61 named-lane IDENTITY join error."""


def _reject(message: str) -> None:
    raise I61LiveEvalNamedLaneIdentityJoinError(message)


def is_i61_named_lane_identity_join_registered() -> bool:
    """True iff the I61 named-lane IDENTITY join is registered on live I61 surfaces."""
    return I61_NAMED_LANE_IDENTITY_JOIN_REGISTERED is True


def _looks_like_filesystem_path(value: str) -> bool:
    return "/" in value or "\\" in value


def _optional_sidecar(value: str | None, *, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        _reject(f"malformed plane data rejected: sidecar {field} is invalid")
    return value


def _require_identity(identity: object) -> str:
    if identity is None:
        _reject("implicit absence rejected: I61 named-lane IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


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
        _reject(f"malformed plane data rejected: I61 live surface {surface} carries {content[0]}")
    allowed = (
        _REQUIRED_METRICS_KEYS | _OPTIONAL_METRICS_KEYS if surface == "metrics" else _SESSION_KEYS
    )
    extra = sorted(keys - allowed - _FORBIDDEN_LIVE_KEYS - _FORBIDDEN_LIVE_CONTENT_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I61 {surface} field: {extra[0]}")


def _validate_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    missing = sorted(key for key in _REQUIRED_METRICS_KEYS if key not in payload)
    if missing:
        _reject(f"malformed plane data rejected: I61 metrics missing {missing[0]}")
    if not isinstance(payload["symbols"], list):
        _reject("malformed plane data rejected: I61 metrics symbols is not a list")
    breakdown = payload["side_breakdown"]
    if not isinstance(breakdown, Mapping):
        _reject("malformed plane data rejected: I61 metrics side_breakdown is not an object")
    for side in ("buy", "sell"):
        if side not in breakdown or not isinstance(breakdown[side], Mapping):
            _reject(f"malformed plane data rejected: I61 metrics side_breakdown missing {side}")
        stats = breakdown[side]
        for field in ("count", "qty", "notional"):
            if field not in stats:
                _reject(
                    f"malformed plane data rejected: I61 metrics side_breakdown.{side} missing {field}"
                )
    if not isinstance(payload["realized_pnl_per_symbol"], Mapping):
        _reject(
            "malformed plane data rejected: I61 metrics realized_pnl_per_symbol is not an object"
        )
    try:
        total_fills = int(payload["total_fills"])
    except (TypeError, ValueError) as exc:
        _reject(f"malformed plane data rejected: I61 metrics total_fills is invalid: {exc}")
    if total_fills < 0:
        _reject("malformed plane data rejected: I61 metrics total_fills is invalid")
    return {}


def _validate_session(payload: Mapping[str, Any]) -> dict[str, Any]:
    if "session_dir" not in payload:
        _reject("malformed plane data rejected: I61 session missing session_dir")
    session_dir = payload["session_dir"]
    if (
        not isinstance(session_dir, str)
        or not session_dir.strip()
        or session_dir != session_dir.strip()
    ):
        _reject("malformed plane data rejected: I61 session_dir is invalid")
    if not _looks_like_filesystem_path(session_dir):
        _reject("malformed plane data rejected: I61 session_dir is not a filesystem path")
    return {"session_dir": session_dir}


def _extract_live_fields(live: Mapping[str, Any], *, surface: str) -> dict[str, Any]:
    if surface == "session":
        return _validate_session(live)
    return _validate_metrics(live)


def join_i61_named_lane_identity_v1(
    live: object,
    *,
    surface: str,
    experiment_identity_id: str | None = None,
    run_id: str | None = None,
    campaign_id: str | None = None,
    session_id: str | None = None,
    session_dir: str | None = None,
    legacy_alias_md5_12: str | None = None,
    content_sha256: str | None = None,
    evidence_ref: str | None = None,
    historical_provenance: Mapping[str, Any] | None = None,
) -> CrossLaneIdentityJoinV1:
    """Join Package-N SHA256 IDENTITY onto a named I61 live contract payload.

    Does not mutate inputs and does not rewrite Fill, CSV IO, or the eval CLI.
    """
    if surface not in LIVE_CONTRACT_SURFACES:
        _reject(f"malformed plane data rejected: unknown I61 live surface {surface}")
    if isinstance(live, (list, tuple)):
        _reject("ambiguous join rejected: I61 live surface has multiple Package-N assignments")
    if not isinstance(live, Mapping):
        _reject("malformed plane data rejected: I61 live payload is not an object")
    snapshot = copy.deepcopy(dict(live))
    _reject_forbidden_keys(live, surface=surface)

    identity = _require_identity(experiment_identity_id)
    extracted = _extract_live_fields(live, surface=surface)
    sidecar_run = _optional_sidecar(run_id, field="run_id")
    sidecar_campaign = _optional_sidecar(campaign_id, field="campaign_id")
    sidecar_session = _optional_sidecar(session_id, field="session_id")
    sidecar_dir = _optional_sidecar(session_dir, field="session_dir")
    sidecar_alias = _optional_sidecar(legacy_alias_md5_12, field="legacy_alias_md5_12")
    sidecar_hash = _optional_sidecar(content_sha256, field="content_sha256")
    sidecar_evidence = _optional_sidecar(evidence_ref, field="evidence_ref")
    if sidecar_dir is not None and not _looks_like_filesystem_path(sidecar_dir):
        _reject("malformed plane data rejected: I61 session_dir is not a filesystem path")

    live_dir = extracted.get("session_dir")
    if sidecar_dir is not None and live_dir and sidecar_dir != live_dir:
        _reject("conflicting identity rejected: session_dir values disagree")

    payload: dict[str, Any] = {"experiment_identity_id": identity}
    if live_dir:
        payload["session_dir"] = live_dir
    elif sidecar_dir is not None:
        payload["session_dir"] = sidecar_dir
    if sidecar_run is not None:
        payload["run_id"] = sidecar_run
    if sidecar_campaign is not None:
        payload["campaign_id"] = sidecar_campaign
    if sidecar_session is not None:
        payload["session_id"] = sidecar_session
    if sidecar_alias is not None:
        payload["legacy_alias_md5_12"] = sidecar_alias
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
        record = attach_i61_live_eval_join_v1(payload)
    except I61LiveEvalJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message or "session-dir path is not" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        if "Package-N SHA256" in message or "must not be UUID" in message:
            _reject(f"noncanonical ID substitution rejected: {exc}")
        raise I61LiveEvalNamedLaneIdentityJoinError(
            f"I61 named-lane IDENTITY join rejected by R8 attachment: {exc}"
        ) from exc

    if dict(live) != snapshot:
        _reject("I61 live payload input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I61LiveEvalNamedLaneIdentityJoinError",
    "I61_NAMED_LANE_IDENTITY_JOIN_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i61_named_lane_identity_join_registered",
    "join_i61_named_lane_identity_v1",
]
