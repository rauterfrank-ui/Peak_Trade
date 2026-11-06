#!/usr/bin/env python3
"""Explicit governed runtime: one bounded Enter-order POST (Owner-GO scoped)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_envelope(path: Path):
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        FinalOrderEnvelopeV1,
        assert_envelope_unmodified_v1,
        compute_final_order_envelope_digest_v1,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("ENVELOPE_JSON_NOT_OBJECT")
    digest = str(payload.get("envelope_digest") or "")
    body = {k: v for k, v in payload.items() if k not in {"envelope_id", "envelope_digest"}}
    if not digest:
        digest = compute_final_order_envelope_digest_v1(body)
    envelope = FinalOrderEnvelopeV1(
        envelope_id=str(payload["envelope_id"]),
        envelope_digest=digest,
        instrument_id=str(payload["instrument_id"]),
        side=str(payload["side"]),
        order_type=str(payload["order_type"]),
        quantity=str(payload["quantity"]),
        quantity_unit=str(payload.get("quantity_unit") or "contract"),
        price=str(payload.get("price") or ""),
        td_mode=str(payload["td_mode"]),
        pos_side=str(payload.get("pos_side") or ""),
        reduce_only=bool(payload.get("reduce_only")),
        client_order_id=str(payload["client_order_id"]),
        path_kind=str(payload["path_kind"]),
        venue_plan_clordid=str(payload.get("venue_plan_clordid") or payload["client_order_id"]),
        quantity_source=str(payload["quantity_source"]),
        side_source=str(payload["side_source"]),
        instrument_source=str(payload["instrument_source"]),
        admission_ref=str(payload["admission_ref"]),
        provenance_ref=str(payload["provenance_ref"]),
        creation_epoch=str(payload["creation_epoch"]),
    )
    assert_envelope_unmodified_v1(envelope)
    return envelope


def _main() -> int:
    parser = argparse.ArgumentParser(description="One-shot Enter POST (governed)")
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--envelope-json", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--pre-live-only", action="store_true")
    parser.add_argument(
        "--confirm-real-venue-post",
        action="store_true",
        help="Required to perform the single authorized HTTP POST",
    )
    parser.add_argument(
        "--k1-backend",
        choices=("none", "macos"),
        default="none",
        help="Pre-live / POST join K1 lookup backend (macos requires canonical K1 Owner-GO scope)",
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
        K1_OPAQUE_SIGNING_OWNER_GO,
        resolve_macos_security_framework_k1_lookup_backend_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        OWNER_GO,
        execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1,
        prove_pre_live_actual_venue_post_readiness_v1,
    )

    def _resolve_k1_backend():
        if args.k1_backend == "macos":
            return resolve_macos_security_framework_k1_lookup_backend_v1(
                k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO
            )
        return None

    envelope = _load_envelope(args.envelope_json)
    if args.pre_live_only:
        k1_backend = _resolve_k1_backend()
        if k1_backend is None:
            print(
                "FAIL_CLOSED: --pre-live-only requires --k1-backend macos for PRE_LIVE_PROOF_COMPLETE",
                file=sys.stderr,
            )
            return 2
        proof = prove_pre_live_actual_venue_post_readiness_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=args.store_root,
            k1_backend=k1_backend,
        )
        print(json.dumps(proof, sort_keys=True))
        return 0 if proof.get("PRE_LIVE_PROOF_COMPLETE") == "true" else 2
    if args.confirm_real_venue_post is not True:
        print(
            "FAIL_CLOSED: pass --confirm-real-venue-post to authorize the single POST",
            file=sys.stderr,
        )
        return 2
    k1_backend = _resolve_k1_backend()
    if k1_backend is None:
        print(
            "FAIL_CLOSED: real POST requires --k1-backend macos",
            file=sys.stderr,
        )
        return 2
    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
        open_current_productive_k1_opaque_signing_handle_session_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )

    with open_current_productive_k1_opaque_signing_handle_session_v1(
        owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        backend=k1_backend,
    ) as session:
        read_transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=session.signing_handle,
            max_request_count=24,
        )
        result = execute_current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1(
            owner_go=OWNER_GO,
            baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
            envelope=envelope,
            store_root=args.store_root,
            evidence_root=args.evidence_root,
            perform_real_venue_post=True,
            k1_backend=k1_backend,
            opener_factory=None,
            read_only_get_transport=read_transport,
        )
    print(
        json.dumps(
            {
                "POST_OUTCOME": result.post_outcome,
                "REAL_VENUE_POST_PERFORMED": result.real_venue_post_performed,
                "EVIDENCE_ROOT": result.evidence_root,
                "MANIFEST_VERIFY_RC": result.manifest_verify_rc,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
