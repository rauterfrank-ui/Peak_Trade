"""Durable evidence writer for standing supervisor closure."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
    EVIDENCE_ROOT_RELATIVE,
    WORK_PACKAGE_ID,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.trace_v1 import (
    StandingSupervisorTraceV1,
)


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_standing_supervisor_closure_evidence_v1(
    *,
    repo_root: Path,
    tested_code_sha: str,
    baseline_sha: str,
    trace: StandingSupervisorTraceV1,
    ok: bool,
    owner_go_consumed: bool,
    authority_invariants_ok: bool,
    transport_scope: str,
    post_allowed: bool,
    external_effect_authorized: bool,
    real_venue_post_allowed: bool,
    continuous_admission_granted: bool,
    extra: Mapping[str, Any] | None = None,
) -> Path:
    stamp = _utc_stamp_v1()
    out_dir = repo_root / EVIDENCE_ROOT_RELATIVE / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "artifact_kind": "STANDING_SUPERVISOR_CLOSURE_V1",
        "work_package_id": WORK_PACKAGE_ID,
        "utc_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BASELINE_SHA": baseline_sha,
        "TESTED_CODE_SHA": tested_code_sha,
        "ok": ok,
        "run_id": trace.run_id,
        "cycles_completed": trace.governed_cycle_count,
        "accepted_c1_count": trace.accepted_c1_count,
        "governed_cycle_count": trace.governed_cycle_count,
        "POST_COUNT": trace.post_count,
        "post_allowed": post_allowed,
        "external_effect_authorized": external_effect_authorized,
        "real_venue_post_allowed": real_venue_post_allowed,
        "continuous_admission_granted": continuous_admission_granted,
        "owner_go_consumed": owner_go_consumed,
        "recovery_before_cycle": trace.recovery_completed,
        "public_supply_refreshed": trace.public_supply_refreshed,
        "pretrade_truth_refreshed": trace.pretrade_truth_refreshed,
        "transport_scope": transport_scope,
        "authority_invariants_ok": authority_invariants_ok,
        "trace": asdict(trace),
    }
    if extra:
        payload["extra"] = dict(extra)
    path = out_dir / "STANDING_SUPERVISOR_CLOSURE_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
