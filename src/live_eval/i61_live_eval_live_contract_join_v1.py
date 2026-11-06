"""EG-I82-JOIN U-I82-R15 — dormant I61 live-contract join registration.

Binds Package-N SHA256 IDENTITY onto validated I61 eval metrics / session-dir
payloads without rewriting Fill, CSV IO, or the eval CLI, without hooking
Cap 7.2 / src.execution, and without persistence, migration, or backfill.
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

CONTRACT_ID = "i61_live_eval_live_contract_join_v1"
I61_LIVE_CONTRACT_REGISTERED = True

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
_KNOWN_ENVELOPE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "metrics",
        "session",
        "session_id",
        "session_dir",
        "run_id",
        "campaign_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
        "historical_provenance",
    }
)
_FORBIDDEN_ENVELOPE_KEYS = frozenset(
    {
        "fills",
        "ts",
        "symbol",
        "side",
        "qty",
        "fill_price",
        "experiment_id",
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
    }
)
_LIVE_IDENTITY_SUBSTITUTE_KEYS = frozenset(
    {
        "experiment_identity_id",
        "experiment_id",
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
        "I65",
    }
)
_FILL_FIELD_KEYS = frozenset({"fills", "ts", "symbol", "side", "qty", "fill_price"})


class I61LiveEvalLiveContractJoinError(ValueError):
    """Fail-closed I61 live-contract join registration error."""


def _reject(message: str) -> None:
    raise I61LiveEvalLiveContractJoinError(message)


def is_i61_live_contract_registered() -> bool:
    """True iff the dormant I61 live-contract join surface is registered."""
    return I61_LIVE_CONTRACT_REGISTERED is True


def _looks_like_filesystem_path(value: str) -> bool:
    return "/" in value or "\\" in value


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
        _reject("implicit absence rejected: I61 live-contract IDENTITY is missing")
    identity = envelope.get("experiment_identity_id")
    if identity is None:
        _reject("implicit absence rejected: I61 live-contract IDENTITY is missing")
    if not isinstance(identity, str) or not is_package_n_sha256_canonical_id(identity):
        _reject(
            "noncanonical ID substitution rejected: experiment_identity_id must be Package-N SHA256"
        )
    return identity


def _snapshot_live_payload(raw: object, *, surface: str) -> dict[str, Any]:
    if raw is None:
        _reject(f"implicit absence rejected: I61 live surface {surface} is missing")
    if isinstance(raw, (list, tuple)):
        if not raw:
            _reject(f"implicit absence rejected: I61 live surface {surface} is missing")
        if len(raw) != 1:
            _reject(
                f"ambiguous join rejected: I61 live surface {surface} has multiple Package-N assignments"
            )
        return _snapshot_live_payload(raw[0], surface=surface)
    if not isinstance(raw, Mapping):
        _reject(f"malformed plane data rejected: I61 live surface {surface} is not an object")
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
    fill_fields = sorted(str(key) for key in payload.keys() if str(key) in _FILL_FIELD_KEYS)
    if fill_fields:
        _reject(
            f"cross-plane substitution rejected: I61 live surface {surface} carries {fill_fields[0]}"
        )


def _select_live_surface(envelope: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    present = [name for name in LIVE_CONTRACT_SURFACES if name in envelope]
    if not present:
        _reject("implicit absence rejected: I61 live contract surface is missing")
    if len(present) != 1:
        _reject("ambiguous join rejected: I61 live contract has multiple Package-N assignments")
    surface = present[0]
    return surface, _snapshot_live_payload(envelope[surface], surface=surface)


def _validate_metrics(payload: Mapping[str, Any]) -> dict[str, Any]:
    extra = sorted(
        str(key)
        for key in payload.keys()
        if str(key) not in _REQUIRED_METRICS_KEYS | _OPTIONAL_METRICS_KEYS
    )
    if extra:
        _reject(f"malformed plane data rejected: unknown I61 metrics field: {extra[0]}")
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
    extra = sorted(str(key) for key in payload.keys() if str(key) not in _SESSION_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I61 session field: {extra[0]}")
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


_SURFACE_VALIDATORS = {
    "metrics": _validate_metrics,
    "session": _validate_session,
}


def _join_payload(
    *,
    identity_id: str,
    live: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"experiment_identity_id": identity_id}
    live_dir = live.get("session_dir")
    envelope_dir = _optional_str(envelope, "session_dir")
    if envelope_dir is not None and live_dir and envelope_dir != live_dir:
        _reject("conflicting identity rejected: session_dir values disagree")
    if live_dir:
        payload["session_dir"] = live_dir
    elif envelope_dir is not None:
        payload["session_dir"] = envelope_dir
    for key in (
        "session_id",
        "run_id",
        "campaign_id",
        "legacy_alias_md5_12",
        "evidence_ref",
        "content_sha256",
    ):
        value = _optional_str(envelope, key)
        if value is not None:
            payload[key] = value
    provenance = envelope.get("historical_provenance")
    if provenance is not None:
        payload["historical_provenance"] = copy.deepcopy(provenance)
    return payload


def register_i61_live_contract_join_v1(
    live_join: Mapping[str, Any],
) -> CrossLaneIdentityJoinV1:
    """Register an I61 live-contract payload onto the Package-N SHA256 join path."""
    if not isinstance(live_join, Mapping):
        _reject("malformed plane data rejected: I61 live-contract envelope is not an object")
    snapshot = copy.deepcopy(dict(live_join))
    forbidden = sorted(str(key) for key in live_join.keys() if str(key) in _FORBIDDEN_ENVELOPE_KEYS)
    if forbidden:
        if forbidden[0] in {"I16", "I17", "I52", "I56", "I65"}:
            _reject(f"cross-lane substitution rejected: {forbidden[0]}")
        if forbidden[0] in {"plane_presence", "join_key"} | _FILL_FIELD_KEYS:
            _reject(f"cross-plane substitution rejected: {forbidden[0]}")
        _reject(f"noncanonical ID substitution rejected: {forbidden[0]}")
    extra = sorted(str(key) for key in live_join.keys() if str(key) not in _KNOWN_ENVELOPE_KEYS)
    if extra:
        _reject(f"malformed plane data rejected: unknown I61 live-contract field: {extra[0]}")

    identity_id = _require_identity(live_join)
    surface, live_payload = _select_live_surface(live_join)
    _reject_live_identity_substitution(live_payload, surface=surface)
    validated = _SURFACE_VALIDATORS[surface](live_payload)
    attachment = _join_payload(identity_id=identity_id, live=validated, envelope=live_join)
    try:
        record = attach_i61_live_eval_join_v1(attachment)
    except I61LiveEvalJoinAttachmentError as exc:
        message = str(exc)
        if "must not substitute" in message or "session-dir path is not" in message:
            _reject(f"cross-plane substitution rejected: {exc}")
        if "conflicting" in message:
            _reject(f"conflicting identity rejected: {exc}")
        raise I61LiveEvalLiveContractJoinError(
            f"I61 live-contract join rejected by R8 attachment: {exc}"
        ) from exc

    if dict(live_join) != snapshot:
        _reject("I61 live-contract envelope input was mutated")
    return record


__all__ = [
    "CONTRACT_ID",
    "CURRENT_EFFECTIVE_MAX_CONCURRENT_POSITIONS",
    "I61LiveEvalLiveContractJoinError",
    "I61_LIVE_CONTRACT_REGISTERED",
    "LIVE_CONTRACT_SURFACES",
    "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    "SECOND_EXECUTION_AUTHORITY_AUTHORIZED",
    "is_i61_live_contract_registered",
    "register_i61_live_contract_join_v1",
]
