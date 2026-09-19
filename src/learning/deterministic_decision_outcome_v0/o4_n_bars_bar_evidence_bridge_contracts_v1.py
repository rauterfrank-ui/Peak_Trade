"""O4→DDO N_BARS bar evidence bridge contracts v1 (translate/bind only).

Does not mint evaluation information sets, actual_outcome_ref, or supplier_input.
Does not import src.ops.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    require_event_time_utc,
    require_mapping,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    compute_content_hash_v0,
)

O4_N_BARS_BAR_EVIDENCE_BRIDGE_ID: Final[str] = (
    "peak_trade.learning.ddo.o4_n_bars_bar_evidence_bridge_v1"
)

O4_SNAPSHOT_SCHEMA_NAME: Final[str] = "o4_n_bars_bar_evidence_snapshot"
O4_SNAPSHOT_SCHEMA_VERSION: Final[str] = "o4_n_bars_bar_evidence_snapshot_v1"
BRIDGE_TRANSLATION_SCHEMA_NAME: Final[str] = "ddo_n_bars_bridge_translation"
BRIDGE_TRANSLATION_SCHEMA_VERSION: Final[str] = "ddo_n_bars_bridge_translation_v1"

O4_STATE_FINALIZED: Final[str] = "FINALIZED_BAR"
O4_STATE_CORRECTED: Final[str] = "CORRECTED_BAR"
O4_STATE_MISSING: Final[str] = "MISSING_BAR"
O4_STATE_STALE: Final[str] = "STALE_BAR"
O4_STATE_IN_PROGRESS: Final[str] = "IN_PROGRESS_BAR"

CHAIN_GAPLESS_FINALIZED: Final[str] = "GAPLESS_FINALIZED"
CHAIN_INCOMPLETE: Final[str] = "INCOMPLETE"

O4_BAR_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "canonical_instrument_id",
        "venue_instrument_id",
        "venue",
        "interval",
        "bar_open_time",
        "bar_close_time",
        "finalization_state",
        "quality_state",
        "last_observation_identity",
        "session_id",
        "repository_sha",
        "config_digest",
        "close",
        "revision",
    }
)

_INTERVAL_SECONDS: Final[dict[str, int]] = {
    "PT1H": 3600,
    "1H": 3600,
}


def _require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DdoValidationError(f"INVALID_POSITIVE_INT:{field}")
    if value <= 0:
        raise DdoValidationError(f"N_BARS_MUST_BE_POSITIVE:{field}")
    return value


def _normalize_o4_interval_id(raw: str) -> tuple[str, int]:
    token = str(raw or "").strip().upper()
    if token in {"PT1H", "1H", "60M"}:
        token = "PT1H"
    duration = _INTERVAL_SECONDS.get(token)
    if duration is None:
        raise DdoValidationError(f"UNSUPPORTED_O4_INTERVAL:{raw}")
    return token, duration


def unix_seconds_to_event_time_utc(value: Any, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DdoValidationError(f"INVALID_UNIX_TIME:{field}")
    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0:
        raise DdoValidationError(f"INVALID_UNIX_TIME:{field}")
    whole = int(seconds)
    micro = int(round((seconds - whole) * 1_000_000))
    if micro >= 1_000_000:
        whole += 1
        micro = 0
    dt = datetime.fromtimestamp(whole, tz=timezone.utc).replace(microsecond=micro)
    text = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if micro:
        text += f".{micro:06d}".rstrip("0").rstrip(".")
    text += "Z"
    require_event_time_utc(text, field)
    return text


def _hash_safe_json_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".12g")
    if isinstance(value, Mapping):
        return {str(k): _hash_safe_json_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_hash_safe_json_value(v) for v in value]
    if isinstance(value, tuple):
        return [_hash_safe_json_value(v) for v in value]
    return value


def mint_ddo_content_ref_v1(*, prefix: str, payload: Mapping[str, Any]) -> str:
    digest = compute_content_hash_v0(_hash_safe_json_value(dict(payload)))
    ref = f"{prefix}{digest}"
    if len(ref) > 128:
        raise DdoValidationError("MINTED_REF_TOO_LONG")
    if len(ref) < 8:
        raise DdoValidationError("MINTED_REF_TOO_SHORT")
    return ref


def validate_o4_bar_snapshot_element_v1(raw: Any, index: int) -> Mapping[str, Any]:
    bar = require_mapping(raw, f"o4_bars[{index}]")
    missing = sorted(O4_BAR_REQUIRED_FIELDS - set(bar.keys()))
    if missing:
        raise DdoValidationError(f"O4_BAR_MISSING_FIELDS:{index}:{missing}")
    identity = bar.get("last_observation_identity")
    if not isinstance(identity, Mapping):
        raise DdoValidationError(f"O4_BAR_INVALID_OBSERVATION_IDENTITY:{index}")
    return bar


def validate_o4_n_bars_bar_evidence_snapshot_v1(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "o4_n_bars_bar_evidence_snapshot")
    if raw.get("schema_name") != O4_SNAPSHOT_SCHEMA_NAME:
        raise DdoValidationError("O4_SNAPSHOT_SCHEMA_NAME_MISMATCH")
    if raw.get("schema_version") != O4_SNAPSHOT_SCHEMA_VERSION:
        raise DdoValidationError("O4_SNAPSHOT_SCHEMA_VERSION_MISMATCH")
    decision_event_ref = raw.get("decision_event_ref")
    if not isinstance(decision_event_ref, str) or not decision_event_ref.strip():
        raise DdoValidationError("O4_SNAPSHOT_DECISION_EVENT_REF_REQUIRED")
    horizon_start = require_event_time_utc(
        raw.get("horizon_start_time_utc"), "horizon_start_time_utc"
    )
    n_bars = _require_positive_int(raw.get("n_bars"), "n_bars")
    interval_token, _duration = _normalize_o4_interval_id(str(raw.get("o4_interval_id")))
    bars_raw = raw.get("o4_bars")
    if not isinstance(bars_raw, (list, tuple)):
        raise DdoValidationError("O4_BARS_MUST_BE_LIST")
    if len(bars_raw) != n_bars:
        raise DdoValidationError("O4_BARS_COUNT_MISMATCH")
    bars = tuple(validate_o4_bar_snapshot_element_v1(item, i) for i, item in enumerate(bars_raw))
    return MappingProxyType(
        {
            "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
            "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
            "decision_event_ref": decision_event_ref.strip(),
            "horizon_start_time_utc": horizon_start,
            "n_bars": n_bars,
            "o4_interval_id": interval_token,
            "o4_bars": bars,
        }
    )


@dataclass(frozen=True)
class DdoNbarsBridgeTranslationV1:
    schema_name: str
    schema_version: str
    decision_event_ref: str
    horizon_start_time_utc: str
    n_bars: int
    instrument_ref: str
    bar_spec_ref: str
    bar_close_times_utc: tuple[str, ...]
    bar_identity_refs: tuple[str, ...]
    chain_completeness: str
    horizon_observation_status: str
    horizon_observation_reason: str | None
    o4_provenance: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "decision_event_ref": self.decision_event_ref,
            "horizon_start_time_utc": self.horizon_start_time_utc,
            "n_bars": self.n_bars,
            "instrument_ref": self.instrument_ref,
            "bar_spec_ref": self.bar_spec_ref,
            "bar_close_times_utc": list(self.bar_close_times_utc),
            "bar_identity_refs": list(self.bar_identity_refs),
            "chain_completeness": self.chain_completeness,
            "horizon_observation_status": self.horizon_observation_status,
            "horizon_observation_reason": self.horizon_observation_reason,
            "o4_provenance": dict(self.o4_provenance),
        }


def _bar_state_token(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise DdoValidationError("O4_BAR_STATE_REQUIRED")
    token = raw.strip().upper()
    aliases = {
        "FINALIZED": O4_STATE_FINALIZED,
        "FINALIZED_BAR": O4_STATE_FINALIZED,
        "CORRECTED": O4_STATE_CORRECTED,
        "CORRECTED_BAR": O4_STATE_CORRECTED,
        "MISSING": O4_STATE_MISSING,
        "MISSING_BAR": O4_STATE_MISSING,
        "STALE": O4_STATE_STALE,
        "STALE_BAR": O4_STATE_STALE,
        "IN_PROGRESS": O4_STATE_IN_PROGRESS,
        "IN_PROGRESS_BAR": O4_STATE_IN_PROGRESS,
    }
    if token not in aliases:
        raise DdoValidationError(f"UNKNOWN_O4_BAR_STATE:{raw}")
    return aliases[token]


def _provenance_from_bars(bars: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    first = bars[0]
    session_id = str(first["session_id"])
    repository_sha = str(first["repository_sha"])
    config_digest = str(first["config_digest"])
    for index, bar in enumerate(bars[1:], start=1):
        if str(bar["session_id"]) != session_id:
            raise DdoValidationError(f"O4_PROVENANCE_SESSION_MISMATCH:{index}")
        if str(bar["repository_sha"]) != repository_sha:
            raise DdoValidationError(f"O4_PROVENANCE_REPOSITORY_SHA_MISMATCH:{index}")
        if str(bar["config_digest"]) != config_digest:
            raise DdoValidationError(f"O4_PROVENANCE_CONFIG_DIGEST_MISMATCH:{index}")
    return {
        "session_id": session_id,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
    }


def translate_o4_snapshot_to_ddo_n_bars_bindings_v1(
    snapshot: Mapping[str, Any],
) -> DdoNbarsBridgeTranslationV1:
    """Translate validated O4 snapshot into DDO field bindings (no REAL minting)."""
    validated = validate_o4_n_bars_bar_evidence_snapshot_v1(snapshot)
    bars_list = sorted(
        validated["o4_bars"],
        key=lambda item: float(item["bar_open_time"]),
    )
    n_bars = validated["n_bars"]
    interval_token, duration = _normalize_o4_interval_id(validated["o4_interval_id"])
    horizon_start = validated["horizon_start_time_utc"]

    first_bar = bars_list[0]
    instrument_ref = mint_ddo_content_ref_v1(
        prefix="ddo.o4.inst.",
        payload={
            "canonical_instrument_id": str(first_bar["canonical_instrument_id"]),
            "venue": str(first_bar["venue"]),
            "venue_instrument_id": str(first_bar["venue_instrument_id"]),
        },
    )
    bar_spec_ref = mint_ddo_content_ref_v1(
        prefix="ddo.o4.barspec.",
        payload={"o4_interval_id": interval_token},
    )

    for bar in bars_list:
        expected_inst = str(first_bar["canonical_instrument_id"])
        if str(bar["canonical_instrument_id"]) != expected_inst:
            raise DdoValidationError("O4_BAR_INSTRUMENT_MISMATCH")

    status = "OK"
    reason: str | None = None
    chain = CHAIN_INCOMPLETE

    for bar in bars_list:
        fin = _bar_state_token(bar.get("finalization_state"))
        qual = _bar_state_token(bar.get("quality_state"))
        if fin == O4_STATE_MISSING or qual == O4_STATE_MISSING:
            status = "MISSING"
            reason = "O4_MISSING_BAR"
            break
        if fin == O4_STATE_STALE or qual == O4_STATE_STALE:
            status = "STALE"
            reason = "O4_STALE_BAR"
            break
        if fin == O4_STATE_IN_PROGRESS:
            status = "PARTIAL"
            reason = "O4_IN_PROGRESS_BAR"
            break

    bar_close_times: list[str] = []
    bar_identities: list[str] = []
    if status == "OK":
        for index, bar in enumerate(bars_list):
            fin = _bar_state_token(bar.get("finalization_state"))
            if fin not in {O4_STATE_FINALIZED, O4_STATE_CORRECTED}:
                status = "PARTIAL"
                reason = "O4_BAR_NOT_FINALIZED"
                break
            open_t = float(bar["bar_open_time"])
            close_t = float(bar["bar_close_time"])
            if close_t - open_t != float(duration):
                status = "GAP"
                reason = "O4_BAR_WINDOW_DURATION_MISMATCH"
                break
            if index > 0:
                prev_open = float(bars_list[index - 1]["bar_open_time"])
                if open_t != prev_open + float(duration):
                    status = "GAP"
                    reason = "O4_BAR_OPEN_GRID_GAP"
                    break
            close_utc = unix_seconds_to_event_time_utc(close_t, f"bar_close[{index}]")
            bar_close_times.append(close_utc)
            bar_identities.append(
                mint_ddo_content_ref_v1(
                    prefix="ddo.o4.bar.",
                    payload={
                        "canonical_instrument_id": str(bar["canonical_instrument_id"]),
                        "interval": str(bar["interval"]),
                        "bar_open_time": format(open_t, ".12g"),
                        "revision": int(bar["revision"]),
                    },
                )
            )
        if status == "OK" and bar_close_times:
            if bar_close_times[0] < horizon_start:
                status = "GAP"
                reason = "HORIZON_START_AFTER_FIRST_BAR_CLOSE"
            elif len(bar_close_times) == n_bars:
                chain = CHAIN_GAPLESS_FINALIZED
            else:
                status = "GAP"
                reason = "BAR_CLOSE_COUNT_MISMATCH"

    if status != "OK":
        chain = CHAIN_INCOMPLETE

    provenance = _provenance_from_bars(bars_list)

    return DdoNbarsBridgeTranslationV1(
        schema_name=BRIDGE_TRANSLATION_SCHEMA_NAME,
        schema_version=BRIDGE_TRANSLATION_SCHEMA_VERSION,
        decision_event_ref=str(validated["decision_event_ref"]),
        horizon_start_time_utc=horizon_start,
        n_bars=n_bars,
        instrument_ref=instrument_ref,
        bar_spec_ref=bar_spec_ref,
        bar_close_times_utc=tuple(bar_close_times),
        bar_identity_refs=tuple(bar_identities),
        chain_completeness=chain,
        horizon_observation_status=status if chain != CHAIN_GAPLESS_FINALIZED else "OK",
        horizon_observation_reason=reason,
        o4_provenance=MappingProxyType(provenance),
    )
