"""Single-run DEVELOPMENT panel evaluation v7: identical V6 exits + reentry cooldown.

IMPLEMENTATION_ONLY wiring. Authorized panel evaluation requires explicit
hypothesis-id authorization. Default CLI path is preflight-only.

Control: V6 composite midband/max-hold exits, cooldown OFF.
Treatment: identical exits, cooldown ON (24 PT1H bars, scope instrument+direction).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
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
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    MidbandExitMechanismError,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_midband_max_holding_exit_mechanism_v6 import (
    mechanism_freeze_payload,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.constants_v6 import (
    REQUIRED_FROZEN_EXIT_PARAMETERS as V6_REQUIRED_FROZEN_EXIT_PARAMETERS,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6 import (
    load_json,
)
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
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.constants_v7 import (
    BASELINE_CONFIG_ID,
    BB_PERIOD,
    BINDING_FIX_SURFACE,
    CONTRACT_REL_PATH,
    COST_MULTIPLIER,
    DATASET_CLASS,
    DATASET_ID,
    DECISION_END_EXCLUSIVE,
    DECISION_START,
    DEVELOPMENT_PREREGISTRATION_DIGEST,
    EVALUATION_RUN_ID,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    FEE_BPS,
    HALF_SPREAD_BPS,
    HYPOTHESIS_ID,
    INFRASTRUCTURE_DIAGNOSTIC_CLASS_DEFAULT,
    INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
    LIFECYCLE_CHECKPOINT_SURFACE,
    LIFECYCLE_TERMINAL_INCONCLUSIVE_INFRA,
    MAX_FEATURE_LOOKBACK_HOURS,
    MAX_TRADE_COUNT_REDUCTION_FRACTION,
    MECHANISM_ID,
    MINIMUM_TRADE_COUNT,
    OBSERVABILITY_SURFACE,
    OPERATOR_CLARIFICATION_AUTHORITY_ID,
    OWNER_SURFACE,
    PORTFOLIO_AGGREGATION_ID,
    PRIMARY_SEED,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
    SHARED_INITIAL_CAPITAL,
    SLEEVE_INITIAL_CASH,
    SLIPPAGE_BPS,
    STRATEGY_ID,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.decision_v7 import (
    decide_development_evaluation_v7,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.measurement_validity_preflight_v7 import (
    run_measurement_validity_preflight,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.reentry_cooldown_gate_v7 import (
    optional_v7_control_or_treatment_gate,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7 import (
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v7 import (
    resolve_effective_evaluation_authorization,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7 import (
    AUTHORIZED_STATUS,
    READY_STATUS,
    OperatorClarificationAuthorityError,
    b7_b8_technical_proof,
    load_and_validate_authority,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    included_panel_members,
    load_member_bars,
    resolve_development_archive_root,
    verify_development_panel_hashes,
)
from src.research.evaluation_runner_lifecycle_observability_v1.atomic_io_v1 import (
    atomic_write_json_v1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.shared_portfolio_equity_research_v1 import (
    build_equal_weight_portfolio_equity,
    portfolio_metrics_from_equity,
)
from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


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


class _LifecycleCheckpointTrackerV7:
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


def _claim_run_slot_atomic_v7(
    output_dir: Path, *, repo: Path, started_at: str
) -> dict[str, object]:
    claim_path = output_dir / "run_slot_claim.json"
    if claim_path.is_file():
        raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CLAIMED")
    payload = {
        "schema_version": "bollinger_mr_midband_exit_reentry_cooldown_development_v7_run_slot_claim.v1",
        "hypothesis_id": HYPOTHESIS_ID,
        "evaluation_run_id": EVALUATION_RUN_ID,
        "dataset_id": DATASET_ID,
        "dataset_class": DATASET_CLASS,
        "development_preregistration_digest": DEVELOPMENT_PREREGISTRATION_DIGEST,
        "contract_ref": CONTRACT_REL_PATH,
        "runner_script": (
            "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7.py"
        ),
        "runner_version": "v7",
        "mechanism_id": MECHANISM_ID,
        "lifecycle_state": "RUNNING",
        "commit_sha": _git_base_sha(repo),
        "claim_timestamp_utc": started_at,
        "process_id": os.getpid(),
        "evaluation_run_count_authorized": 1,
        "evaluation_run_count_after_claim": 1,
        "run_limit": 1,
        "slot_claimed": True,
        "slot_consumed": True,
        "holdout_data_accessed": False,
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
        fees = rec.get("fee_total")
        if fees is None:
            fees = rec.get("fee")
        slip = rec.get("slippage_total")
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
                "gross_pnl": float(rec["gross_pnl"]),
                "fees": float(fees),
                "slippage": float(slip),
                "net_pnl": float(rec["pnl"]),
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
    midband_exit_count: int = 0,
    max_holding_exit_count: int = 0,
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
    long_net = float(sum(float(t["net_pnl"]) for t in enriched if str(t["side"]).lower() == "long"))
    return {
        "portfolio_aggregation_id": PORTFOLIO_AGGREGATION_ID,
        "trade_count": int(core["trade_count"]),
        "long_trades": long_n,
        "short_trades": short_n,
        "short_trade_count": short_n,
        "long_net_pnl": long_net,
        "gross_pnl": float(core["gross_pnl"]),
        "net_pnl": float(core["net_pnl"]),
        "fees": float(core["fees"]),
        "slippage": float(core["slippage"]),
        "cost_drag": float(core["gross_pnl"]) - float(core["net_pnl"]),
        "net_return": float(port["net_return"]),
        "net_return_after_costs": float(port["net_return"]),
        "max_drawdown": float(port["max_drawdown"]),
        "profit_factor": core["net_profit_factor"],
        "net_profit_factor": core["net_profit_factor"],
        "turnover": float(core["trade_count"]),
        "worst1_abs_net_share": concentration["worst1_abs_net_share"],
        "exits_forced_by_gate": int(exits_forced_by_gate),
        "midband_exit_count": int(midband_exit_count),
        "max_holding_exit_count": int(max_holding_exit_count),
        "cost_multiplier": COST_MULTIPLIER,
        "_portfolio_equity": portfolio_eq,
        "_instrument_attribution": instruments,
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
    cooldown_enabled: bool,
    lifecycle: Any | None = None,
    lc_tracker: _LifecycleCheckpointTrackerV7 | None = None,
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
    midband_exit_total = 0
    max_holding_exit_total = 0

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
        with optional_v7_control_or_treatment_gate(
            cooldown_enabled=cooldown_enabled, bars=bars, instrument_id=native
        ) as gate_bundle:
            result = run_mv2_research_backtest_wiring_v1(
                bars,
                strategy_id=STRATEGY_ID,
                cfg=cfg,
                instrument_id=CANONICAL_INSTRUMENT_ID,
                profile_binding=_profile(),
                observational_panel_member_instrument_id=canon,
            )
            counters = gate_bundle.get("exit_counters") or {}
            cooldown_attr = gate_bundle["cooldown_state"].attribution()
        trades, eq_dec = _extract_member_trades(
            result,
            instrument_id=canon,
            decision_start=d_start,
            decision_end=d_end,
        )
        forced = int(counters.get("exits_forced_by_gate") or 0)
        exits_forced_total += forced
        exit_bars_total += int(counters.get("exit_bars_observed") or 0)
        midband_exit_total += int(counters.get("midband_exit_count") or 0)
        max_holding_exit_total += int(counters.get("max_holding_exit_count") or 0)
        all_trades.extend(trades)
        equity_curves[canon] = eq_dec
        rows.append(
            {
                "member_id": canon,
                "trade_count": len(trades),
                "exits_forced_by_gate": forced,
                "exit_bars_observed": int(counters.get("exit_bars_observed") or 0),
                "blocked_same_side_reentry_count": int(
                    cooldown_attr.get("blocked_same_side_reentry_count") or 0
                ),
                "cooldown_activation_count": int(
                    cooldown_attr.get("cooldown_activation_count") or 0
                ),
                "cooldown_attribution": cooldown_attr,
            }
        )
        if lifecycle is not None:
            lifecycle.record_member_progress(
                phase=arm,
                member_index=i,
                members_total=len(members),
                member_id=native,
                extra={"trades": len(trades)},
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
        midband_exit_count=midband_exit_total,
        max_holding_exit_count=max_holding_exit_total,
    )
    exit_attr = {
        "cooldown_enabled": cooldown_enabled,
        "exits_forced_by_gate": exits_forced_total,
        "exit_bars_observed": exit_bars_total,
        "midband_exit_count": midband_exit_total,
        "max_holding_exit_count": max_holding_exit_total,
    }
    return ArmResult(
        arm=arm,
        rows=rows,
        metrics=metrics,
        enriched_trades=enriched,
        exit_attribution=exit_attr,
        wallclock_seconds=float(time.perf_counter() - t0),
    )


def _assert_no_v6_partial_reuse(contract: Mapping[str, Any]) -> None:
    if contract.get("predecessor_hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID:
        raise RuntimeError("PREDECESSOR_V6_HYPOTHESIS_ID_MISMATCH")
    if contract.get("v6_partial_results_reused") is True:
        raise RuntimeError("V6_PARTIAL_RESULTS_REUSED_FORBIDDEN")
    if contract.get("v6_economic_result_imported") is True:
        raise RuntimeError("V6_ECONOMIC_RESULT_IMPORT_FORBIDDEN")


def assert_v7_frozen_exit_parameters_unchanged() -> None:
    """Bind V7 freeze to V6 composite constants; do not mutate immutable prereg JSON."""
    if REQUIRED_FROZEN_EXIT_PARAMETERS != V6_REQUIRED_FROZEN_EXIT_PARAMETERS:
        raise MidbandExitMechanismError("FROZEN_EXIT_PARAMETERS_MISMATCH")


def assert_v7_authority_and_prereg_gates(
    *,
    repo: Path,
    require_evaluation_authorized: bool,
    require_ready_status: bool = True,
) -> dict[str, Any]:
    """Fail-closed gates before any panel/holdout access or run-slot claim.

    Effective authorization is derived from the separate ratification SSOT +
    authority lifecycle state. The immutable preregistration contract keeps
    ``evaluation_authorized=false`` (DEFINITION_ONLY field).
    """
    reject_holdout_dataset_or_path(DATASET_ID)
    report = load_and_validate_repo_contract(repo)
    if report.get("hypothesis_id") != HYPOTHESIS_ID:
        raise RuntimeError("CONTRACT_HYPOTHESIS_ID_NOT_V7")
    if int(report.get("evaluation_run_count", -1)) != 0:
        raise RuntimeError("CONTRACT_EVALUATION_RUN_COUNT_NOT_ZERO")
    if str(report.get("development_preregistration_digest")) != DEVELOPMENT_PREREGISTRATION_DIGEST:
        raise RuntimeError("PREREGISTRATION_DIGEST_MISMATCH")

    try:
        authority_report = load_and_validate_authority(
            repo,
            require_registered=True,
            require_ready_status=require_ready_status,
            require_authorized_status=False,
        )
    except OperatorClarificationAuthorityError as exc:
        raise RuntimeError(f"OPERATOR_CLARIFICATION_AUTHORITY_GATE:{exc}") from exc

    authority = authority_report["authority"]
    status = str(authority_report.get("status") or "")
    if require_ready_status and status not in (READY_STATUS, AUTHORIZED_STATUS):
        raise RuntimeError(f"STATUS_NOT_READY_OR_AUTHORIZED:{status}")
    if not authority.get("b1_through_b6_fully_resolved"):
        raise RuntimeError("UNRESOLVED_B1_THROUGH_B6")

    b7b8 = b7_b8_technical_proof(authority=authority)
    if not b7b8.get("b7_requires_wiring_and_tests") or not b7b8.get("b8_requires_wiring_and_tests"):
        raise RuntimeError("B7_B8_TECHNICAL_FULFILLMENT_MARKERS_MISSING")

    contract = load_json(repo / CONTRACT_REL_PATH)
    # Prereg boolean remains false forever; effective auth is ratification/lifecycle.
    if contract.get("evaluation_authorized") is not False:
        raise RuntimeError("PREREG_EVALUATION_AUTHORIZED_FIELD_MUST_REMAIN_FALSE")
    if int(contract.get("evaluation_run_count", -1)) != 0:
        raise RuntimeError("CONTRACT_EVALUATION_RUN_COUNT_NOT_ZERO")

    effective = resolve_effective_evaluation_authorization(repo)
    eval_auth = bool(effective.get("evaluation_authorized"))
    if require_evaluation_authorized and not eval_auth:
        raise RuntimeError(
            f"V7_EVALUATION_NOT_AUTHORIZED:{effective.get('reason') or 'effective_false'}"
        )

    return {
        "prereg_report": report,
        "authority_report": authority_report,
        "authority_digest": authority_report["authority_digest"],
        "evaluation_authorized": eval_auth,
        "effective_authorization": effective,
        "b7_b8": b7b8,
        "authority_id": OPERATOR_CLARIFICATION_AUTHORITY_ID,
        "lifecycle_status": status,
    }


def run_preflight_only(
    *,
    output_dir: Path,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Synthetic measurement-validity preflight. No slot claim. No panel access."""
    repo = repo_root or _repo_root()
    # Authority/prereg gates BEFORE any output artifact creation.
    gates = assert_v7_authority_and_prereg_gates(
        repo=repo,
        require_evaluation_authorized=False,
        require_ready_status=True,
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    validity = run_measurement_validity_preflight(repo_root=repo)
    b7_b8_ok = bool(validity.get("passed")) and bool(
        (validity.get("gates") or {}).get("control_treatment_isolation_ok")
    )
    payload = {
        "schema_version": "bollinger_mr_v7_preflight_only.v1",
        "hypothesis_id": HYPOTHESIS_ID,
        "mode": "preflight",
        "evaluation_run_count": 0,
        "runner_started": False,
        "run_slot_claimed": False,
        "panel_data_accessed": False,
        "development_panel_accessed": False,
        "holdout_data_accessed": False,
        "measurement_validity": validity,
        "operator_clarification_authority_id": gates["authority_id"],
        "operator_clarification_authority_digest": gates["authority_digest"],
        "b7_b8_technically_fulfilled": b7_b8_ok,
        "owner_surface": OWNER_SURFACE,
        "result_class": validity.get("result_class"),
        "passed": validity.get("passed") and b7_b8_ok,
    }
    (output_dir / "measurement_validity_preflight.json").write_text(
        json.dumps(validity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "preflight_only_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def run_development_evaluation(
    *,
    output_dir: Path,
    archive_root: Path | None = None,
    repo_root: Path | None = None,
    lifecycle: Any | None = None,
    authorize_hypothesis_id: str | None = None,
    allow_panel_run: bool = False,
) -> dict[str, Any]:
    """Authorized single DEVELOPMENT evaluation. Fail-closed without explicit auth."""
    if authorize_hypothesis_id != HYPOTHESIS_ID or allow_panel_run is not True:
        raise RuntimeError(
            "V7_EVALUATION_NOT_AUTHORIZED:"
            "require --mode evaluate and "
            f"--authorize-single-development-evaluation {HYPOTHESIS_ID}"
        )

    repo = repo_root or _repo_root()
    # Authority + contract evaluation_authorized gates BEFORE output/slot/panel.
    gates = assert_v7_authority_and_prereg_gates(
        repo=repo,
        require_evaluation_authorized=True,
        require_ready_status=True,
    )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.json"
    if summary_path.is_file():
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
        if int(existing.get("evaluation_run_count", -1)) >= 1:
            raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CONSUMED")
    if (output_dir / "run_slot_claim.json").is_file():
        raise RuntimeError("EVALUATION_RUN_SLOT_ALREADY_CLAIMED")

    contract = load_json(repo / CONTRACT_REL_PATH)
    _assert_no_v6_partial_reuse(contract)

    started_at = _utc_now()
    lc_tracker = _LifecycleCheckpointTrackerV7(
        output_dir, run_id=EVALUATION_RUN_ID, started_at=started_at
    )
    lc_tracker.mark(LIFECYCLE_STATE_PREFLIGHT_RUNNING)
    validity = run_measurement_validity_preflight(repo_root=repo)
    (output_dir / "measurement_validity_preflight.json").write_text(
        json.dumps(validity, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if validity.get("passed") is True:
        lc_tracker.mark(LIFECYCLE_STATE_PREFLIGHT_PASSED)

    # Slot consumed at authorized runner start persistence (before panel / freeze asserts).
    claim = _claim_run_slot_atomic_v7(output_dir, repo=repo, started_at=started_at)
    claim["operator_clarification_authority_digest"] = gates["authority_digest"]
    atomic_write_json_v1(output_dir / "run_slot_claim.json", claim)
    lc_tracker.mark(LIFECYCLE_STATE_RUN_SLOT_CLAIMED, status="STARTED")
    lc_tracker.mark(LIFECYCLE_STATE_RUNNER_STARTED)

    try:
        assert_v7_frozen_exit_parameters_unchanged()
    except MidbandExitMechanismError as exc:
        summary = {
            "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_summary.v7",
            "evaluation_run_id": EVALUATION_RUN_ID,
            "evaluation_run_count": 1,
            "evaluation_started": True,
            "evaluation_completed": False,
            "panel_backtest_executed": False,
            "hypothesis_id": HYPOTHESIS_ID,
            "result_class": RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            "diagnostic_class": "PRE_PANEL_FROZEN_EXIT_PARAMETERS_MISMATCH_NO_PANEL_BACKTEST",
            "lifecycle_terminal_state": LIFECYCLE_TERMINAL_INCONCLUSIVE_INFRA,
            "economic_verdict": "NOT_EVALUATED",
            "reason": str(exc),
            "error": str(exc)[:2000],
            "partial_metrics_authoritative": False,
            "operator_clarification_authority_digest": gates["authority_digest"],
            "holdout_data_accessed": False,
            "rerun_allowed": False,
            "auto_rerun_executed": False,
            "owner_surface": OWNER_SURFACE,
            "base_sha": _git_base_sha(repo),
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        write_manifest_sha256(output_dir)
        try:
            lc_tracker.mark(
                LIFECYCLE_STATE_SUMMARY_COMMITTED,
                result_class=RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            )
            lc_tracker.mark(
                LIFECYCLE_STATE_TERMINAL_COMMITTED,
                result_class=RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            )
        except Exception:  # noqa: BLE001
            pass
        return summary

    if validity.get("passed") is not True:
        invalid_class = str(validity.get("result_class") or "INVALID_MEASUREMENT_BINDING_MISSING")
        summary = {
            "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_summary.v7",
            "evaluation_run_id": EVALUATION_RUN_ID,
            "evaluation_run_count": 1,
            "evaluation_started": True,
            "evaluation_completed": True,
            "panel_backtest_executed": False,
            "hypothesis_id": HYPOTHESIS_ID,
            "result_class": invalid_class,
            "economic_verdict": "NOT_EVALUATED",
            "measurement_validity": validity,
            "operator_clarification_authority_digest": gates["authority_digest"],
            "holdout_data_accessed": False,
            "rerun_allowed": False,
            "auto_rerun_executed": False,
            "observability_surface": OBSERVABILITY_SURFACE,
            "lifecycle_checkpoint_surface": LIFECYCLE_CHECKPOINT_SURFACE,
            "owner_surface": OWNER_SURFACE,
            "base_sha": _git_base_sha(repo),
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        write_manifest_sha256(output_dir)
        lc_tracker.mark(LIFECYCLE_STATE_SUMMARY_COMMITTED, result_class=invalid_class)
        lc_tracker.mark(LIFECYCLE_STATE_TERMINAL_COMMITTED, result_class=invalid_class)
        return summary

    try:
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

        control = run_arm(
            arm="control",
            cfg=cfg,
            archive_root=root,
            members=members,
            load_start=load_start,
            decision_start=DECISION_START,
            decision_end=DECISION_END_EXCLUSIVE,
            cooldown_enabled=False,
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
            cooldown_enabled=True,
            lifecycle=lifecycle,
            lc_tracker=lc_tracker,
        )
        lc_tracker.mark(LIFECYCLE_STATE_PANEL_COMPLETED)

        control_exit_times = {
            (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in control.enriched_trades
        }
        treatment_exit_times = {
            (t["instrument_id"], t["entry_time"]): t["exit_time"] for t in treatment.enriched_trades
        }
        shared = set(control_exit_times) & set(treatment_exit_times)
        exit_fills_identical = all(control_exit_times[k] == treatment_exit_times[k] for k in shared)
        blocked = int(
            sum(int(r.get("blocked_same_side_reentry_count") or 0) for r in treatment.rows)
        )
        cooldown_activations = int(
            sum(int(r.get("cooldown_activation_count") or 0) for r in treatment.rows)
        )
        forced_midband = int(treatment.metrics.get("midband_exit_count") or 0)
        reentry_divergence_observed = blocked >= 1 or cooldown_activations >= 1
        gates_m = validity.get("gates") or {}
        decision_out = decide_development_evaluation_v7(
            control=control.metrics,
            treatment=treatment.metrics,
            reentry_divergence_observed=reentry_divergence_observed,
            exit_fills_identical=exit_fills_identical,
            effective_configs_differ=bool(gates_m.get("effective_configs_differ", True)),
            open_side_binding_observed=bool(gates_m.get("open_side_binding_observed", True)),
            exit_bars_observed=int(treatment.exit_attribution.get("exit_bars_observed") or 0),
            forced_midband_exit_count=forced_midband,
            cooldown_activation_count=cooldown_activations,
            blocked_same_side_reentry_count=blocked,
            authority_binding_ok=True,
            control_treatment_isolation_ok=bool(
                gates_m.get("control_treatment_isolation_ok", True)
            ),
            minimum_trade_count=MINIMUM_TRADE_COUNT,
            max_trade_count_reduction_fraction=MAX_TRADE_COUNT_REDUCTION_FRACTION,
            instrument_concentration_worst1_max=INSTRUMENT_CONCENTRATION_WORST1_ABS_NET_SHARE_MAX,
            cost_multiplier_treatment=COST_MULTIPLIER,
        )

        def _public(m: dict[str, Any]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for k, v in m.items():
                if str(k).startswith("_"):
                    continue
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    out[k] = None
                else:
                    out[k] = v
            return out

        control.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_control.csv")
        treatment.metrics["_portfolio_equity"].to_csv(output_dir / "portfolio_equity_treatment.csv")
        (output_dir / "control_metrics.json").write_text(
            json.dumps(_public(control.metrics), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "treatment_metrics.json").write_text(
            json.dumps(_public(treatment.metrics), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        attribution = {
            "blocked_reentry_count": blocked,
            "blocked_same_side_reentry_count": blocked,
            "cooldown_activation_count": cooldown_activations,
            "forced_midband_exit_count": forced_midband,
            "exit_fills_identical": exit_fills_identical,
            "reentry_divergence_observed": reentry_divergence_observed,
            "treatment_rows": treatment.rows,
        }
        (output_dir / "reentry_attribution.json").write_text(
            json.dumps(attribution, indent=2, sort_keys=True, default=str) + "\n",
            encoding="utf-8",
        )
        (output_dir / "comparison_decision.json").write_text(
            json.dumps(decision_out, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        summary = {
            "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_summary.v7",
            "evaluation_run_id": EVALUATION_RUN_ID,
            "evaluation_run_count": 1,
            "evaluation_started": True,
            "evaluation_completed": True,
            "panel_backtest_executed": True,
            "hypothesis_id": HYPOTHESIS_ID,
            "mechanism_id": MECHANISM_ID,
            "result_class": decision_out["result_class"],
            "economic_verdict": decision_out.get("economic_verdict"),
            "decision": decision_out,
            "pass": decision_out["result_class"] == "PASS",
            "fail": decision_out["result_class"] == "FAIL",
            "operator_clarification_authority_digest": gates["authority_digest"],
            "holdout_data_accessed": False,
            "development_panel_accessed": True,
            "rerun_allowed": False,
            "auto_rerun_executed": False,
            "observability_surface": OBSERVABILITY_SURFACE,
            "lifecycle_checkpoint_surface": LIFECYCLE_CHECKPOINT_SURFACE,
            "binding_fix_surface": BINDING_FIX_SURFACE,
            "owner_surface": OWNER_SURFACE,
            "fee_bps": FEE_BPS,
            "slippage_bps": SLIPPAGE_BPS,
            "base_sha": _git_base_sha(repo),
            "python_version": sys.version.split()[0],
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
        )
        write_manifest_sha256(output_dir)
        lc_tracker.mark(
            LIFECYCLE_STATE_SUMMARY_COMMITTED, result_class=decision_out["result_class"]
        )
        lc_tracker.mark(
            LIFECYCLE_STATE_TERMINAL_COMMITTED, result_class=decision_out["result_class"]
        )
        return summary
    except Exception as exc:  # noqa: BLE001 — infrastructure closeout (B3)
        summary = {
            "schema_version": "evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_summary.v7",
            "evaluation_run_id": EVALUATION_RUN_ID,
            "evaluation_run_count": 1,
            "evaluation_started": True,
            "evaluation_completed": False,
            "panel_backtest_executed": False,
            "hypothesis_id": HYPOTHESIS_ID,
            "result_class": RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            "diagnostic_class": INFRASTRUCTURE_DIAGNOSTIC_CLASS_DEFAULT,
            "lifecycle_terminal_state": LIFECYCLE_TERMINAL_INCONCLUSIVE_INFRA,
            "economic_verdict": "NOT_EVALUATED",
            "reason": str(exc.__class__.__name__),
            "error": str(exc)[:2000],
            "partial_metrics_authoritative": False,
            "operator_clarification_authority_digest": gates["authority_digest"],
            "holdout_data_accessed": False,
            "rerun_allowed": False,
            "auto_rerun_executed": False,
            "owner_surface": OWNER_SURFACE,
            "base_sha": _git_base_sha(repo),
        }
        (output_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        write_manifest_sha256(output_dir)
        try:
            lc_tracker.mark(
                LIFECYCLE_STATE_SUMMARY_COMMITTED,
                result_class=RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            )
            lc_tracker.mark(
                LIFECYCLE_STATE_TERMINAL_COMMITTED,
                result_class=RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
            )
        except Exception:  # noqa: BLE001
            pass
        return summary


__all__ = [
    "assert_v7_authority_and_prereg_gates",
    "run_development_evaluation",
    "run_preflight_only",
]
