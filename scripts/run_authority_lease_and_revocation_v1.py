#!/usr/bin/env python3
"""
Offline authority lease and revocation contract v1.

Consumes exactly one verified handoff_trust_policy_v1 bundle with explicit lease
request parameters, producing a manifested LEVEL_3 non-authorizing lease contract.

Usage:
    python3 scripts/run_authority_lease_and_revocation_v1.py \\
        --handoff-trust-policy-bundle-dir /path/to/handoff_trust_policy \\
        --authority-domain TRADING_DECISION_CORE \\
        --subject-identity-ref <ref> \\
        --subject-identity-digest <sha256> \\
        --issuer-identity-ref peak_trade_offline_authority_lease_issuer_v1 \\
        --issuer-identity-digest <sha256> \\
        --valid-from 2026-06-29T00:00:00+00:00 \\
        --valid-until 2026-06-30T00:00:00+00:00 \\
        --evaluation-time 2026-06-29T12:00:00+00:00 \\
        --allowed-capability CAN_DESCRIBE_OFFLINE_AUTHORITY_SCOPE \\
        --allowed-capability CAN_BIND_HANDOFF_TRUST_POLICY_REF \\
        --output-dir /var/evidence/authority_lease_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.authority_lease_and_revocation_v1 import (
    AuthorityLeaseAndRevocationError,
    AuthorityLeaseInputs,
    AuthorityLeaseRequest,
    default_lease_request,
    produce_authority_lease_and_revocation_v1,
    verify_handoff_trust_policy_bundle,
)

EXIT_OK = 0
EXIT_LEASE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline authority lease and revocation v1: deterministically describe "
            "a bounded authority lease contract without granting authority, activating "
            "leases, executing revocation, or creating runtime permissions."
        )
    )
    parser.add_argument(
        "--handoff-trust-policy-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published handoff_trust_policy_v1 bundle.",
    )
    parser.add_argument(
        "--authority-domain",
        default=None,
        help="Authority domain (TRADING_DECISION_CORE or SAFETY_EXECUTION_RUNTIME_CORE).",
    )
    parser.add_argument(
        "--subject-identity-ref",
        default=None,
        help="Subject/holder identity ref. Defaults to strategy identity from handoff.",
    )
    parser.add_argument(
        "--subject-identity-digest",
        default=None,
        help="Subject/holder identity digest. Defaults to strategy digest from handoff.",
    )
    parser.add_argument(
        "--issuer-identity-ref",
        default=None,
        help="Issuer identity ref.",
    )
    parser.add_argument(
        "--issuer-identity-digest",
        default=None,
        help="Issuer identity digest.",
    )
    parser.add_argument(
        "--valid-from",
        default=None,
        help="Lease valid_from UTC instant (+00:00 or Z).",
    )
    parser.add_argument(
        "--valid-until",
        default=None,
        help="Lease valid_until UTC instant (+00:00 or Z).",
    )
    parser.add_argument(
        "--evaluation-time",
        default=None,
        help="Explicit evaluation time UTC instant (+00:00 or Z).",
    )
    parser.add_argument(
        "--allowed-capability",
        action="append",
        default=None,
        dest="allowed_capabilities",
        help="Allowed capability (repeatable).",
    )
    parser.add_argument(
        "--denied-capability",
        action="append",
        default=None,
        dest="denied_capabilities",
        help="Explicit denied capability (repeatable).",
    )
    parser.add_argument(
        "--revocation-state",
        default="NOT_REVOKED",
        choices=("NOT_REVOKED", "REVOKED", "UNKNOWN"),
        help="Offline revocation state for contract description.",
    )
    parser.add_argument(
        "--revocation-ref",
        default=None,
        help="Revocation evidence ref when revocation-state is REVOKED.",
    )
    parser.add_argument(
        "--revocation-digest",
        default=None,
        help="Revocation evidence digest when present.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit authority lease output directory (must not exist).",
    )
    return parser.parse_args(argv)


def _resolve_lease_request(args: argparse.Namespace) -> AuthorityLeaseRequest:
    handoff = verify_handoff_trust_policy_bundle(args.handoff_trust_policy_bundle_dir)
    defaults = default_lease_request(handoff=handoff)
    explicit_fields = (
        args.authority_domain,
        args.subject_identity_ref,
        args.subject_identity_digest,
        args.issuer_identity_ref,
        args.issuer_identity_digest,
        args.valid_from,
        args.valid_until,
        args.evaluation_time,
        args.allowed_capabilities,
    )
    if all(field is None for field in explicit_fields) and args.revocation_state == "NOT_REVOKED":
        return defaults
    return AuthorityLeaseRequest(
        authority_domain=args.authority_domain or defaults.authority_domain,
        subject_identity_ref=args.subject_identity_ref or defaults.subject_identity_ref,
        subject_identity_digest=args.subject_identity_digest or defaults.subject_identity_digest,
        issuer_identity_ref=args.issuer_identity_ref or defaults.issuer_identity_ref,
        issuer_identity_digest=args.issuer_identity_digest or defaults.issuer_identity_digest,
        valid_from=args.valid_from or defaults.valid_from,
        valid_until=args.valid_until or defaults.valid_until,
        evaluation_time=args.evaluation_time or defaults.evaluation_time,
        allowed_capabilities=tuple(args.allowed_capabilities or defaults.allowed_capabilities),
        denied_capabilities=tuple(args.denied_capabilities or ()),
        revocation_state=args.revocation_state,
        revocation_ref=args.revocation_ref,
        revocation_digest=args.revocation_digest,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.handoff_trust_policy_bundle_dir.is_dir():
        print(
            "[authority_lease_and_revocation_v1] ERROR: handoff trust policy bundle not found: "
            f"{args.handoff_trust_policy_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        lease_request = _resolve_lease_request(args)
    except AuthorityLeaseAndRevocationError as exc:
        print(f"[authority_lease_and_revocation_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_LEASE_ERROR

    inputs = AuthorityLeaseInputs(
        handoff_trust_policy_bundle_dir=args.handoff_trust_policy_bundle_dir,
        lease_request=lease_request,
    )

    try:
        result = produce_authority_lease_and_revocation_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except AuthorityLeaseAndRevocationError as exc:
        print(f"[authority_lease_and_revocation_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_LEASE_ERROR

    print(
        "[authority_lease_and_revocation_v1] OK "
        f"lease_id={result.lease_id} "
        f"lease_status={result.lease_status} "
        f"handoff_trust_policy_ref={result.handoff_trust_policy_ref} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
