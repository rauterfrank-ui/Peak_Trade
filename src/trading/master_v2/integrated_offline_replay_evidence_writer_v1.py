# src/trading/master_v2/integrated_offline_replay_evidence_writer_v1.py
"""
Offline evidence writer for integrated trading logic replay v1.

Test-harness / local evidence only. No runtime or trading effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayIntermediateV1,
    IntegratedOfflineReplayResultV1,
)

INTEGRATED_OFFLINE_REPLAY_EVIDENCE_WRITER_LAYER_VERSION = "v1"


def _jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: _jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, Enum):
        return obj.value
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
