"""Fixtures for authority_lease_and_revocation_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
    AuthorityLeaseInputs,
    AuthorityLeaseRequest,
    default_lease_request,
    produce_authority_lease_and_revocation_v1,
)
from tests.meta.handoff_trust_policy_v1_fixtures import produce_handoff_trust_policy_fixture


@dataclass(frozen=True)
class AuthorityLeaseFixtureBundle:
    handoff_trust_policy_bundle_dir: Path
    authority_lease_bundle_dir: Path | None = None


def produce_authority_lease_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    authority_domain: str = "TRADING_DECISION_CORE",
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    valid_from: str = "2026-06-29T00:00:00+00:00",
    valid_until: str = "2026-06-30T00:00:00+00:00",
    revocation_state: str = "NOT_REVOKED",
    revocation_ref: str | None = None,
    produce_output: bool = True,
    lease_name: str = "authority_lease",
) -> AuthorityLeaseFixtureBundle:
    handoff = produce_handoff_trust_policy_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
    )
    assert handoff.handoff_trust_policy_bundle_dir is not None
    lease_dir: Path | None = None
    if produce_output:
        from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
            verify_handoff_trust_policy_bundle,
        )

        verified = verify_handoff_trust_policy_bundle(handoff.handoff_trust_policy_bundle_dir)
        request = default_lease_request(
            handoff=verified,
            authority_domain=authority_domain,
            evaluation_time=evaluation_time,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        if revocation_state != "NOT_REVOKED":
            request = AuthorityLeaseRequest(
                authority_domain=request.authority_domain,
                subject_identity_ref=request.subject_identity_ref,
                subject_identity_digest=request.subject_identity_digest,
                issuer_identity_ref=request.issuer_identity_ref,
                issuer_identity_digest=request.issuer_identity_digest,
                valid_from=request.valid_from,
                valid_until=request.valid_until,
                evaluation_time=request.evaluation_time,
                allowed_capabilities=request.allowed_capabilities,
                revocation_state=revocation_state,
                revocation_ref=revocation_ref or "offline_revocation_evidence_v1",
                revocation_digest="deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            )
        lease_dir = durable_root / lease_name
        produce_authority_lease_and_revocation_v1(
            inputs=AuthorityLeaseInputs(
                handoff_trust_policy_bundle_dir=handoff.handoff_trust_policy_bundle_dir,
                lease_request=request,
            ),
            output_dir=lease_dir,
        )
    return AuthorityLeaseFixtureBundle(
        handoff_trust_policy_bundle_dir=handoff.handoff_trust_policy_bundle_dir,
        authority_lease_bundle_dir=lease_dir,
    )
