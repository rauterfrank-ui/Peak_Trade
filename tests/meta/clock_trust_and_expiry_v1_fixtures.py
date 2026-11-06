"""Fixtures for clock_trust_and_expiry_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    ClockTrustAndExpiryInputs,
    default_clock_trust_request,
    produce_clock_trust_and_expiry_v1,
    verify_authority_lease_bundle,
    verify_secure_handoff_envelope_bundle_for_clock_trust,
)
from src.meta.learning_loop.handoff_atomic_claim_consume_v1 import (
    HandoffAtomicClaimConsumeInputs,
    default_claim_consume_request,
    produce_handoff_atomic_claim_consume_v1,
    verify_secure_handoff_envelope_bundle,
)
from tests.meta.secure_handoff_envelope_v1_fixtures import produce_secure_handoff_envelope_fixture


@dataclass(frozen=True)
class ClockTrustAndExpiryFixtureBundle:
    secure_handoff_envelope_bundle_dir: Path
    handoff_atomic_claim_consume_bundle_dir: Path
    authority_lease_bundle_dir: Path
    clock_trust_and_expiry_bundle_dir: Path | None = None


def produce_clock_trust_and_expiry_fixture(
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
    clock_trust_name: str = "clock_trust_and_expiry",
) -> ClockTrustAndExpiryFixtureBundle:
    envelope_fixture = produce_secure_handoff_envelope_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
        envelope_name="clock_trust_envelope",
    )
    assert envelope_fixture.secure_handoff_envelope_bundle_dir is not None
    assert envelope_fixture.authority_lease_bundle_dir is not None

    verified = verify_secure_handoff_envelope_bundle(
        envelope_fixture.secure_handoff_envelope_bundle_dir
    )
    claim_consume_dir = durable_root / "clock_trust_claim_consume"
    produce_handoff_atomic_claim_consume_v1(
        inputs=HandoffAtomicClaimConsumeInputs(
            secure_handoff_envelope_bundle_dir=envelope_fixture.secure_handoff_envelope_bundle_dir,
            claim_consume_request=default_claim_consume_request(envelope=verified),
        ),
        output_dir=claim_consume_dir,
    )

    clock_trust_dir: Path | None = None
    if produce_output:
        envelope = verify_secure_handoff_envelope_bundle_for_clock_trust(
            envelope_fixture.secure_handoff_envelope_bundle_dir
        )
        authority_lease = verify_authority_lease_bundle(envelope_fixture.authority_lease_bundle_dir)
        request = default_clock_trust_request(
            envelope=envelope,
            authority_lease=authority_lease,
            maximum_clock_skew_seconds=maximum_clock_skew_seconds,
            maximum_evidence_age_seconds=maximum_evidence_age_seconds,
        )
        clock_trust_dir = durable_root / clock_trust_name
        produce_clock_trust_and_expiry_v1(
            inputs=ClockTrustAndExpiryInputs(
                secure_handoff_envelope_bundle_dir=envelope_fixture.secure_handoff_envelope_bundle_dir,
                handoff_atomic_claim_consume_bundle_dir=claim_consume_dir,
                authority_lease_and_revocation_bundle_dir=envelope_fixture.authority_lease_bundle_dir,
                clock_trust_request=request,
            ),
            output_dir=clock_trust_dir,
        )

    return ClockTrustAndExpiryFixtureBundle(
        secure_handoff_envelope_bundle_dir=envelope_fixture.secure_handoff_envelope_bundle_dir,
        handoff_atomic_claim_consume_bundle_dir=claim_consume_dir,
        authority_lease_bundle_dir=envelope_fixture.authority_lease_bundle_dir,
        clock_trust_and_expiry_bundle_dir=clock_trust_dir,
    )
