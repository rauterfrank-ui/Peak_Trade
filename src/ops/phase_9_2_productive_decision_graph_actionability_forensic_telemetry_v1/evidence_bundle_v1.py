"""Evidence bundle writer + manifest for actionability forensic telemetry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_decision_graph_actionability_forensic_telemetry_v1.constants_v1 import (
    AGGREGATE_COUNTERS_FILENAME,
    AUTHORITY_MATRIX_FILENAME,
    BOTTLENECK_INTERPRETATION_FILENAME,
    CALL_ORDER_PROOF_FILENAME,
    CONFIG_DIGEST_FILENAME,
    CYCLE_TERMINALS_FILENAME,
    DISTANCE_STATS_FILENAME,
    ENTRY_FUNNEL_FILENAME,
    EXIT_FUNNEL_FILENAME,
    GOLDEN_PARITY_PROOF_FILENAME,
    MANIFEST_FILENAME,
    SECONDARY_REASON_HISTOGRAM_FILENAME,
    STAGE_EVENTS_FILENAME,
    SUMMARY_FILENAME,
    TERMINAL_BLOCKER_HISTOGRAM_FILENAME,
    VERIFIER_RESULT_FILENAME,
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def materialize_actionability_evidence_bundle_v1(
    *,
    evidence_root: Path,
    campaign: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(evidence_root)
    binding = root / "productive_binding"
    binding.mkdir(parents=True, exist_ok=True)

    telemetry = dict(campaign.get("telemetry") or {})
    hist = dict(telemetry.get("histograms") or {})
    _write_jsonl(binding / STAGE_EVENTS_FILENAME, list(campaign.get("stage_events") or []))
    _write_jsonl(binding / CYCLE_TERMINALS_FILENAME, list(campaign.get("cycle_terminals") or []))
    _write_json(binding / AGGREGATE_COUNTERS_FILENAME, dict(campaign.get("counters") or {}))
    _write_json(
        binding / TERMINAL_BLOCKER_HISTOGRAM_FILENAME,
        {
            "terminal_outcomes": hist.get("terminal_outcomes") or {},
            "primary_reasons": hist.get("primary_reasons") or {},
        },
    )
    _write_json(
        binding / SECONDARY_REASON_HISTOGRAM_FILENAME,
        {"secondary_reasons": hist.get("secondary_reasons") or {}},
    )
    _write_json(binding / ENTRY_FUNNEL_FILENAME, dict(campaign.get("entry_funnel") or {}))
    _write_json(binding / EXIT_FUNNEL_FILENAME, dict(campaign.get("exit_funnel") or {}))
    _write_json(
        binding / DISTANCE_STATS_FILENAME,
        dict(telemetry.get("distance_stats") or {}),
    )
    _write_json(
        binding / CALL_ORDER_PROOF_FILENAME,
        {
            "authority": campaign.get("authority"),
            "CALL_ORDER_FROZEN": bool((campaign.get("authority") or {}).get("CALL_ORDER_FROZEN")),
        },
    )
    _write_json(binding / GOLDEN_PARITY_PROOF_FILENAME, dict(campaign.get("parity") or {}))
    _write_json(binding / AUTHORITY_MATRIX_FILENAME, dict(campaign.get("authority") or {}))
    _write_json(binding / VERIFIER_RESULT_FILENAME, dict(campaign.get("verifier") or {}))
    _write_json(
        binding / CONFIG_DIGEST_FILENAME,
        {
            "repository_sha": campaign.get("repository_sha"),
            "config_digest": campaign.get("config_digest"),
        },
    )
    _write_json(
        binding / BOTTLENECK_INTERPRETATION_FILENAME,
        dict(campaign.get("bottleneck") or {}),
    )

    summary = {
        "capability_id": campaign.get("capability_id"),
        "owner": campaign.get("owner"),
        "repository_sha": campaign.get("repository_sha"),
        "config_digest": campaign.get("config_digest"),
        "PRODUCTIVE_CALLER_ADDED": campaign.get("PRODUCTIVE_CALLER_ADDED"),
        "PRODUCTIVE_DECISION_GRAPH_OBSERVED": campaign.get("PRODUCTIVE_DECISION_GRAPH_OBSERVED"),
        "PARALLEL_DECISION_ENGINE_CREATED": campaign.get("PARALLEL_DECISION_ENGINE_CREATED"),
        "counters": campaign.get("counters"),
        "entry_funnel": campaign.get("entry_funnel"),
        "exit_funnel": campaign.get("exit_funnel"),
        "bottleneck": campaign.get("bottleneck"),
        "verifier": campaign.get("verifier"),
        "parity": {
            k: (campaign.get("parity") or {}).get(k)
            for k in (
                "GOLDEN_VECTOR_PARITY_PASS",
                "CALL_ORDER_PARITY_PROVEN",
                "INPUT_OUTPUT_PARITY_PROVEN",
                "STATE_TRANSITION_PARITY_PROVEN",
                "DECISION_REASON_PARITY_PROVEN",
                "RISK_PARITY_PROVEN",
                "SAFETY_PARITY_PROVEN",
                "EXIT_PRECEDENCE_PARITY_PROVEN",
                "CORE_LOGIC_CHANGED",
                "EFFECTIVE_CONFIG_VALUES_UNCHANGED",
            )
        },
        "restart_clears_ephemeral_counters": campaign.get("restart_clears_ephemeral_counters"),
    }
    _write_json(root / SUMMARY_FILENAME, summary)

    # Manifest over productive_binding + SUMMARY
    files: list[Path] = [root / SUMMARY_FILENAME]
    files.extend(sorted(binding.rglob("*")))
    lines: list[str] = []
    for path in files:
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        lines.append(f"{_sha256_file(path)}  {rel}")
    manifest_path = root / MANIFEST_FILENAME
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "evidence_root": str(root),
        "manifest_path": str(manifest_path),
        "file_count": len(lines),
        "SUMMARY": summary,
    }


def verify_manifest_v1(evidence_root: Path) -> int:
    root = Path(evidence_root)
    manifest = root / MANIFEST_FILENAME
    if not manifest.is_file():
        return 2
    rc = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, rel = line.partition("  ")
        path = root / rel
        if not path.is_file():
            rc = 1
            continue
        if _sha256_file(path) != digest:
            rc = 1
    return rc
