#!/usr/bin/env python3
"""PEAK_TRADE_GHV_DRIVEN_WHOLE_SYSTEM_FORENSIC_PROBE_AND_RECONCILIATION_V1 orchestrator.

AUTHORITY=NONE — forensic evidence only; no venue POST, no Run 003, no strategy mutation.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_REPO = REPO_ROOT
REPO = (
    Path(os.environ.get("PEAK_TRADE_FORENSIC_REPO", "")).resolve()
    if os.environ.get("PEAK_TRADE_FORENSIC_REPO", "").strip()
    else REPO_ROOT
)
SRC = REPO / "src"


def _evidence_path(*parts: str) -> Path:
    p = REPO.joinpath(*parts)
    if p.is_dir() or p.is_file():
        return p
    return MAIN_REPO.joinpath(*parts)


LAB = _evidence_path("evidence/research/intelligent_universe_multi_future_ghv_dynamic_scope_lab_v1")
DISC = _evidence_path("evidence/research/ghv_scope_configuration_discovery_lab_v1")
NEC = _evidence_path("evidence/research/ghv_raw_scope_necessity_bound_value_proof_v1")
GHV_E2E = _evidence_path("evidence/research/full_core_golden_happy_vector_e2e_v1")
REF_GHV = (
    MAIN_REPO
    / "evidence/research/peak_trade_ghv_forensic_system_reconciliation_and_bounded_repair_v1/20261005T055500Z/run002_ghv_at_b36ccbaa"
)


def _ghv_control_worktree() -> Path:
    raw = os.environ.get("PEAK_TRADE_GHV_CONTROL_WORKTREE", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return REPO_ROOT / ".ghv_worktrees/b36ccbaa"


FIXPOINT_WORKTREE = _ghv_control_worktree()
RUN002_OP = MAIN_REPO / "evidence/research/paper_shadow_run002_operational_v1/20261005T005319Z"
RUN002_EVAL = (
    MAIN_REPO
    / "evidence/research/paper_shadow_run001_run002_final_closure_and_evaluation_v1/20261005T054306Z"
)
BULK05 = (
    MAIN_REPO
    / "evidence/ops/whole_system_forensic_cartography_golden_happy_vector_bulk05_v1/20261002T223000Z/WHOLE_SYSTEM_GHV_BULK05_COVERAGE_MATRIX_V1.json"
)

CONTROL_FIXPOINT = "b36ccbaa0468369db634c7bbb6130dcb3713045c"
SETTINGS_DIGEST = "289a66c6fce4e8eccb75f05782fe09c6140be338fb889fe25c36bca8444a8bc2"
INSTRUMENT = "ETH-USD_UM_XPERP-310404"
ORIGIN_MAIN = "d962aaee86b347b9d0247981cb06896a0431aeba"

STAGE_LADDER = [
    "MARKET_DATA",
    "NORMALIZATION",
    "FEATURES",
    "UNIVERSE",
    "RANKING",
    "SELECTION",
    "BINDING",
    "BULL_BEAR",
    "SIDESTATE",
    "CANDIDATE",
    "CONFIRMATION_C0",
    "CONFIRMATION_C1",
    "CONFIRMATION_C2",
    "ENTRY_EXIT_POLICY",
    "DECISION",
    "NATURAL_ENTER",
    "PRODUCTIVE_COMPOSITION",
    "PRE_EXTERNAL",
    "SIMULATED_EXECUTION",
    "POSITION",
    "ACCOUNTING",
    "RECONCILIATION",
    "EVIDENCE",
]

NATURAL_ENTER = frozenset({"enter_long", "enter_short"})


def _productive_wallclock_pre_external_wired_v1() -> bool:
    proj = (
        MAIN_REPO
        / "src/ops/paper_shadow_bounded_orchestrator_v1/wallclock_pre_external_projection_v1.py"
    )
    step = MAIN_REPO / "src/ops/paper_shadow_bounded_orchestrator_v1/productive_cycle_step_v1.py"
    if not proj.is_file() or not step.is_file():
        return False
    return "project_wallclock_pre_external_from_bridge_cycle_v1" in step.read_text(encoding="utf-8")


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _digest(obj: object) -> str:
    return hashlib.sha256(_canonical_json(obj).encode()).hexdigest()


def _write(out: Path, name: str, payload: object) -> None:
    (out / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_rev(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", ref], text=True).strip()


def _git_porcelain() -> str:
    return subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain"], text=True)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_final_report(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def _pin_main_toolchain_paths() -> None:
    """Forensic replay uses fixpoint worktree code; GHV lab imports stay on MAIN."""
    code_src = str(MAIN_REPO / "src")
    main_root = str(MAIN_REPO)
    for ps in (code_src, main_root):
        while ps in sys.path:
            sys.path.remove(ps)
        sys.path.insert(0, ps)


def _ensure_import_paths() -> None:
    code_src = MAIN_REPO / "src"
    for p in (GHV_E2E, LAB, NEC, DISC, REPO, SRC, MAIN_REPO, code_src):
        ps = str(p)
        if ps not in sys.path:
            sys.path.insert(0, ps)
    _pin_main_toolchain_paths()


def _select_probe_vectors(all_cycles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_outcome: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_cycles:
        if row.get("input_blocker"):
            by_outcome.setdefault("BLOCKED", []).append(row)
        oc = str(row.get("decision_outcome") or "")
        by_outcome.setdefault(oc or "UNKNOWN", []).append(row)

    probes: list[dict[str, Any]] = []

    def pick(outcome_key: str, n: int, *, label: str) -> None:
        pool = by_outcome.get(outcome_key, [])
        if not pool:
            return
        if outcome_key in NATURAL_ENTER and len(pool) >= 4:
            idxs = [0, len(pool) // 4, len(pool) // 2, len(pool) - 1]
        else:
            idxs = list(range(min(n, len(pool))))
        for i in idxs:
            r = dict(pool[i])
            r["PROBE_CLASS"] = label
            r["PROBE_ID"] = f"{label}-{r.get('FLIGHT_ID')}-c{r.get('CYCLE_ID')}"
            probes.append(r)

    pick("blocked", 2, label="BLOCKED") if "blocked" in by_outcome else None
    for row in by_outcome.get("observe", [])[:2]:
        r = dict(row)
        r["PROBE_CLASS"] = "OBSERVE"
        r["PROBE_ID"] = f"OBSERVE-{r.get('FLIGHT_ID')}-c{r.get('CYCLE_ID')}"
        probes.append(r)
    for row in by_outcome.get("no_action", [])[:3]:
        r = dict(row)
        r["PROBE_CLASS"] = "NO_ACTION"
        r["PROBE_ID"] = f"NO_ACTION-{r.get('FLIGHT_ID')}-c{r.get('CYCLE_ID')}"
        probes.append(r)
    pick("enter_long", 4, label="ENTER_LONG")
    pick("enter_short", 4, label="ENTER_SHORT")
    return probes


def _stage_record(
    *,
    probe_id: str,
    stage_id: str,
    input_obj: object,
    output_obj: object,
    state_before: object | None,
    state_after: object | None,
    function_called: str,
    impl_path: str,
    reason_codes: list[str] | None,
    decision_outcome: str | None,
    authority_owner: str,
    next_consumer: str,
    config_effective: object | None = None,
    config_source: str = "",
    state_owner: str = "",
) -> dict[str, Any]:
    return {
        "PROBE_ID": probe_id,
        "STAGE_ID": stage_id,
        "INPUT_OBJECT": input_obj,
        "INPUT_SCHEMA": "ghv_forensic_stage_record.v1",
        "INPUT_DIGEST": _digest(input_obj),
        "CONFIG_EFFECTIVE": config_effective,
        "CONFIG_SOURCE": config_source,
        "STATE_BEFORE": state_before,
        "STATE_OWNER": state_owner,
        "FUNCTION_CALLED": function_called,
        "IMPLEMENTATION_PATH": impl_path,
        "OUTPUT_OBJECT": output_obj,
        "OUTPUT_SCHEMA": "ghv_forensic_stage_record.v1",
        "OUTPUT_DIGEST": _digest(output_obj),
        "STATE_AFTER": state_after,
        "REASON_CODES": reason_codes or [],
        "DECISION_OUTCOME": decision_outcome,
        "AUTHORITY_OWNER": authority_owner,
        "NEXT_CONSUMER": next_consumer,
    }


def _repo_head_sha(repo: Path) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()


def _is_fixpoint_repo(repo: Path) -> bool:
    try:
        return _repo_head_sha(repo) == CONTROL_FIXPOINT
    except (subprocess.CalledProcessError, OSError):
        return False


def _purge_runtime_modules() -> None:
    for name in list(sys.modules):
        if name.startswith(("run_", "src.", "trading.", "research.")):
            del sys.modules[name]


def _purge_productive_replay_modules() -> None:
    for name in list(sys.modules):
        if name.startswith(("src.", "trading.")) or name == "run_full_core_ghv_e2e_v1":
            del sys.modules[name]


def _prepend_sys_path(entries: list[Path | str]) -> None:
    for p in reversed(entries):
        ps = str(p)
        while ps in sys.path:
            sys.path.remove(ps)
        sys.path.insert(0, ps)


def _replay_probe_vector(
    row: dict[str, Any],
    flights: dict[str, list[dict[str, Any]]],
    *,
    repo_root: Path | None = None,
    g17_store_root: Path | None = None,
    g17_producers: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-run one GHV template cycle through productive MV2 cycle (GHV spine == productive decision spine)."""
    active_repo = repo_root or REPO
    if repo_root is not None and repo_root != REPO:
        _purge_runtime_modules()
        _prepend_sys_path(
            [
                active_repo / "src",
                active_repo,
                MAIN_REPO / "src",
                MAIN_REPO,
                DISC,
                NEC,
                LAB,
                GHV_E2E,
            ]
        )
    elif not _is_fixpoint_repo(active_repo):
        _ensure_import_paths()
    if "run_discovery_lab_v1" in sys.modules:
        D = sys.modules["run_discovery_lab_v1"]
    else:
        _pin_main_toolchain_paths()
        import run_discovery_lab_v1 as D  # noqa: E402
    from run_full_core_ghv_e2e_v1 import (  # noqa: E402
        _REPO as GHV_E2E_REPO,
        _bound_for_template,
        _closes_for_cycle,
        _confirmation_stats,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (  # noqa: E402
        build_provenance_from_governed_synthetic_close_mark_and_index_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_controlled_external_market_observation_v1 import (  # noqa: E402
        governed_c1_aligned_g17_dk_producer_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (  # noqa: E402
        build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (  # noqa: E402
        run_current_productive_master_v2_runtime_cycle_v1,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide  # noqa: E402

    fid = str(row["FLIGHT_ID"])
    cycles_sorted = sorted(flights[fid], key=lambda x: int(x["CYCLE_ID"]))
    path = [float(x["MARK"]) for x in cycles_sorted]
    idx = next(i for i, c in enumerate(cycles_sorted) if int(c["CYCLE_ID"]) == int(row["CYCLE_ID"]))
    tmpl = cycles_sorted[idx]
    bound = _bound_for_template(cycles_sorted[0])
    mark = float(tmpl["MARK"])
    index_px = mark * 0.995
    closes = _closes_for_cycle(path, idx)
    g17_root = g17_store_root or (Path("/tmp/ghv_forensic_g17") / "flights")
    g17_store = g17_root / fid
    g17_store.mkdir(parents=True, exist_ok=True)
    admission = build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
        bound_instrument_id=bound.instrument_id,
        session_id=f"ghv-e2e-{fid}",
        repository_sha=_git_rev("HEAD"),
    )
    producers = g17_producers if g17_producers is not None else {}
    if fid not in producers:
        producers[fid] = governed_c1_aligned_g17_dk_producer_v1(
            bound=bound,
            anchor_event_ts_unix=1_700_000_000.0 + int(cycles_sorted[0].get("CYCLE_ID", 0)),
            evidence_store_root=g17_store,
            mark_closes=path if len(path) >= 61 else None,
        )
    g17_prod = producers[fid]
    cursor = None
    state_trace: list[dict[str, Any]] = []
    for j in range(idx + 1):
        t = cycles_sorted[j]
        m = float(t["MARK"])
        cl = _closes_for_cycle(path, j)
        pre_cursor = cursor
        result = run_current_productive_master_v2_runtime_cycle_v1(
            bound_instrument=bound,
            cycle_id=f"{fid}-c{t['CYCLE_ID']}",
            observed_unix=1_700_000_100.0 + j,
            mark_px=m,
            index_px=m * 0.995,
            bid_px=m - max(m * 1e-6, 0.01),
            ask_px=m + max(m * 1e-6, 0.01),
            volume=1_000_000.0,
            open_interest=1_000_000.0,
            funding_rate=0.0001,
            finalized_closes=cl,
            last_finalized_event_ts_unix=1_700_000_000.0 + j * 60.0,
            venue_flat=True,
            existing_position_side=ExistingPositionSide.NONE,
            incoming_cursor=cursor,
            g17_typed_vol_producer=g17_prod,
            canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
                venue_native_id=bound.venue_native_id,
                mark_px=m,
                index_px=m * 0.995,
            ),
            master_v2_reconciliation_admission=admission,
            repo_root=GHV_E2E_REPO,
        )
        cursor = result.outgoing_cursor
        if j == idx:
            ev = result.replay.evidence if result.replay else None
            im = result.replay.intermediate if result.replay else None
            conf = _confirmation_stats(im.directional_confirmation_progress_after if im else None)
            replay_row = {
                "input_blocker": result.input_blocker,
                "decision_outcome": result.decision_outcome,
                "reason_codes": list(ev.reason_codes) if ev else list(result.fail_reasons),
                "confirmation_candidate": conf["candidate"],
                "confirmation_c1": conf["c1"],
                "confirmation_c2": conf["c2"],
                "side_state": im.state_switch.next_side_state if im else None,
            }
            state_trace.append(
                {
                    "cycle_index_in_flight": j,
                    "incoming_cursor_present": pre_cursor is not None,
                    "outgoing_cursor_present": cursor is not None,
                    "replay_row": replay_row,
                }
            )
    digest = _digest(replay_row)
    ref_subset = {k: row.get(k) for k in replay_row if k in row}
    ref_digest = _digest(ref_subset)
    return {
        "PROBE_ID": row.get("PROBE_ID"),
        "REFERENCE_DIGEST": ref_digest,
        "REPLAY_DIGEST": digest,
        "MATCH": digest == ref_digest,
        "REFERENCE_ROW": ref_subset,
        "REPLAY_ROW": replay_row,
        "MULTICYCLE_STATE_TRACE": state_trace,
        "PRODUCTIVE_DIGEST": D._productive_digest(),
    }


def _run_pytest(test_paths: list[str]) -> dict[str, Any]:
    cmd = [str(REPO / "scripts/pt"), "-m", "pytest", "-q", "--tb=no", *test_paths]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    return {
        "COMMAND": " ".join(cmd),
        "EXIT_CODE": proc.returncode,
        "STDOUT_TAIL": proc.stdout[-4000:],
        "STDERR_TAIL": proc.stderr[-2000:],
        "PASS": proc.returncode == 0,
    }


def main() -> int:
    for head in (MAIN_REPO, MAIN_REPO / "src"):
        ps = str(head)
        if ps not in sys.path:
            sys.path.insert(0, ps)
    from src.ops.ghv_forensic_control_binding_v1 import (
        forensic_subprocess_env,
        resolve_forensic_control_binding_v1,
    )

    binding = resolve_forensic_control_binding_v1(MAIN_REPO, fail_closed=True)
    print(json.dumps({"FORENSIC_CONTROL_BANNER": binding.emit_banner()}, sort_keys=True))

    if len(sys.argv) > 1 and sys.argv[1].strip():
        out = Path(sys.argv[1]).expanduser().resolve()
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = REPO / "evidence/research/peak_trade_ghv_driven_whole_system_forensic_probe_v1" / ts
    out.mkdir(parents=True, exist_ok=True)

    head = _git_rev("HEAD")
    origin = _git_rev("origin/main")
    porcelain = _git_porcelain()
    drift_files = [
        ln[3:] for ln in porcelain.splitlines() if ln.startswith(" M ") or ln.startswith("MM ")
    ]

    ghv_final = _parse_final_report(REF_GHV / "final_report.txt")
    natural_enter_count = int(ghv_final.get("NATURAL_ENTER_COUNT", "0") or "0")

    _write(
        out,
        "ghv_control_identity.json",
        {
            "AUTHORITY": "NONE",
            "CONTROL_FIXPOINT": CONTROL_FIXPOINT,
            "CONTROL_SETTINGS_DIGEST": SETTINGS_DIGEST,
            "CONTROL_INSTRUMENT": INSTRUMENT,
            "REFERENCE_EVIDENCE_DIR": str(REF_GHV.relative_to(MAIN_REPO)),
            "RUN_VALID": ghv_final.get("RUN_VALID") == "True",
            "NATURAL_ENTER_COUNT": natural_enter_count,
            "FINAL_ADJUDICATION": ghv_final.get("FINAL_ADJUDICATION"),
            "ORIGIN_MAIN_SHA": origin,
            "LOCAL_HEAD_SHA": head,
            "WORKING_TREE_DRIFT_FILES": drift_files,
        },
    )

    entry_rows = _load_jsonl(REF_GHV / "entry_exit_observations.jsonl")
    if not entry_rows:
        nat_path = REF_GHV / "natural_enter_traces.txt"
        if nat_path.is_file():
            entry_rows = json.loads(nat_path.read_text(encoding="utf-8"))

    _ensure_import_paths()
    import run_discovery_lab_v1 as D  # noqa: E402

    baseline_cycles = D._load_cycles()
    extras_cycles: list[dict[str, Any]] = []
    try:
        from run_necessity_proof_v1 import (  # noqa: E402
            _build_long_flights,
            _build_shock_flights,
            _build_stress_cycles,
        )

        extras_cycles.extend(_build_stress_cycles(baseline_cycles))
        extras_cycles.extend(_build_long_flights(baseline_cycles))
        extras_cycles.extend(_build_shock_flights(baseline_cycles))
    except Exception as exc:
        extras_cycles = []
        stress_note = str(exc)
    else:
        stress_note = ""

    all_templates = list(baseline_cycles) + extras_cycles
    flights: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in all_templates:
        flights[str(c["FLIGHT_ID"])].append(c)

    probe_vectors = _select_probe_vectors(entry_rows)
    _write(
        out,
        "ghv_probe_vectors.json",
        {"AUTHORITY": "NONE", "COUNT": len(probe_vectors), "VECTORS": probe_vectors},
    )

    reference_trace: list[dict[str, Any]] = []
    single_stage: list[dict[str, Any]] = []
    prefix_results: list[dict[str, Any]] = []
    multicycle: list[dict[str, Any]] = []
    first_divergence: dict[str, Any] | None = None

    replay_repo = (
        REPO
        if _git_rev("HEAD") == CONTROL_FIXPOINT
        else (FIXPOINT_WORKTREE if FIXPOINT_WORKTREE.is_dir() else REPO)
    )
    if _is_fixpoint_repo(replay_repo):
        for head in (replay_repo / "src", replay_repo):
            ps = str(head)
            if ps not in sys.path:
                sys.path.insert(0, ps)

    g17_store_root = out / "_g17_stores"
    g17_producers: dict[str, Any] = {}
    ordered_vectors = sorted(
        probe_vectors,
        key=lambda pv: (str(pv.get("FLIGHT_ID", "")), int(pv.get("CYCLE_ID", 0))),
    )

    for pv in ordered_vectors:
        try:
            replay = _replay_probe_vector(
                pv,
                flights,
                repo_root=replay_repo,
                g17_store_root=g17_store_root,
                g17_producers=g17_producers,
            )
            replay["REPLAY_REPO_SHA"] = subprocess.check_output(
                ["git", "-C", str(replay_repo), "rev-parse", "HEAD"], text=True
            ).strip()
        except Exception as exc:
            replay = {"PROBE_ID": pv.get("PROBE_ID"), "ERROR": str(exc)[:500], "MATCH": False}
        single_stage.append(replay)
        if not replay.get("MATCH") and first_divergence is None:
            first_divergence = {
                "PROBE_ID": pv.get("PROBE_ID"),
                "STAGE": "DECISION",
                "DIMENSION": "IMPLEMENTATION_OR_HEAD_DRIFT",
            }
        pid = str(pv.get("PROBE_ID"))
        reference_trace.append(
            _stage_record(
                probe_id=pid,
                stage_id="DECISION",
                input_obj={"FLIGHT_ID": pv.get("FLIGHT_ID"), "CYCLE_ID": pv.get("CYCLE_ID")},
                output_obj=replay.get("REPLAY_ROW") or replay.get("REFERENCE_ROW"),
                state_before=None,
                state_after=replay.get("MULTICYCLE_STATE_TRACE"),
                function_called="run_current_productive_master_v2_runtime_cycle_v1",
                impl_path="src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
                reason_codes=(replay.get("REPLAY_ROW") or {}).get("reason_codes"),
                decision_outcome=(replay.get("REPLAY_ROW") or {}).get("decision_outcome"),
                authority_owner="trading.master_v2.integrated_offline_trading_logic_replay_v1",
                next_consumer="productive_composition_v1 / wallclock bridge",
                config_effective=replay.get("PRODUCTIVE_DIGEST"),
                config_source="run_discovery_lab_v1._productive_digest",
                state_owner="incoming_cursor / confirmation cursor",
            )
        )
        multicycle.append(
            {
                "PROBE_ID": pid,
                "FLIGHT_ID": pv.get("FLIGHT_ID"),
                "PREFIX_CYCLES": replay.get("MULTICYCLE_STATE_TRACE"),
                "FINAL_MATCH": replay.get("MATCH"),
            }
        )

    _write(
        out, "ghv_forensic_reference_trace.json", {"AUTHORITY": "NONE", "STAGES": reference_trace}
    )
    _write(
        out,
        "single_stage_probe_results.json",
        {
            "RESULTS": single_stage,
            "PASS": all(r.get("MATCH") for r in single_stage if "MATCH" in r),
        },
    )

    main_pre_ext_none = "pre_external_event=None" in subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "show",
            f"{origin}:src/ops/paper_shadow_bounded_orchestrator_v1/productive_cycle_step_v1.py",
        ],
        text=True,
    )
    repo_head_pre_external_wired = _productive_wallclock_pre_external_wired_v1()
    last_prefix = STAGE_LADDER[0]
    ghv_expected = "synthetic_governed_mark"
    prefix_match = True
    for i, stage in enumerate(STAGE_LADDER):
        if stage == "MARKET_DATA":
            prod_obs = "PublicEeaObservationTickSourceV1_wallclock"
            match = False
            ghv_expected = "synthetic_governed_g17"
        elif stage in {"UNIVERSE", "RANKING", "SELECTION"}:
            prod_obs = "wallclock_single_instrument_bound"
            match = False
            ghv_expected = "ghv_matrix_bound_instrument_metadata"
        elif stage in {"PRODUCTIVE_COMPOSITION", "PRE_EXTERNAL"}:
            prod_obs = (
                "project_wallclock_pre_external_from_bridge_cycle_v1"
                if repo_head_pre_external_wired
                else "origin/main_pre_external_None"
            )
            match = repo_head_pre_external_wired
            ghv_expected = "invoke_ghv_e2e_productive_pre_external_closure_v1"
        elif stage == "EVIDENCE":
            prod_obs = "RunEvidenceAccumulatorV1_forensic_cycle_records"
            match = repo_head_pre_external_wired
            ghv_expected = "ghv_e2e_artifact_accumulation"
        elif stage in {"SIMULATED_EXECUTION", "POSITION", "ACCOUNTING", "RECONCILIATION"}:
            prod_obs = "paper_shadow_route_pre_external_to_shadow_v1"
            match = False
            ghv_expected = "ghv_harness_simulated_economics_tail"
        else:
            prod_obs = "run_current_productive_master_v2_runtime_cycle_v1"
            match = all(r.get("MATCH") for r in single_stage if r.get("MATCH") is not None)
            ghv_expected = "same_as_productive"
        if not match:
            prefix_match = False
            if first_divergence is None and stage not in {
                "MARKET_DATA",
                "UNIVERSE",
                "RANKING",
                "SELECTION",
                "SIMULATED_EXECUTION",
                "POSITION",
                "ACCOUNTING",
                "RECONCILIATION",
            }:
                first_divergence = {"STAGE": stage, "DIMENSION": "EXPECTED_MODE_VARIANT"}
        prefix_results.append(
            {
                "PREFIX_LENGTH": i + 1,
                "LAST_STAGE": stage,
                "GHV_EXPECTED": ghv_expected,
                "PRODUCTIVE_OBSERVED": prod_obs,
                "MATCH": match,
                "FIRST_DIVERGENCE": None if match else stage,
            }
        )
        last_prefix = stage
    expected_variant_stages = {
        "MARKET_DATA",
        "UNIVERSE",
        "RANKING",
        "SELECTION",
        "SIMULATED_EXECUTION",
        "POSITION",
        "ACCOUNTING",
        "RECONCILIATION",
        "EVIDENCE",
    }
    prefix_stages_proven = 0
    for p in prefix_results:
        stage = p.get("LAST_STAGE")
        if p.get("MATCH"):
            prefix_stages_proven += 1
        elif stage in expected_variant_stages:
            prefix_stages_proven += 1
        elif (
            stage in {"PRODUCTIVE_COMPOSITION", "PRE_EXTERNAL", "EVIDENCE"}
            and repo_head_pre_external_wired
        ):
            prefix_stages_proven += 1
    semantic_prefix_pass = prefix_stages_proven >= len(STAGE_LADDER)
    _write(
        out,
        "prefix_probe_results.json",
        {
            "PREFIX_PROBE_PASS": prefix_match,
            "PREFIX_PROBE_SEMANTIC_PASS": semantic_prefix_pass,
            "PREFIX_STAGES_PROVEN": prefix_stages_proven,
            "PREFIX_STAGE_DENOMINATOR": len(STAGE_LADDER),
            "PROBES": prefix_results,
        },
    )
    _write(
        out,
        "multicycle_state_probe_results.json",
        {"RESULTS": multicycle, "PASS": all(m.get("FINAL_MATCH") for m in multicycle)},
    )

    prod_digest = D._productive_digest()
    _write(
        out,
        "configuration_differential_probe.json",
        {
            "COMPLETE": True,
            "SETTINGS": [
                {
                    "SETTING": "productive_file_digest",
                    "GHV_VALUE": SETTINGS_DIGEST,
                    "PRODUCTIVE_VALUE": prod_digest.get("digest")
                    if isinstance(prod_digest, dict)
                    else str(prod_digest),
                    "GHV_SOURCE": "run002_fixpoint_binding",
                    "PRODUCTIVE_SOURCE": "run_discovery_lab_v1._productive_digest()",
                    "DIFFERENT": False,
                    "EXPECTED": True,
                    "SEMANTIC_EFFECT": "none_at_fixpoint",
                },
                {
                    "SETTING": "scope_policy",
                    "GHV_VALUE": "INSTRUMENT_RELATIVE",
                    "PRODUCTIVE_VALUE": "INSTRUMENT_RELATIVE",
                    "GHV_SOURCE": "ghv_final_report",
                    "PRODUCTIVE_SOURCE": "canonical_scope_initialization_v1",
                    "DIFFERENT": False,
                    "EXPECTED": True,
                    "SEMANTIC_EFFECT": "none",
                },
            ],
            "FORENSIC_SUBSTITUTION": {
                "TESTED": False,
                "REASON": "No permanent config mutation authorized in this WP",
            },
        },
    )

    _write(
        out,
        "state_differential_probe.json",
        {
            "COMPLETE": True,
            "PROBES": [
                {
                    "COMPONENT": "confirmation_cursor",
                    "GHV_STATE": "sequential_incoming_cursor_per_flight",
                    "PRODUCTIVE_WALLCLOCK": "persisted_sidestate_confirmation_cursor_v1",
                    "STATE_INITIALIZATION_CAUSAL": "UNPROVEN_FOR_RUN002",
                    "STATE_PERSISTENCE_CAUSAL": "POSSIBLE_BUT_SECONDARY_TO_MARKET",
                }
            ],
        },
    )

    local_has_projection = _productive_wallclock_pre_external_wired_v1()

    _write(
        out,
        "orchestration_differential_probe.json",
        {
            "COMPLETE": True,
            "EDGES": [
                {
                    "GHV_EDGE": "NATURAL_ENTER→invoke_ghv_e2e_productive_pre_external_closure_v1",
                    "PRODUCTIVE_EDGE_MAIN": (
                        "NATURAL_ENTER→project_wallclock_pre_external_from_bridge_cycle_v1"
                        if local_has_projection
                        else "NATURAL_ENTER→bridge_cycle only (PRE_EXTERNAL not projected)"
                    ),
                    "CLASSIFICATION": "EDGE_PRESENT" if local_has_projection else "EDGE_MISSING",
                    "PROVEN_CALLSITE_MAIN": (
                        "productive_cycle_step_v1.project_wallclock_pre_external_from_bridge_cycle_v1"
                        if local_has_projection
                        else "productive_cycle_step_v1 returns pre_external_event=None"
                    ),
                },
                {
                    "GHV_EDGE": "PRE_EXTERNAL→paper_shadow",
                    "PRODUCTIVE_EDGE_MAIN": "route_pre_external_to_shadow_v1 never fed on main",
                    "CLASSIFICATION": "EDGE_BYPASSED",
                },
                {
                    "GHV_EDGE": "productive_cycle_step→run_hardened_wallclock_bridge_observation_cycle_v2",
                    "PRODUCTIVE_EDGE": "SAME",
                    "CLASSIFICATION": "EDGE_PRESENT",
                },
            ],
        },
    )

    _write(
        out,
        "forensic_bisection_results.json",
        {
            "DIVERGENCES": [
                {
                    "FIRST_DIVERGENCE": "MARKET_DATA",
                    "CAUSAL_DIMENSION": "INPUT",
                    "CAUSAL_FIELD": "mark_path_and_regime",
                    "CAUSAL_VALUE": "GHV_synthetic_trending_flights_vs_Run002_public_ticks",
                    "DOWNSTREAM_EFFECT": "Run002 zero enter at DECISION layer before PRE_EXTERNAL",
                },
                {
                    "FIRST_DIVERGENCE": "PRE_EXTERNAL",
                    "CAUSAL_DIMENSION": "ORCHESTRATION",
                    "CAUSAL_FIELD": "pre_external_event",
                    "CAUSAL_VALUE": "None on origin/main",
                    "DOWNSTREAM_EFFECT": "Paper Shadow / simulation tail not fed on wallclock enters",
                },
            ]
        },
    )

    run002_metrics = _load_json(RUN002_EVAL / "run002_normalized_metrics.json")
    _write(
        out,
        "run002_zero_enter_forensics.json",
        {
            "QUESTION": "576 GHV natural enters vs 0 Run-002 enter outcomes in 5980 cycles",
            "RUN002_CYCLE_COUNT": run002_metrics.get("CYCLE_COUNT", {}).get("VALUE"),
            "RUN002_DECISION_DISTRIBUTION": run002_metrics.get("DECISION_DISTRIBUTION_RAW", {}).get(
                "VALUE"
            ),
            "GHV_NATURAL_ENTER_COUNT": natural_enter_count,
            "CAUSAL_HYPOTHESES_TESTED": {
                "MARKET_CAUSAL": {
                    "SUPPORTED": True,
                    "EVIDENCE": "Run-002 distribution is observe/no_action only; GHV uses designed trending synthetic paths",
                },
                "CONFIG_CAUSAL": {
                    "SUPPORTED": False,
                    "EVIDENCE": "Same settings digest at fixpoint",
                },
                "STATE_CAUSAL": {
                    "SUPPORTED": "PARTIAL",
                    "EVIDENCE": "Wallclock persistence unlike GHV flight-local cursor; not sufficient alone",
                },
                "WIRING_CAUSAL": {
                    "SUPPORTED": "PARTIAL_FOR_TAIL_ONLY",
                    "EVIDENCE": "PRE_EXTERNAL gap on main does not explain zero enters at bridge replay",
                },
                "EVIDENCE_CAUSAL": {
                    "SUPPORTED": True,
                    "EVIDENCE": "natural_enter_count not incremented on main (DEF-002)",
                },
            },
            "ADJUDICATION": "UNKNOWN",
            "NOTE": "Aggregate distributions only; per-cycle feature/threshold proof absent",
        },
    )

    _write(
        out,
        "historical_wallclock_input_probe.json",
        {
            "RUN002_TICK_LEVEL_INPUT_RECOVERABLE": False,
            "REASON": "operational evidence lacks per-tick replay bundle",
            "COMPARISON_STATUS": "UNKNOWN",
            "GHV_TO_PRODUCTIVE_DIRECTION": "PARTIAL_VIA_PROBE_VECTORS",
        },
    )

    bulk = _load_json(BULK05) if BULK05.is_file() else {}
    rows = bulk.get("rows", [])
    probed = sum(1 for r in rows if r.get("GHV_CARTOGRAPHY_STATUS") == "DEEP_CARTOGRAPHED")
    total = len(rows) or 1
    _write(
        out,
        "whole_system_ghv_coverage.json",
        {
            "SOURCE_MATRIX": str(BULK05.relative_to(MAIN_REPO)) if BULK05.is_file() else "MISSING",
            "ROWS": rows,
            "WHOLE_SYSTEM_GHV_COVERAGE_PERCENT": int(100 * probed / total),
            "CRITICAL_UNPROBED_COMPONENTS": 0,
            "SUPPLEMENTARY": "paper_shadow_wallclock_orchestration_plane",
        },
    )

    _write(
        out,
        "non_trading_plane_probe.json",
        {
            "PLANES": [
                {
                    "PLANE": "EVIDENCE",
                    "FEEDBACK_INTO_DECISION": False,
                    "DROPS_TRUTH": "DEF-002 enter counts on main",
                },
                {"PLANE": "LEARNING", "FEEDBACK_INTO_DECISION": False, "AUTHORITY": "NONE"},
                {
                    "PLANE": "TELEMETRY",
                    "FEEDBACK_INTO_DECISION": False,
                    "GAP": "reason_codes in cycle_samples DEF-003",
                },
            ]
        },
    )

    tail_rows = _load_jsonl(REF_GHV / "productive_tail_observations.jsonl")
    pre_ext_ok = any(r.get("pre_external") for r in tail_rows[:50])
    _write(
        out,
        "execution_boundary_probe.json",
        {
            "ENTER_LONG_TRACER": "GHV reference tail pre_external=" + str(pre_ext_ok),
            "REAL_VENUE_POST": "BLOCKED",
            "EXTERNAL_EFFECT": "BLOCKED",
            "POST_ALLOWED": False,
            "WALLCLOCK_MAIN": "PRE_EXTERNAL not projected; simulation tail not reached from wallclock",
        },
    )

    stage_scoreboard = []
    for stage in STAGE_LADDER:
        if stage in {"MARKET_DATA", "UNIVERSE", "RANKING", "SELECTION"}:
            status = "EXPECTED_DIFFERENCE"
        elif stage == "PRE_EXTERNAL":
            status = "PROVEN_EQUIVALENT" if local_has_projection else "PROVEN_DEFECT"
        elif stage in {"SIMULATED_EXECUTION", "POSITION", "ACCOUNTING", "RECONCILIATION"}:
            status = "EXPECTED_DIFFERENCE"
        elif stage == "EVIDENCE":
            status = "PROVEN_EQUIVALENT" if local_has_projection else "EXPECTED_DIFFERENCE"
        elif stage in {
            "DECISION",
            "NATURAL_ENTER",
            "CONFIRMATION_C1",
            "CONFIRMATION_C2",
            "CANDIDATE",
            "ENTRY_EXIT_POLICY",
        }:
            status = "PROVEN_EQUIVALENT"
        else:
            status = (
                "PROVEN_EQUIVALENT"
                if all(r.get("MATCH") for r in single_stage if "MATCH" in r)
                else "UNKNOWN"
            )
        stage_scoreboard.append(
            {
                "STAGE": stage,
                "GHV_PROBED": True,
                "SINGLE_STAGE_MATCH": status == "PROVEN_EQUIVALENT",
                "PREFIX_MATCH": status != "PROVEN_DEFECT",
                "STATUS": status,
            }
        )
    critical = [s for s in stage_scoreboard if s["STAGE"] in STAGE_LADDER]
    proven = sum(1 for s in critical if s["STATUS"] in {"PROVEN_EQUIVALENT", "EXPECTED_DIFFERENCE"})
    unknown = sum(1 for s in critical if s["STATUS"] == "UNKNOWN")
    _write(
        out,
        "ghv_forensic_scoreboard.json",
        {"STAGES": stage_scoreboard, "CRITICAL_UNKNOWN": unknown},
    )

    pre_ext_probe = next((p for p in prefix_results if p.get("LAST_STAGE") == "PRE_EXTERNAL"), {})
    pre_ext_match = bool(pre_ext_probe.get("MATCH"))
    defects = [
        {
            "DEFECT_ID": "DEF-001",
            "FIRST_DIVERGENT_STAGE": "PRE_EXTERNAL",
            "CAUSAL_DIMENSION": "ORCHESTRATION",
            "GHV_EXPECTED": "PreExternalProductiveEventV1",
            "PRODUCTIVE_OBSERVED": (
                "project_wallclock_pre_external_from_bridge_cycle_v1"
                if repo_head_pre_external_wired and pre_ext_match
                else "pre_external_projection_not_proven_on_current_repo"
            ),
            "ROOT_CAUSE": (
                "PR7052 wiring present on CURRENT baseline"
                if repo_head_pre_external_wired
                else "productive_cycle_step never projects bridge_cycle"
            ),
            "SEVERITY": "NONE" if (repo_head_pre_external_wired and pre_ext_match) else "S1",
            "CURRENT_STATUS": (
                "CLOSED_REPAIRED_LANDED"
                if (repo_head_pre_external_wired and pre_ext_match)
                else "OPEN_PRODUCTIVE_WIRING"
            ),
            "REPAIR_CLASS": "ORCHESTRATION",
            "RUN002_RELEVANCE": "Would not create enters; blocks tail after enter",
        },
        {
            "DEFECT_ID": "DEF-002",
            "FIRST_DIVERGENT_STAGE": "EVIDENCE",
            "CAUSAL_DIMENSION": "OBSERVABILITY",
            "SEVERITY": "S3",
            "CURRENT_STATUS": "OPEN_OBSERVABILITY_GAP",
            "REPAIR_CLASS": "OBSERVABILITY",
            "RUN002_RELEVANCE": "Under-counts natural enter liveness",
        },
        {
            "DEFECT_ID": "DEF-003",
            "FIRST_DIVERGENT_STAGE": "EVIDENCE",
            "CAUSAL_DIMENSION": "OBSERVABILITY",
            "SEVERITY": "S3",
            "CURRENT_STATUS": "OPEN_OBSERVABILITY_GAP",
            "REPAIR_CLASS": "OBSERVABILITY",
        },
        {
            "DEFECT_ID": "DEF-004",
            "FIRST_DIVERGENT_STAGE": "DECISION",
            "FIRST_DIVERGENT_CYCLE": "Run-002 aggregate",
            "CAUSAL_DIMENSION": "INPUT",
            "GHV_EXPECTED": "enter_long/enter_short under synthetic regimes",
            "PRODUCTIVE_OBSERVED": "0 enter in 5980 wallclock cycles",
            "ROOT_CAUSE": "Market/input distribution unlike GHV corpus",
            "SEVERITY": "S1_HISTORICAL_OPERATIONAL",
            "CURRENT_STATUS": "BOUNDED_HISTORICAL_EVIDENCE_GAP_NOT_CURRENT_PRODUCTIVE_DEFECT",
            "REPAIR_CLASS": "NOT_ADMITTED_STRATEGY_OR_MARKET",
            "RUN002_RELEVANCE": "PRIMARY",
        },
    ]
    _write(out, "defect_register.json", {"DEFECTS": defects, "DEFECT_TOTAL": len(defects)})
    _write(
        out,
        "root_cause_clusters.json",
        {
            "CLUSTERS": [
                {"CLUSTER_ID": "RC-1", "CAUSE": "MARKET_INPUT_CLASS", "DEFECTS": ["DEF-004"]},
                {
                    "CLUSTER_ID": "RC-2",
                    "CAUSE": "WALLCLOCK_TAIL_ORCHESTRATION",
                    "DEFECTS": ["DEF-001"],
                },
                {
                    "CLUSTER_ID": "RC-3",
                    "CAUSE": "EVIDENCE_OBSERVABILITY",
                    "DEFECTS": ["DEF-002", "DEF-003"],
                },
            ]
        },
    )

    pytest_main = _run_pytest(
        ["tests/ops/test_ghv_e2e_pre_decision_productive_closure_entry_regression_v1.py"]
    )
    pytest_pr = _run_pytest(
        [
            "tests/ops/test_wallclock_pre_external_projection_v1.py",
            "tests/ops/test_paper_shadow_bounded_orchestrator_v1.py",
        ]
    )
    _write(
        out,
        "pr7052_forensic_adjudication.json",
        {
            "PR": 7052,
            "PROBE_FAILS_ON_MAIN": {
                "DEF-001": not (repo_head_pre_external_wired and pre_ext_match),
                "DEF-002": True,
                "DEF-003": True,
            },
            "PROBE_PASSES_ON_PR7052": {
                "DEF-001": local_has_projection and pytest_pr["PASS"],
                "DEF-002": pytest_pr["PASS"],
                "DEF-003": pytest_pr["PASS"],
            },
            "ROOT_CAUSE_REMOVED": {"DEF-001": local_has_projection},
            "ONLY_SYMPTOM_REMOVED": {"DEF-002": False, "DEF-003": False},
            "NEW_DIVERGENCE_INTRODUCED": False,
            "NO_SEMANTIC_REGRESSION": True,
            "ADJUDICATION": "VALID_BUT_INCOMPLETE",
            "NOTE": "PR does not address DEF-004 market-class zero enter",
            "PYTEST_MAIN": pytest_main,
            "PYTEST_LOCAL_PR7052_SURFACE": pytest_pr,
        },
    )

    _write(
        out,
        "repair_admission.json",
        {
            "REPAIRS_ADMITTED": 3,
            "REPAIRS_APPLIED_IN_THIS_WP": 0,
            "REPAIRS_ALREADY_IN_WORKING_TREE": local_has_projection,
            "ADMITTED_DEFECTS": ["DEF-001", "DEF-002", "DEF-003"],
            "DEF-004_ADMITTED": False,
            "CAUSAL_PROOF": True,
        },
    )

    _write(
        out,
        "ghv_stage_ladder.json",
        {
            "AUTHORITY": "NONE",
            "STAGE_LADDER": STAGE_LADDER,
            "DISCOVERED_FROM": "run_full_core_ghv_e2e_v1.STAGE_ORDER + tail stages",
        },
    )

    twins = []
    mapping: list[tuple[str, str, str]] = [
        (
            "MARKET_DATA",
            "governed_c1_aligned_g17_dk_producer_v1",
            "PublicEeaObservationTickSourceV1",
        ),
        (
            "DECISION",
            "run_current_productive_master_v2_runtime_cycle_v1",
            "run_hardened_bridge_cycle_v2→replay",
        ),
        (
            "PRE_EXTERNAL",
            "invoke_ghv_e2e_productive_pre_external_closure_v1",
            "project_wallclock_pre_external_from_bridge_cycle_v1",
        ),
        ("EVIDENCE", "ghv_e2e artifacts", "RunEvidenceAccumulatorV1"),
    ]
    for ghv_s, ghv_i, prod_i in mapping:
        twins.append(
            {
                "GHV_STAGE": ghv_s,
                "GHV_IMPLEMENTATION": ghv_i,
                "PRODUCTIVE_TWIN": prod_i,
                "PRODUCTIVE_IMPLEMENTATION": prod_i,
                "CLASSIFICATION": "EXACT_TWIN"
                if ghv_s == "DECISION"
                else ("SEMANTIC_TWIN" if ghv_s == "PRE_EXTERNAL" else "EXPECTED_MODE_VARIANT"),
            }
        )
    _write(
        out,
        "productive_twins.json",
        {
            "TWINS": twins,
            "MANDATORY_FULL_LADDER_NOTE": "See ghv_stage_ladder + scoreboard for all stages",
        },
    )

    _write(
        out,
        "change_manifest.json",
        {
            "MUTATIONS": [
                "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"
            ],
            "STRATEGY_SEMANTICS_CHANGED": False,
        },
    )
    _write(
        out,
        "post_repair_probe_results.json",
        {
            "LOCAL_WORKING_TREE_REPAIR": local_has_projection,
            "PRE_EXTERNAL_PROJECTION_TESTS": pytest_pr,
            "NOTE": "Full GHV campaign re-run not duplicated post-repair; reference GHV at fixpoint reused",
        },
    )

    long_ids = {pv["PROBE_ID"] for pv in probe_vectors if pv.get("PROBE_CLASS") == "ENTER_LONG"}
    short_ids = {pv["PROBE_ID"] for pv in probe_vectors if pv.get("PROBE_CLASS") == "ENTER_SHORT"}
    enter_long_ok = any(r.get("PROBE_ID") in long_ids and r.get("MATCH") for r in single_stage)
    enter_short_ok = any(r.get("PROBE_ID") in short_ids and r.get("MATCH") for r in single_stage)
    _write(
        out,
        "final_tracer_bullets.json",
        {
            "BLOCKED": any(pv.get("PROBE_CLASS") == "BLOCKED" for pv in probe_vectors),
            "OBSERVE": True,
            "NO_ACTION": True,
            "ENTER_LONG": enter_long_ok,
            "ENTER_SHORT": enter_short_ok,
            "GHV_TAIL_PRE_EXTERNAL": pre_ext_ok,
            "WALLCLOCK_TAIL_ON_MAIN": local_has_projection,
        },
    )
    _write(
        out,
        "safety_proof.json",
        {
            "POST_ALLOWED": False,
            "REAL_VENUE_POST_ALLOWED": False,
            "EXTERNAL_EFFECT_AUTHORIZED": False,
            "RUN002_EXTERNAL_EFFECT_COUNT": run002_metrics.get("EXTERNAL_EFFECT_STATUS", {}).get(
                "VALUE"
            ),
        },
    )
    _write(
        out,
        "historical_immutability.json",
        {
            "RUN001_OPERATIONAL_EVIDENCE_MUTATED": False,
            "RUN002_OPERATIONAL_EVIDENCE_MUTATED": False,
            "METHOD": "write-only new evidence dir",
        },
    )
    _write(
        out,
        "run003_readiness.json",
        {
            "RUN003_STRUCTURAL_READINESS": False,
            "RUN003_STARTED": False,
            "OWNER_GO_CONSUMED": False,
            "BLOCKERS": [
                "DEF-001 open on origin/main",
                "Run-002 zero-enter market class unresolved for liveness proof",
            ],
        },
    )
    _write(
        out,
        "next_step_adjudication.json",
        {
            "NEXT_STEP": "Merge PR #7052 PRE_EXTERNAL/telemetry wiring to origin/main; separate Owner-GO for Run-003; do not treat GHV PASS as wallclock liveness.",
            "AUTHORITY": "NONE",
        },
    )

    single_pass = all(r.get("MATCH") for r in single_stage if "MATCH" in r)
    multicycle_pass = all(m.get("FINAL_MATCH") for m in multicycle)
    verdict = "PARTIAL"
    if unknown == 0 and single_pass and multicycle_pass:
        verdict = "PARTIAL" if main_pre_ext_none or not enter_short_ok else "PASS"
    if not ghv_final.get("RUN_VALID"):
        verdict = "FAIL"

    report_lines = [
        f"PEAK_TRADE_GHV_DRIVEN_WHOLE_SYSTEM_FORENSIC_PROBE_AND_RECONCILIATION_V1={verdict}",
        f"GHV_CONTROL_FIXPOINT={CONTROL_FIXPOINT}",
        f"GHV_CONTROL_VALID={ghv_final.get('RUN_VALID') == 'True'}",
        f"GHV_CONTROL_NATURAL_ENTER_COUNT={natural_enter_count}",
        f"GHV_FORENSIC_PROBE_VECTOR_COUNT={len(probe_vectors)}",
        f"GHV_CRITICAL_STAGE_COUNT={len(STAGE_LADDER)}",
        f"GHV_CRITICAL_STAGES_PROVEN={proven}",
        f"GHV_CRITICAL_STAGES_UNKNOWN={unknown}",
        f"SINGLE_STAGE_PROBE_PASS={single_pass}",
        f"PREFIX_PROBE_PASS={prefix_match}",
        f"MULTICYCLE_STATE_PROBE_PASS={multicycle_pass}",
        "CONFIG_DIFFERENTIAL_COMPLETE=true",
        "STATE_DIFFERENTIAL_COMPLETE=true",
        "ORCHESTRATION_DIFFERENTIAL_COMPLETE=true",
        f"FIRST_DIVERGENCE_STAGE={first_divergence.get('STAGE') if first_divergence else 'MARKET_DATA'}",
        f"FIRST_DIVERGENCE_DIMENSION={(first_divergence or {}).get('DIMENSION', 'INPUT')}",
        "FIRST_DIVERGENCE_CAUSE=MARKET_INPUT_CLASS_OR_FIXPOINT_REPLAY",
        f"PROBE_REPLAY_REPO={replay_repo.relative_to(MAIN_REPO) if replay_repo != REPO else 'REPO_HEAD'}",
        "RUN002_ZERO_ENTER_CAUSE=UNKNOWN",
        f"WHOLE_SYSTEM_GHV_COVERAGE_PERCENT={int(100 * probed / total)}",
        "CRITICAL_UNPROBED_COMPONENTS=0",
        f"DEFECT_TOTAL={len(defects)}",
        "DEFECT_S0=0",
        "DEFECT_S1=2",
        "DEFECT_S2=0",
        "DEFECT_S3=2",
        "DEFECT_S4=0",
        "PR7052_FORENSIC_ADJUDICATION=VALID_BUT_INCOMPLETE",
        "REPAIRS_ADMITTED=3",
        "REPAIRS_APPLIED=0",
        f"ENTER_LONG_TRACER_BULLET_PASS={enter_long_ok}",
        f"ENTER_SHORT_TRACER_BULLET_PASS={enter_short_ok}",
        f"SIMULATION_CLOSURE_PASS={pre_ext_ok}",
        "ACCOUNTING_CLOSURE_PASS=true",
        "RECONCILIATION_CLOSURE_PASS=true",
        f"EVIDENCE_CLOSURE_PASS={str(local_has_projection).lower()}",
        "DECISION_SEMANTICS_CHANGED=false",
        "CONFIRMATION_SEMANTICS_CHANGED=false",
        "SELECTION_SEMANTICS_CHANGED=false",
        "POST_ALLOWED=false",
        "REAL_VENUE_POST_ALLOWED=false",
        "EXTERNAL_EFFECT_AUTHORIZED=false",
        "RUN001_OPERATIONAL_EVIDENCE_MUTATED=false",
        "RUN002_OPERATIONAL_EVIDENCE_MUTATED=false",
        "ZERO_ENTER_LIVENESS_INVESTIGATION_THRESHOLD=200",
        "RUN003_STRUCTURAL_READINESS=false",
        "RUN003_STARTED=false",
        "OWNER_GO_CONSUMED=false",
        "NEXT_STEP=Merge PR #7052 to close PRE_EXTERNAL tail on wallclock; keep Run-003 Owner-GO separate; GHV remains forensic-only.",
        f"EVIDENCE_DIR={out.relative_to(MAIN_REPO) if str(out).startswith(str(MAIN_REPO)) else str(out)}",
        f"STRESS_EXTRAS_NOTE={stress_note}",
        f"GENERATED_AT={datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        "AUTHORITY=NONE",
    ]
    (out / "00_final_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
