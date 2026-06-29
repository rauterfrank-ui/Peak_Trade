"""Fixtures for independent_pre_trade_safety_kernel_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.independent_pre_trade_safety_kernel_v1 import (
    IndependentPreTradeSafetyKernelInputs,
    default_pre_trade_safety_evaluation_request,
    produce_independent_pre_trade_safety_kernel_v1,
    verify_clock_trust_and_expiry_bundle,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
    verify_venue_capability_snapshot_bundle,
)
from src.meta.learning_loop.clock_trust_and_expiry_v1 import verify_authority_lease_bundle
from tests.meta.runtime_state_reconciliation_v1_fixtures import (
    produce_runtime_state_reconciliation_fixture,
)
from tests.meta.trading_core_decision_attestation_v1_fixtures import (
    produce_trading_core_decision_attestation_fixture,
)
from tests.meta.venue_capability_snapshot_v1_fixtures import (
    produce_venue_capability_snapshot_fixture,
)


@dataclass(frozen=True)
class IndependentPreTradeSafetyKernelFixtureBundle:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    trading_core_decision_attestation_bundle_dir: Path
    venue_capability_snapshot_bundle_dir: Path
    clock_trust_and_expiry_bundle_dir: Path
    authority_lease_bundle_dir: Path
    independent_pre_trade_safety_kernel_bundle_dir: Path | None = None


def _session_bundle_refs(
    trading_session_bundle_dir: Path,
    *,
    durable_root: Path,
) -> tuple[Path, Path]:
    payload = read_manifest(trading_session_bundle_dir / "trading_session_single_writer_v1.json")
    clock_ref = Path(str(payload.get("clock_trust_and_expiry_bundle_ref", "")))
    if not clock_ref.is_dir():
        raise ValueError(f"clock trust bundle not found: {clock_ref}")
    clock_payload = read_manifest(clock_ref / "clock_trust_and_expiry_v1.json")
    lease_ref = Path(str(clock_payload.get("authority_lease_and_revocation_bundle_ref", "")))
    if not lease_ref.is_dir():
        raise ValueError(f"authority lease bundle not found: {lease_ref}")

    ok, msg = verify_manifest_sha256(lease_ref)
    if not ok:
        fallback = durable_root / "authority_lease"
        if fallback.is_dir():
            ok_fb, msg_fb = verify_manifest_sha256(fallback)
            if ok_fb:
                lease_ref = fallback
            else:
                raise ValueError(
                    f"authority lease MANIFEST.sha256 missing: {lease_ref} ({msg}); "
                    f"fallback {fallback} ({msg_fb})"
                )
        else:
            raise ValueError(f"authority lease MANIFEST.sha256 missing: {lease_ref} ({msg})")

    return clock_ref, lease_ref


def produce_independent_pre_trade_safety_kernel_fixture(
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
    reconciliation_name: str = "runtime_state_reconciliation_for_pre_trade_safety",
    attestation_name: str = "trading_core_decision_attestation_for_pre_trade_safety",
    venue_capability_name: str = "venue_capability_snapshot_for_pre_trade_safety",
    safety_kernel_name: str = "independent_pre_trade_safety_kernel",
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    client_order_id: str = "generic-futures-client-order-001",
    correlation_id: str = "offline-pre-trade-safety-correlation-001",
) -> IndependentPreTradeSafetyKernelFixtureBundle:
    attestation_fixture = produce_trading_core_decision_attestation_fixture(
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
        idempotency_name="order_intent_idempotency_for_pre_trade_safety",
        attestation_name=attestation_name,
        client_order_id=client_order_id,
        instrument_type=instrument_type,
        instrument=instrument,
        correlation_id=correlation_id,
    )
    assert attestation_fixture.order_intent_idempotency_bundle_dir is not None
    assert attestation_fixture.trading_core_decision_attestation_bundle_dir is not None

    reconciliation_fixture = produce_runtime_state_reconciliation_fixture(
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
        reconciliation_name=reconciliation_name,
        instrument_type=instrument_type,
        instrument=instrument,
        correlation_id=correlation_id,
    )
    assert reconciliation_fixture.runtime_state_reconciliation_bundle_dir is not None

    venue_fixture = produce_venue_capability_snapshot_fixture(
        tmp_path,
        durable_root,
        produce_output=True,
        snapshot_name=venue_capability_name,
        instrument=instrument,
    )
    assert venue_fixture.snapshot_bundle_dir is not None

    attestation_payload = read_manifest(
        attestation_fixture.trading_core_decision_attestation_bundle_dir
        / "trading_core_decision_attestation_v1.json"
    )
    bindings = attestation_payload.get("upstream_bindings", {})
    session_ref = Path(str(bindings.get("trading_session_single_writer_bundle_ref", "")))
    clock_trust_dir, authority_lease_dir = _session_bundle_refs(
        session_ref,
        durable_root=durable_root,
    )

    idempotency = verify_order_intent_idempotency_bundle(
        attestation_fixture.order_intent_idempotency_bundle_dir
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        reconciliation_fixture.runtime_state_reconciliation_bundle_dir
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        attestation_fixture.trading_core_decision_attestation_bundle_dir
    )
    venue_capability = verify_venue_capability_snapshot_bundle(venue_fixture.snapshot_bundle_dir)
    authority_lease = verify_authority_lease_bundle(authority_lease_dir)
    clock_trust = verify_clock_trust_and_expiry_bundle(clock_trust_dir)
    request = default_pre_trade_safety_evaluation_request(
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
        venue_capability=venue_capability,
        authority_lease=authority_lease,
        clock_trust=clock_trust,
    )

    safety_dir: Path | None = None
    if produce_output:
        safety_dir = durable_root / safety_kernel_name
        produce_independent_pre_trade_safety_kernel_v1(
            inputs=IndependentPreTradeSafetyKernelInputs(
                runtime_state_reconciliation_bundle_dir=(
                    reconciliation_fixture.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=(
                    attestation_fixture.order_intent_idempotency_bundle_dir
                ),
                trading_core_decision_attestation_bundle_dir=(
                    attestation_fixture.trading_core_decision_attestation_bundle_dir
                ),
                venue_capability_snapshot_bundle_dir=venue_fixture.snapshot_bundle_dir,
                clock_trust_and_expiry_bundle_dir=clock_trust_dir,
                authority_lease_bundle_dir=authority_lease_dir,
                request=request,
            ),
            output_dir=safety_dir,
        )

    return IndependentPreTradeSafetyKernelFixtureBundle(
        runtime_state_reconciliation_bundle_dir=(
            reconciliation_fixture.runtime_state_reconciliation_bundle_dir
        ),
        order_intent_idempotency_bundle_dir=attestation_fixture.order_intent_idempotency_bundle_dir,
        trading_core_decision_attestation_bundle_dir=(
            attestation_fixture.trading_core_decision_attestation_bundle_dir
        ),
        venue_capability_snapshot_bundle_dir=venue_fixture.snapshot_bundle_dir,
        clock_trust_and_expiry_bundle_dir=clock_trust_dir,
        authority_lease_bundle_dir=authority_lease_dir,
        independent_pre_trade_safety_kernel_bundle_dir=safety_dir,
    )
