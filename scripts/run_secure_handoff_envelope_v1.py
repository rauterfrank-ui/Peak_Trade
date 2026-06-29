#!/usr/bin/env python3
"""
Offline secure handoff envelope contract v1.

Consumes exactly one verified authority_lease_and_revocation_v1 bundle, producing a
manifested LEVEL_3 non-authorizing secure handoff envelope for offline evidence only.

Usage:
    python3 scripts/run_secure_handoff_envelope_v1.py \\
        --authority-lease-bundle-dir /path/to/authority_lease \\
        --evaluation-time 2026-06-29T12:00:00+00:00 \\
        --allowed-offline-capability CAN_DESCRIBE_OFFLINE_HANDOFF_ENVELOPE \\
        --output-dir /var/evidence/secure_handoff_envelope_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.secure_handoff_envelope_v1 import (
    SecureHandoffEnvelopeError,
    SecureHandoffEnvelopeInputs,
    SecureHandoffEnvelopeRequest,
    default_envelope_request,
    produce_secure_handoff_envelope_v1,
    verify_authority_lease_bundle,
)

EXIT_OK = 0
EXIT_ENVELOPE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline secure handoff envelope v1: deterministically package verified "
            "authority lease, handoff trust policy, and versioned artifact contracts "
            "into an immutable envelope without executing handoff, invoking consumers, "
            "or activating authority."
        )
    )
    parser.add_argument(
        "--authority-lease-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published authority_lease_and_revocation_v1 bundle.",
    )
    parser.add_argument(
        "--evaluation-time",
        default=None,
        help="Explicit evaluation time UTC instant (+00:00 or Z).",
    )
    parser.add_argument(
        "--allowed-offline-capability",
        action="append",
        default=None,
        dest="allowed_offline_capabilities",
        help="Allowed offline capability (repeatable).",
    )
    parser.add_argument(
        "--denied-capability",
        action="append",
        default=None,
        dest="denied_capabilities",
        help="Explicit denied capability (repeatable).",
    )
    parser.add_argument(
        "--intended-consumer-identity-ref",
        default=None,
        help="Intended consumer identity ref (defaults from handoff trust policy).",
    )
    parser.add_argument(
        "--intended-consumer-identity-version",
        default=None,
        help="Intended consumer identity version (defaults from handoff trust policy).",
    )
    parser.add_argument(
        "--source-revision",
        default=None,
        help="Source revision for provenance metadata.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit secure handoff envelope output directory (must not exist).",
    )
    return parser.parse_args(argv)


def _resolve_envelope_request(args: argparse.Namespace) -> SecureHandoffEnvelopeRequest:
    lease = verify_authority_lease_bundle(args.authority_lease_bundle_dir)
    defaults = default_envelope_request(lease=lease)
    explicit_fields = (
        args.evaluation_time,
        args.allowed_offline_capabilities,
        args.intended_consumer_identity_ref,
        args.intended_consumer_identity_version,
        args.source_revision,
    )
    if all(field is None for field in explicit_fields) and not args.denied_capabilities:
        return defaults
    return SecureHandoffEnvelopeRequest(
        evaluation_time=args.evaluation_time or defaults.evaluation_time,
        allowed_offline_capabilities=tuple(
            args.allowed_offline_capabilities or defaults.allowed_offline_capabilities
        ),
        denied_capabilities=tuple(args.denied_capabilities or ()),
        source_revision=args.source_revision or defaults.source_revision,
        intended_consumer_identity_ref=(
            args.intended_consumer_identity_ref or defaults.intended_consumer_identity_ref
        ),
        intended_consumer_identity_version=(
            args.intended_consumer_identity_version or defaults.intended_consumer_identity_version
        ),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.authority_lease_bundle_dir.is_dir():
        print(
            "[secure_handoff_envelope_v1] ERROR: authority lease bundle not found: "
            f"{args.authority_lease_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        envelope_request = _resolve_envelope_request(args)
    except SecureHandoffEnvelopeError as exc:
        print(f"[secure_handoff_envelope_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_ENVELOPE_ERROR

    inputs = SecureHandoffEnvelopeInputs(
        authority_lease_bundle_dir=args.authority_lease_bundle_dir,
        envelope_request=envelope_request,
    )

    try:
        result = produce_secure_handoff_envelope_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except SecureHandoffEnvelopeError as exc:
        print(f"[secure_handoff_envelope_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_ENVELOPE_ERROR

    print(
        "[secure_handoff_envelope_v1] OK "
        f"envelope_id={result.envelope_id} "
        f"envelope_status={result.envelope_status} "
        f"payload_digest={result.payload_digest} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
