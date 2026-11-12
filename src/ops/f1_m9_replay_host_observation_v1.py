"""Observe and archive the original F1/M9 host return during one offline replay."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from inspect import unwrap
from pathlib import Path
from types import FrameType
from typing import Any, Mapping

from trading.master_v2 import double_play_old_effective_host_contract_v1 as host_contract
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)

_F1_M9_HOST_OBSERVATION_FILE = "f1_m9_replay_host_observation.json"
_F1_M9_HOST_OBSERVATION_SCHEMA = "f1_m9_replay_host_observation_v1"


def _jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {field.name: _jsonable(getattr(obj, field.name)) for field in fields(obj)}
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(obj.items())}
    return obj


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_observed_replay(
    *,
    out_dir: str | Path,
    replay_input: IntegratedOfflineReplayInputV1,
    replay_result: IntegratedOfflineReplayResultV1,
    observation: dict[str, Any],
) -> Path:
    # Keep the integrated replay artifact layout, including typed input timestamps.
    root = Path(out_dir)
    intermediate = replay_result.intermediate
    evidence = replay_result.evidence
    artifacts: dict[str, Any] = {
        "replay_input.json": replay_input,
        "canonical_trading_decision_evidence.json": replay_result.evidence,
        "component_versions.json": dict(replay_result.evidence.component_versions),
        "policy_versions.json": dict(replay_result.evidence.policy_versions),
        "reason_trace.json": {
            "fail_reasons": list(replay_result.fail_reasons),
            "reason_codes": list(replay_result.evidence.reason_codes),
            "decision_precedence_trace": list(replay_result.evidence.decision_precedence_trace),
        },
        _F1_M9_HOST_OBSERVATION_FILE: {
            "schema_version": _F1_M9_HOST_OBSERVATION_SCHEMA,
            "authority": "NONE",
            "observation_source": "OFFLINE_PROFILE_ORIGINAL_HOST_RETURN",
            "observation": observation,
            "decision_evidence_digest": evidence.semantic_digest,
            "decision_outcome": evidence.decision_outcome,
            "replay_pass": replay_result.replay_pass,
            "post_gate_pipeline_observed": intermediate is not None,
            "execution_eligible": evidence.execution_eligible,
        },
    }
    if intermediate is not None:
        artifacts.update(
            {
                "market_context.json": intermediate.market_context,
                "scope_initialization.json": intermediate.scope_initialization,
                "scope_event.json": intermediate.scope_event,
                "bull_assessment.json": intermediate.bull_assessment,
                "bear_assessment.json": intermediate.bear_assessment,
                "state_switch.json": intermediate.state_switch,
                "survival_results.json": {
                    "bull": intermediate.bull_survival,
                    "bear": intermediate.bear_survival,
                },
                "suitability_results.json": {
                    "bull": intermediate.bull_suitability,
                    "bear": intermediate.bear_suitability,
                },
                "composition_result.json": intermediate.composition_result,
                "entry_exit_policy_result.json": intermediate.entry_exit_decision,
            }
        )

    manifest_lines: list[str] = []
    for name in sorted(artifacts):
        path = root / name
        _write_json(path, artifacts[name])
        manifest_lines.append(f"{_file_sha256(path)}  {name}\n")

    evidence_canonical_path = root / "canonical_trading_decision_evidence.canonical.json"
    evidence_canonical_path.write_text(
        serialize_canonical_trading_decision_evidence_canonical(replay_result.evidence) + "\n",
        encoding="utf-8",
    )
    manifest_lines.append(
        f"{_file_sha256(evidence_canonical_path)}  canonical_trading_decision_evidence.canonical.json\n"
    )

    manifest_path = root / "MANIFEST.sha256"
    manifest_path.write_text("".join(sorted(manifest_lines)), encoding="utf-8")
    return manifest_path


def _run_observed_replay(
    replay_input: IntegratedOfflineReplayInputV1,
) -> tuple[IntegratedOfflineReplayResultV1, dict[str, Any]]:
    if sys.getprofile() is not None:
        raise ValueError("F1_M9_REPLAY_HOST_PROFILE_ALREADY_ACTIVE")
    replay_code = unwrap(run_integrated_offline_trading_logic_replay_v1).__code__
    resolver_code = host_contract.resolve_alpha_scope_entry_for_integrated_replay_v1.__code__
    compatibility_code = host_contract.integrated_replay_presence_alpha_at_dp_boundary_v1.__code__
    compatibility_returns: list[bool] = []
    resolver_returns: list[tuple[Any, Any, tuple[bool, tuple[str, ...]]]] = []

    def observe_return(frame: FrameType, event: str, value: Any) -> None:
        caller = frame.f_back
        if event != "return" or caller is None:
            return
        if frame.f_code is resolver_code and caller.f_code is replay_code and value is not None:
            resolver_returns.append(
                (frame.f_locals["presence_gate"], frame.f_locals["consumer_path"], value)
            )
        if (
            frame.f_code is compatibility_code
            and caller.f_code is resolver_code
            and caller.f_back is not None
            and caller.f_back.f_code is replay_code
            and type(value) is bool
        ):
            compatibility_returns.append(value)

    # The profile hook is scoped to the calling thread. Neither the resolver nor
    # its arguments or return values are replaced during the replay.
    sys.setprofile(observe_return)
    try:
        result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    finally:
        sys.setprofile(None)
    if len(resolver_returns) != 1 or len(compatibility_returns) != 1:
        raise ValueError("F1_M9_REPLAY_HOST_DECISION_NOT_OBSERVED")
    ((presence, consumer, (effective_alpha, reasons)),) = resolver_returns
    (use_presence_alpha,) = compatibility_returns
    context = replay_input.canonical_market_context
    age = presence.max_age_policy_evidence
    seam = replay_input.governed_authorized_productive_parameter_seam_record
    bound_seam = (
        seam
        if seam is not None
        and consumer.seam_digest is not None
        and seam.get("seam_digest") == consumer.seam_digest
        else {}
    )
    return result, {
        "replay_id": replay_input.replay_id,
        "instrument_id": replay_input.instrument_id,
        "trading_epoch": replay_input.trading_epoch,
        "replay_input_digest": replay_input.input_digest,
        "market_context_ref": context.context_id,
        "submitted_market_context_digest": context.input_digest,
        "submitted_market_event_time": context.market_event_time,
        "submitted_decision_time": context.decision_time,
        "configuration_digest": bound_seam.get("configuration_digest"),
        "seam_digest": consumer.seam_digest,
        "owner_apply_record_digest": bound_seam.get("owner_apply_authorization_record_digest"),
        "owner_threshold_record_digest": consumer.owner_threshold_record_digest,
        "configuration_runtime_applied": consumer.configuration_runtime_applied,
        "threshold_seconds": consumer.threshold_numeric_max_age_seconds,
        "typed_estimate_present": presence.typed_estimate_present,
        "reference_event_time": age.reference_event_time if age is not None else None,
        "estimate_as_of_event_time": age.estimate_as_of_event_time if age is not None else None,
        "estimate_age_seconds": age.computed_age_seconds if age is not None else None,
        "presence_alpha_allowed": presence.alpha_scope_entry_authority_allowed,
        "local_enforcement_applied": consumer.enforcement_applied,
        "local_alpha_allowed": consumer.alpha_scope_entry_authority_allowed,
        "local_reason_codes": consumer.reason_codes,
        "host_uses_presence_alpha": use_presence_alpha,
        "effective_host_alpha_allowed": effective_alpha,
        "host_compatibility_reasons": reasons,
    }


def run_and_write_f1_m9_replay_host_observation_v1(
    *, out_dir: str | Path, replay_input: IntegratedOfflineReplayInputV1
) -> tuple[Path, str]:
    """Run the original offline host and return the path and digest of its evidence manifest."""
    if not replay_input.require_productive_typed_volatility_presence_gate:
        raise ValueError("F1_M9_REPLAY_HOST_DECISION_NOT_OBSERVED")
    root = Path(out_dir).expanduser().resolve()
    if root.exists():
        raise FileExistsError(root)
    replay_result, observation = _run_observed_replay(replay_input)
    if any(
        observation[key] != getattr(replay_result.evidence, key)
        for key in ("replay_id", "instrument_id", "trading_epoch")
    ):
        raise ValueError("F1_M9_REPLAY_HOST_OBSERVATION_LINEAGE_MISMATCH")
    root.mkdir(parents=True, exist_ok=False)
    manifest = _write_observed_replay(
        out_dir=root,
        replay_input=replay_input,
        replay_result=replay_result,
        observation=observation,
    )
    return manifest, _file_sha256(manifest)


def read_f1_m9_replay_host_observation_v1(
    *, manifest_path: Path, expected_manifest_sha256: str
) -> dict[str, Any]:
    """Read the observed host decision using an independently retained manifest digest."""
    manifest = manifest_path.read_bytes()
    if hashlib.sha256(manifest).hexdigest() != expected_manifest_sha256:
        raise ValueError("F1_M9_REPLAY_HOST_MANIFEST_DIGEST_MISMATCH")
    listed = {}
    for line in manifest.decode("utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or name in listed:
            raise ValueError("F1_M9_REPLAY_HOST_MANIFEST_INVALID")
        listed[name] = digest
    payloads = {}
    for name in (
        _F1_M9_HOST_OBSERVATION_FILE,
        "canonical_trading_decision_evidence.json",
        "replay_input.json",
    ):
        path = manifest_path.parent / name
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != listed.get(name):
            raise ValueError(f"F1_M9_REPLAY_HOST_ARTIFACT_DIGEST_MISMATCH:{name}")
        payloads[name] = json.loads(data)
    record = payloads[_F1_M9_HOST_OBSERVATION_FILE]
    evidence = payloads["canonical_trading_decision_evidence.json"]
    replay_input = payloads["replay_input.json"]
    context = replay_input["canonical_market_context"]
    observation = record["observation"]
    if (
        record["schema_version"] != _F1_M9_HOST_OBSERVATION_SCHEMA
        or record["authority"] != "NONE"
        or record["decision_evidence_digest"] != evidence["semantic_digest"]
        or record["decision_outcome"] != evidence["decision_outcome"]
        or record["execution_eligible"] != evidence["execution_eligible"]
        or observation["replay_input_digest"] != replay_input["input_digest"]
        or observation["market_context_ref"] != context["context_id"]
        or observation["submitted_market_context_digest"] != context["input_digest"]
        or observation.get("submitted_market_event_time", context["market_event_time"])
        != context["market_event_time"]
        or observation.get("submitted_decision_time", context["decision_time"])
        != context["decision_time"]
        or any(
            observation[key] != evidence[key] or observation[key] != replay_input[key]
            for key in ("replay_id", "instrument_id", "trading_epoch")
        )
    ):
        raise ValueError("F1_M9_REPLAY_HOST_OBSERVATION_LINEAGE_MISMATCH")
    return record
