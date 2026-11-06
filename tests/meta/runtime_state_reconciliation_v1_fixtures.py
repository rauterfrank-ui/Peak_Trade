"""Fixtures for runtime_state_reconciliation_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.runtime_state_reconciliation_v1 import (
    RuntimeStateReconciliationInputs,
    default_runtime_reconciliation_request,
    produce_runtime_state_reconciliation_v1,
    verify_trading_logic_semantic_diff_evidence_bundle,
)
from tests.meta.trading_logic_semantic_diff_evidence_v1_fixtures import (
    produce_trading_logic_semantic_diff_evidence_fixture,
)


@dataclass(frozen=True)
class RuntimeStateReconciliationFixtureBundle:
    trading_logic_semantic_diff_evidence_bundle_dir: Path
    runtime_state_reconciliation_bundle_dir: Path | None = None


def produce_runtime_state_reconciliation_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    valid_from: str = "2026-06-29T00:00:00+00:00",
    valid_until: str = "2026-06-30T00:00:00+00:00",
    revocation_state: str = "NOT_REVOKED",
    produce_output: bool = True,
    semantic_diff_name: str = "trading_logic_semantic_diff_evidence",
    reconciliation_name: str = "runtime_state_reconciliation",
    declared_reconciliation_state: str = "CLEAN",
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    correlation_id: str = "offline-runtime-reconciliation-correlation-001",
) -> RuntimeStateReconciliationFixtureBundle:
    semantic_diff_fixture = produce_trading_logic_semantic_diff_evidence_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
        produce_output=True,
        semantic_diff_name=semantic_diff_name,
        instrument_type=instrument_type,
        instrument=instrument,
    )
    assert semantic_diff_fixture.trading_logic_semantic_diff_evidence_bundle_dir is not None

    semantic_diff = verify_trading_logic_semantic_diff_evidence_bundle(
        semantic_diff_fixture.trading_logic_semantic_diff_evidence_bundle_dir
    )
    request = default_runtime_reconciliation_request(
        semantic_diff=semantic_diff,
        declared_reconciliation_state=declared_reconciliation_state,
        instrument_type=instrument_type,
        correlation_id=correlation_id,
    )

    reconciliation_dir: Path | None = None
    if produce_output:
        reconciliation_dir = durable_root / reconciliation_name
        produce_runtime_state_reconciliation_v1(
            inputs=RuntimeStateReconciliationInputs(
                trading_logic_semantic_diff_evidence_bundle_dir=(
                    semantic_diff_fixture.trading_logic_semantic_diff_evidence_bundle_dir
                ),
                reconciliation_request=request,
            ),
            output_dir=reconciliation_dir,
        )

    return RuntimeStateReconciliationFixtureBundle(
        trading_logic_semantic_diff_evidence_bundle_dir=(
            semantic_diff_fixture.trading_logic_semantic_diff_evidence_bundle_dir
        ),
        runtime_state_reconciliation_bundle_dir=reconciliation_dir,
    )
