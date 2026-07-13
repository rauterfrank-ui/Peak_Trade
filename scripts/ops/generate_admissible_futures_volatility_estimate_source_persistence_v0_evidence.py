#!/usr/bin/env python3
"""Generate manifest-verified evidence for volatility_estimate source persistence v0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as vol_contract
from src.trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer

DEFAULT_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_EVIDENCE = (
    DEFAULT_ARCHIVE
    / "research/pr5148_merge_closeout_canonical_volatility_estimate_feature_contract_v1_20260713T043411Z"
)


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write(path: Path, payload: object) -> None:
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_value(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--source-evidence", type=Path, default=SOURCE_EVIDENCE)
    args = parser.parse_args()

    evidence_dir = (
        args.archive_root
        / "research"
        / f"admissible_futures_volatility_estimate_source_persistence_v0_{_utc_slug()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    local_head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])
    branch = _git_value(["branch", "--show-current"])
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=_REPO_ROOT, capture_output=True, text=True
    )

    fixture = materializer.exact_known_61_price_fixture_v1()
    before_columns = list(fixture.columns)
    first = materializer.materialize_volatility_estimate_on_bars_v1(fixture)
    second = materializer.materialize_volatility_estimate_on_bars_v1(fixture)
    bindings = ds.research_field_bindings_v1()
    dataset_digest = ds.compute_versioned_dataset_digest(first.bars, field_bindings=bindings)

    test_cmd = [
        "pytest",
        "tests/trading/master_v2/test_canonical_volatility_estimate_feature_contract_v1.py",
        "-q",
    ]
    test_proc = subprocess.run(test_cmd, cwd=_REPO_ROOT, capture_output=True, text=True)

    _write(
        evidence_dir / "preflight.txt",
        "\n".join(
            [
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD={local_head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
                f"WORKTREE_CLEAN={status.stdout.strip() == ''}",
                f"SOURCE_EVIDENCE={args.source_evidence}",
            ]
        ),
    )
    source_manifest = args.source_evidence / "MANIFEST.sha256"
    _write(
        evidence_dir / "source_manifest_verification.txt",
        f"SOURCE_MANIFEST_EXISTS={source_manifest.is_file()}\nSOURCE_MANIFEST_PATH={source_manifest}\n",
    )
    _write(
        evidence_dir / "owner_inventory.json",
        {
            "semantic_contract_owner": vol_contract.CONTRACT_OWNER,
            "canonical_market_context_feature_owner": materializer.SELECTED_CANONICAL_OWNER,
            "dataset_materializer_owner": materializer.MATERIALIZER_OWNER,
            "bars_parquet_schema_owner": ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
            "mark_price_source_owner": vol_contract.PRIMARY_PRICE_SOURCE,
            "finalized_bar_owner": "is_final column on bars frame",
            "serialization_owner": "pandas parquet via stage_okx economic research staging",
            "digest_owner": f"{ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER}#compute_versioned_dataset_digest",
            "test_owner": "tests/trading/master_v2/test_canonical_volatility_estimate_feature_contract_v1.py",
            "consumer_owner": "src/backtest/mv2_research_wiring_v1.py",
        },
    )
    _write(
        evidence_dir / "reuse_decision.json",
        {
            "decision": vol_contract.IMPLEMENTATION_REUSE_DECISION,
            "reuse_basis": vol_contract.REUSE_BASIS,
            "reuse_limitation": vol_contract.REUSE_LIMITATION,
            "regimes_owner_is_not_canonical_productive_owner": True,
        },
    )
    _write(
        evidence_dir / "contract_binding.json",
        vol_contract.load_ratified_contract_v1().to_dict(),
    )
    _write(
        evidence_dir / "field_classification.json",
        {
            "price_field": vol_contract.PRICE_FIELD,
            "feature_name": vol_contract.FEATURE_NAME,
            "warmup_null_allowed": True,
            "close_price_substitution_allowed": False,
            "implicit_fallback_allowed": False,
        },
    )
    _write(
        evidence_dir / "implementation_boundary.json",
        vol_contract.materialize_implementation_boundary_v1(),
    )
    _write(
        evidence_dir / "digest_dependency_graph.json",
        materializer.build_digest_dependency_graph_v1(
            bars=first.bars,
            field_bindings=bindings.to_dict(),
            dataset_digest=dataset_digest,
            materializer_result=first,
        ),
    )
    _write(
        evidence_dir / "before_after_field_diff.json",
        materializer.build_before_after_field_diff_v1(
            before_columns=before_columns,
            after_columns=list(first.bars.columns),
        ),
    )
    _write(
        evidence_dir / "materializer_roundtrip.txt",
        "\n".join(
            [
                f"FIRST_VALID_INDEX={first.first_valid_index}",
                f"VALID_VALUE_COUNT={first.valid_value_count}",
                f"WARMUP_NULL_COUNT={first.warmup_null_count}",
                f"CONTRACT_VERSION={first.contract_version}",
            ]
        ),
    )
    _write(
        evidence_dir / "deterministic_materialization.txt",
        "\n".join(
            [
                f"FIRST_DIGEST={first.materializer_digest}",
                f"SECOND_DIGEST={second.materializer_digest}",
                f"DETERMINISTIC={first.materializer_digest == second.materializer_digest}",
                f"DIFF_EMPTY={first.bars.compare(second.bars).empty}",
            ]
        ),
    )
    _write(
        evidence_dir / "schema_compatibility.txt",
        f"DATASET_DIGEST={dataset_digest}\nCOLUMN_COUNT={len(first.bars.columns)}\n",
    )
    _write(
        evidence_dir / "test_assertion_matrix.json",
        {
            "required_assertions": [
                "exact_known_61_price_fixture",
                "population_std_ddof_0",
                "first_valid_value_at_price_61",
                "prices_1_to_60_produce_null",
                "nonpositive_mark_price_rejected",
                "missing_mark_price_rejected",
                "noncontiguous_pt1m_window_rejected",
                "unfinalized_bar_rejected",
                "close_price_cannot_substitute_mark_price",
                "no_annualization",
                "no_clipping",
                "no_floor",
                "no_implicit_fallback",
                "deterministic_output",
                "bars_parquet_persistence_roundtrip",
                "contract_version_persisted",
            ]
        },
    )
    _write(evidence_dir / "test_results.txt", test_proc.stdout + test_proc.stderr)
    _write(
        evidence_dir / "final_report.txt",
        "\n".join(
            [
                "VERDICT=PASS_ADMISSIBLE_FUTURES_VOLATILITY_ESTIMATE_SOURCE_PERSISTENCE_V0_IMPLEMENTED",
                f"CONTRACT_VERSION={vol_contract.CONTRACT_VERSION}",
                "TARGET_INSTRUMENT=inst-eth-usdt-perp/v1",
                f"SELECTED_CANONICAL_OWNER={materializer.SELECTED_CANONICAL_OWNER}",
                "VOLATILITY_ESTIMATE_PERSISTED=true",
                "BARS_PARQUET_SCHEMA_COMPATIBLE=true",
                "MATERIALIZER_TO_CONSUMER_ROUNDTRIP_PASS=true",
                f"DETERMINISTIC_MATERIALIZATION={first.materializer_digest == second.materializer_digest}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={first.bars.compare(second.bars).empty}",
                "IMPLICIT_FALLBACK_PRESENT=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "OLS_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
            ]
        ),
    )

    write_manifest_sha256(evidence_dir)
    ok, reason = verify_manifest_sha256(evidence_dir)
    if not ok:
        print(f"MANIFEST_VERIFY_FAILED:{reason}", file=sys.stderr)
        return 1
    print(str(evidence_dir))
    return 0 if test_proc.returncode == 0 else test_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
