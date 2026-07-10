#!/usr/bin/env python3
"""Bound offline economic baseline evaluation runner for bouchaud OHLCV proxy v1.

Offline-only. Validates ratified scope and digests; supports admissibility validation
without executing economic evaluation. Full baseline path reserved for separately
authorized evaluation GO. No runtime, credentials, orders, or authority effect.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

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
from src.backtest.step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 import (  # noqa: E402
    EVALUATION_GO_TOKEN,
    evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1,
    load_bouchaud_microstructure_ohlcv_proxy_v1_evaluation_config_v1,
)
from src.core.metrics import metrics as resilience_metrics  # noqa: E402
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    BLOCKED_EVALUATION_DIR,
    DATA_PERIOD,
    DATASET_DIGEST,
    INSTRUMENT_ID,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    PR5097_CLOSEOUT_DIR,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    verify_manifest_sha256,
)
from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (  # noqa: E402
    compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0,
    compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0,
)

ALLOWED_GO_TOKENS = frozenset({EVALUATION_GO_TOKEN})
STRATEGY_ID = "bouchaud_microstructure"
EVAL_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_bouchaud_microstructure_ohlcv_proxy_v1_"
    "economic_evaluation_v1.json"
)
BINDING_CONFIG_PATH = VERSIONED_BINDING_CONFIG_REL_PATH
MATERIAL_DIFFERENCE_PATH = MATERIAL_DIFFERENCE_CONFIG_REL_PATH
SCOPE_RATIFICATION_PATH = SCOPE_RATIFICATION_CONFIG_REL_PATH

FORBIDDEN_RUNTIME_ENVIRONMENTS = frozenset(
    {"runtime", "scheduler", "shadow", "paper", "testnet", "canary", "live"}
)
FORBIDDEN_RUNTIME_ENV_KEYS = (
    "PEAK_TRADE_RUNTIME_MODE",
    "PEAK_TRADE_RUNTIME_ENVIRONMENT",
    "RUNTIME_ENVIRONMENT",
)

CANONICAL_ENTRY_POINT = "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"


class RunnerVerdict(str, Enum):
    ADMISSIBILITY_PASS = "ADMISSIBILITY_PASS"
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_git(args: list[str], repo_root: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def enforce_offline_boundaries_v0(env: Mapping[str, str] | None = None) -> None:
    mapping = os.environ if env is None else env
    for key in FORBIDDEN_RUNTIME_ENV_KEYS:
        value = mapping.get(key, "").strip().lower()
        if value in FORBIDDEN_RUNTIME_ENVIRONMENTS:
            raise SystemExit(f"ERR: forbidden_runtime_environment:{key}={value}")


def verify_source_evidence_manifests_v0() -> None:
    for bundle in (PR5097_CLOSEOUT_DIR, BLOCKED_EVALUATION_DIR):
        verification = verify_manifest_sha256(bundle)
        if verification.manifest_verify_rc != 0:
            raise SystemExit(f"ERR: source_manifest_verification_failed:{bundle}")


def verify_scope_ratification_invariants_v0(
    scope_ratification: Mapping[str, Any],
) -> None:
    required_true = (
        ("offline_economic_evaluation_scope_ratified", True),
        ("offline_only", True),
        ("proxy_semantics", True),
        ("single_instrument_only", True),
        ("evaluation_infrastructure_ready", True),
    )
    required_false = (
        ("economic_evaluation_executed", False),
        ("economic_evaluation_authorized", False),
        ("evaluation_execution_authorized", False),
        ("true_tick_l2_microstructure", False),
        ("trading_logic_mutated", False),
    )
    for key, expected in required_true:
        if scope_ratification.get(key) is not expected:
            raise SystemExit(f"ERR: scope_ratification_invariant_failed:{key}")
    for key, expected in required_false:
        if scope_ratification.get(key) is not expected:
            raise SystemExit(f"ERR: scope_ratification_invariant_failed:{key}")
    if scope_ratification.get("instrument_id") != INSTRUMENT_ID:
        raise SystemExit("ERR: instrument_id_mismatch")
    if scope_ratification.get("data_period") != DATA_PERIOD:
        raise SystemExit("ERR: data_period_mismatch")
    if scope_ratification.get("data_digest") != DATASET_DIGEST:
        raise SystemExit("ERR: data_digest_mismatch")
    if scope_ratification.get("go_token") != EVALUATION_GO_TOKEN:
        raise SystemExit("ERR: scope_ratification_go_token_mismatch")


def verify_binding_identities_v0(
    *,
    repo_root: Path,
    scope_ratification: Mapping[str, Any],
    binding_cfg: Mapping[str, Any],
    material_diff: Mapping[str, Any],
    admissibility: Any,
) -> tuple[str, str]:
    digest_bindings = binding_cfg["binding"]["digest_bindings"]
    config_digest = admissibility.config_digest
    strategy_params_digest = admissibility.strategy_params_digest
    implementation_digest = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(repo_root)
    binding_digest = compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
        config_digest=config_digest,
        data_digest=DATASET_DIGEST,
        implementation_digest=implementation_digest,
        strategy_params_digest=strategy_params_digest,
        material_difference_digest=str(material_diff["material_difference_digest"]),
        hypothesis_id=str(binding_cfg["hypothesis_id"]),
        instrument_id=INSTRUMENT_ID,
        data_period=DATA_PERIOD,
    )

    ratified_config = str(scope_ratification.get("config_digest", ""))
    ratified_impl = str(scope_ratification.get("implementation_digest", ""))
    ratified_binding = str(scope_ratification.get("binding_digest", ""))

    if ratified_config and config_digest != ratified_config:
        raise SystemExit(
            f"ERR: config_digest_mismatch:computed={config_digest}:ratified={ratified_config}"
        )
    if ratified_impl and implementation_digest != ratified_impl:
        raise SystemExit(
            f"ERR: implementation_digest_mismatch:computed={implementation_digest}:ratified={ratified_impl}"
        )
    if ratified_binding and binding_digest != ratified_binding:
        raise SystemExit(
            f"ERR: binding_digest_mismatch:computed={binding_digest}:ratified={ratified_binding}"
        )
    if digest_bindings["config_digest"]["value"] != config_digest:
        raise SystemExit("ERR: versioned_binding_config_digest_mismatch")
    if digest_bindings["implementation_digest"]["value"] != implementation_digest:
        raise SystemExit("ERR: versioned_binding_implementation_digest_mismatch")
    if (
        str(binding_cfg.get("binding_digest", ""))
        and binding_cfg["binding_digest"] != binding_digest
    ):
        raise SystemExit("ERR: versioned_binding_digest_mismatch")
    return implementation_digest, binding_digest


def run_admissibility_validation_v0(
    *,
    confirm_go_token: str,
    repo_root: Path,
) -> dict[str, Any]:
    if confirm_go_token not in ALLOWED_GO_TOKENS:
        raise SystemExit(f"ERR: invalid_go_token:{confirm_go_token}")

    enforce_offline_boundaries_v0()
    verify_source_evidence_manifests_v0()

    scope_ratification = _load_json(repo_root / SCOPE_RATIFICATION_PATH)
    verify_scope_ratification_invariants_v0(scope_ratification)

    binding_cfg = _load_json(repo_root / BINDING_CONFIG_PATH)
    material_diff = _load_json(repo_root / MATERIAL_DIFFERENCE_PATH)

    admissibility = evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=repo_root,
    )
    if admissibility.admissibility_result.value != "PASS":
        raise SystemExit(f"ERR: admissibility_blocked:{admissibility.blocking_reasons}")

    cfg = load_bouchaud_microstructure_ohlcv_proxy_v1_evaluation_config_v1(
        repo_root, EVAL_CONFIG_PATH
    )
    eval_binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    dataset_path = Path(str(eval_binding["dataset_path"]))
    manifest_path = dataset_path.parent / "dataset_manifest.json"
    manifest = _load_json(manifest_path)
    descriptor, _ = ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
        manifest,
        manifest_path=str(manifest_path),
    )
    if descriptor.dataset_digest != DATASET_DIGEST:
        raise SystemExit("ERR: dataset_identity_digest_mismatch")
    if str(eval_binding["canonical_instrument_id"]) != INSTRUMENT_ID:
        raise SystemExit("ERR: instrument_binding_mismatch")

    implementation_digest, binding_digest = verify_binding_identities_v0(
        repo_root=repo_root,
        scope_ratification=scope_ratification,
        binding_cfg=binding_cfg,
        material_diff=material_diff,
        admissibility=admissibility,
    )

    return {
        "verdict": RunnerVerdict.ADMISSIBILITY_PASS.value,
        "canonical_entry_point": CANONICAL_ENTRY_POINT,
        "config_digest": admissibility.config_digest,
        "implementation_digest": implementation_digest,
        "binding_digest": binding_digest,
        "data_digest": descriptor.dataset_digest,
        "strategy_params_digest": admissibility.strategy_params_digest,
        "economic_evaluation_executed": False,
        "evaluation_execution_count": 0,
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
        "research_scope": scope_ratification["research_scope"],
        "instrument_id": INSTRUMENT_ID,
        "data_period": DATA_PERIOD,
    }


def run_baseline_evaluation(
    *,
    confirm_go_token: str,
    repo_root: Path,
    durable_evidence_root: Path,
    admissibility_validation_only: bool = False,
    source_closeout_bundle: Path | None = None,
    prior_implementation_digest: str | None = None,
) -> dict[str, Any]:
    if admissibility_validation_only:
        return run_admissibility_validation_v0(
            confirm_go_token=confirm_go_token,
            repo_root=repo_root,
        )

    import pandas as pd

    from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (  # noqa: E402
        materialize_legacy_backtest_accounting_reconciliation_v0,
        materialize_resilience_metrics_summary_json_v0,
        METRICS_SUMMARY_FILENAME,
    )

    if confirm_go_token not in ALLOWED_GO_TOKENS:
        raise SystemExit(f"ERR: invalid_go_token:{confirm_go_token}")

    enforce_offline_boundaries_v0()
    verify_source_evidence_manifests_v0()

    head = _run_git(["rev-parse", "HEAD"], repo_root)
    origin_main = _run_git(["rev-parse", "origin/main"], repo_root)

    admissibility = evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=repo_root,
    )
    if admissibility.admissibility_result.value != "PASS":
        raise SystemExit(f"ERR: admissibility_blocked:{admissibility.blocking_reasons}")

    scope_ratification = _load_json(repo_root / SCOPE_RATIFICATION_PATH)
    verify_scope_ratification_invariants_v0(scope_ratification)

    cfg = load_bouchaud_microstructure_ohlcv_proxy_v1_evaluation_config_v1(
        repo_root, EVAL_CONFIG_PATH
    )
    binding_cfg = _load_json(repo_root / BINDING_CONFIG_PATH)
    material_diff = _load_json(repo_root / MATERIAL_DIFFERENCE_PATH)
    digest_bindings = binding_cfg["binding"]["digest_bindings"]

    eval_binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    dataset_path = Path(str(eval_binding["dataset_path"]))
    manifest_path = dataset_path.parent / "dataset_manifest.json"
    manifest = _load_json(manifest_path)
    descriptor, _ = ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
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
    canonical_metrics = mv2_wiring.compute_mv2_backtest_metrics_v1(backtest)
    net_expectancy = float(canonical_metrics.get("expectancy", 0.0))

    accounting = materialize_legacy_backtest_accounting_reconciliation_v0(
        backtest,
        initial_cash=initial_cash,
    )
    accounting_pass = bool(accounting.get("accounting_reconciliation_pass"))

    policy = default_economic_validity_policy_v1()
    gate = evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=EconomicValidityEvidenceMetricsV1(
            net_expectancy=net_expectancy,
            profit_factor=float(stats.get("profit_factor", 0.0)),
            trade_count=trade_count,
            max_drawdown=float(stats.get("max_drawdown", 0.0)),
        ),
        expected_policy_digest=policy.policy_digest(),
    )

    implementation_digest, binding_digest = verify_binding_identities_v0(
        repo_root=repo_root,
        scope_ratification=scope_ratification,
        binding_cfg=binding_cfg,
        material_diff=material_diff,
        admissibility=admissibility,
    )
    if prior_implementation_digest and prior_implementation_digest == implementation_digest:
        raise SystemExit("ERR: defect_repair_requires_implementation_digest_change")

    ts = _utc_slug()
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0_{ts}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=False)

    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                "VERDICT=BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0",
                f"BINDING_DIGEST={binding_digest}",
                f"IMPLEMENTATION_DIGEST={implementation_digest}",
                f"TRADE_COUNT={trade_count}",
                f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={gate.gates_pass}",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    materialize_resilience_metrics_summary_json_v0(evidence_dir, resilience_metrics)
    manifest_rc, _ = retention.finalize_durable_bundle_manifest(evidence_dir)

    return {
        "verdict": "EVALUATION_COMPLETE",
        "accounting_reconciliation_pass": accounting_pass,
        "implementation_digest": implementation_digest,
        "binding_digest": binding_digest,
        "manifest_verify_rc": manifest_rc,
        "evidence_dir": str(evidence_dir),
        "economic_evaluation_executed": True,
        "trade_count": trade_count,
        "net_return": net_return,
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
    parser.add_argument("--admissibility-validation-only", action="store_true")
    parser.add_argument("--source-closeout-bundle", type=Path, default=None)
    parser.add_argument("--prior-implementation-digest", default=None)
    args = parser.parse_args()

    operator_go = args.confirm_go_token
    result = run_baseline_evaluation(
        confirm_go_token=operator_go,
        repo_root=args.repo_root,
        durable_evidence_root=args.durable_evidence_root,
        admissibility_validation_only=args.admissibility_validation_only,
        source_closeout_bundle=args.source_closeout_bundle,
        prior_implementation_digest=args.prior_implementation_digest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
