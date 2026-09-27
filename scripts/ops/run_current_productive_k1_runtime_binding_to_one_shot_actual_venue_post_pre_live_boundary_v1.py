#!/usr/bin/env python3
"""Governed K1 PRE-POST runtime binding to one-shot POST pre-live boundary (no POST)."""

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
    parser = argparse.ArgumentParser(
        description="K1 PRE-POST binding to one-shot POST pre-live boundary"
    )
    parser.add_argument("--store-root", type=Path, required=True)
    parser.add_argument("--envelope-json", type=Path, required=True)
    parser.add_argument(
        "--k1-backend",
        choices=("none", "macos"),
        default="none",
        help="macos = MacosSecurityFrameworkLookupBackendV1 under ephemeral K1 scope",
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1 import (
        EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        K1_OPAQUE_SIGNING_OWNER_GO,
        POST_OWNER_GO,
        attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1,
    )

    envelope = _load_envelope(args.envelope_json)
    if args.k1_backend == "none":
        print(
            "FAIL_CLOSED: pass --k1-backend macos for real ephemeral Keychain lookup",
            file=sys.stderr,
        )
        return 2
    result = attempt_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1(
        k1_owner_go=K1_OPAQUE_SIGNING_OWNER_GO,
        post_owner_go=POST_OWNER_GO,
        baseline_origin_main_sha=EXPECTED_BASELINE_ORIGIN_MAIN_SHA,
        envelope=envelope,
        store_root=args.store_root,
        use_macos_security_framework=True,
        repo_root=REPO_ROOT,
    )
    print(json.dumps(result.to_public_dict_v1(), sort_keys=True))
    return 0 if result.pre_live_proof_complete == "true" else 2


if __name__ == "__main__":
    raise SystemExit(_main())
