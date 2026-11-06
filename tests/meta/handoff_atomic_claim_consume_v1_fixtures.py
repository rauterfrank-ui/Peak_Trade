"""Fixtures for handoff_atomic_claim_consume_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.handoff_atomic_claim_consume_v1 import (
    HandoffAtomicClaimConsumeInputs,
    default_claim_consume_request,
    produce_handoff_atomic_claim_consume_v1,
    verify_secure_handoff_envelope_bundle,
)
from tests.meta.secure_handoff_envelope_v1_fixtures import produce_secure_handoff_envelope_fixture


@dataclass(frozen=True)
class HandoffAtomicClaimConsumeFixtureBundle:
    secure_handoff_envelope_bundle_dir: Path
    handoff_atomic_claim_consume_bundle_dir: Path | None = None


def produce_handoff_atomic_claim_consume_fixture(
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
    claim_consume_name: str = "handoff_atomic_claim_consume",
) -> HandoffAtomicClaimConsumeFixtureBundle:
    envelope = produce_secure_handoff_envelope_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
    )
    assert envelope.secure_handoff_envelope_bundle_dir is not None
    claim_consume_dir: Path | None = None
    if produce_output:
        verified = verify_secure_handoff_envelope_bundle(
            envelope.secure_handoff_envelope_bundle_dir
        )
        request = default_claim_consume_request(envelope=verified)
        claim_consume_dir = durable_root / claim_consume_name
        produce_handoff_atomic_claim_consume_v1(
            inputs=HandoffAtomicClaimConsumeInputs(
                secure_handoff_envelope_bundle_dir=envelope.secure_handoff_envelope_bundle_dir,
                claim_consume_request=request,
            ),
            output_dir=claim_consume_dir,
        )
    return HandoffAtomicClaimConsumeFixtureBundle(
        secure_handoff_envelope_bundle_dir=envelope.secure_handoff_envelope_bundle_dir,
        handoff_atomic_claim_consume_bundle_dir=claim_consume_dir,
    )
