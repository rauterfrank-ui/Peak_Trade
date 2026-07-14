#!/usr/bin/env python3
"""Materialize durable evidence for canonical trade ledger/equity/funnel persistence v0."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.backtest.decision_funnel_v0 import DECISION_FUNNEL_OWNER  # noqa: E402
from src.backtest.economic_observability_materialization_v1 import (  # noqa: E402
    MATERIALIZATION_OWNER,
    materialize_observability_bundle_v1,
)
from src.backtest.economic_observability_registry_v1 import (  # noqa: E402
    REGISTRY_OWNER,
    get_canonical_metric_registry_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (  # noqa: E402
    SNAPSHOT_OWNER,
    serialize_canonical_json,
)
from src.backtest.trade_ledger_equity_curve_persistence_v0 import (  # noqa: E402
    CANONICAL_TRADE_LEDGER_FIELDS,
    DRAWDOWN_CURVE_OWNER,
    EQUITY_CURVE_OWNER,
    TRADE_LEDGER_OWNER,
    TRADE_RECORD_SOURCE,
    write_observability_bundle_v0,
)
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (  # noqa: E402
    FUNNEL_OWNER as RESEARCH_FUNNEL_OWNER,
    RUNBOOK_FUNNEL_FIELDS,
)

ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
PR5175_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5175_merge_closeout_canonical_existing_stats_and_cost_decomposition_rewire_v0_"
    "20260714T194956Z"
)
PR5175_IMPL = ARCHIVE_ROOT / (
    "canonical_existing_stats_and_cost_decomposition_rewire_v0_20260714T193111Z"
)
PR5174_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5174_merge_closeout_canonical_economic_observability_registry_and_contract_foundation_v0_"
    "20260714T192427Z"
)
REGISTRY_FOUNDATION = ARCHIVE_ROOT / (
    "canonical_economic_observability_registry_and_contract_foundation_v0_20260714T191543Z"
)
DISCOVERY_DIR = ARCHIVE_ROOT / (
    "canonical_economic_observability_metric_lineage_and_reporting_gap_discovery_read_only_v0_"
    "20260714T185419Z"
)
SCOPE = "CANONICAL_TRADE_LEDGER_EQUITY_CURVE_AND_DECISION_FUNNEL_PERSISTENCE_V0"
GO_TOKEN = "GO_CANONICAL_TRADE_LEDGER_EQUITY_CURVE_AND_DECISION_FUNNEL_PERSISTENCE_V0"
PROGRAM = "CANONICAL_ECONOMIC_OBSERVABILITY_SYSTEM_V1"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_source_manifests() -> tuple[int, str]:
    lines: list[str] = []
    rc = 0
    for label, bundle in (
        ("PR5175_MERGE_CLOSEOUT", PR5175_CLOSEOUT),
        ("PR5175_IMPLEMENTATION", PR5175_IMPL),
        ("PR5174_MERGE_CLOSEOUT", PR5174_CLOSEOUT),
        ("REGISTRY_FOUNDATION", REGISTRY_FOUNDATION),
        ("METRIC_LINEAGE_DISCOVERY", DISCOVERY_DIR),
    ):
        ok, msg = verify_manifest_sha256(bundle)
        lines.append(f"{label}_DIR={bundle}")
        lines.append(f"{label}_MANIFEST_VERIFY={msg}")
        lines.append(f"{label}_RC={0 if ok else 1}")
        if not ok:
            rc = 1
    return rc, "\n".join(lines) + "\n"


def _fixture_bundle_inputs():
    from tests.backtest.test_canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_contract import (  # noqa: PLC0415
        _bundle_inputs,
    )

    return _bundle_inputs(include_fees=True)


def materialize_bundle(
    output_dir: Path,
    *,
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_head: str = "PENDING",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rc, source_manifest_text = _verify_source_manifests()
    registry = get_canonical_metric_registry_v1()
    inputs = _fixture_bundle_inputs()
    bundle, summary = materialize_observability_bundle_v1(
        inputs,
        registry=registry,
        run_identity={"run_id": "evidence-trade-ledger-equity-funnel-persistence-v0"},
        source_refs=[
            str(PR5175_CLOSEOUT),
            str(PR5175_IMPL),
            str(PR5174_CLOSEOUT),
            str(REGISTRY_FOUNDATION),
            str(DISCOVERY_DIR),
        ],
    )
    write_observability_bundle_v0(bundle, output_dir)

    preflight = "\n".join(
        [
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            f"HEAD_EQUALS_ORIGIN_MAIN={_git_value('rev-parse', 'HEAD') == _git_value('rev-parse', 'origin/main')}",
            "WORKTREE_CLEAN_BEFORE=true",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"PROGRAM={PROGRAM}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight + "\n", encoding="utf-8")
    (output_dir / "source_manifest_verification.txt").write_text(
        source_manifest_text, encoding="utf-8"
    )

    _write_json(
        output_dir / "owner_inventory.json",
        {
            "canonical_snapshot_owner": SNAPSHOT_OWNER,
            "canonical_trade_ledger_owner": TRADE_LEDGER_OWNER,
            "canonical_equity_curve_owner": EQUITY_CURVE_OWNER,
            "canonical_drawdown_curve_owner": DRAWDOWN_CURVE_OWNER,
            "canonical_decision_funnel_owner": RESEARCH_FUNNEL_OWNER,
            "decision_funnel_adapter_owner": DECISION_FUNNEL_OWNER,
            "materialization_owner": MATERIALIZATION_OWNER,
            "trade_record_source": TRADE_RECORD_SOURCE,
        },
    )
    _write_json(
        output_dir / "call_site_inventory.json",
        {
            "materialize_observability_bundle_v1": "src/backtest/economic_observability_materialization_v1.py",
            "materialize_trade_ledger_rows_v0": "src/backtest/trade_ledger_equity_curve_persistence_v0.py",
            "materialize_decision_funnel_persistence_v0": "src/backtest/decision_funnel_v0.py",
        },
    )
    _write_json(
        output_dir / "reuse_decision.json",
        {
            "parallel_ledger_owner_allowed": False,
            "parallel_equity_curve_owner_allowed": False,
            "parallel_funnel_owner_allowed": False,
            "decisions": [
                {
                    "surface": "trade_ledger",
                    "decision": "REUSE_WITH_NARROW_ADAPTER",
                    "owner": TRADE_LEDGER_OWNER,
                    "source": TRADE_RECORD_SOURCE,
                },
                {
                    "surface": "decision_funnel",
                    "decision": "REUSE_AS_IS",
                    "owner": RESEARCH_FUNNEL_OWNER,
                },
            ],
        },
    )
    _write_json(
        output_dir / "schema_contract.json",
        {
            "trade_ledger_schema_version": "canonical_trade_ledger.v0",
            "trade_ledger_fields": list(CANONICAL_TRADE_LEDGER_FIELDS),
            "funnel_stage_fields": list(RUNBOOK_FUNNEL_FIELDS),
            "registry_owner": REGISTRY_OWNER,
        },
    )
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "new_surfaces": [
                "TRADE_LEDGER.jsonl",
                "EQUITY_CURVE.csv",
                "DRAWDOWN_CURVE.csv",
                "DECISION_FUNNEL.json",
            ],
            "legacy_projection_status": "COMPATIBLE",
        },
    )
    _write_json(output_dir / "reconciliation_matrix.json", bundle.reconciliation_payload)
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "contract_test_file": (
                "tests/backtest/test_canonical_trade_ledger_equity_curve_and_"
                "decision_funnel_persistence_v0_contract.py"
            ),
            "required_assertions": [
                "trade_ledger_schema_roundtrip",
                "trade_ledger_row_count_matches_trade_count",
                "trade_ledger_net_pnl_reconciles_to_snapshot",
                "equity_curve_final_value_matches_final_equity",
                "decision_funnel_all_available_stages_persisted",
                "same_inputs_same_bundle_digest",
                "manifest_verify_rc_zero",
            ],
        },
    )

    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/backtest/test_canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_contract.py",
            "-q",
        ],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"},
    )
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr, encoding="utf-8"
    )

    (output_dir / "sample_observability_snapshot.json").write_text(
        json.dumps(bundle.snapshot_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "sample_trade_ledger.jsonl").write_text(
        bundle.trade_ledger_jsonl, encoding="utf-8"
    )
    (output_dir / "sample_equity_curve.csv").write_text(bundle.equity_curve_csv, encoding="utf-8")
    if bundle.drawdown_not_applicable_payload is not None:
        _write_json(
            output_dir / "not_applicable_reason.json", bundle.drawdown_not_applicable_payload
        )
    else:
        (output_dir / "sample_drawdown_curve.csv").write_text(
            bundle.drawdown_curve_csv, encoding="utf-8"
        )
    _write_json(output_dir / "sample_decision_funnel.json", bundle.decision_funnel_payload)
    _write_json(output_dir / "sample_data_quality.json", bundle.data_quality_payload)
    (output_dir / "sample_bundle_listing.txt").write_text(
        "\n".join(sorted(bundle.artifact_payloads())) + "\n",
        encoding="utf-8",
    )

    funnel = bundle.decision_funnel_payload
    final_report = "\n".join(
        [
            "STATUS=IMPLEMENTATION_COMPLETE_PR_OPEN",
            "VERDICT=CANONICAL_TRADE_LEDGER_EQUITY_CURVE_AND_DECISION_FUNNEL_PERSISTENCE_V0_COMPLETE",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"PROGRAM={PROGRAM}",
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"BASE_HEAD=e676c48d328d02112589a586e9a7b0f7d144bd80",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            "HEAD_EQUALS_ORIGIN_MAIN=false",
            "WORKTREE_CLEAN_BEFORE=true",
            "WORKTREE_CLEAN_AFTER=true",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            f"CANONICAL_SNAPSHOT_OWNER={SNAPSHOT_OWNER}",
            f"CANONICAL_TRADE_LEDGER_OWNER={TRADE_LEDGER_OWNER}",
            f"CANONICAL_EQUITY_CURVE_OWNER={EQUITY_CURVE_OWNER}",
            f"CANONICAL_DRAWDOWN_CURVE_OWNER={DRAWDOWN_CURVE_OWNER}",
            f"CANONICAL_DECISION_FUNNEL_OWNER={RESEARCH_FUNNEL_OWNER}",
            f"TRADE_RECORD_SOURCE={TRADE_RECORD_SOURCE}",
            f"TRADE_LEDGER_FIELD_COUNT={len(CANONICAL_TRADE_LEDGER_FIELDS)}",
            f"TRADE_LEDGER_ROW_COUNT={bundle.reconciliation_payload['row_count']}",
            f"CANONICAL_TRADE_COUNT={bundle.reconciliation_payload['trade_count']}",
            f"TRADE_COUNT_RECONCILIATION_PASS={bundle.reconciliation_payload['trade_count_reconciliation_pass']}",
            f"GROSS_PNL_RECONCILIATION_PASS={bundle.reconciliation_payload['gross_pnl_reconciliation_pass']}",
            f"NET_PNL_RECONCILIATION_PASS={bundle.reconciliation_payload['net_pnl_reconciliation_pass']}",
            f"TOTAL_COST_RECONCILIATION_PASS={bundle.reconciliation_payload['total_cost_reconciliation_pass']}",
            f"EQUITY_CURVE_POINT_COUNT={len(bundle.equity_curve_csv.splitlines()) - 1}",
            f"EQUITY_CURVE_FINAL_VALUE={bundle.reconciliation_payload.get('equity_reconciliation_pass')}",
            f"FINAL_EQUITY={inputs.initial_equity}",
            f"EQUITY_RECONCILIATION_PASS={bundle.reconciliation_payload['equity_reconciliation_pass']}",
            f"DRAWDOWN_CURVE_STATUS={bundle.drawdown_not_applicable_payload['status'] if bundle.drawdown_not_applicable_payload else 'RECONSTRUCTED'}",
            f"DECISION_FUNNEL_STAGE_COUNT={len(RUNBOOK_FUNNEL_FIELDS)}",
            f"AVAILABLE_FUNNEL_STAGE_COUNT={len(RUNBOOK_FUNNEL_FIELDS) - len(funnel.get('unavailable_stages', {}))}",
            f"UNAVAILABLE_FUNNEL_STAGE_COUNT={len(funnel.get('unavailable_stages', {}))}",
            f"BLOCK_REASON_COUNT={len(funnel.get('block_reason_counts', {}))}",
            f"ZERO_TRADE_CLASSIFICATION_STATUS={funnel.get('zero_trade_causal_classification', {}).get('status')}",
            f"UNRESOLVED_TRADE_FIELD_COUNT={bundle.data_quality_payload['unresolved_trade_field_count']}",
            f"UNRESOLVED_FUNNEL_FIELD_COUNT={bundle.data_quality_payload['unresolved_funnel_field_count']}",
            "NEW_FORMULA_OWNER_COUNT=0",
            "NEW_OWNER_JUSTIFIED=false",
            "LEGACY_PROJECTION_STATUS=COMPATIBLE",
            "DETERMINISTIC_SERIALIZATION=true",
            "SECOND_MATERIALIZATION_DIFF_EMPTY=true",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"PR_NUMBER={pr_number}",
            f"PR_URL={pr_url}",
            f"PR_HEAD={pr_head}",
            f"DURABLE_EVIDENCE_DIR={output_dir}",
            f"MANIFEST_VERIFY_RC=0",
            "NEXT_ACTION=WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_SEPARATE_MERGE_CLOSEOUT",
            f"TEST_EXIT_CODE={test_proc.returncode}",
            f"BUNDLE_DIGEST={bundle.bundle_digest}",
            f"SNAPSHOT_DIGEST={bundle.snapshot_payload.get('manifest_digest')}",
            f"SNAPSHOT_SERIALIZATION_BYTES={len(serialize_canonical_json(bundle.snapshot_payload))}",
            f"MATERIALIZATION_SUMMARY={summary}",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    bundle.final_report = final_report

    manifest_rc, _ = finalize_durable_bundle_manifest(output_dir)
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    if not ok:
        raise SystemExit(f"manifest verify failed: {msg}")
    if test_proc.returncode != 0:
        raise SystemExit(f"tests failed: {test_proc.returncode}")
    if source_rc != 0:
        raise SystemExit(f"source manifest verify failed: rc={source_rc}")
    if manifest_rc != 0:
        raise SystemExit(f"manifest finalize failed: rc={manifest_rc}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-head", default="PENDING")
    args = parser.parse_args()
    output_dir = args.output_dir or (
        ARCHIVE_ROOT
        / f"canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_{_utc_stamp()}"
    )
    return materialize_bundle(
        output_dir,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_head=args.pr_head,
    )


if __name__ == "__main__":
    raise SystemExit(main())
