"""S03 evidence schema writers (campaign-bound; never mutates S01/S02)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_SESSION_ID,
    BOUND_SESSION_LABEL,
    COUNTERFACTUAL_RUNTIME_IS_NON_AUTHORITY,
    DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME,
    EVIDENCE_CAMPAIGN_ROOT_REL,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    S01_SESSION_ID,
    S02_SESSION_ID,
    S03_CONNECTIVITY_FILENAME,
    S03_COUNTERFACTUAL_FILENAME,
    S03_DECISION_SENSITIVITY_FILENAME,
    S03_DRIFT_FILENAME,
    S03_EXIT_RISK_SAFETY_FILENAME,
    S03_HEARTBEAT_FILENAME,
    S03_INTEGRITY_MANIFEST_FILENAME,
    S03_MARKET_SAMPLES_FILENAME,
    S03_METADATA_FILENAME,
    S03_SESSIONS_REL,
    S03_TERMINAL_VERDICT_FILENAME,
    S03_VOLATILITY_FILENAME,
    SCHEMA_COUNTERFACTUAL,
    SCHEMA_DECISION_SENSITIVITY,
    SCHEMA_DRIFT,
    SCHEMA_HEARTBEAT,
    SCHEMA_MARKET_SAMPLE,
    SCHEMA_SESSION_METADATA,
    SCHEMA_VOLATILITY,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    MarketSampleV1,
    S03ScopeBindingsV1,
    sha256_hex_canonical,
)


def resolve_s03_session_dir_v1(*, evidence_root: Path) -> Path:
    root = Path(evidence_root)
    session_dir = root / S03_SESSIONS_REL
    # Refuse paths that escape the additional-evidence campaign root.
    campaign_root = (root / EVIDENCE_CAMPAIGN_ROOT_REL).resolve()
    if not str(session_dir.resolve()).startswith(str(campaign_root)):
        raise AdditionalEvidenceS03SessionExecutionOwnerError("evidence_path_outside_s03_root")
    return session_dir


def assert_not_s01_s02_path_v1(path: Path) -> None:
    text = str(path)
    if EXISTING_EXHAUSTED_CAMPAIGN_ID in text and BOUND_CAMPAIGN_ID not in text:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("s01_s02_evidence_path_forbidden")
    if S01_SESSION_ID in text or S02_SESSION_ID in text:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("s01_s02_evidence_path_forbidden")


def _common_bindings(bindings: S03ScopeBindingsV1) -> dict[str, Any]:
    return bindings.to_dict()


def write_json_v1(path: Path, payload: Mapping[str, Any]) -> None:
    assert_not_s01_s02_path_v1(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def append_jsonl_v1(path: Path, payload: Mapping[str, Any]) -> None:
    assert_not_s01_s02_path_v1(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(payload), sort_keys=True, separators=(",", ":")) + "\n")


def build_session_metadata_v1(
    *,
    bindings: S03ScopeBindingsV1,
    mode: str,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA_SESSION_METADATA,
        **_common_bindings(bindings),
        "session_label": BOUND_SESSION_LABEL,
        "mode": mode,
        "campaign_id": BOUND_CAMPAIGN_ID,
        "session_id": BOUND_SESSION_ID,
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_heartbeat_v1(
    *,
    bindings: S03ScopeBindingsV1,
    monotonic_elapsed_seconds: float,
    receive_time_unix_seconds: float,
    seq: int,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA_HEARTBEAT,
        **_common_bindings(bindings),
        "seq": int(seq),
        "monotonic_elapsed_seconds": float(monotonic_elapsed_seconds),
        "receive_time": float(receive_time_unix_seconds),
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_market_sample_record_v1(
    *,
    bindings: S03ScopeBindingsV1,
    sample: MarketSampleV1,
    duplicate: bool,
    out_of_order: bool,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA_MARKET_SAMPLE,
        **_common_bindings(bindings),
        **sample.to_dict(),
        "event_time": float(sample.event_time_unix_seconds),
        "receive_time": float(sample.receive_time_unix_seconds),
        "duplicate": bool(duplicate),
        "out_of_order": bool(out_of_order),
        "DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME": (
            DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME
        ),
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_volatility_record_v1(
    *,
    bindings: S03ScopeBindingsV1,
    monotonic_elapsed_seconds: float,
    receive_time_unix_seconds: float,
    old_volatility: float,
    old_age_seconds: int,
    old_as_of_event_time: float,
    estimator: str,
    unit: str,
    horizon: str,
    annualized: bool,
    observation_count: int,
    source_digest: str,
    fresh_volatility: float,
    recomputation_input_digest: str,
    consuming_decision_context: str,
) -> dict[str, Any]:
    abs_drift = abs(float(fresh_volatility) - float(old_volatility))
    rel_drift: Optional[float]
    if float(old_volatility) == 0.0:
        rel_drift = None
    else:
        rel_drift = abs_drift / abs(float(old_volatility))
    payload = {
        "schema": SCHEMA_VOLATILITY,
        **_common_bindings(bindings),
        "monotonic_elapsed_seconds": float(monotonic_elapsed_seconds),
        "receive_time": float(receive_time_unix_seconds),
        "event_time": float(old_as_of_event_time),
        "old_volatility_value": float(old_volatility),
        "old_volatility_age_seconds": int(old_age_seconds),
        "old_volatility_as_of_event_time": float(old_as_of_event_time),
        "estimator": estimator,
        "unit": unit,
        "horizon": horizon,
        "annualized": bool(annualized),
        "observation_count": int(observation_count),
        "source_digest": source_digest,
        "fresh_recomputed_volatility": float(fresh_volatility),
        "recomputation_input_digest": recomputation_input_digest,
        "drift_absolute": abs_drift,
        "drift_relative": rel_drift,
        "consuming_decision_context": consuming_decision_context,
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_drift_comparison_v1(
    *,
    bindings: S03ScopeBindingsV1,
    volatility_record: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA_DRIFT,
        **_common_bindings(bindings),
        "volatility_record_digest": volatility_record.get("record_digest"),
        "drift_absolute": volatility_record.get("drift_absolute"),
        "drift_relative": volatility_record.get("drift_relative"),
        "old_volatility_value": volatility_record.get("old_volatility_value"),
        "fresh_recomputed_volatility": volatility_record.get("fresh_recomputed_volatility"),
        "monotonic_elapsed_seconds": volatility_record.get("monotonic_elapsed_seconds"),
        "receive_time": volatility_record.get("receive_time"),
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_decision_sensitivity_v1(
    *,
    bindings: S03ScopeBindingsV1,
    other_inputs_digest: str,
    old_decision: str,
    fresh_counterfactual_decision: str,
    monotonic_elapsed_seconds: float,
    receive_time_unix_seconds: float,
) -> dict[str, Any]:
    age_only = old_decision != fresh_counterfactual_decision
    payload = {
        "schema": SCHEMA_DECISION_SENSITIVITY,
        **_common_bindings(bindings),
        "other_inputs_digest": other_inputs_digest,
        "old_volatility_decision": old_decision,
        "fresh_volatility_counterfactual_decision": fresh_counterfactual_decision,
        "AGE_ONLY_DECISION_CHANGE": bool(age_only),
        "comparable": True,
        "monotonic_elapsed_seconds": float(monotonic_elapsed_seconds),
        "receive_time": float(receive_time_unix_seconds),
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def build_counterfactual_record_v1(
    *,
    bindings: S03ScopeBindingsV1,
    runtime_decision: str,
    counterfactual_decision: str,
    monotonic_elapsed_seconds: float,
    receive_time_unix_seconds: float,
) -> dict[str, Any]:
    if not COUNTERFACTUAL_RUNTIME_IS_NON_AUTHORITY:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            "counterfactual_runtime_authority_flag_drift"
        )
    payload = {
        "schema": SCHEMA_COUNTERFACTUAL,
        **_common_bindings(bindings),
        "runtime_decision_used_old_volatility": runtime_decision,
        "counterfactual_decision_fresh_volatility": counterfactual_decision,
        "COUNTERFACTUAL_RUNTIME_AUTHORITY_OCCURRED": False,
        "runtime_state_mutated_by_counterfactual": False,
        "position_mutated_by_counterfactual": False,
        "risk_path_mutated_by_counterfactual": False,
        "safety_path_mutated_by_counterfactual": False,
        "monotonic_elapsed_seconds": float(monotonic_elapsed_seconds),
        "receive_time": float(receive_time_unix_seconds),
    }
    payload["record_digest"] = sha256_hex_canonical(payload)
    return payload


def classify_sample_ordering_v1(
    *,
    sample: MarketSampleV1,
    seen_identities: set[str],
    last_event_time: Optional[float],
) -> tuple[bool, bool, bool]:
    """Return (duplicate, out_of_order, advances_market_time)."""
    duplicate = sample.sample_identity in seen_identities
    out_of_order = last_event_time is not None and float(sample.event_time_unix_seconds) < float(
        last_event_time
    )
    advances = (not duplicate) and (not out_of_order)
    if duplicate and not DUPLICATE_SAMPLE_CANNOT_ADVANCE_MARKET_TIME:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            "duplicate_market_time_advance_forbidden_flag_drift"
        )
    return duplicate, out_of_order, advances


def evidence_file_map_v1(session_dir: Path) -> dict[str, Path]:
    return {
        "session_metadata": session_dir / S03_METADATA_FILENAME,
        "heartbeat": session_dir / S03_HEARTBEAT_FILENAME,
        "connectivity_events": session_dir / S03_CONNECTIVITY_FILENAME,
        "market_samples": session_dir / S03_MARKET_SAMPLES_FILENAME,
        "volatility_records": session_dir / S03_VOLATILITY_FILENAME,
        "volatility_drift_comparisons": session_dir / S03_DRIFT_FILENAME,
        "decision_sensitivity": session_dir / S03_DECISION_SENSITIVITY_FILENAME,
        "exit_risk_safety_independence": session_dir / S03_EXIT_RISK_SAFETY_FILENAME,
        "counterfactual_decisions": session_dir / S03_COUNTERFACTUAL_FILENAME,
        "terminal_verdict": session_dir / S03_TERMINAL_VERDICT_FILENAME,
        "integrity_manifest": session_dir / S03_INTEGRITY_MANIFEST_FILENAME,
    }


def scan_artifacts_for_confirm_token_plaintext_v1(
    *,
    root: Path,
    forbidden_substrings: Iterable[str],
) -> list[str]:
    hits: list[str] = []
    if not root.exists():
        return hits
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        for token in forbidden_substrings:
            if token and token in text:
                hits.append(str(path))
                break
    return hits
