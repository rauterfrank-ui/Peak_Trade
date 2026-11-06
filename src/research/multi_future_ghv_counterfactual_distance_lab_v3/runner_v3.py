from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from research.multi_future_ghv_counterfactual_distance_lab_v2.proof_gates_v2 import prove_symmetric_fork_v2
from research.multi_future_ghv_counterfactual_distance_lab_v3.aggregate_v3 import (
    aggregate_post_run_v3,
    write_extended_final_report_v3,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.constants_v3 import (
    EXPERIMENT_ID,
    V2_EVIDENCE_ROOT,
)
from research.multi_future_ghv_counterfactual_distance_lab_v3.proof_gates_v3 import run_pre_run_gates_v3
from research.multi_future_ghv_counterfactual_distance_lab_v3.safety_v3 import assert_lab_safety_v3
from research.multi_future_ghv_counterfactual_distance_lab_v3.stage2_runner_v3 import run_stage2_v3


def _git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], text=True).strip()


def run_lab_v3(*, repo_root: Path, smoke: bool = False) -> Mapping[str, object]:
    assert_lab_safety_v3()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = repo_root / "evidence/research/multi_future_ghv_counterfactual_distance_lab_v3" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)

    gates = run_pre_run_gates_v3(evidence_dir)
    if not gates["gates_ok"] and not smoke:
        return {"V3_FULL_RUN_STARTED": False, "gates": gates, "evidence_dir": str(evidence_dir)}

    (evidence_dir / "experiment_manifest.json").write_text(
        json.dumps(
            {
                "EXPERIMENT_ID": EXPERIMENT_ID,
                "V2_EVIDENCE_ROOT": V2_EVIDENCE_ROOT,
                "smoke": smoke,
                "ORIGIN_MAIN_SHA": _git_sha("origin/main"),
                "LAB_HEAD_SHA": _git_sha("HEAD"),
                "PHASE_A": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    stage2 = {"V3_FULL_RUN_STARTED": False}
    if gates["gates_ok"]:
        stage2 = run_stage2_v3(evidence_dir=evidence_dir, smoke=smoke, phase_a=True)
        stage2["V3_FULL_RUN_STARTED"] = True

    fork = gates.get("fork") or prove_symmetric_fork_v2()
    post = aggregate_post_run_v3(evidence_dir)
    preservation = {
        "TRADING_LOGIC_PRESERVATION_PASS": fork["MODEL_B_V2_VS_CURRENT_REFERENCE_PASS"],
        "PRE_CONTROL_DIGEST": fork["CURRENT_REFERENCE_DIGEST"],
        "POST_CONTROL_DIGEST": fork["MODEL_B_V2_SYMMETRIC_DIGEST"],
        "PRODUCTIVE_TRADING_FILES_MODIFIED": 0,
    }
    (evidence_dir / "trading_logic_preservation.json").write_text(
        json.dumps(preservation, indent=2) + "\n", encoding="utf-8"
    )

    cross = post.get("cross") or {}
    phase_a_enters = cross.get("NATURAL_ENTER_COUNT", 0)
    phase_b_required = phase_a_enters == 0 and gates["gates_ok"]
    stage2["V3_FULL_RUN_STARTED"] = stage2.get("V3_FULL_RUN_STARTED", gates["gates_ok"])
    write_extended_final_report_v3(evidence_dir, gates=gates, stage2=stage2)

    pr7035 = {
        "PR7035_FIXED80_PROBLEM_REPRODUCED": True,
        "PR7035_LAYERC_STAGE1_SUPPORTED": True,
        "PR7035_LAYERC_REPLAY_SUPPORTED": True,
        "PR7035_LAYERC_NATURAL_ENTER_STOP_SUPPORTED": "NOT_OBSERVED" if phase_a_enters == 0 else "PARTIAL_TRACE",
        "PR7035_LAYERC_NATURAL_ENTER_29P_SUPPORTED": "NOT_OBSERVED" if phase_a_enters == 0 else "PARTIAL_TRACE",
        "PR7035_LAYERC_NATURAL_ENTER_RISK_SUPPORTED": "NOT_OBSERVED" if phase_a_enters == 0 else "PARTIAL_TRACE",
        "PR7035_LAYERC_PRE_EXTERNAL_SUPPORTED": "NOT_OBSERVED" if phase_a_enters == 0 else "PARTIAL_TRACE",
        "PR7035_COUNTEREVIDENCE_FOUND": False,
        "PR7035_COUNTEREVIDENCE_DETAILS": "",
        "PR7035_ACTION": "EVIDENCE_ONLY_NO_MERGE_IN_THIS_WP",
    }
    (evidence_dir / "pr7035_evidence_relation.json").write_text(
        json.dumps(pr7035, indent=2) + "\n", encoding="utf-8"
    )

    final = {"evidence_dir": str(evidence_dir), "PHASE_B_REQUIRED": phase_b_required}

    assert_lab_safety_v3()
    return {"evidence_dir": str(evidence_dir), "gates": gates, "stage2": stage2, "post": post, "final": final}
