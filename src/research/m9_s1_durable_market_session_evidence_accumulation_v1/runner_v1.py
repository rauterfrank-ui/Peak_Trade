"""Orchestration for offline replay and owner-review artifact emission."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evidence_loader_v1 import (
    load_research_evidence_records_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    DEFAULT_M9_S1_OBSERVATION_LEDGER_RELATIVE_PATH,
    JOIN_LEDGER_RELATIVE_PATH,
    SCHEMA_VERSION,
    WORKPACKAGE_ID,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.counterfactual_replay_v1 import (
    run_counterfactual_replay_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.data_quality_v1 import (
    summarize_data_quality_raw_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    ObservationSourceClassV1,
    canonical_json_bytes,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.observation_ledger_v1 import (
    load_m9_s1_observation_ledger_v1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.owner_review_v1 import (
    build_owner_review_accumulation_report_v1,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, sort_keys=True, indent=2, default=str)
    path.write_text(text + "\n", encoding="utf-8")


def run_offline_replay_and_owner_review_v1(
    *,
    repo_root: Path,
    join_ledger_path: Path | None = None,
    m9_s1_observation_ledger_path: Path | None = None,
    output_dir: Path,
    repository_sha: str,
) -> dict[str, Any]:
    root = Path(repo_root)
    join_path = Path(join_ledger_path or (root / JOIN_LEDGER_RELATIVE_PATH))
    obs_path = Path(
        m9_s1_observation_ledger_path or (root / DEFAULT_M9_S1_OBSERVATION_LEDGER_RELATIVE_PATH)
    )

    source_class_counts: Counter[str] = Counter()
    if obs_path.exists():
        for row in load_m9_s1_observation_ledger_v1(obs_path):
            source_class_counts[str(row.get("evidence_source_class") or "UNKNOWN")] += 1

    records = load_research_evidence_records_v1(join_path) if join_path.exists() else tuple()
    data_quality = summarize_data_quality_raw_v1(
        records,
        source_class_counts=source_class_counts,
    )
    replay = (
        run_counterfactual_replay_v1(join_ledger_path=join_path)
        if join_path.exists()
        else {
            "schema_version": "m9_s1_market_session_counterfactual_replay/v1",
            "workpackage_id": WORKPACKAGE_ID,
            "observation_count": 0,
            "per_candidate": [],
            "input_record_digest": None,
            "artifact_digest": None,
        }
    )

    real_market = sum(
        source_class_counts.get(label.value, 0)
        for label in (
            ObservationSourceClassV1.LIVE_OBSERVED,
            ObservationSourceClassV1.TESTNET_OBSERVED,
            ObservationSourceClassV1.SHADOW_OBSERVED,
        )
    )
    pipeline_flags = {
        "PIPELINE_IMPLEMENTED": True,
        "PIPELINE_TESTED_WITH_FIXTURE": False,
        "REAL_SESSION_CAPTURE_READY": True,
        "REAL_SESSION_EVIDENCE_ACCUMULATED": real_market > 0,
    }

    report = build_owner_review_accumulation_report_v1(
        data_quality=data_quality,
        counterfactual_replay=replay,
        source_class_counts=dict(source_class_counts),
        repository_sha=repository_sha,
        pipeline_flags=pipeline_flags,
    )

    out = Path(output_dir)
    _write_json(out / "counterfactual_replay_artifact.json", dict(replay))
    _write_json(out / "owner_review_accumulation_report.json", report)

    package = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "repository_sha": repository_sha,
        "join_ledger_path": str(join_path),
        "m9_s1_observation_ledger_path": str(obs_path),
        "replay_artifact_digest": replay.get("artifact_digest"),
        "owner_review_digest": report.get("report_digest"),
        "pipeline_flags": pipeline_flags,
    }
    _write_json(out / "m9_s1_offline_replay_package.json", package)
    return package


def deterministic_replay_digest_v1(artifact: dict[str, Any]) -> str:
    import hashlib

    return hashlib.sha256(canonical_json_bytes(artifact)).hexdigest()
