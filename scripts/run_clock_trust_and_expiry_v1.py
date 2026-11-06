#!/usr/bin/env python3
"""
Offline clock trust and expiry contract v1.

Consumes exactly one verified secure_handoff_envelope_v1 bundle, one verified
handoff_atomic_claim_consume_v1 bundle, and one verified authority_lease_and_revocation_v1
bundle, producing a manifested LEVEL_3 non-authorizing clock trust and expiry
contract for offline evidence only.

Usage:
    python3 scripts/run_clock_trust_and_expiry_v1.py \\
        --secure-handoff-envelope-bundle-dir /path/to/envelope \\
        --handoff-atomic-claim-consume-bundle-dir /path/to/claim_consume \\
        --authority-lease-bundle-dir /path/to/lease \\
        --evaluation-time 2026-06-29T12:00:00+00:00 \\
        --maximum-clock-skew-seconds 3600 \\
        --maximum-evidence-age-seconds 86400 \\
        --output-dir /var/evidence/clock_trust_and_expiry_001
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.clock_trust_and_expiry_v1 import (
    ClockTrustAndExpiryError,
    ClockTrustAndExpiryInputs,
    ClockTrustAndExpiryRequest,
    default_clock_trust_request,
    produce_clock_trust_and_expiry_v1,
    verify_clock_trust_and_expiry_inputs,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline clock trust and expiry v1: deterministically evaluate temporal "
            "trust and expiry bindings for verified handoff evidence without reading "
            "system clock, executing expiry, claim, consume, or state mutation."
        )
    )
    parser.add_argument(
        "--secure-handoff-envelope-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published secure_handoff_envelope_v1 bundle.",
    )
    parser.add_argument(
        "--handoff-atomic-claim-consume-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published handoff_atomic_claim_consume_v1 bundle.",
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
        "--evaluation-time-source",
        default=None,
        help="Evaluation time source (default OFFLINE_DETERMINISTIC_EVIDENCE).",
    )
    parser.add_argument(
        "--evaluation-time-source-identity",
        default=None,
        help="Evaluation time source identity.",
    )
    parser.add_argument(
        "--evaluation-time-provenance-json",
        default=None,
        help="JSON object for evaluation_time_provenance.",
    )
    parser.add_argument(
        "--maximum-clock-skew-seconds",
        type=int,
        default=None,
        help="Maximum allowed clock skew in seconds.",
    )
    parser.add_argument(
        "--maximum-evidence-age-seconds",
        type=int,
        default=None,
        help="Maximum allowed evidence age in seconds.",
    )
    parser.add_argument(
        "--prior-temporal-evidence-digest",
        default="",
        help="Optional prior temporal evidence digest for replay detection.",
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
        help="Explicit clock trust and expiry output directory (must not exist).",
    )
    return parser.parse_args(argv)


def _resolve_request(args: argparse.Namespace) -> ClockTrustAndExpiryRequest:
    skew = args.maximum_clock_skew_seconds
    age = args.maximum_evidence_age_seconds
    if skew is None or age is None:
        raise ClockTrustAndExpiryError(
            "maximum_clock_skew_seconds and maximum_evidence_age_seconds are required"
        )

    placeholder_inputs = ClockTrustAndExpiryInputs(
        secure_handoff_envelope_bundle_dir=args.secure_handoff_envelope_bundle_dir,
        handoff_atomic_claim_consume_bundle_dir=args.handoff_atomic_claim_consume_bundle_dir,
        authority_lease_and_revocation_bundle_dir=args.authority_lease_bundle_dir,
        clock_trust_request=ClockTrustAndExpiryRequest(
            evaluation_time="1970-01-01T00:00:00+00:00",
            evaluation_time_source="OFFLINE_DETERMINISTIC_EVIDENCE",
            evaluation_time_source_identity="placeholder",
            evaluation_time_provenance={"placeholder": True},
        ),
    )
    envelope, _claim_consume, authority_lease = verify_clock_trust_and_expiry_inputs(
        placeholder_inputs
    )

    defaults = default_clock_trust_request(
        envelope=envelope,
        authority_lease=authority_lease,
        maximum_clock_skew_seconds=skew,
        maximum_evidence_age_seconds=age,
    )

    provenance = defaults.evaluation_time_provenance
    if args.evaluation_time_provenance_json:
        loaded = json.loads(args.evaluation_time_provenance_json)
        if not isinstance(loaded, dict):
            raise ClockTrustAndExpiryError("evaluation_time_provenance must be a JSON object")
        provenance = loaded

    return ClockTrustAndExpiryRequest(
        evaluation_time=args.evaluation_time or defaults.evaluation_time,
        evaluation_time_source=args.evaluation_time_source or defaults.evaluation_time_source,
        evaluation_time_source_identity=(
            args.evaluation_time_source_identity or defaults.evaluation_time_source_identity
        ),
        evaluation_time_provenance=provenance,
        maximum_clock_skew_seconds=skew,
        maximum_evidence_age_seconds=age,
        prior_temporal_evidence_digest=args.prior_temporal_evidence_digest,
        source_revision=args.source_revision or defaults.source_revision,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    for label, path in (
        ("secure handoff envelope bundle", args.secure_handoff_envelope_bundle_dir),
        ("handoff atomic claim consume bundle", args.handoff_atomic_claim_consume_bundle_dir),
        ("authority lease bundle", args.authority_lease_bundle_dir),
    ):
        if not path.is_dir():
            print(
                f"[clock_trust_and_expiry_v1] ERROR: {label} not found: {path}",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

    try:
        clock_trust_request = _resolve_request(args)
    except (ClockTrustAndExpiryError, json.JSONDecodeError) as exc:
        print(f"[clock_trust_and_expiry_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    inputs = ClockTrustAndExpiryInputs(
        secure_handoff_envelope_bundle_dir=args.secure_handoff_envelope_bundle_dir,
        handoff_atomic_claim_consume_bundle_dir=args.handoff_atomic_claim_consume_bundle_dir,
        authority_lease_and_revocation_bundle_dir=args.authority_lease_bundle_dir,
        clock_trust_request=clock_trust_request,
    )

    try:
        result = produce_clock_trust_and_expiry_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ClockTrustAndExpiryError as exc:
        print(f"[clock_trust_and_expiry_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        "[clock_trust_and_expiry_v1] OK "
        f"contract_id={result.contract_id} "
        f"contract_status={result.contract_status} "
        f"clock_trust_status={result.clock_trust_status} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
