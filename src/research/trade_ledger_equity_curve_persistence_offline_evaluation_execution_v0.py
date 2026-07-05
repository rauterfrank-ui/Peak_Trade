"""Trade ledger equity curve persistence offline evaluation execution v0 owner.

Bounded offline evaluation with TRADE_LEDGER_V1.jsonl and EQUITY_CURVE_V1.jsonl persistence
under ratified evidence class TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0. Reuses canonical
STEP31F economic evaluation and MV2 research backtest wiring. No runtime, order, credentials,
arming, or authority effect. Execution requires operator GO after binding materialization merge.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.economic_viability_evidence_v1 import (
    EconomicViabilityEvidenceError,
    load_economic_viability_evidence_bundle_v1,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    extract_dataset_paths_from_config,
    run_candidate_economic_evaluation_v0,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    load_step31f_evaluation_config_v0,
)

PACKAGE_MARKER = "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "trade_ledger_equity_curve_persistence_offline_evaluation_execution.v0"
EXECUTION_ID = "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0"
EXECUTION_VERSION = "v0"

OPERATOR_GO = "GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"
EXPECTED_ORIGIN_MAIN_SHA = "5e86ed8e0ab21c42fbbd97c8510d58e74db263ec"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

EXECUTION_AUTHORIZED = False
EVALUATION_AUTHORIZED = False
RUNTIME_AUTHORIZED = False
ORDERS_ALLOWED = False
CREDENTIALS_REQUIRED = False

EVIDENCE_CLASS_ID = "TRADE_LEDGER_AND_EQUITY_CURVE_PERSISTENCE_V0"
STRATEGY_BINDING_REF = "trend_following/v1"
STRATEGY_BINDING_DIGEST = "ea3bde558a2ffd903ed7b7f678cb0cf0a8a4b1f1bb7f5978f7b5bc8f69ab8478"
STRATEGY_ID = "trend_following"
STRATEGY_VERSION = "v1"
PRIMARY_FAILURE_CLASS = "NEGATIVE_RAW_EDGE"

BINDING_MATERIALIZATION_CONFIG_REL = (
    "config/research/trade_ledger_equity_curve_execution_binding_materialization_v0.json"
)
EVIDENCE_CLASS_SCOPE_REL = "config/research/trade_ledger_equity_curve_evidence_class_scope_v0.json"
PARAMETER_BINDING_REL = (
    "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
)

TRADE_LEDGER_V1_JSONL_EXPORT_OWNER_REF = EVIDENCE_CLASS_SCOPE_REL
EQUITY_CURVE_V1_JSONL_EXPORT_OWNER_REF = EVIDENCE_CLASS_SCOPE_REL
MANIFEST_POLICY_MODULE_REL = "scripts/ops/primary_evidence_retention_v0.py"

ALLOWED_OUTPUT_ARTIFACTS = ("TRADE_LEDGER_V1.jsonl", "EQUITY_CURVE_V1.jsonl")
NO_OUTPUT_JSONL_MATERIALIZED_IN_REPO = True

DEFAULT_DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DURABLE_EVIDENCE_BUNDLE_PREFIX = (
    "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0"
)

FAIL_CLOSED_REASON = "EXECUTION_BINDING_MATERIALIZED_NOT_AUTHORIZED"
INCONCLUSIVE_SENTINEL = "INCONCLUSIVE"

REASON_WORKTREE_DIRTY = "WORKTREE_NOT_CLEAN"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_ORIGIN_MAIN_MISMATCH = "ORIGIN_MAIN_SHA_MISMATCH"
REASON_BINDING_CONFIG_MISSING = "BINDING_MATERIALIZATION_CONFIG_MISSING"
REASON_BINDING_DIGEST_MISMATCH = "STRATEGY_BINDING_DIGEST_MISMATCH"
REASON_BINDING_REF_MISSING = "MATERIALIZED_REF_MISSING"
REASON_AUTHORITY_VIOLATION = "AUTHORITY_EFFECT_VIOLATION"
REASON_JSONL_EMPTY = "JSONL_EVIDENCE_EMPTY"
REASON_JSONL_SCHEMA = "JSONL_SCHEMA_VALIDATION_FAILED"
REASON_NO_TRADES = "NO_TRADES_PRODUCED"
REASON_NO_EQUITY_CURVE = "NO_EQUITY_CURVE_PRODUCED"
REASON_MANIFEST_FAILED = "MANIFEST_VERIFY_FAILED"
REASON_REPO_JSONL_LEAK = "JSONL_LEAKED_INTO_REPO"


class PersistenceExecutionVerdict(str, Enum):
    PASS = "PASS"
    FAIL_CLOSED = "FAIL_CLOSED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class PersistenceExecutionScopeV0:
    operator_go: str
    scope_classification: str
    expected_origin_main_sha: str
    strategy_binding_ref: str
    strategy_binding_digest: str
    strategy_id: str
    strategy_version: str
    primary_failure_class: str
    binding_materialization_config_rel: str
    parameter_binding_rel: str
    execution_id: str
    durable_evidence_bundle_prefix: str
    schema_version: str = SCHEMA_VERSION


DEFAULT_PERSISTENCE_EXECUTION_SCOPE_V0 = PersistenceExecutionScopeV0(
    operator_go=OPERATOR_GO,
    scope_classification=SCOPE_CLASSIFICATION,
    expected_origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    strategy_binding_ref=STRATEGY_BINDING_REF,
    strategy_binding_digest=STRATEGY_BINDING_DIGEST,
    strategy_id=STRATEGY_ID,
    strategy_version=STRATEGY_VERSION,
    primary_failure_class=PRIMARY_FAILURE_CLASS,
    binding_materialization_config_rel=BINDING_MATERIALIZATION_CONFIG_REL,
    parameter_binding_rel=PARAMETER_BINDING_REL,
    execution_id=EXECUTION_ID,
    durable_evidence_bundle_prefix=DURABLE_EVIDENCE_BUNDLE_PREFIX,
)


@dataclass(frozen=True)
class ExecutionResultV0:
    verdict: PersistenceExecutionVerdict
    evidence_root: Path
    manifest_verify_rc: int
    trade_ledger_path: Path
    equity_curve_path: Path
    trade_count: int
    equity_point_count: int
    metric_summary: dict[str, Any]
    evaluation_summary: dict[str, Any]
    origin_main_sha: str
    fail_reasons: tuple[str, ...]


def assert_execution_not_authorized_v0() -> None:
    """Fail closed when invoked without operator GO (static contract guard)."""
    raise RuntimeError(FAIL_CLOSED_REASON)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _resolve_origin_main_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_dirty_count(repo_root: Path) -> int:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _resolve_repo_path(repo_root: Path, ref: str) -> Path:
    path_part = ref.split("#", 1)[0]
    return repo_root / path_part


def _metric_value(payload: Mapping[str, Any], field: str) -> Any:
    raw = payload.get(field)
    if isinstance(raw, Mapping):
        return raw.get("value")
    return raw


def verify_preconditions_v0(
    *,
    repo_root: Path,
    confirm: str,
    origin_main_sha: str | None = None,
    require_clean_worktree: bool = True,
    scope: PersistenceExecutionScopeV0 | None = None,
) -> tuple[bool, tuple[str, ...]]:
    active_scope = scope or DEFAULT_PERSISTENCE_EXECUTION_SCOPE_V0
    reasons: list[str] = []
    if confirm != active_scope.operator_go:
        reasons.append(REASON_GO_TOKEN_INVALID)
    resolved = origin_main_sha or _resolve_origin_main_sha(repo_root)
    if resolved != active_scope.expected_origin_main_sha:
        reasons.append(f"{REASON_ORIGIN_MAIN_MISMATCH}:{resolved}")
    if require_clean_worktree and _worktree_dirty_count(repo_root) > 0:
        reasons.append(REASON_WORKTREE_DIRTY)
    return not reasons, tuple(reasons)


def verify_binding_materialization_preflight_v0(
    *,
    repo_root: Path,
    binding_config_path: Path,
    scope: PersistenceExecutionScopeV0 | None = None,
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    active_scope = scope or DEFAULT_PERSISTENCE_EXECUTION_SCOPE_V0
    reasons: list[str] = []
    if not binding_config_path.is_file():
        return False, (REASON_BINDING_CONFIG_MISSING,), {}

    binding = _load_json(binding_config_path)
    if binding.get("authority_effect") != AUTHORITY_EFFECT:
        reasons.append(REASON_AUTHORITY_VIOLATION)
    if binding.get("runtime_authorized") is not False:
        reasons.append("RUNTIME_AUTHORIZED_MUST_BE_FALSE")
    if binding.get("orders_allowed") is not False:
        reasons.append("ORDERS_ALLOWED_MUST_BE_FALSE")
    if binding.get("credentials_required") is not False:
        reasons.append("CREDENTIALS_REQUIRED_MUST_BE_FALSE")
    if str(binding.get("strategy_binding_digest", "")) != active_scope.strategy_binding_digest:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if str(binding.get("strategy_binding_ref", "")) != active_scope.strategy_binding_ref:
        reasons.append("STRATEGY_BINDING_REF_MISMATCH")

    materialized_refs = (
        "execution_owner_ref",
        "execution_runner_ref",
        "trade_ledger_v1_jsonl_export_owner_ref",
        "equity_curve_v1_jsonl_export_owner_ref",
        "manifest_policy_ref",
    )
    for field in materialized_refs:
        ref = str(binding.get(field, "")).strip()
        if not ref:
            reasons.append(f"{REASON_BINDING_REF_MISSING}:{field}")
            continue
        if not _resolve_repo_path(repo_root, ref).is_file():
            reasons.append(f"{REASON_BINDING_REF_MISSING}:{field}:{ref}")

    param_ref = str(binding.get("binding_set", {}).get("parameter_binding_ref", ""))
    if param_ref and not _resolve_repo_path(repo_root, param_ref).is_file():
        reasons.append(f"{REASON_BINDING_REF_MISSING}:parameter_binding_ref")

    return not reasons, tuple(reasons), binding


def _repo_has_jsonl_leak(repo_root: Path) -> bool:
    for pattern in ("**/TRADE_LEDGER_V1.jsonl", "**/EQUITY_CURVE_V1.jsonl"):
        if list(repo_root.glob(pattern)):
            return True
    return False


def _load_bars(dataset_path: Path) -> pd.DataFrame:
    from scripts.ops.run_economic_viability_evidence_evaluation_v1 import (  # noqa: PLC0415
        _load_bars_from_dataset_path,
    )

    return _load_bars_from_dataset_path(dataset_path)


def _side_from_size(size: float) -> str:
    if size > 0:
        return "long"
    if size < 0:
        return "short"
    return INCONCLUSIVE_SENTINEL


def _iso_ts(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return INCONCLUSIVE_SENTINEL
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _equity_at_time(equity_curve: pd.Series, ts: Any) -> Any:
    if ts is None or equity_curve.empty:
        return INCONCLUSIVE_SENTINEL
    stamp = pd.Timestamp(ts)
    if stamp in equity_curve.index:
        return float(equity_curve.loc[stamp])
    idx = equity_curve.index.get_indexer([stamp], method="pad")
    if idx.size and idx[0] >= 0:
        return float(equity_curve.iloc[idx[0]])
    return INCONCLUSIVE_SENTINEL


def materialize_trade_ledger_v1_records_v0(
    *,
    trades_df: pd.DataFrame,
    evaluation_id: str,
    candidate_id: str,
    strategy_id: str,
    strategy_version: str,
    instrument_id: str,
    venue: str,
    equity_curve: pd.Series,
    binding_set: Mapping[str, Any],
    input_digest: str,
    config_digest: str,
    implementation_digest: str,
    required_fields: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if trades_df is None or trades_df.empty:
        return records

    for idx, row in trades_df.iterrows():
        size = float(row.get("size", 0.0) or 0.0)
        entry_price = row.get("entry_price")
        exit_price = row.get("exit_price")
        pnl = row.get("pnl")
        pnl_pct = row.get("pnl_pct")
        entry_time = row.get("entry_time")
        exit_time = row.get("exit_time")
        quantity = abs(size) if size else INCONCLUSIVE_SENTINEL
        entry_price_f = _safe_float(entry_price)
        notional = (
            entry_price_f * abs(size)
            if isinstance(entry_price_f, (int, float)) and size
            else INCONCLUSIVE_SENTINEL
        )
        return_bps = (
            _safe_float(pnl_pct) * 10000.0
            if isinstance(_safe_float(pnl_pct), (int, float))
            else INCONCLUSIVE_SENTINEL
        )
        holding_seconds = INCONCLUSIVE_SENTINEL
        if entry_time is not None and exit_time is not None:
            try:
                holding_seconds = (
                    pd.Timestamp(exit_time) - pd.Timestamp(entry_time)
                ).total_seconds()
            except (TypeError, ValueError):
                holding_seconds = INCONCLUSIVE_SENTINEL

        equity_before = _equity_at_time(equity_curve, entry_time)
        equity_after = _equity_at_time(equity_curve, exit_time)
        drawdown_after = INCONCLUSIVE_SENTINEL
        if isinstance(equity_after, (int, float)) and not equity_curve.empty:
            running_max = equity_curve.cummax()
            if exit_time is not None:
                stamp = pd.Timestamp(exit_time)
                if stamp in running_max.index:
                    peak = float(running_max.loc[stamp])
                    if peak > 0:
                        drawdown_after = (float(equity_after) - peak) / peak

        record: dict[str, Any] = {
            "trade_id": f"{evaluation_id}-trade-{idx}",
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "strategy_id": strategy_id,
            "strategy_version": strategy_version,
            "instrument_id": instrument_id,
            "venue": venue,
            "market_type": "perp",
            "side": _side_from_size(size),
            "entry_time": _iso_ts(entry_time),
            "exit_time": _iso_ts(exit_time),
            "entry_price": _safe_float(entry_price),
            "exit_price": _safe_float(exit_price),
            "quantity": quantity,
            "notional": notional,
            "gross_pnl": _safe_float(pnl),
            "fees": INCONCLUSIVE_SENTINEL,
            "slippage": INCONCLUSIVE_SENTINEL,
            "funding": INCONCLUSIVE_SENTINEL,
            "net_pnl": _safe_float(pnl),
            "return_bps": return_bps,
            "holding_period_seconds": holding_seconds,
            "entry_reason_codes": [str(row.get("exit_reason", ""))]
            if row.get("exit_reason") not in (None, "")
            else [],
            "exit_reason_codes": [str(row.get("exit_reason", ""))]
            if row.get("exit_reason") not in (None, "")
            else [],
            "signal_bucket": INCONCLUSIVE_SENTINEL,
            "ranking_score": INCONCLUSIVE_SENTINEL,
            "regime_label": INCONCLUSIVE_SENTINEL,
            "walk_forward_split_id": INCONCLUSIVE_SENTINEL,
            "data_period_id": INCONCLUSIVE_SENTINEL,
            "parameter_binding_id": str(binding_set.get("parameter_binding_ref", "")),
            "fee_model_binding_id": str(binding_set.get("fee_model_binding_ref", "")),
            "slippage_model_binding_id": str(binding_set.get("slippage_model_binding_ref", "")),
            "funding_model_binding_id": str(binding_set.get("funding_model_binding_ref", "")),
            "execution_model_binding_id": str(binding_set.get("execution_model_binding_ref", "")),
            "equity_before": equity_before,
            "equity_after": equity_after,
            "drawdown_after_trade": drawdown_after,
            "input_digest": input_digest,
            "config_digest": config_digest,
            "implementation_digest": implementation_digest,
        }
        for field in required_fields:
            record.setdefault(field, INCONCLUSIVE_SENTINEL)
        records.append(record)
    return records


def _safe_float(value: Any) -> Any:
    if value is None:
        return INCONCLUSIVE_SENTINEL
    try:
        if pd.isna(value):
            return INCONCLUSIVE_SENTINEL
        return float(value)
    except (TypeError, ValueError):
        return INCONCLUSIVE_SENTINEL


def materialize_equity_curve_v1_records_v0(
    *,
    equity_curve: pd.Series,
    evaluation_id: str,
    candidate_id: str,
    instrument_id: str,
    input_digest: str,
    required_fields: Sequence[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if equity_curve is None or equity_curve.empty:
        return records

    running_max = equity_curve.cummax()
    drawdown = equity_curve - running_max
    drawdown_pct = drawdown / running_max.replace(0, pd.NA)

    for ts, equity in equity_curve.items():
        dd = drawdown.loc[ts]
        dd_pct = drawdown_pct.loc[ts]
        record: dict[str, Any] = {
            "timestamp": _iso_ts(ts),
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "instrument_id_or_universe": instrument_id,
            "equity": _safe_float(equity),
            "cash": INCONCLUSIVE_SENTINEL,
            "unrealized_pnl": INCONCLUSIVE_SENTINEL,
            "realized_pnl": INCONCLUSIVE_SENTINEL,
            "cumulative_fees": INCONCLUSIVE_SENTINEL,
            "cumulative_slippage": INCONCLUSIVE_SENTINEL,
            "cumulative_funding": INCONCLUSIVE_SENTINEL,
            "drawdown": _safe_float(dd),
            "drawdown_pct": _safe_float(dd_pct),
            "exposure_notional": INCONCLUSIVE_SENTINEL,
            "position_count": INCONCLUSIVE_SENTINEL,
            "active_side_count": INCONCLUSIVE_SENTINEL,
            "walk_forward_split_id": INCONCLUSIVE_SENTINEL,
            "regime_label": INCONCLUSIVE_SENTINEL,
            "data_quality_status": "PARTIAL_FIELDS_INCONCLUSIVE",
            "input_digest": input_digest,
        }
        for field in required_fields:
            record.setdefault(field, INCONCLUSIVE_SENTINEL)
        records.append(record)
    return records


def validate_jsonl_records_v0(
    records: Sequence[Mapping[str, Any]],
    required_fields: Sequence[str],
) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not records:
        failures.append("records_empty")
        return False, failures
    for i, record in enumerate(records):
        for field in required_fields:
            if field not in record:
                failures.append(f"row_{i}:missing_field:{field}")
    return not failures, failures


def _write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    lines = [json.dumps(record, sort_keys=True, default=str) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _build_metric_summary(
    *,
    evidence_payload: Mapping[str, Any],
    candidate_result_manifest_rc: int,
    trade_count: int,
    equity_point_count: int,
    primary_failure_class: str,
) -> dict[str, Any]:
    return {
        "schema_version": "trade_ledger_equity_curve_metric_summary.v0",
        "trade_count": trade_count,
        "equity_point_count": equity_point_count,
        "gross_return": _metric_value(evidence_payload, "gross_return"),
        "net_return": _metric_value(evidence_payload, "net_return"),
        "net_expectancy": _metric_value(evidence_payload, "net_expectancy"),
        "profit_factor": _metric_value(evidence_payload, "profit_factor"),
        "sharpe": _metric_value(evidence_payload, "sharpe"),
        "sortino": _metric_value(evidence_payload, "sortino"),
        "max_drawdown": _metric_value(evidence_payload, "max_drawdown"),
        "calmar": _metric_value(evidence_payload, "calmar"),
        "turnover": _metric_value(evidence_payload, "turnover"),
        "fee_drag": _metric_value(evidence_payload, "fee_drag"),
        "funding_drag": _metric_value(evidence_payload, "funding_drag"),
        "slippage_impact": _metric_value(evidence_payload, "slippage_impact"),
        "evidence_status": evidence_payload.get("status"),
        "primary_failure_class": primary_failure_class,
        "primary_failure_class_unchanged": True,
        "economic_validity_offline_gate_pass": evidence_payload.get("gates_pass"),
        "candidate_manifest_verify_rc": candidate_result_manifest_rc,
    }


def run_execution_v0(
    *,
    confirm: str,
    repo_root: Path,
    durable_evidence_root: Path,
    binding_config_path: Path | None = None,
    require_clean_worktree: bool = True,
    scope: PersistenceExecutionScopeV0 | None = None,
) -> ExecutionResultV0:
    active_scope = scope or DEFAULT_PERSISTENCE_EXECUTION_SCOPE_V0
    origin_main = _resolve_origin_main_sha(repo_root)
    pre_ok, pre_reasons = verify_preconditions_v0(
        repo_root=repo_root,
        confirm=confirm,
        origin_main_sha=origin_main,
        require_clean_worktree=require_clean_worktree,
        scope=active_scope,
    )
    if not pre_ok:
        raise ValueError(f"PRECONDITION_FAILED:{pre_reasons}")

    binding_path = binding_config_path or (
        repo_root / active_scope.binding_materialization_config_rel
    )
    bind_ok, bind_reasons, binding = verify_binding_materialization_preflight_v0(
        repo_root=repo_root,
        binding_config_path=binding_path,
        scope=active_scope,
    )
    if not bind_ok:
        raise ValueError(f"BINDING_PREFLIGHT_FAILED:{bind_reasons}")

    if _repo_has_jsonl_leak(repo_root):
        raise ValueError(REASON_REPO_JSONL_LEAK)

    evidence_class_scope = _load_json(repo_root / EVIDENCE_CLASS_SCOPE_REL)
    trade_ledger_fields = list(evidence_class_scope.get("trade_ledger_required_fields", []))
    equity_curve_fields = list(evidence_class_scope.get("equity_curve_required_fields", []))

    evidence_root = (
        durable_evidence_root / f"{active_scope.durable_evidence_bundle_prefix}_{_utc_slug()}"
    )
    evidence_root.mkdir(parents=True, exist_ok=False)

    evaluation_id = f"{active_scope.execution_id}-{uuid.uuid4().hex[:12]}"
    binding_set = binding.get("binding_set", {})
    config_path = repo_root / active_scope.parameter_binding_rel
    candidate_dir = evidence_root / "candidate_economic_evaluation"

    candidate_result = run_candidate_economic_evaluation_v0(
        repo_root=repo_root,
        strategy_id=active_scope.strategy_id,
        strategy_version=active_scope.strategy_version,
        config_path=config_path,
        output_dir=candidate_dir,
    )

    try:
        loaded = load_economic_viability_evidence_bundle_v1(candidate_dir)
        evidence_payload = loaded.evidence.to_dict()
    except EconomicViabilityEvidenceError as exc:
        raise ValueError(f"EVIDENCE_BUNDLE_LOAD_FAILED:{exc}") from exc

    cfg = load_step31f_evaluation_config_v0(repo_root, active_scope.strategy_id)
    dataset_path, _manifest_path = extract_dataset_paths_from_config(cfg)
    bars = _load_bars(Path(dataset_path))
    real_binding = cfg.get("real_admissible_futures_evaluation_binding_v1", {})
    instrument_id = str(real_binding.get("canonical_instrument_id", "inst-eth-usdt-perp"))
    venue = str(real_binding.get("source_venue", "OKX"))

    wiring_result = mv2_wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=active_scope.strategy_id,
        cfg=cfg,
        instrument_id=instrument_id,
    )
    backtest = wiring_result.backtest_result
    trades_df = backtest.trades
    equity_curve = backtest.equity_curve

    input_digest = str(binding_set.get("data_digest", ""))
    config_digest = str(binding_set.get("config_digest", ""))
    implementation_digest = str(binding_set.get("implementation_digest", ""))

    trade_records = materialize_trade_ledger_v1_records_v0(
        trades_df=trades_df,
        evaluation_id=evaluation_id,
        candidate_id=active_scope.strategy_binding_ref,
        strategy_id=active_scope.strategy_id,
        strategy_version=active_scope.strategy_version,
        instrument_id=instrument_id,
        venue=venue,
        equity_curve=equity_curve,
        binding_set=binding_set,
        input_digest=input_digest,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        required_fields=trade_ledger_fields,
    )
    equity_records = materialize_equity_curve_v1_records_v0(
        equity_curve=equity_curve,
        evaluation_id=evaluation_id,
        candidate_id=active_scope.strategy_binding_ref,
        instrument_id=instrument_id,
        input_digest=input_digest,
        required_fields=equity_curve_fields,
    )

    fail_reasons: list[str] = []
    if not trade_records:
        fail_reasons.append(REASON_NO_TRADES)
    if not equity_records:
        fail_reasons.append(REASON_NO_EQUITY_CURVE)

    trade_ok, trade_failures = validate_jsonl_records_v0(trade_records, trade_ledger_fields)
    equity_ok, equity_failures = validate_jsonl_records_v0(equity_records, equity_curve_fields)
    if not trade_ok:
        fail_reasons.extend(trade_failures)
    if not equity_ok:
        fail_reasons.extend(equity_failures)

    trade_ledger_path = evidence_root / "TRADE_LEDGER_V1.jsonl"
    equity_curve_path = evidence_root / "EQUITY_CURVE_V1.jsonl"
    _write_jsonl(trade_ledger_path, trade_records)
    _write_jsonl(equity_curve_path, equity_records)

    resolved_primary_failure_class = str(
        evidence_payload.get("primary_failure_class") or active_scope.primary_failure_class
    )
    metric_summary = _build_metric_summary(
        evidence_payload=evidence_payload,
        candidate_result_manifest_rc=candidate_result.manifest_verify_rc,
        trade_count=len(trade_records),
        equity_point_count=len(equity_records),
        primary_failure_class=resolved_primary_failure_class,
    )

    evaluation_summary = {
        "schema_version": active_scope.schema_version,
        "execution_id": active_scope.execution_id,
        "evaluation_id": evaluation_id,
        "scope_classification": active_scope.scope_classification,
        "go_token_consumed": active_scope.operator_go,
        "origin_main_sha": origin_main,
        "strategy_binding_ref": active_scope.strategy_binding_ref,
        "strategy_binding_digest": active_scope.strategy_binding_digest,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "primary_failure_class": resolved_primary_failure_class,
        "primary_failure_class_unchanged": True,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "runtime_authorized": False,
        "orders_allowed": False,
        "credentials_required": False,
        "offline_only": True,
        "candidate_runner_execution_success": candidate_result.runner_execution_success,
        "candidate_terminal_status": candidate_result.terminal_status.value,
        "candidate_economic_validity_result": candidate_result.economic_validity_result,
        "candidate_evidence_status": candidate_result.evidence_status,
        "trade_ledger_record_count": len(trade_records),
        "equity_curve_record_count": len(equity_records),
        "durable_evidence_root": str(evidence_root),
        "created_at_utc": _utc_now_z(),
        "fail_reasons": fail_reasons,
    }

    if fail_reasons:
        evaluation_summary["process_verdict"] = PersistenceExecutionVerdict.FAIL_CLOSED.value
    else:
        evaluation_summary["process_verdict"] = PersistenceExecutionVerdict.PASS.value

    (evidence_root / "execution_binding_snapshot.json").write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "selected_binding_snapshot.json").write_text(
        json.dumps(
            {
                "strategy_binding_ref": active_scope.strategy_binding_ref,
                "strategy_binding_digest": active_scope.strategy_binding_digest,
                "binding_set": binding_set,
                "parameter_binding_ref": active_scope.parameter_binding_rel,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "evaluation_summary.json").write_text(
        json.dumps(evaluation_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "metric_summary.json").write_text(
        json.dumps(metric_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_root / "safety_invariants.txt").write_text(
        "\n".join(
            [
                "authority_effect=NONE",
                "runtime_authorized=false",
                "orders_allowed=false",
                "credentials_required=false",
                "promotion_authorized=false",
                "offline_only=true",
                "no_output_jsonl_materialized_in_repo=true",
                f"primary_failure_class={resolved_primary_failure_class}",
                "primary_failure_class_unchanged=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_root / "stdout_stderr.log").write_text(
        f"execution_id={evaluation_id}\n"
        f"candidate_runner_success={candidate_result.runner_execution_success}\n"
        f"trade_count={len(trade_records)}\n"
        f"equity_point_count={len(equity_records)}\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: PLC0415

    manifest_rc, manifest_msg = retention.finalize_durable_bundle_manifest(evidence_root)
    if manifest_rc != 0:
        fail_reasons.append(f"{REASON_MANIFEST_FAILED}:{manifest_msg}")

    if _repo_has_jsonl_leak(repo_root):
        fail_reasons.append(REASON_REPO_JSONL_LEAK)

    if fail_reasons:
        verdict = PersistenceExecutionVerdict.FAIL_CLOSED
    elif candidate_result.terminal_status.value == "INCONCLUSIVE":
        verdict = PersistenceExecutionVerdict.INCONCLUSIVE
    else:
        verdict = PersistenceExecutionVerdict.PASS

    return ExecutionResultV0(
        verdict=verdict,
        evidence_root=evidence_root,
        manifest_verify_rc=manifest_rc,
        trade_ledger_path=trade_ledger_path,
        equity_curve_path=equity_curve_path,
        trade_count=len(trade_records),
        equity_point_count=len(equity_records),
        metric_summary=metric_summary,
        evaluation_summary=evaluation_summary,
        origin_main_sha=origin_main,
        fail_reasons=tuple(fail_reasons),
    )


__all__ = [
    "OPERATOR_GO",
    "SCOPE_CLASSIFICATION",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "AUTHORITY_EFFECT",
    "RUNTIME_EFFECT",
    "ORDER_EFFECT",
    "EVIDENCE_CLASS_ID",
    "STRATEGY_BINDING_DIGEST",
    "PersistenceExecutionScopeV0",
    "DEFAULT_PERSISTENCE_EXECUTION_SCOPE_V0",
    "PersistenceExecutionVerdict",
    "verify_preconditions_v0",
    "verify_binding_materialization_preflight_v0",
    "run_execution_v0",
    "ExecutionResultV0",
    "assert_execution_not_authorized_v0",
    "FAIL_CLOSED_REASON",
    "EXECUTION_AUTHORIZED",
]
