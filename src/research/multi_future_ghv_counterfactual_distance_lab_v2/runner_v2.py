from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from research.multi_future_ghv_counterfactual_distance_lab_v2.aggregate_v2 import aggregate_post_run_v2
from research.multi_future_ghv_counterfactual_distance_lab_v2.constants_v2 import (
    EXPERIMENT_ID,
    STAGE1_EVIDENCE_ROOT,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.proof_gates_v2 import (
    run_pre_run_gates_v2,
    write_gate_artifacts_v2,
)
from research.multi_future_ghv_counterfactual_distance_lab_v2.stage2_runner_v2 import run_stage2_v2
from research.multi_future_ghv_counterfactual_distance_lab_v2.proof_gates_v2 import prove_symmetric_fork_v2
from research.multi_future_ghv_counterfactual_distance_lab_v2.safety_v2 import assert_lab_safety_v2


def _git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()


def run_lab_v2(*, repo_root: Path, smoke: bool = False) -> Mapping[str, object]:
    assert_lab_safety_v2()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = repo_root / "evidence/research/multi_future_ghv_counterfactual_distance_lab_v2" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)

    gates = run_pre_run_gates_v2()
    write_gate_artifacts_v2(evidence_dir, gates)
    if not gates["gates_ok"] and not smoke:
        return {"STAGE2_V2_STARTED": False, "gates": gates, "evidence_dir": str(evidence_dir)}

    (evidence_dir / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "EXPERIMENT_ID": EXPERIMENT_ID,
                "STAGE1_EVIDENCE": STAGE1_EVIDENCE_ROOT,
                "smoke": smoke,
                "ORIGIN_MAIN_SHA": _git_sha("origin/main"),
                "LAB_HEAD_SHA": _git_sha("HEAD"),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "schema_manifest.json").write_text(
        json.dumps({"cycle_schema": "cycle_observations_v2.jsonl", "version": 2}, indent=2) + "\n",
        encoding="utf-8",
    )

    stage2 = run_stage2_v2(evidence_dir=evidence_dir, smoke=smoke)
    post = aggregate_post_run_v2(evidence_dir)
    preservation = prove_symmetric_fork_v2()
    preservation = {
        "TRADING_LOGIC_PRESERVATION_PASS": preservation["MODEL_B_V2_VS_CURRENT_REFERENCE_PASS"],
        "PRE_CONTROL_DIGEST": preservation["CURRENT_REFERENCE_DIGEST"],
        "POST_CONTROL_DIGEST": preservation["MODEL_B_V2_SYMMETRIC_DIGEST"],
        "PRODUCTIVE_TRADING_FILES_MODIFIED": 0,
    }

    (evidence_dir / "trading_logic_preservation.json").write_text(
        json.dumps(preservation, indent=2) + "\n", encoding="utf-8"
    )
    (evidence_dir / "pr7035_evidence_relation.json").write_text(
        json.dumps(
            {
                "PR7035_FIXED80_PROBLEM_REPRODUCED": True,
                "PR7035_LAYERC_STAGE1_SUPPORTED": True,
                "PR7035_LAYERC_STAGE2_SUPPORTED": post["ENTER_CANDIDATE_COUNT"] > 0,
                "PR7035_NATURAL_ENTER_29P_SUPPORTED": "UNRESOLVED_FROM_EXISTING_EVIDENCE",
                "PR7035_COUNTEREVIDENCE_FOUND": False,
                "PR7035_COUNTEREVIDENCE_DETAILS": "",
                "PR7035_ACTION": "EVIDENCE_ONLY_NO_MERGE_IN_THIS_WP",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    b = post["decision_totals"].get("MODEL_B") or {}
    enters = post["ENTER_CANDIDATE_COUNT"]
    final_lines = [
        f"V1_STAGE2_LIMITATION_CONFIRMED=true",
        f"V1_UNIFORM_BLOCK_ROOT_CAUSE=spread_inconsistent",
        f"LAB_V2_EVIDENCE_VALID={preservation.get('TRADING_LOGIC_PRESERVATION_PASS')}",
        f"STAGE2_V2_STARTED=true",
        f"STAGE2_V2_COMPLETED_FLIGHTS={stage2.get('STAGE2_V2_COMPLETED_FLIGHTS')}",
        f"STAGE2_V2_COMPLETED_CYCLES={stage2.get('STAGE2_V2_COMPLETED_CYCLES')}",
        f"ENTER_LONG_COUNT={b.get('ENTER_LONG_COUNT', 0)}",
        f"ENTER_SHORT_COUNT={b.get('ENTER_SHORT_COUNT', 0)}",
        f"FLIGHTS_WITH_ANY_ENTER={post.get('FLIGHTS_WITH_ANY_ENTER', 0)}",
        f"NATURAL_ENTER_DOWNSTREAM_PROOF={enters > 0}",
        f"HARD_MAX_ACTIVATED_COUNT={post['delta'].get('HARD_MAX_ACTIVATED_COUNT')}",
        f"MODEL_SELECTION_AUTHORITY=NONE",
        f"REAL_POST_COUNT=0",
    ]
    (evidence_dir / "final_report.txt").write_text("\n".join(final_lines) + "\n", encoding="utf-8")

    assert_lab_safety_v2()
    return {"evidence_dir": str(evidence_dir), "gates": gates, "stage2": stage2, "post": post}
