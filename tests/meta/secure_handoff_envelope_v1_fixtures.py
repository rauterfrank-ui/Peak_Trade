"""Fixtures for secure_handoff_envelope_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.secure_handoff_envelope_v1 import (
    SecureHandoffEnvelopeInputs,
    SecureHandoffEnvelopeRequest,
    default_envelope_request,
    produce_secure_handoff_envelope_v1,
)
from tests.meta.authority_lease_and_revocation_v1_fixtures import produce_authority_lease_fixture


@dataclass(frozen=True)
class SecureHandoffEnvelopeFixtureBundle:
    authority_lease_bundle_dir: Path
    secure_handoff_envelope_bundle_dir: Path | None = None


def produce_secure_handoff_envelope_fixture(
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
    envelope_name: str = "secure_handoff_envelope",
) -> SecureHandoffEnvelopeFixtureBundle:
    lease = produce_authority_lease_fixture(
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
    assert lease.authority_lease_bundle_dir is not None
    envelope_dir: Path | None = None
    if produce_output:
        from src.meta.learning_loop.secure_handoff_envelope_v1 import verify_authority_lease_bundle

        verified = verify_authority_lease_bundle(lease.authority_lease_bundle_dir)
        request = default_envelope_request(lease=verified)
        if evaluation_time != request.evaluation_time:
            request = SecureHandoffEnvelopeRequest(
                evaluation_time=evaluation_time,
                allowed_offline_capabilities=request.allowed_offline_capabilities,
                intended_consumer_identity_ref=request.intended_consumer_identity_ref,
                intended_consumer_identity_version=request.intended_consumer_identity_version,
            )
        envelope_dir = durable_root / envelope_name
        produce_secure_handoff_envelope_v1(
            inputs=SecureHandoffEnvelopeInputs(
                authority_lease_bundle_dir=lease.authority_lease_bundle_dir,
                envelope_request=request,
            ),
            output_dir=envelope_dir,
        )
    return SecureHandoffEnvelopeFixtureBundle(
        authority_lease_bundle_dir=lease.authority_lease_bundle_dir,
        secure_handoff_envelope_bundle_dir=envelope_dir,
    )
