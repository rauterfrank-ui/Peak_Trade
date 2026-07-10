#!/usr/bin/env python3
"""Bound offline economic baseline evaluation runner for ehlers_cycle_filter/v1 (STEP29M).

Offline-only. Uses MV2 research wiring and canonical legacy accounting reconciliation.
No runtime, credentials, orders, or authority effect.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (REPO_ROOT / "src", REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts.ops import primary_evidence_retention_v0 as retention  # noqa: E402
from src.backtest import admissible_versioned_futures_dataset_v1 as ds  # noqa: E402
from src.backtest import mv2_research_wiring_v1 as mv2_wiring  # noqa: E402
from src.backtest.admissible_versioned_futures_dataset_v1 import (  # noqa: E402
    load_profile_binding_from_manifest,
)
from src.backtest.economic_validity_policy_v1 import (  # noqa: E402
    EconomicValidityEvidenceMetricsV1,
    default_economic_validity_policy_v1,
    evaluate_economic_validity_against_policy_v1,
)
from src.backtest.step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1 import (  # noqa: E402
    evaluate_ehlers_cycle_filter_v1_admissibility_contract_v1,
    load_ehlers_cycle_filter_v1_evaluation_config_v1,
)
from src.core.metrics import metrics as resilience_metrics  # noqa: E402
from src.research.step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0 import (  # noqa: E402
    METRICS_SUMMARY_FILENAME,
    compute_step29m_ehlers_binding_digest_v0,
    compute_step29m_ehlers_implementation_digest_v0,
    materialize_legacy_backtest_accounting_reconciliation_v0,
    materialize_resilience_metrics_summary_json_v0,
)

ALLOWED_GO_TOKENS = frozenset(
    {
        "GO_EHLERS_CYCLE_FILTER_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0",
        "GO_EHLERS_CYCLE_FILTER_V1_DEFECT_REPAIR_SAME_BINDING_REEVALUATION_V0",
        "GO_OFFLINE_EVALUATION_RESILIENCE_METRICS_SUMMARY_IN_DURABLE_EVIDENCE_V0",
    }
)
STRATEGY_ID = "ehlers_cycle_filter"
EVAL_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json"
)
BINDING_CONFIG_PATH = "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json"
MATERIAL_DIFFERENCE_PATH = (
    "config/research/ehlers_cycle_filter_v1_material_difference_and_non_claim_contract_v0.json"
)


class EconomicClassification(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify_sample(trade_count: int, minimum: int) -> str:
    return "INSUFFICIENT_TRADE_SAMPLE" if trade_count < minimum else "SUFFICIENT_TRADE_SAMPLE"


def _classify_baseline(
    *,
    trade_count: int,
    net_return: float,
    accounting_pass: bool,
    sample_status: str,
) -> tuple[EconomicClassification, str]:
    if not accounting_pass:
        return EconomicClassification.INCONCLUSIVE, "BASELINE_INCONCLUSIVE_OR_INSUFFICIENT_SAMPLE"
    if sample_status != "SUFFICIENT_TRADE_SAMPLE":
        return EconomicClassification.INCONCLUSIVE, "BASELINE_INCONCLUSIVE_OR_INSUFFICIENT_SAMPLE"
    if trade_count == 0:
        return EconomicClassification.INCONCLUSIVE, "BASELINE_INCONCLUSIVE_OR_INSUFFICIENT_SAMPLE"
    if net_return < 0.0:
        return EconomicClassification.FAIL, "BASELINE_TERMINAL_NEGATIVE"
    if net_return > 0.0:
        return EconomicClassification.INCONCLUSIVE, "BASELINE_INCONCLUSIVE_POSITIVE_UNROBUST"
    return EconomicClassification.INCONCLUSIVE, "BASELINE_INCONCLUSIVE_OR_INSUFFICIENT_SAMPLE"


def run_baseline_evaluation(
    *,
    confirm_go_token: str,
    repo_root: Path,
    durable_evidence_root: Path,
    source_closeout_bundle: Path | None = None,
    prior_implementation_digest: str | None = None,
) -> dict[str, Any]:
    if confirm_go_token not in ALLOWED_GO_TOKENS:
        raise SystemExit(f"ERR: invalid_go_token:{confirm_go_token}")

    head = _run_git(["rev-parse", "HEAD"])
    origin_main = _run_git(["rev-parse", "origin/main"])
    worktree_clean = (
        subprocess.check_output(["git", "status", "--porcelain"], cwd=repo_root, text=True).strip()
        == ""
    )

    admissibility = evaluate_ehlers_cycle_filter_v1_admissibility_contract_v1(repo_root=repo_root)
    if admissibility.admissibility_result.value != "PASS":
        raise SystemExit(f"ERR: admissibility_blocked:{admissibility.blocking_reasons}")

    cfg = load_ehlers_cycle_filter_v1_evaluation_config_v1(repo_root, EVAL_CONFIG_PATH)
    binding_cfg = _load_json(repo_root / BINDING_CONFIG_PATH)
    material_diff = _load_json(repo_root / MATERIAL_DIFFERENCE_PATH)
    binding_section = binding_cfg["binding"]
    digest_bindings = binding_section["digest_bindings"]

    eval_binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    dataset_path = Path(str(eval_binding["dataset_path"]))
    manifest_path = dataset_path.parent / "dataset_manifest.json"
    manifest = _load_json(manifest_path)
    descriptor, provenance = ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
        manifest,
        manifest_path=str(manifest_path),
    )
    if descriptor.dataset_digest != digest_bindings["data_digest"]["value"]:
        raise SystemExit("ERR: data_digest_mismatch")

    bars = pd.read_parquet(dataset_path)
    if not isinstance(bars.index, pd.DatetimeIndex):
        if "timestamp" in bars.columns:
            bars = bars.copy()
            bars.index = pd.to_datetime(bars["timestamp"], utc=True)
        elif "time" in bars.columns:
            bars = bars.copy()
            bars.index = pd.to_datetime(bars["time"], utc=True)
        else:
            bars = bars.set_index("timestamp")
    if not isinstance(bars.index, pd.DatetimeIndex):
        raise SystemExit("ERR: bars_index_not_datetime")
    if bars.index.tz is None:
        bars.index = bars.index.tz_localize("UTC")
    bars = bars.sort_index()

    profile_binding = load_profile_binding_from_manifest(manifest)
    wiring = mv2_wiring.run_mv2_research_backtest_wiring_v1(
        bars,
        strategy_id=STRATEGY_ID,
        cfg=cfg,
        instrument_id=str(eval_binding["canonical_instrument_id"]),
        profile_binding=profile_binding,
    )
    backtest = wiring.backtest_result
    initial_cash = float(cfg["backtest"]["initial_cash"])
    stats = backtest.stats
    trade_count = int(stats.get("total_trades", 0))
    net_return = float(stats.get("total_return", 0.0))

    accounting = materialize_legacy_backtest_accounting_reconciliation_v0(
        backtest,
        initial_cash=initial_cash,
    )
    accounting_pass = bool(accounting.get("accounting_reconciliation_pass"))

    policy = default_economic_validity_policy_v1()
    gate = evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=EconomicValidityEvidenceMetricsV1(
            net_expectancy=float(stats.get("expectancy", 0.0)),
            profit_factor=float(stats.get("profit_factor", 0.0)),
            trade_count=trade_count,
            max_drawdown=float(stats.get("max_drawdown", 0.0)),
        ),
        expected_policy_digest=policy.policy_digest(),
    )

    minimum_trade_count = int(policy.minimum_trade_count.value or 50)
    sample_status = _classify_sample(trade_count, minimum_trade_count)
    baseline_class, failure_class = _classify_baseline(
        trade_count=trade_count,
        net_return=net_return,
        accounting_pass=accounting_pass,
        sample_status=sample_status,
    )

    implementation_digest = compute_step29m_ehlers_implementation_digest_v0(repo_root)
    if prior_implementation_digest and prior_implementation_digest == implementation_digest:
        raise SystemExit("ERR: defect_repair_requires_implementation_digest_change")

    config_digest = admissibility.config_digest
    strategy_params_digest = admissibility.strategy_params_digest
    data_period = f"{descriptor.start_time}..{descriptor.end_time}"
    binding_digest = compute_step29m_ehlers_binding_digest_v0(
        config_digest=config_digest,
        data_digest=descriptor.dataset_digest,
        implementation_digest=implementation_digest,
        strategy_params_digest=strategy_params_digest,
        material_difference_digest=str(material_diff["material_difference_digest"]),
        hypothesis_id=str(binding_cfg["hypothesis_id"]),
        instrument_id=str(eval_binding["canonical_instrument_id"]),
        data_period=data_period,
    )

    ts = _utc_slug()
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0_{ts}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)

    trades_path = evidence_dir / "trade_ledger.jsonl"
    if backtest.trades is not None and not backtest.trades.empty:
        with trades_path.open("w", encoding="utf-8") as handle:
            for row in backtest.trades.to_dict(orient="records"):
                handle.write(json.dumps(row, default=str) + "\n")

    (evidence_dir / "accounting_reconciliation.json").write_text(
        json.dumps(accounting, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "sample_sufficiency.json").write_text(
        json.dumps(
            {
                "minimum_trade_count_policy": minimum_trade_count,
                "policy_version": "economic_validity_policy_v1",
                "status": sample_status,
                "trade_count": trade_count,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "immutable_binding_snapshot.json").write_text(
        json.dumps(
            {
                "bar_interval": "1m",
                "binding_digest": binding_digest,
                "binding_immutable": True,
                "config_digest": config_digest,
                "data_digest": descriptor.dataset_digest,
                "data_period": data_period,
                "hypothesis_id": binding_cfg["hypothesis_id"],
                "implementation_digest": implementation_digest,
                "instrument_id": eval_binding["canonical_instrument_id"],
                "material_difference_digest": material_diff["material_difference_digest"],
                "research_scope": "ehlers_cycle_filter/v1",
                "strategy_params_digest": strategy_params_digest,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "performance_metrics.json").write_text(
        json.dumps(
            {
                "net_return": net_return,
                "net_expectancy": float(stats.get("expectancy", 0.0)),
                "profit_factor": float(stats.get("profit_factor", 0.0)),
                "sharpe": float(stats.get("sharpe", 0.0)),
                "max_drawdown": float(stats.get("max_drawdown", 0.0)),
                "trade_count": trade_count,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "evaluation_context.json").write_text(
        json.dumps(
            {
                "accounting_owner": (
                    "src/research/cross_sectional_single_slot_accounting_reconciliation_v0.py"
                ),
                "baseline_runner": str(Path(__file__).relative_to(repo_root)),
                "go_token": confirm_go_token,
                "head": head,
                "head_equals_origin_main": head == origin_main,
                "materialization_owner": (
                    "src/research/step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0.py"
                ),
                "metrics_summary_file": METRICS_SUMMARY_FILENAME,
                "origin_main": origin_main,
                "reevaluation_class": (
                    "DEFECT_REPAIR_REEVALUATION"
                    if confirm_go_token.endswith("REEVALUATION_V0")
                    else "INITIAL_BASELINE"
                ),
                "resilience_metrics_owner": "src/core/metrics.py",
                "source_closeout_bundle": str(source_closeout_bundle or ""),
                "worktree_clean": worktree_clean,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    materialize_resilience_metrics_summary_json_v0(evidence_dir, resilience_metrics)

    final_report = "\n".join(
        [
            f"VERDICT={baseline_class.value}_EHLERS_CYCLE_FILTER_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0",
            f"REPO={repo_root}",
            f"HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"BINDING_DIGEST={binding_digest}",
            f"IMPLEMENTATION_DIGEST={implementation_digest}",
            f"CONFIG_DIGEST={config_digest}",
            f"DATA_DIGEST={descriptor.dataset_digest}",
            f"STRATEGY_PARAMS_DIGEST={strategy_params_digest}",
            f"TRADE_COUNT={trade_count}",
            f"SAMPLE_SUFFICIENCY_STATUS={sample_status}",
            f"ACCOUNTING_RECONCILIATION_PASS={accounting_pass}",
            f"BASELINE_STATUS={baseline_class.value}",
            f"FAILURE_CLASS={failure_class}",
            f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={gate.gates_pass}",
            f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            "WALK_FORWARD_EXECUTED=false",
            "MONTE_CARLO_EXECUTED=false",
            "STRESS_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            "REPO_MUTATION=false",
        ]
    )
    (evidence_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")

    manifest_rc, _ = retention.finalize_durable_bundle_manifest(evidence_dir)
    return {
        "verdict": baseline_class.value,
        "accounting_reconciliation_pass": accounting_pass,
        "sample_sufficiency_status": sample_status,
        "implementation_digest": implementation_digest,
        "config_digest": config_digest,
        "data_digest": descriptor.dataset_digest,
        "strategy_params_digest": strategy_params_digest,
        "binding_digest": binding_digest,
        "manifest_verify_rc": manifest_rc,
        "evidence_dir": str(evidence_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--durable-evidence-root",
        type=Path,
        default=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
    )
    parser.add_argument("--source-closeout-bundle", type=Path, default=None)
    parser.add_argument("--prior-implementation-digest", default=None)
    args = parser.parse_args()
    result = run_baseline_evaluation(
        confirm_go_token=args.confirm_go_token,
        repo_root=args.repo_root,
        durable_evidence_root=args.durable_evidence_root,
        source_closeout_bundle=args.source_closeout_bundle,
        prior_implementation_digest=args.prior_implementation_digest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
