# src/trading/master_v2/integrated_offline_replay_evidence_writer_v1.py
"""
Offline evidence writer for integrated trading logic replay v1.

Test-harness / local evidence only. No runtime or trading effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.f1_m9_replay_host_observation_v1 import (
    F1M9ReplayHostObservationV1,
    capture_f1_m9_replay_host_observations_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayIntermediateV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)

INTEGRATED_OFFLINE_REPLAY_EVIDENCE_WRITER_LAYER_VERSION = "v1"
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


def write_integrated_offline_replay_evidence_bundle_v1(
    *,
    out_dir: str | Path,
    replay_input: IntegratedOfflineReplayInputV1,
    replay_result: IntegratedOfflineReplayResultV1,
    f1_m9_host_observation: F1M9ReplayHostObservationV1 | None = None,
) -> Path:
    """Write deterministic offline evidence artifacts and MANIFEST.sha256."""
    root = Path(out_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    intermediate = replay_result.intermediate
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
    }
    if f1_m9_host_observation is not None:
        observation = f1_m9_host_observation
        evidence = replay_result.evidence
        if (
            observation.replay_id != replay_input.replay_id
            or observation.replay_id != evidence.replay_id
            or observation.instrument_id != evidence.instrument_id
            or observation.trading_epoch != evidence.trading_epoch
            or observation.replay_input_digest != replay_input.input_digest
            or observation.market_context_ref != replay_input.canonical_market_context.context_id
        ):
            raise ValueError("F1_M9_REPLAY_HOST_OBSERVATION_LINEAGE_MISMATCH")
        artifacts[_F1_M9_HOST_OBSERVATION_FILE] = {
            "schema_version": _F1_M9_HOST_OBSERVATION_SCHEMA,
            "authority": "NONE",
            "observation": observation,
            "decision_evidence_digest": evidence.semantic_digest,
            "decision_outcome": evidence.decision_outcome,
            "replay_pass": replay_result.replay_pass,
            "post_gate_pipeline_observed": intermediate is not None,
            "execution_eligible": evidence.execution_eligible,
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


def run_and_write_f1_m9_replay_host_observation_v1(
    *, out_dir: str | Path, replay_input: IntegratedOfflineReplayInputV1
) -> tuple[Path, str]:
    """Run the original offline host and return the path and digest of its evidence manifest."""
    if not replay_input.require_productive_typed_volatility_presence_gate:
        raise ValueError("F1_M9_REPLAY_HOST_DECISION_NOT_OBSERVED")
    root = Path(out_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=False)
    with capture_f1_m9_replay_host_observations_v1(replay_input) as observations:
        replay_result = run_integrated_offline_trading_logic_replay_v1(replay_input)
    if len(observations) != 1:
        root.rmdir()
        raise ValueError("F1_M9_REPLAY_HOST_DECISION_NOT_OBSERVED")
    manifest = write_integrated_offline_replay_evidence_bundle_v1(
        out_dir=root,
        replay_input=replay_input,
        replay_result=replay_result,
        f1_m9_host_observation=observations[0],
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


def verify_evidence_manifest_v1(manifest_path: str | Path) -> int:
    """Verify MANIFEST.sha256 against files in the same directory. Returns 0 on success."""
    manifest = Path(manifest_path).expanduser().resolve()
    if not manifest.is_file():
        return 1
    base = manifest.parent
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, _, name = line.partition("  ")
        file_path = base / name.strip()
        if not file_path.is_file():
            return 2
        if _file_sha256(file_path) != digest.strip():
            return 3
    return 0
