#!/usr/bin/env python3
"""Run WP-2 side executor on CURRENT repo and historical worktree; emit differential JSON."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[3]
WT = BASE / "wt_historical"
EXECUTOR = BASE / "wp2_side_executor_v1.py"
CURRENT_JSON = BASE / "side_current.json"
HIST_JSON = BASE / "side_historical.json"
DIFF_JSON = BASE / "WP_DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1.json"


def _run_side(side: str, repo: Path, out: Path) -> None:
    pt = repo / "scripts" / "pt"
    if not (repo / ".venv").is_dir():
        subprocess.check_call([str(repo / "scripts" / "pt-bootstrap")], cwd=repo)
    env = {
        **os.environ,
        "WP2_SIDE": side,
        "WP2_OUTPUT_JSON": str(out),
        "WP2_REPO_ROOT": str(repo),
    }
    subprocess.check_call(
        [
            str(pt),
            "-m",
            "pytest",
            str(BASE / "test_wp2_harness_runner_v1.py"),
            "-q",
            "--tb=short",
            "-k",
            "current" if side == "current" else "historical",
        ],
        cwd=repo,
        env=env,
    )


def _layered_markers(repo: Path) -> dict[str, bool]:
    path = (
        repo
        / "src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py"
    )
    if not path.is_file():
        return {"file_present": False}
    text = path.read_text(encoding="utf-8")
    return {
        "file_present": True,
        "cmc_mark_obs_helper": "_observation_candidates_from_cmc_mark_v1" in text,
        "finalized_closes_grid_helper": "_observation_candidates_from_finalized_closes_v1" in text,
        "transition_carryforward_param": "side_state_from_transition_carryforward" in text,
    }


def _classify_checkpoint(old: Any, new: Any) -> str:
    if old == new:
        return "IDENTICAL"
    if old is None or new is None:
        return "BEHAVIORALLY_DIVERGENT" if old != new else "IDENTICAL"
    return "BEHAVIORALLY_DIVERGENT"


def _compare_vectors(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"comparisons": {}, "first_divergences": []}

    def add_first(vid: str, cycle: int, checkpoint: str, wp1_id: str, old_v: Any, new_v: Any):
        report["first_divergences"].append(
            {
                "vector_id": vid,
                "cycle": cycle,
                "checkpoint": checkpoint,
                "wp1_divergence_id": wp1_id,
                "old": old_v,
                "current": new_v,
            }
        )

    # A/B enter outcomes
    for key, wp1, field in (
        ("A", "CORE_N/A", "enter_long"),
        ("B", "CORE_N/A", "enter_short"),
    ):
        o = old["vectors"][key].get(field)
        n = new["vectors"][key].get(field)
        cls = _classify_checkpoint(o, n)
        report["comparisons"][f"vector_{key}_{field}"] = cls
        if cls == "BEHAVIORALLY_DIVERGENT":
            add_first(f"VECTOR_{key}", 0, field, wp1, o, n)

    # C duplicate
    o_dup = old["vectors"]["C"].get("duplicate_advanced_confirmation")
    n_dup = new["vectors"]["C"].get("duplicate_advanced_confirmation")
    report["comparisons"]["vector_C_duplicate_advanced"] = _classify_checkpoint(o_dup, n_dup)
    o_dist = old["vectors"]["C"].get("duplicate_distinct_increment")
    n_dist = new["vectors"]["C"].get("duplicate_distinct_increment")
    if o_dist != n_dist:
        add_first("VECTOR_C", 2, "duplicate_distinct_increment", "SINGLE-LANE-LIFECYCLE-01", o_dist, n_dist)

    # D/E F1M9
    for phase in ("fresh", "stale"):
        oa = old["vectors"]["D_E"][phase]["old_presence_alpha_allowed"]
        na = new["vectors"]["D_E"][phase]["new_consumer_alpha_allowed"]
        # On historical executor, keys are old_presence; on current both exist
        if "new_consumer_alpha_allowed" in old["vectors"]["D_E"][phase]:
            oa = old["vectors"]["D_E"][phase]["new_consumer_alpha_allowed"]
        oc = new["vectors"]["D_E"][phase].get("new_consumer_alpha_allowed")
        if phase == "fresh":
            report["comparisons"][f"f1m9_{phase}_alpha"] = _classify_checkpoint(oa, oc)
        else:
            # stale: compare old presence vs new consumer
            op = old["vectors"]["D_E"][phase]["old_presence_alpha_allowed"]
            np = new["vectors"]["D_E"][phase]["new_consumer_alpha_allowed"]
            if op != np:
                add_first(
                    "VECTOR_E",
                    0,
                    "alpha_scope_entry_authority_allowed",
                    "F1M9-MAX-AGE-ENFORCEMENT-01",
                    op,
                    np,
                )
                report["comparisons"]["f1m9_stale_alpha"] = "BEHAVIORALLY_DIVERGENT"
            else:
                report["comparisons"]["f1m9_stale_alpha"] = "IDENTICAL"

    # F recon — expect identical at replay enum level
    for i, (oc, nc) in enumerate(
        zip(old["vectors"]["F"]["cases"], new["vectors"]["F"]["cases"], strict=True)
    ):
        cls = _classify_checkpoint(oc["decision_outcome"], nc["decision_outcome"])
        report["comparisons"][f"vector_F_{i}"] = cls

    # G two-cycle carrier
    for i in range(min(len(old["vectors"]["G"]["cycles"]), len(new["vectors"]["G"]["cycles"]))):
        ob = old["vectors"]["G"]["cycles"][i].get("carrier_after")
        nb = new["vectors"]["G"]["cycles"][i].get("carrier_after")
        if ob != nb:
            add_first(
                "VECTOR_G",
                i,
                "carrier_after",
                "SINGLE-LANE-LIFECYCLE-01",
                ob,
                nb,
            )
            report["comparisons"][f"vector_G_cycle_{i}_carrier"] = "BEHAVIORALLY_DIVERGENT"
        else:
            report["comparisons"][f"vector_G_cycle_{i}_carrier"] = "IDENTICAL"

    # G17 policy string
    og = old["vectors"].get("G17", {}).get("estimate_absent_policy")
    ng = new["vectors"].get("G17", {}).get("estimate_absent_policy")
    if og and ng and og != ng:
        add_first("G17", 0, "estimate_absent_policy", "G17-CMC-BIND-01", og, ng)
        report["comparisons"]["g17_policy"] = "STRUCTURALLY_DIFFERENT_SEMANTICALLY_EQUIVALENT"

    # H layered markers
    report["layered_core_markers"] = {
        "historical": _layered_markers(WT),
        "current": _layered_markers(REPO),
    }
    hm = report["layered_core_markers"]["historical"]
    cm = report["layered_core_markers"]["current"]
    if hm != cm:
        report["comparisons"]["vector_H_layered_init"] = "BEHAVIORALLY_DIVERGENT"
        add_first(
            "VECTOR_H",
            0,
            "observation_init_helpers",
            "LAYERED-CORE-OBS-INIT-01",
            hm,
            cm,
        )
    else:
        report["comparisons"]["vector_H_layered_init"] = "IDENTICAL"

    # I provenance — CURRENT only feature
    report["comparisons"]["vector_I"] = "CURRENT_SAFETY_BOUNDARY_ONLY"

    return report


def main() -> int:
    _run_side("current", REPO, CURRENT_JSON)
    _run_side("historical", WT, HIST_JSON)
    old = json.loads(HIST_JSON.read_text(encoding="utf-8"))
    new = json.loads(CURRENT_JSON.read_text(encoding="utf-8"))
    diff = _compare_vectors(old, new)
    payload = {
        "wp_id": "DOUBLE_PLAY_DIFFERENTIAL_GOLDEN_VECTOR_V1",
        "current_sha": new["repository_sha"],
        "historical_sha": old["repository_sha"],
        "wp1_minimal_divergence_set": [
            "F1M9-CONSUMER-PATH-01",
            "F1M9-MAX-AGE-ENFORCEMENT-01",
            "G17-CMC-BIND-01",
            "SINGLE-LANE-LIFECYCLE-01",
            "LAYERED-CORE-OBS-INIT-01",
            "RECON-ADMISSION-GATE-01",
        ],
        "side_current": new,
        "side_historical": old,
        "differential": diff,
    }
    DIFF_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {DIFF_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
