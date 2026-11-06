"""Single-run DEVELOPMENT panel evaluation v5: baseline vs midband exit-efficiency gate.

New independently preregistered DEVELOPMENT_ONLY measurement
(HYPOTHESIS_ID ...DEVELOPMENT_V5). Not a rerun of V1, V2, V3, or V4. Reuses the frozen
V1 mechanism/gate/decision modules by import only; no V1/V2/V3/V4 partial result,
checkpoint, or economic claim is transferred. Binds PANEL_RUNNER_FALSY_ZERO
hygiene, MV2 wiring_mod capture-alias open_side binding fix, and fail-closed
measurement-validity prerequisites before the real panel run.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from src.backtest.admissible_versioned_futures_dataset_v1 import (
    DatasetProfileBindingV1,
    DatasetProfileV1,
    ExecutionCostBindingV1,
    L1ObservationStatusV1,
)
from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1
from src.research.adx_di_direction_confirmation_mr_eligibility_development_evaluation_v1.panel_runner_v1 import (
    _classify_side,
    load_runtime_cfg,
)
from src.research.bollinger_mr_economic_failure_decomposition_development_v1.metrics_v1 import (
    aggregate_core_metrics,
    concentration_stats,
    enrich_trade_excursions,
    instrument_attribution,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.decision_v1 import (
    decide_development_evaluation,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.exit_efficiency_gate_v1 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    assert_frozen_parameters_match_contract,
    mechanism_freeze_payload,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v5.constants_v5 import (
    BINDING_FIX_SURFACE,
    BASELINE_CONFIG_ID,
    BB_PERIOD,
    CONTRACT_REL_PATH,
    COST_MULTIPLIER,
    DATASET_CLASS,
    DATASET_ID,
    DECISION_END_EXCLUSIVE,
    DECISION_START,
    DEVELOPMENT_SPLIT_DIGEST,
    EVALUATION_RUN_ID,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    FEE_BPS,
    HALF_SPREAD_BPS,
    HYPOTHESIS_ID,
    INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
    MAX_FEATURE_LOOKBACK_HOURS,
    MAX_TRADE_COUNT_REDUCTION_FRACTION,
    MINIMUM_TRADE_COUNT,
    PORTFOLIO_AGGREGATION_ID,
    PRIMARY_SEED,
    SHARED_INITIAL_CAPITAL,
    SLEEVE_INITIAL_CASH,
    SLIPPAGE_BPS,
    STOP_PCT,
    STRATEGY_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v5.measurement_validity_preflight_v5 import (
    run_measurement_validity_preflight,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v5 import (
    FORBIDDEN_PARTIAL_TRANSFER_KEYS,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    canonical_json_sha256,
    load_and_validate_repo_contract,
    load_json,
    reject_holdout_dataset_or_path,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_development_archive_root,
    verify_development_panel_hashes,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.shared_portfolio_equity_research_v1 import (
    build_equal_weight_portfolio_equity,
    portfolio_metrics_from_equity,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.checkpoint_v5 import (
    commit_checkpoint_v5,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.constants_v5 import (
    LIFECYCLE_STATE_CHECKPOINT_COMMITTED,
    LIFECYCLE_STATE_MEMBER_COMPLETED,
    LIFECYCLE_STATE_MEMBER_STARTED,
    LIFECYCLE_STATE_NOT_STARTED,
    LIFECYCLE_STATE_PANEL_COMPLETED,
    LIFECYCLE_STATE_PREFLIGHT_PASSED,
    LIFECYCLE_STATE_PREFLIGHT_RUNNING,
    LIFECYCLE_STATE_RUNNER_STARTED,
    LIFECYCLE_STATE_RUN_SLOT_CLAIMED,
    LIFECYCLE_STATE_SUMMARY_COMMITTED,
    LIFECYCLE_STATE_TERMINAL_COMMITTED,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.state_machine_v5 import (
    assert_monotonic_transition,
)
from src.research.evaluation_runner_lifecycle_observability_v1.atomic_io_v1 import (
    atomic_write_json_v1,
)
import os
from datetime import datetime, timezone


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class _LifecycleCheckpointTrackerV5:
    """Durable V5 process-lifecycle checkpoints (diagnostic only; no rerun/slot reclaim)."""

    def __init__(self, diagnostics_dir: Path, *, run_id: str, started_at: str) -> None:
        self.diagnostics_dir = Path(diagnostics_dir)
        self.run_id = run_id
        self.started_at = started_at
        self.process_id = os.getpid()
        self.state = LIFECYCLE_STATE_NOT_STARTED
        self.seq = 0
        self.completed_member_count = 0
        self.total_member_count: int | None = None
        self.current_member_index: int | None = None
        self.last_completed_member_id: str | None = None

    def _commit(self, state: str, **extra: object) -> None:
        assert_monotonic_transition(from_state=self.state, to_state=state)
        self.state = state
        self.seq += 1
        progress = {
            "run_id": self.run_id,
            "process_id": self.process_id,
            "started_at": self.started_at,
            "last_heartbeat_at": _utc_now(),
            "current_member_index": self.current_member_index,
            "completed_member_count": self.completed_member_count,
            "total_member_count": self.total_member_count,
            "last_completed_member_id": self.last_completed_member_id,
            "lifecycle_state": self.state,
            "checkpoint_sequence": self.seq,
        }
        commit_checkpoint_v5(
            self.diagnostics_dir,
            progress=progress,
            extra_diagnostics={k: v for k, v in extra.items() if v is not None},
        )

    def mark(self, state: str, **extra: object) -> None:
        self._commit(state, **extra)

    def member_started(
        self, *, member_index: int, member_id: str, members_total: int, phase: str
    ) -> None:
        self.current_member_index = member_index
        self.total_member_count = members_total
        self._commit(LIFECYCLE_STATE_MEMBER_STARTED, phase=phase, member_id=member_id)

    def member_completed(
        self, *, member_index: int, member_id: str, members_total: int, phase: str
    ) -> None:
        self.current_member_index = member_index
        self.total_member_count = members_total
        self.completed_member_count += 1
        self.last_completed_member_id = member_id
        self._commit(LIFECYCLE_STATE_MEMBER_COMPLETED, phase=phase, member_id=member_id)
        self._commit(LIFECYCLE_STATE_CHECKPOINT_COMMITTED, phase=phase, member_id=member_id)


def _claim_run_slot_atomic_v5(
    output_dir: Path,
    *,
    repo: Path,
    started_at: str,
) -> dict[str, object]:
    """Atomically claim the one-shot run slot before panel access."""
    claim_path = output_dir / "run_slot_claim.json"
    if claim_path.is_file():
        raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CLAIMED")
    payload = {
        "schema_version": "bollinger_mr_midband_exit_efficiency_development_v5_run_slot_claim.v1",
        "hypothesis_id": HYPOTHESIS_ID,
        "evaluation_run_id": EVALUATION_RUN_ID,
        "dataset_id": DATASET_ID,
        "dataset_class": DATASET_CLASS,
        "panel_class": DATASET_CLASS,
        "development_preregistration_digest": (
            "b85903ebc76d1fefdb576075e88a1b72d9abb852ad4da5f1f8c5bc9c0bd21b2e"
        ),
        "contract_ref": CONTRACT_REL_PATH,
        "runner_script": (
            "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v5.py"
        ),
        "runner_version": "v5",
        "commit_sha": _git_base_sha(repo),
        "claim_timestamp_utc": started_at,
        "process_id": os.getpid(),
        "evaluation_run_count_authorized": 1,
        "evaluation_run_count_after_claim": 1,
        "run_limit": 1,
        "slot_claimed": True,
        "slot_consumed": True,
        "holdout_data_accessed": False,
        "note": (
            "Atomic one-shot slot claim before panel access; slot remains consumed "
            "regardless of process outcome; no rerun authorized."
        ),
    }
    atomic_write_json_v1(claim_path, payload)
    return payload


@dataclass(frozen=True)
class ArmResult:
    arm: str
    rows: list[dict[str, Any]]
    metrics: dict[str, Any]
    enriched_trades: list[dict[str, Any]]
    exit_attribution: dict[str, Any]
    wallclock_seconds: float


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_base_sha(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        sha = out.stdout.strip()
        return sha or None
    except Exception:  # noqa: BLE001
        return None


def _profile() -> DatasetProfileBindingV1:
    return DatasetProfileBindingV1(
        dataset_profile=DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        execution_cost_binding=ExecutionCostBindingV1(
            spread_model_version="research_conservative_bps_v1",
            execution_price_observation_source="MODELLED_NOT_OBSERVED",
            conservative_half_spread_bps=HALF_SPREAD_BPS,
        ),
        l1_observation_status=L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
    )


def _extract_member_trades(
    result: Any,
    *,
    instrument_id: str,
    decision_start: pd.Timestamp,
    decision_end: pd.Timestamp,
) -> tuple[list[dict[str, Any]], pd.Series]:
    bt = result.backtest_result
    trades_df = getattr(bt, "trades", None)
    trade_records: list[dict[str, Any]] = []
    if trades_df is not None and hasattr(trades_df, "empty") and not trades_df.empty:
        trade_records = trades_df.to_dict(orient="records")

    filtered: list[dict[str, Any]] = []
    for rec in trade_records:
        et = rec.get("entry_time")
        if et is None:
            continue
        ets = pd.Timestamp(et)
        if ets.tzinfo is None:
            ets = ets.tz_localize("UTC")
        else:
            ets = ets.tz_convert("UTC")
        if not (decision_start <= ets < decision_end):
            continue
        side = _classify_side(rec)
        if side not in {"long", "short"}:
            raise ValueError(f"TRADE_SIDE_UNKNOWN:{side}")
        fees = rec.get("fee_total")
        if fees is None:
            fees = rec.get("fee")
        if fees is None:
            raise ValueError("TRADE_FEES_MISSING")
        slip = rec.get("slippage_total")
        if slip is None:
            raise ValueError("TRADE_SLIPPAGE_MISSING")
        gross = rec.get("gross_pnl")
        net = rec.get("pnl")
        if gross is None or net is None:
            raise ValueError("TRADE_PNL_MISSING")
        if rec.get("entry_price") is None:
            raise ValueError("ENTRY_PRICE_MISSING")
        filtered.append(
            {
                "instrument_id": instrument_id,
                "side": side,
                "entry_time": str(rec.get("entry_time")),
                "exit_time": str(rec.get("exit_time")),
                "entry_price": float(rec["entry_price"]),
                "exit_price": float(rec["exit_price"])
                if rec.get("exit_price") is not None
                else None,
                "size": float(rec["size"]) if rec.get("size") is not None else None,
                "gross_pnl": float(gross),
                "fees": float(fees),
                "slippage": float(slip),
                "net_pnl": float(net),
                "exit_reason": str(rec.get("exit_reason") or "UNKNOWN"),
            }
        )

    equity = getattr(bt, "equity_curve", None)
    if equity is None or len(equity) == 0:
        raise ValueError(f"MISSING_EQUITY:{instrument_id}")
    eq = equity.astype(float)
    eq.index = pd.to_datetime(eq.index, utc=True)
    eq_dec = eq[(eq.index >= decision_start) & (eq.index < decision_end)]
    if eq_dec.empty:
        pre = eq[eq.index < decision_start]
        start_val = float(pre.iloc[-1]) if len(pre) else SLEEVE_INITIAL_CASH
        eq_dec = pd.Series(
            [start_val, start_val],
            index=pd.DatetimeIndex([decision_start, decision_end - pd.Timedelta(hours=1)]),
        )
    return filtered, eq_dec


def _aggregate_arm(
    *,
    enriched: list[dict[str, Any]],
    equity_curves: dict[str, pd.Series],
    exits_forced_by_gate: int,
) -> dict[str, Any]:
    core = aggregate_core_metrics(enriched)
    instruments = instrument_attribution(enriched)
    concentration = concentration_stats(instruments)
    portfolio_eq = build_equal_weight_portfolio_equity(
        equity_curves, initial_capital=SHARED_INITIAL_CAPITAL
    )
    port = portfolio_metrics_from_equity(portfolio_eq, initial_capital=SHARED_INITIAL_CAPITAL)
    long_n = sum(1 for t in enriched if str(t["side"]).lower() == "long")
    short_n = sum(1 for t in enriched if str(t["side"]).lower() == "short")
    return {
        "portfolio_aggregation_id": PORTFOLIO_AGGREGATION_ID,
        "initial_capital": SHARED_INITIAL_CAPITAL,
        "instrument_count": len(equity_curves),
        "trade_count": int(core["trade_count"]),
        "long_trades": long_n,
        "short_trades": short_n,
        "gross_pnl": float(core["gross_pnl"]),
        "net_pnl": float(core["net_pnl"]),
        "fees": float(core["fees"]),
        "slippage": float(core["slippage"]),
        "cost_drag": float(core["gross_pnl"]) - float(core["net_pnl"]),
        "net_return": float(port["net_return"]),
        "sharpe": float(port["sharpe"]),
        "max_drawdown": float(port["max_drawdown"]),
        "profit_factor": core["net_profit_factor"],
        "net_profit_factor": core["net_profit_factor"],
        "turnover": float(core["trade_count"]),
        "mean_realized_pnl_over_mfe_capture_ratio": core[
            "mean_realized_pnl_over_mfe_capture_ratio"
        ],
        "mean_mfe_to_exit_leakage": core["mean_mfe_to_exit_leakage"],
        "mean_holding_period_hours": core["mean_holding_period_hours"],
        "worst1_abs_net_share": concentration["worst1_abs_net_share"],
        "worst5_abs_net_share": concentration["worst5_abs_net_share"],
        "exits_forced_by_gate": int(exits_forced_by_gate),
        "cost_multiplier": COST_MULTIPLIER,
        "final_equity": float(port["final_equity"]),
        "_portfolio_equity": portfolio_eq,
        "_instrument_attribution": instruments,
        "_concentration": concentration,
        "_core": core,
    }


def run_arm(
    *,
    arm: str,
    cfg: dict[str, Any],
    archive_root: Path,
    members: list[dict[str, str]],
    load_start: str,
    decision_start: str,
    decision_end: str,
    gate: bool,
    lifecycle: Any | None = None,
    lc_tracker: _LifecycleCheckpointTrackerV5 | None = None,
) -> ArmResult:
    t0 = time.perf_counter()
    d_start = pd.Timestamp(decision_start)
    d_end = pd.Timestamp(decision_end)
    all_trades: list[dict[str, Any]] = []
    equity_curves: dict[str, pd.Series] = {}
    bars_by_instrument: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, Any]] = []
    exits_forced_total = 0
    exit_bars_total = 0

    for i, member in enumerate(members, start=1):
        native = member["native_instrument_id"]
        canon = member["canonical_instrument_id"]
        if lc_tracker is not None:
            lc_tracker.member_started(
                member_index=i,
                member_id=native,
                members_total=len(members),
                phase=arm,
            )
        bars = load_member_bars(
            archive_root,
            native_instrument_id=native,
            start_inclusive=load_start,
            end_exclusive=decision_end,
        )
        bars_by_instrument[canon] = bars
        with optional_treatment_exit_efficiency_gate(enabled=gate, bars=bars) as counters:
            result = run_mv2_research_backtest_wiring_v1(
                bars,
                strategy_id=STRATEGY_ID,
                cfg=cfg,
                instrument_id=CANONICAL_INSTRUMENT_ID,
                profile_binding=_profile(),
                observational_panel_member_instrument_id=canon,
            )
        trades, eq_dec = _extract_member_trades(
            result,
            instrument_id=canon,
            decision_start=d_start,
            decision_end=d_end,
        )
        forced = int(counters["exits_forced_by_gate"])
        exits_forced_total += forced
        exit_bars_total += int(counters["exit_bars_observed"])
        all_trades.extend(trades)
        equity_curves[canon] = eq_dec
        rows.append(
            {
                "member_id": canon,
                "trade_count": len(trades),
                "exits_forced_by_gate": forced,
                "exit_bars_observed": int(counters["exit_bars_observed"]),
                "entries_altered_by_gate": int(counters["entries_altered_by_gate"]),
            }
        )
        print(
            json.dumps(
                {
                    "phase": arm,
                    "i": i,
                    "n": len(members),
                    "member": native,
                    "trades": len(trades),
                    "exits_forced_by_gate": forced,
                }
            ),
            flush=True,
        )
        # Durable lifecycle progress (stdout alone is not a death diagnostic).
        if lifecycle is not None:
            lifecycle.record_member_progress(
                phase=arm,
                member_index=i,
                members_total=len(members),
                member_id=native,
                extra={
                    "trades": len(trades),
                    "exits_forced_by_gate": forced,
                },
            )
        if lc_tracker is not None:
            lc_tracker.member_completed(
                member_index=i,
                member_id=native,
                members_total=len(members),
                phase=arm,
            )

    enriched = enrich_trade_excursions(all_trades, bars_by_instrument)
    metrics = _aggregate_arm(
        enriched=enriched,
        equity_curves=equity_curves,
        exits_forced_by_gate=exits_forced_total,
    )
    exit_attr = {
        "exit_efficiency_gate_enabled": gate,
        "exits_forced_by_gate": exits_forced_total,
        "exit_bars_observed": exit_bars_total,
        "instruments_with_forced_exits_count": sum(
            1 for r in rows if int(r["exits_forced_by_gate"]) > 0
        ),
    }
    return ArmResult(
        arm=arm,
        rows=rows,
        metrics=metrics,
        enriched_trades=enriched,
        exit_attribution=exit_attr,
        wallclock_seconds=float(time.perf_counter() - t0),
    )


def _assert_no_predecessor_partial_result_reuse(contract: Mapping[str, Any]) -> None:
    for banned in FORBIDDEN_PARTIAL_TRANSFER_KEYS:
        if banned in contract:
            raise RuntimeError(f"PARTIAL_TRANSFER_FORBIDDEN:{banned}")
    predecessor = contract.get("predecessor_development_v4") or {}
    if predecessor.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise RuntimeError("PREDECESSOR_V4_HYPOTHESIS_ID_MISMATCH")
    if predecessor.get("partial_results_reused") is not False:
        raise RuntimeError("PREDECESSOR_V4_PARTIAL_RESULTS_REUSED")


def run_development_evaluation(
    *,
    output_dir: Path,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
    lifecycle: Any | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Single-run lock: refuse if evidence summary already claims run_count=1.
    summary_path = output_dir / "summary.json"
    if summary_path.is_file():
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
        if int(existing.get("evaluation_run_count") or 0) >= 1:
            raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CONSUMED")

    # Reject holdout *dataset/path* misuse only. The opaque holdout id string itself
    # is an exclusion label in the contract and must not be passed to the path rejector.
    reject_holdout_dataset_or_path(DATASET_ID)

    # Validate against the V5 preregistration validator BEFORE any measurement /
    # contract mutation. The V5 validator accepts DEFINITION_ONLY_PREREGISTERED
    # with evaluation_run_count=0 at the start of this run.
    report = load_and_validate_repo_contract(repo)
    if report.get("hypothesis_id") != HYPOTHESIS_ID:
        raise RuntimeError("CONTRACT_HYPOTHESIS_ID_NOT_V5")
    # Use dict.get default — do NOT use `x or -1` (Python treats 0 as falsy).
    if int(report.get("evaluation_run_count", -1)) != 0:
        raise RuntimeError("CONTRACT_EVALUATION_RUN_COUNT_NOT_ZERO")

    contract = load_json(repo / CONTRACT_REL_PATH)
    if contract.get("hypothesis_id") != HYPOTHESIS_ID:
        raise RuntimeError("CONTRACT_HYPOTHESIS_ID_NOT_V5")
    if int(contract.get("evaluation_run_count", -1)) != 0:
        raise RuntimeError("CONTRACT_EVALUATION_RUN_COUNT_NOT_ZERO")
    if contract.get("development_only") is not True:
        raise RuntimeError("CONTRACT_NOT_DEVELOPMENT_ONLY")
    if contract.get("holdout_allowed") is not False:
        raise RuntimeError("CONTRACT_HOLDOUT_ALLOWED")
    _assert_no_predecessor_partial_result_reuse(contract)
    assert_frozen_parameters_match_contract(contract)

    started_at = _utc_now()
    lc_tracker = _LifecycleCheckpointTrackerV5(
        output_dir, run_id=EVALUATION_RUN_ID, started_at=started_at
    )
    # Refuse second start if prior claim exists (slot already consumed).
    if (output_dir / "run_slot_claim.json").is_file():
        raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CLAIMED")
    lc_tracker.mark(LIFECYCLE_STATE_PREFLIGHT_RUNNING)

    # Measurement-validity prerequisites BEFORE real panel (synthetic only; no archive).
    # Fail-closed INVALID_* terminalizes without panel backtest. Slot claim / summary
    # persistence for INVALID_* happens only when this function is invoked by an
    # authorized evaluation Operator-GO — not at import time.
    validity = run_measurement_validity_preflight(
        declared_runtime_cfg={"seed": PRIMARY_SEED, "strategy_id": STRATEGY_ID},
        repo_root=repo,
    )
    (output_dir / "measurement_validity_preflight.json").write_text(
        json.dumps(validity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    # Slot claim AFTER preflight computation but BEFORE any panel archive access.
    # Consumes the one-shot slot regardless of subsequent panel/process outcome.
    if validity.get("passed") is True:
        lc_tracker.mark(LIFECYCLE_STATE_PREFLIGHT_PASSED)
    _claim_run_slot_atomic_v5(output_dir, repo=repo, started_at=started_at)
    lc_tracker.mark(
        LIFECYCLE_STATE_RUN_SLOT_CLAIMED,
        evaluation_run_count="1/1",
        status="STARTED",
        hypothesis_id=HYPOTHESIS_ID,
        dataset_id=DATASET_ID,
        dataset_class=DATASET_CLASS,
        repo_sha=_git_base_sha(repo),
    )
    lc_tracker.mark(LIFECYCLE_STATE_RUNNER_STARTED)

    if validity.get("passed") is not True:
        invalid_class = str(validity.get("result_class") or "INVALID_MEASUREMENT_BINDING_MISSING")
        freeze = mechanism_freeze_payload()
        (output_dir / "exit_mechanism_formula_freeze.json").write_text(
            json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        command = (
            "PYTHONPATH=src:. python3 scripts/research/"
            "run_evaluate_bollinger_mr_midband_exit_efficiency_development_v5.py "
            f"--output-dir {output_dir}"
        )
        summary = {
            "schema_version": "evaluate_bollinger_mr_midband_exit_efficiency_development_summary.v5",
            "evaluation_run_id": EVALUATION_RUN_ID,
            "evaluation_run_count": 1,
            "evaluation_started": True,
            "evaluation_completed": True,
            "backtest_executed": False,
            "panel_backtest_executed": False,
            "hypothesis_id": HYPOTHESIS_ID,
            "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
            "v1_rerun": False,
            "v2_rerun": False,
            "v3_rerun": False,
            "v1_partial_results_reused": False,
            "v2_partial_results_reused": False,
            "v3_partial_results_reused": False,
            "contract_id": contract["schema_version"],
            "contract_ref": CONTRACT_REL_PATH,
            "config_id": BASELINE_CONFIG_ID,
            "dataset_id": DATASET_ID,
            "dataset_class": DATASET_CLASS,
            "development_only": True,
            "development_panel_accessed": False,
            "measurement_validity": validity,
            "result_class": invalid_class,
            "economic_verdict": "NOT_EVALUATED",
            "decision": {
                "result_class": invalid_class,
                "reason": validity.get("reason"),
                "evaluable": False,
            },
            "pass": False,
            "fail": False,
            "acceptance_criteria_met": False,
            "command": command,
            "holdout_accessed": False,
            "holdout_data_accessed": False,
            "sealed_holdout_content_inspected": False,
            "productive_trading_logic_changed": False,
            "production_strategy_semantics_changed": False,
            "double_play_authority_changed": False,
            "risk_sizing_execution_semantics_changed": False,
            "authority_changed": False,
            "economic_validity_offline_gate_changed": False,
            "economic_gate_open": False,
            "promotion_eligible": False,
            "runtime_activated": False,
            "shadow_activated": False,
            "testnet_activated": False,
            "orders_sent": False,
            "pass_criteria_changed": False,
            "cost_model_changed": False,
            "entry_eligibility_retuned": False,
            "observability_surface": "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1",
            "observability_surface_bound": True,
            "lifecycle_checkpoint_surface": (
                "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5"
            ),
            "lifecycle_checkpoint_surface_bound": True,
            "binding_fix_surface": BINDING_FIX_SURFACE,
            "binding_fix_bound": True,
            "run_slot_claimed": True,
            "v4_rerun": False,
            "v4_partial_results_reused": False,
            "partial_metrics_authoritative": False,
            "auto_rerun_executed": False,
            "rerun_allowed": False,
            "base_sha": _git_base_sha(repo),
            "python_version": sys.version.split()[0],
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
        )
        (output_dir / "README.md").write_text(
            "\n".join(
                [
                    "# Evaluate Bollinger/MR midband exit-efficiency DEVELOPMENT v5",
                    "",
                    f"HYPOTHESIS_ID={HYPOTHESIS_ID}",
                    f"PREDECESSOR_HYPOTHESIS_ID={REQUIRED_PREDECESSOR_HYPOTHESIS_ID}",
                    f"DATASET={DATASET_ID}",
                    "DEVELOPMENT_ONLY=true",
                    "EVALUATION_RUN_COUNT=1",
                    "HOLDOUT_DATA_ACCESSED=false",
                    "PANEL_BACKTEST_EXECUTED=false",
                    f"RESULT_CLASS={invalid_class}",
                    f"REASON={validity.get('reason')}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        write_manifest_sha256(output_dir)
        lc_tracker.mark(LIFECYCLE_STATE_SUMMARY_COMMITTED, result_class=invalid_class)
        lc_tracker.mark(LIFECYCLE_STATE_TERMINAL_COMMITTED, result_class=invalid_class)
        if lifecycle is not None:
            lifecycle.mark_complete()
        return summary

    freeze = mechanism_freeze_payload()
    (output_dir / "exit_mechanism_formula_freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    root = resolve_development_archive_root(archive_root)
    panel_proof = verify_development_panel_hashes(root)
    if panel_proof["manifest_sha256"] != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("PANEL_MANIFEST_SHA_MISMATCH")
    if panel_proof["content_hash"] != EXPECTED_CONTENT_HASH:
        raise RuntimeError("PANEL_CONTENT_HASH_MISMATCH")
    members = included_panel_members(root)
    cfg = load_runtime_cfg(repo, seed=PRIMARY_SEED)
    if float(cfg["backtest"]["fee_bps"]) != FEE_BPS:
        raise RuntimeError("FEE_BPS_MISMATCH")
    if float(cfg["backtest"]["slippage_bps"]) != SLIPPAGE_BPS:
        raise RuntimeError("SLIPPAGE_BPS_MISMATCH")

    load_start_ts = pd.Timestamp(DECISION_START) - pd.Timedelta(
        hours=MAX_FEATURE_LOOKBACK_HOURS + BB_PERIOD
    )
    load_start = load_start_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    baseline = run_arm(
        arm="baseline",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=DECISION_START,
        decision_end=DECISION_END_EXCLUSIVE,
        gate=False,
        lifecycle=lifecycle,
        lc_tracker=lc_tracker,
    )
    treatment = run_arm(
        arm="treatment",
        cfg=cfg,
        archive_root=root,
        members=members,
        load_start=load_start,
        decision_start=DECISION_START,
        decision_end=DECISION_END_EXCLUSIVE,
        gate=True,
        lifecycle=lifecycle,
        lc_tracker=lc_tracker,
    )
    lc_tracker.mark(LIFECYCLE_STATE_PANEL_COMPLETED)

    exits_forced = int(treatment.metrics["exits_forced_by_gate"])
    baseline_exit_times = {
        (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in baseline.enriched_trades
    }
    treatment_exit_times = {
        (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in treatment.enriched_trades
    }
    shared_keys = set(baseline_exit_times) & set(treatment_exit_times)
    exit_time_differs = any(baseline_exit_times[k] != treatment_exit_times[k] for k in shared_keys)
    trade_count_differs = int(treatment.metrics["trade_count"]) != int(
        baseline.metrics["trade_count"]
    )
    exit_reason_baseline = [t.get("exit_reason") for t in baseline.enriched_trades]
    exit_reason_treatment = [t.get("exit_reason") for t in treatment.enriched_trades]
    exit_reasons_differ = exit_reason_baseline != exit_reason_treatment
    exit_divergence_observed = bool(
        exits_forced > 0 or exit_time_differs or trade_count_differs or exit_reasons_differ
    )

    exit_attribution = {
        "exits_forced_by_gate": exits_forced,
        "exit_time_differs": exit_time_differs,
        "trade_count_differs": trade_count_differs,
        "exit_reasons_differ": exit_reasons_differ,
        "exit_divergence_observed": exit_divergence_observed,
        "baseline": baseline.exit_attribution,
        "treatment": treatment.exit_attribution,
    }
    if lifecycle is not None:
        lifecycle.record_persist_phase(note="pre_evidence_persist")
    try:
        (output_dir / "exit_attribution.json").write_text(
            json.dumps(exit_attribution, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        if lifecycle is not None:
            lifecycle.record_persistence_failure(exc)
        raise

    decision_out = decide_development_evaluation(
        baseline=baseline.metrics,
        treatment=treatment.metrics,
        exit_divergence_observed=exit_divergence_observed,
        minimum_trade_count=MINIMUM_TRADE_COUNT,
        max_trade_count_reduction_fraction=MAX_TRADE_COUNT_REDUCTION_FRACTION,
        instrument_concentration_worst1_max=INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
        cost_multiplier_treatment=COST_MULTIPLIER,
        cost_assumption_below_canonical_1x=False,
        cost_drag_fully_included=True,
    )

    def _public_metrics(m: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in m.items():
            if str(k).startswith("_"):
                continue
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                out[k] = None
            else:
                out[k] = v
        return out

    baseline.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_baseline.csv")
    treatment.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_treatment.csv")

    (output_dir / "baseline_metrics.json").write_text(
        json.dumps(_public_metrics(baseline.metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "treatment_metrics.json").write_text(
        json.dumps(_public_metrics(treatment.metrics), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "comparison_decision.json").write_text(
        json.dumps(decision_out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "instrument_attribution.json").write_text(
        json.dumps(
            {
                "baseline": baseline.metrics["_instrument_attribution"],
                "treatment": treatment.metrics["_instrument_attribution"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "trade_ledger_baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "bollinger_mr_midband_exit_efficiency_trade_ledger.v5",
                "arm": "baseline",
                "trade_count": len(baseline.enriched_trades),
                "trades": baseline.enriched_trades,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "trade_ledger_treatment.json").write_text(
        json.dumps(
            {
                "schema_version": "bollinger_mr_midband_exit_efficiency_trade_ledger.v5",
                "arm": "treatment",
                "trade_count": len(treatment.enriched_trades),
                "trades": treatment.enriched_trades,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    config_snapshot = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_efficiency_development_config_snapshot.v5",
        "hypothesis_id": HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "contract_id": contract["schema_version"],
        "baseline_config_id": BASELINE_CONFIG_ID,
        "treatment_id": contract["treatment"]["treatment_id"],
        "dataset_id": DATASET_ID,
        "decision_segment": {"start": DECISION_START, "end_exclusive": DECISION_END_EXCLUSIVE},
        "decision_thresholds": contract["decision_thresholds"],
        "cost_model": contract["cost_model"],
        "seed": PRIMARY_SEED,
        "stop_pct": STOP_PCT,
        "mechanism_id": freeze["mechanism_id"],
    }
    (output_dir / "config_snapshot.json").write_text(
        json.dumps(config_snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    v1_pkg = repo / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v1"
    v5_pkg = repo / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v5"
    code_hashes = {
        "midband_exit_mechanism_v1.py": _sha256_file(v1_pkg / "midband_exit_mechanism_v1.py"),
        "exit_efficiency_gate_v1.py": _sha256_file(v1_pkg / "exit_efficiency_gate_v1.py"),
        "decision_v1.py": _sha256_file(v1_pkg / "decision_v1.py"),
        "panel_runner_v5.py": _sha256_file(v5_pkg / "panel_runner_v5.py"),
        "contract": canonical_json_sha256(contract),
    }
    (output_dir / "code_config_hashes.json").write_text(
        json.dumps(code_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    command = (
        "PYTHONPATH=src:. python3 scripts/research/"
        "run_evaluate_bollinger_mr_midband_exit_efficiency_development_v5.py "
        f"--output-dir {output_dir}"
    )
    summary = {
        "schema_version": "evaluate_bollinger_mr_midband_exit_efficiency_development_summary.v5",
        "evaluation_run_id": EVALUATION_RUN_ID,
        "evaluation_run_count": 1,
        "backtest_executed": True,
        "hypothesis_id": HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "v1_rerun": False,
        "v2_rerun": False,
        "v3_rerun": False,
        "v1_partial_results_reused": False,
        "v2_partial_results_reused": False,
        "v3_partial_results_reused": False,
        "measurement_validity": validity,
        "binding_fix_surface": BINDING_FIX_SURFACE,
        "binding_fix_bound": True,
        "evaluation_started": True,
        "evaluation_completed": True,
        "panel_backtest_executed": True,
        "economic_verdict": (
            decision_out["result_class"] if decision_out.get("evaluable") else "NOT_EVALUATED"
        ),
        "pass": decision_out.get("result_class") == "PASS",
        "fail": decision_out.get("result_class") == "FAIL",
        "acceptance_criteria_met": decision_out.get("result_class") == "PASS",
        "auto_rerun_executed": False,
        "rerun_allowed": False,
        "contract_id": contract["schema_version"],
        "contract_ref": CONTRACT_REL_PATH,
        "config_id": BASELINE_CONFIG_ID,
        "dataset_id": DATASET_ID,
        "dataset_class": DATASET_CLASS,
        "development_only": True,
        "development_panel_accessed": True,
        "development_period": f"{DECISION_START}..{DECISION_END_EXCLUSIVE}",
        "development_split_digest": DEVELOPMENT_SPLIT_DIGEST,
        "instrument_count": len(members),
        "seed": PRIMARY_SEED,
        "cost_model": contract["cost_model"],
        "cost_multiplier": COST_MULTIPLIER,
        "stop_pct": STOP_PCT,
        "command": command,
        "panel_proof": panel_proof,
        "baseline_metrics": _public_metrics(baseline.metrics),
        "treatment_metrics": _public_metrics(treatment.metrics),
        "exit_attribution": exit_attribution,
        "decision": decision_out,
        "result_class": decision_out["result_class"],
        "baseline_wallclock_seconds": baseline.wallclock_seconds,
        "treatment_wallclock_seconds": treatment.wallclock_seconds,
        "holdout_accessed": False,
        "holdout_data_accessed": False,
        "sealed_holdout_content_inspected": False,
        "productive_trading_logic_changed": False,
        "production_strategy_semantics_changed": False,
        "double_play_authority_changed": False,
        "risk_sizing_execution_semantics_changed": False,
        "authority_changed": False,
        "economic_validity_offline_gate_changed": False,
        "economic_gate_open": False,
        "promotion_eligible": False,
        "runtime_activated": False,
        "shadow_activated": False,
        "testnet_activated": False,
        "orders_sent": False,
        "pass_criteria_changed": False,
        "cost_model_changed": False,
        "entry_eligibility_retuned": False,
        "observability_surface": "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1",
        "observability_surface_bound": True,
        "lifecycle_checkpoint_surface": (
            "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5"
        ),
        "lifecycle_checkpoint_surface_bound": True,
        "run_slot_claimed": True,
        "v4_rerun": False,
        "v4_partial_results_reused": False,
        "partial_metrics_authoritative": False,
        "base_sha": _git_base_sha(repo),
        "python_version": sys.version.split()[0],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )

    (output_dir / "determinism_repro.txt").write_text(
        "\n".join(
            [
                f"COMMAND={command}",
                f"DATASET_ID={DATASET_ID}",
                f"SEED={PRIMARY_SEED}",
                f"DECISION_START={DECISION_START}",
                f"DECISION_END_EXCLUSIVE={DECISION_END_EXCLUSIVE}",
                "EVALUATION_RUN_COUNT=1",
                f"MANIFEST_SHA256={panel_proof['manifest_sha256']}",
                f"CONTENT_HASH={panel_proof['content_hash']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "safety_attestation.md").write_text(
        "\n".join(
            [
                "# Safety attestation — midband exit-efficiency DEVELOPMENT evaluation v5",
                "",
                f"- Hypothesis: `{HYPOTHESIS_ID}`",
                f"- Predecessor (terminal, not rerun): `{REQUIRED_PREDECESSOR_HYPOTHESIS_ID}`",
                "- DEVELOPMENT_ONLY=true",
                "- EVALUATION_RUN_COUNT=1",
                "- HOLDOUT_DATA_ACCESSED=false",
                "- V1_PARTIAL_RESULTS_REUSED=false",
                "- V3_PARTIAL_RESULTS_REUSED=false",
                "- V4_PARTIAL_RESULTS_REUSED=false",
                "- V3_RERUN=false",
                "- V4_RERUN=false",
                "- Economic / promotion gates closed",
                "- No Master-V2 / Double-Play / risk / sizing / execution mutation",
                "- No runtime / orders",
                "- PASS_CRITERIA frozen; COST_MODEL_CANONICAL frozen at 1.0x",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# Evaluate Bollinger/MR midband exit-efficiency DEVELOPMENT v5",
                "",
                f"HYPOTHESIS_ID={HYPOTHESIS_ID}",
                f"PREDECESSOR_HYPOTHESIS_ID={REQUIRED_PREDECESSOR_HYPOTHESIS_ID}",
                f"DATASET={DATASET_ID}",
                "DEVELOPMENT_ONLY=true",
                "EVALUATION_RUN_COUNT=1",
                "HOLDOUT_DATA_ACCESSED=false",
                "V1_PARTIAL_RESULTS_REUSED=false",
                "V3_PARTIAL_RESULTS_REUSED=false",
                "V4_PARTIAL_RESULTS_REUSED=false",
                "V3_RERUN=false",
                "V4_RERUN=false",
                f"RESULT_CLASS={decision_out['result_class']}",
                f"REASON={decision_out['reason']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    lc_tracker.mark(
        LIFECYCLE_STATE_SUMMARY_COMMITTED,
        result_class=decision_out["result_class"],
    )
    lc_tracker.mark(
        LIFECYCLE_STATE_TERMINAL_COMMITTED,
        result_class=decision_out["result_class"],
    )
    if lifecycle is not None:
        lifecycle.mark_complete()
    return summary


__all__ = ["run_development_evaluation", "EVALUATION_RUN_ID", "BASELINE_CONFIG_ID"]
