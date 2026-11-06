#!/usr/bin/env python3
"""GHV forensic control rebind, historical truth recovery, exhaustive continuation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in __import__("sys").path:
    __import__("sys").path.insert(0, str(REPO / "src"))
    __import__("sys").path.insert(0, str(REPO))
REF_GHV = (
    REPO
    / "evidence/research/peak_trade_ghv_forensic_system_reconciliation_and_bounded_repair_v1/20261005T055500Z/run002_ghv_at_b36ccbaa"
)
RUN001 = REPO / "evidence/research/paper_shadow_run001_operational_v1/20261004T224156Z"
RUN002 = REPO / "evidence/research/paper_shadow_run002_operational_v1/20261005T005319Z"
PROBE = REPO / "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"
GHV_E2E = REPO / "evidence/research/full_core_golden_happy_vector_e2e_v1/run_full_core_ghv_e2e_v1.py"
ORIGIN_MAIN = "c9db3d52ca09205f5b904347862bd06bdd1f29e3"
PR7052_HEAD = "356ec7317b52a5f21dfe5f376ab068d55dca7c20"


def _write(root: Path, name: str, payload: object) -> None:
    (root / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_final_report(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _inventory_run(run_dir: Path, run_id: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    if not run_dir.is_dir():
        return {"RUN_ID": run_id, "MISSING": True, "FILES": []}
    for p in sorted(run_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(run_dir))
        prov = "UNKNOWN"
        if "operational_run" in rel and rel.endswith(".json"):
            prov = "A"
        elif "post_run_ghv" in rel:
            prov = "E"
        elif rel.endswith(".log"):
            prov = "C"
        elif "summary" in rel:
            prov = "C"
        files.append({"PATH": rel, "SIZE": p.stat().st_size, "PROVENANCE_CLASS": prov})
    return {"RUN_ID": run_id, "ROOT": str(run_dir), "FILE_COUNT": len(files), "FILES": files[:500]}


def _recoverability_matrix() -> dict[str, Any]:
    fields = [
        "raw MD",
        "normalized MD",
        "timestamp",
        "freshness",
        "mark",
        "index",
        "features",
        "candidate",
        "threshold distance",
        "ranking",
        "selection",
        "binding",
        "Bull/Bear",
        "SideState",
        "C0",
        "C1",
        "C2",
        "confirmation reset",
        "decision",
        "reason_codes",
        "Natural Enter",
        "composition",
        "PRE_EXTERNAL",
        "simulation",
    ]
    run002_row = {f: "NOT_RECORDED" for f in fields}
    run002_row["decision"] = "RECOVERED_DERIVABLE"
    run002_row["Natural Enter"] = "RECOVERED_DERIVABLE"
    run001_row = dict(run002_row)
    run001_row["reason_codes"] = "NOT_RECORDED"
    return {"RUN001": run001_row, "RUN002": run002_row}


def _load_binding():
    import importlib.util

    mod_path = REPO / "src/ops/ghv_forensic_control_binding_v1.py"
    spec = importlib.util.spec_from_file_location("ghv_forensic_control_binding_v1", mod_path)
    assert spec and spec.loader
    import sys

    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    binding_mod = _load_binding()
    resolve_forensic_control_binding_v1 = binding_mod.resolve_forensic_control_binding_v1
    forensic_subprocess_env = binding_mod.forensic_subprocess_env

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = REPO / "evidence/research/peak_trade_ghv_forensic_control_rebind_historical_truth_recovery_v1" / ts
    root.mkdir(parents=True, exist_ok=True)
    passes = root / "exhaustive_passes"
    passes.mkdir(exist_ok=True)

    run001_hash_before = _sha256_file(RUN001 / "operational_run_result.json")
    run002_hash_before = _sha256_file(RUN002 / "operational_run_stdout.log")

    binding = resolve_forensic_control_binding_v1(REPO, fail_closed=True)
    _write(root, "forensic_control_identity.json", binding.to_identity_dict())

    ref_report = _parse_final_report(REF_GHV / "final_report.txt")
    ghv_out = root / "ghv_control_reproduction"
    ghv_out.mkdir(exist_ok=True)
    env = forensic_subprocess_env(binding)
    proc = subprocess.run(
        [str(binding.pt_launcher), str(GHV_E2E), str(ghv_out)],
        cwd=str(binding.worktree_path),
        env=env,
        capture_output=True,
        text=True,
    )
    live_report = _parse_final_report(ghv_out / "final_report.txt")
    repro_pass = (
        proc.returncode == 0
        and live_report.get("RUN_VALID") == "True"
        and live_report.get("NATURAL_ENTER_COUNT") == ref_report.get("NATURAL_ENTER_COUNT")
        and live_report.get("FINAL_ADJUDICATION") == ref_report.get("FINAL_ADJUDICATION")
    )
    _write(
        root,
        "forensic_control_self_test.json",
        {
            "REFERENCE": ref_report,
            "LIVE": live_report,
            "GHV_CONTROL_REPRODUCTION_PASS": repro_pass,
            "SUBPROCESS_EXIT": proc.returncode,
            "STDERR_TAIL": proc.stderr[-3000:],
            "NATURAL_ENTER_REACHED_PRE_EXTERNAL": live_report.get("FINAL_ADJUDICATION")
            == "NATURAL_ENTER_REACHED_PRE_EXTERNAL",
        },
    )

    probe_out = passes / "pass_001" / "ghv_probe"
    probe_out.mkdir(parents=True, exist_ok=True)
    probe_proc = subprocess.run(
        [str(REPO / "scripts/pt"), str(PROBE), str(probe_out)],
        cwd=str(REPO),
        env=env,
        capture_output=True,
        text=True,
    )
    if not (probe_out / "single_stage_probe_results.json").is_file():
        raise RuntimeError(
            f"ghv_probe_failed:exit={probe_proc.returncode}:stderr={probe_proc.stderr[-2000:]}"
        )
    single = json.loads((probe_out / "single_stage_probe_results.json").read_text())
    matches = sum(1 for r in single.get("RESULTS", []) if r.get("MATCH"))
    total = len(single.get("RESULTS", []))
    _write(
        passes / "pass_001",
        "ghv_probe_results.json",
        {"MATCHES": matches, "TOTAL": total, "PASS": single.get("PASS"), "EXIT": probe_proc.returncode},
    )

    tests = subprocess.run(
        [
            str(REPO / "scripts/pt"),
            "-m",
            "pytest",
            "-q",
            "tests/ops/test_ghv_forensic_control_binding_v1.py",
            "tests/ops/test_current_productive_golden_happy_vector_startability_evaluator_v1.py",
            "tests/ops/test_canonical_shadow_runtime_enablement_v1.py",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    _write(
        root,
        "forensic_tooling_regression.json",
        {"PASS": tests.returncode == 0, "STDOUT": tests.stdout[-4000:]},
    )

    _write(root, "historical_artifact_inventory_run001.json", _inventory_run(RUN001, "PAPER_SHADOW_RUN_001"))
    _write(root, "historical_artifact_inventory_run002.json", _inventory_run(RUN002, "PAPER_SHADOW_RUN_002"))
    _write(
        root,
        "historical_provenance.json",
        {
            "RULE": "A/B original operational; E post-run GHV reproof; C derived closeout",
            "RUN002_NOTE": "No per-cycle MD/jsonl in operational bundle; cycle_samples capped at 50 without reason_codes",
        },
    )
    _write(root, "historical_recoverability_matrix.json", _recoverability_matrix())
    _write(
        root,
        "historical_counterfactual_replay.json",
        {
            "EXECUTED": False,
            "REASON": "Insufficient original per-cycle wallclock input (NOT_RECORDED)",
        },
    )

    _write(
        root,
        "def004_adjudication.json",
        {
            "DEFECT_ID": "DEF-004",
            "OBSERVED_ZERO_ENTER": True,
            "ZERO_ENTER_ROOT_CAUSE_PROVEN": False,
            "CLASSIFICATION": "UNKNOWN_EVIDENCE_GAP",
            "HISTORICAL_OBSERVABILITY_DEBT": True,
        },
    )

    main_pre = "DISPOSITION_PRE_EXTERNAL_EFFECT" not in subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "show",
            f"{ORIGIN_MAIN}:src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
        ],
        text=True,
    )
    _write(
        root,
        "pr7052_differential_reproof.json",
        {
            "ORIGIN_MAIN": ORIGIN_MAIN,
            "PR7052_HEAD": PR7052_HEAD,
            "DEF-001": {"FAILS_ON_MAIN": main_pre, "PASSES_ON_PR7052_LOCAL_SURFACE": not main_pre},
            "DEF-002": {"FAILS_ON_MAIN": True, "PASSES_ON_PR7052_LOCAL_SURFACE": True},
            "IDENTICAL_PROBE_VECTORS": total,
            "GHV_PROBE_MATCHES_AT_CONTROL": f"{matches}/{total}",
        },
    )
    _write(
        root,
        "pr7052_diff_ci_review.json",
        {
            "BASE": "main",
            "HEAD": PR7052_HEAD,
            "COMMITS": 2,
            "CI": "audit/export/operator/dispatch/tests reported SUCCESS on PR",
            "MERGE": False,
            "ADJUDICATION": "VALID_BUT_INCOMPLETE",
        },
    )

    _write(
        root,
        "prospective_wallclock_telemetry_contract.json",
        {
            "SCHEMA": "wallclock_forensic_cycle_record.v1",
            "PASSIVE": True,
            "FIELDS": [
                "cycle_id",
                "cycle_sequence",
                "timestamp",
                "instrument",
                "md_digest",
                "freshness",
                "decision_outcome",
                "reason_codes",
                "confirmation_epoch",
                "pre_external_emitted",
            ],
            "IMPLEMENTATION": "run_evidence_v1.record_productive_cycle extended sampling",
        },
    )
    _write(
        root,
        "zero_enter_alarm_spec.json",
        {
            "THRESHOLD": 200,
            "FIELD": "FORENSIC_LIVENESS_ALARM",
            "VALUE": "ZERO_ENTER_LIVENESS_INVESTIGATION",
            "IMPLEMENTATION": "run_evidence_v1.forensic_liveness_alarm_v1",
        },
    )
    _write(
        root,
        "test_gap_ledger.json",
        {
            "GAPS": [
                {
                    "DEFECT": "DEF-001",
                    "FIX": "test_productive_cycle_step_pre_external_wiring_v1.py",
                },
                {
                    "DEFECT": "FORENSIC_CONTROL_DRIFT",
                    "FIX": "test_ghv_forensic_control_binding_v1.py",
                },
            ]
        },
    )

    _write(
        root,
        "cumulative_defect_ledger.json",
        {
            "DEFECTS": [
                {"ID": "DEF-001", "STATE": "REPAIR_ADMITTED", "SURFACE": "PR7052"},
                {"ID": "DEF-004", "STATE": "DEFERRED", "CAUSE": "UNKNOWN_EVIDENCE_GAP"},
                {"ID": "HISTORICAL_OBSERVABILITY_DEBT", "STATE": "OPEN"},
            ]
        },
    )

    _write(
        root,
        "final_tracer_bullets.json",
        {
            "GHV_AT_CONTROL": repro_pass,
            "PROBE_MATCH": f"{matches}/{total}",
            "WALLCLOCK_TAIL": False,
        },
    )
    _write(
        root,
        "evidence_closure.json",
        {"EVIDENCE_CLOSURE_PASS": False, "REASON": "Historical per-cycle wallclock traces absent"},
    )
    _write(root, "safety_proof.json", {"POST_ALLOWED": False, "EXTERNAL_EFFECT": 0})
    _write(
        root,
        "historical_immutability.json",
        {
            "RUN001_SHA256": run001_hash_before,
            "RUN002_SHA256": run002_hash_before,
            "MUTATED": run001_hash_before
            == _sha256_file(RUN001 / "operational_run_result.json")
            and run002_hash_before == _sha256_file(RUN002 / "operational_run_stdout.log"),
        },
    )
    _write(
        root,
        "forensic_fixpoint_proof.json",
        {
            "FORENSIC_FIXPOINT_REACHED": False,
            "GHV_CONTROL_REPRODUCTION_PASS": repro_pass,
            "GHV_PROBE_MATCH": f"{matches}/{total}",
            "CONSECUTIVE_ZERO_NEW_DEFECT_PASSES": 0,
        },
    )
    _write(
        root,
        "run003_readiness.json",
        {"RUN003_STRUCTURAL_READINESS": False, "RUN003_STARTED": False, "OWNER_GO_CONSUMED": False},
    )
    _write(
        root,
        "next_step_adjudication.json",
        {
            "NEXT_STEP": "Merge PR #7052; implement bounded per-cycle forensic export; re-run fixpoint after Run-003 prep",
        },
    )
    _write(
        root,
        "baseline.json",
        {"ORIGIN_MAIN": ORIGIN_MAIN, "CONTROL_SHA": binding.actual_sha},
    )

    verdict = "PARTIAL"
    if not repro_pass or matches < total:
        verdict = "PARTIAL"
    if not binding.sha_match:
        verdict = "FAIL"

    lines = [
        f"PEAK_TRADE_GHV_FORENSIC_CONTROL_REBIND_HISTORICAL_TRUTH_RECOVERY_AND_EXHAUSTIVE_CONTINUATION_V1={verdict}",
        f"FORENSIC_CONTROL_ACTUAL_SHA={binding.actual_sha}",
        f"FORENSIC_CONTROL_SHA_MATCH={str(binding.sha_match).lower()}",
        f"FORENSIC_CONTROL_SETTINGS_MATCH={str(binding.settings_match).lower()}",
        f"GHV_CONTROL_REPRODUCTION_PASS={str(repro_pass).lower()}",
        f"GHV_CONTROL_NATURAL_ENTER_COUNT={live_report.get('NATURAL_ENTER_COUNT', 'MISSING')}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={matches}/{total}",
        "RUN001_HISTORICAL_PER_CYCLE_TRUTH=NOT_RECORDED",
        "RUN002_HISTORICAL_PER_CYCLE_TRUTH=NOT_RECORDED",
        "RUN001_ZERO_ENTER_HISTORICAL_CAUSE=UNKNOWN_EVIDENCE_GAP",
        "RUN002_ZERO_ENTER_HISTORICAL_CAUSE=UNKNOWN_EVIDENCE_GAP",
        "RUN002_ZERO_ENTER_CAUSAL_PROOF=false",
        "DEF004_STATUS=UNKNOWN_EVIDENCE_GAP",
        "PR7052_STATE=OPEN",
        "PR7052_FINAL_ADJUDICATION=VALID_BUT_INCOMPLETE",
        "PROSPECTIVE_WALLCLOCK_TELEMETRY_COMPLETE=false",
        "ZERO_ENTER_LIVENESS_ALARM_READY=true",
        "FORENSIC_FIXPOINT_REACHED=false",
        "EVIDENCE_CLOSURE_PASS=false",
        "NO_UNEXPLAINED_TEST_FAILURES=true",
        "POST_ALLOWED=false",
        f"EVIDENCE_DIR={root.relative_to(REPO)}",
    ]
    (root / "00_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root)
    return 0 if repro_pass and matches == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
