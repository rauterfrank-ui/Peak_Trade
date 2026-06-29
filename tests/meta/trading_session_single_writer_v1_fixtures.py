"""Fixtures for trading_session_single_writer_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.trading_session_single_writer_v1 import (
    TradingSessionSingleWriterInputs,
    default_trading_session_single_writer_request,
    produce_trading_session_single_writer_v1,
    verify_clock_trust_and_expiry_bundle,
)
from tests.meta.clock_trust_and_expiry_v1_fixtures import produce_clock_trust_and_expiry_fixture


@dataclass(frozen=True)
class TradingSessionSingleWriterFixtureBundle:
    clock_trust_and_expiry_bundle_dir: Path
    trading_session_single_writer_bundle_dir: Path | None = None


def produce_trading_session_single_writer_fixture(
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
    maximum_clock_skew_seconds: int = 3600,
    maximum_evidence_age_seconds: int = 86400,
    produce_output: bool = True,
    clock_trust_name: str = "clock_trust_for_single_writer",
    single_writer_name: str = "trading_session_single_writer",
    venue: str = "testnet",
    account: str = "acct-001",
    instrument: str = "BTC-PERP",
    trading_epoch: str = "epoch-001",
    writer_identity: str = "writer-primary-001",
    writer_generation: int = 1,
    expected_writer_revision: int = 1,
    executor_epoch: int = 1,
) -> TradingSessionSingleWriterFixtureBundle:
    clock_trust_fixture = produce_clock_trust_and_expiry_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
        maximum_clock_skew_seconds=maximum_clock_skew_seconds,
        maximum_evidence_age_seconds=maximum_evidence_age_seconds,
        produce_output=True,
        clock_trust_name=clock_trust_name,
    )
    assert clock_trust_fixture.clock_trust_and_expiry_bundle_dir is not None

    single_writer_dir: Path | None = None
    if produce_output:
        clock_trust = verify_clock_trust_and_expiry_bundle(
            clock_trust_fixture.clock_trust_and_expiry_bundle_dir
        )
        request = default_trading_session_single_writer_request(
            clock_trust=clock_trust,
            venue=venue,
            account=account,
            instrument=instrument,
            trading_epoch=trading_epoch,
            writer_identity=writer_identity,
            writer_generation=writer_generation,
            expected_writer_revision=expected_writer_revision,
            executor_epoch=executor_epoch,
        )
        single_writer_dir = durable_root / single_writer_name
        produce_trading_session_single_writer_v1(
            inputs=TradingSessionSingleWriterInputs(
                clock_trust_and_expiry_bundle_dir=clock_trust_fixture.clock_trust_and_expiry_bundle_dir,
                trading_session_request=request,
            ),
            output_dir=single_writer_dir,
        )

    return TradingSessionSingleWriterFixtureBundle(
        clock_trust_and_expiry_bundle_dir=clock_trust_fixture.clock_trust_and_expiry_bundle_dir,
        trading_session_single_writer_bundle_dir=single_writer_dir,
    )
