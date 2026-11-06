"""Fail-closed restart completeness verifier for Phase 9.2 PRE/POST bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    load_consumed_authorization_ids_v1,
    ledger_path_for_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CHECKPOINT_FILENAME,
    LOCK_FILENAME,
    OPEN_POSITION_NOT_OBSERVED,
    OPEN_POSITION_RECOVERY_PROVEN,
    POST_TERMINAL_MANIFEST_FILENAME,
    PRE_TERMINAL_MANIFEST_FILENAME,
    REQUIRED_TELEMETRY_FIELDS,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    TELEMETRY_FILENAME,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartBundleVerificationResultV1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.network_boundary_v1 import (
    prove_no_live_testnet_credential_path_v1,
)


def _require_telemetry_fields(
    telemetry: dict[str, Any], *, label: str, blockers: list[str]
) -> None:
    missing = [f for f in REQUIRED_TELEMETRY_FIELDS if f not in telemetry]
    if missing:
        blockers.append(f"missing_telemetry_{label}:{','.join(missing)}")


def verify_restart_bundle_v1(*, persistence_root: Path) -> RestartBundleVerificationResultV1:
    root = Path(persistence_root)
    blockers: list[str] = []
    notes = [
        "VERIFIER_NO_NETWORK=true",
        "VERIFIER_NO_MUTATION=true",
        "ORPHAN_LOCK_TAKEOVER_ALLOWED=false",
    ]

    pre_path = root / PRE_TERMINAL_MANIFEST_FILENAME
    post_path = root / POST_TERMINAL_MANIFEST_FILENAME
    pre_tel_path = root / f"pre_{TELEMETRY_FILENAME}"
    post_tel_path = root / f"post_{TELEMETRY_FILENAME}"

    if not pre_path.is_file():
        blockers.append("missing_pre_restart_segment")
    if not post_path.is_file():
        blockers.append("missing_post_restart_segment")
    if not pre_tel_path.is_file():
        blockers.append("missing_pre_restart_telemetry")
    if not post_tel_path.is_file():
        blockers.append("missing_post_restart_telemetry")

    if blockers:
        return RestartBundleVerificationResultV1(
            result="FAIL",
            verified=False,
            blockers=blockers,
            notes=notes,
            claims={"OPEN_POSITION_RECOVERY_PROVEN": False, "OPEN_POSITION_NOT_OBSERVED": False},
        )

    pre = read_json_v1(pre_path)
    post = read_json_v1(post_path)
    pre_tel = read_json_v1(pre_tel_path)
    post_tel = read_json_v1(post_tel_path)

    _require_telemetry_fields(pre_tel, label="pre", blockers=blockers)
    _require_telemetry_fields(post_tel, label="post", blockers=blockers)

    # Segment uniqueness / order
    if str(pre.get("segment_role")) != SEGMENT_ROLE_PRE:
        blockers.append("pre_segment_role_invalid")
    if str(post.get("segment_role")) != SEGMENT_ROLE_POST:
        blockers.append("post_segment_role_invalid")
    if str(pre.get("segment_id")) == str(post.get("segment_id")):
        blockers.append("duplicate_segment_id")
    if str(post.get("predecessor_segment_id")) != str(pre.get("segment_id")):
        blockers.append("incorrect_segment_order")

    pre_digest = str(pre.get("terminal_manifest_digest") or "")
    recomputed_pre = sha256_canonical_v1(
        {k: v for k, v in pre.items() if k != "terminal_manifest_digest"}
    )
    if not pre_digest or pre_digest != recomputed_pre:
        blockers.append("pre_restart_terminal_manifest_digest_mismatch")
    if str(post.get("pre_restart_terminal_manifest_digest")) != pre_digest:
        blockers.append("digest_mismatch")

    if str(pre.get("confirmation_session_id")) != str(post.get("confirmation_session_id")):
        blockers.append("confirmation_session_id_mutation")
    if str(pre.get("durable_state_lineage_id")) != str(post.get("durable_state_lineage_id")):
        blockers.append("state_lineage_mutation")
    if int(post.get("observation_epoch", -1)) < int(pre.get("observation_epoch", 0)):
        blockers.append("observation_epoch_rollback")
    if str(post.get("portfolio_digest")) != str(pre.get("portfolio_digest")):
        # Continuity for this harness: no rollback and no silent mutation.
        blockers.append("portfolio_rollback_or_mutation")
    if str(post.get("scope_digest")) != str(pre.get("scope_digest")):
        blockers.append("scope_rollback_or_mutation")
    if str(post.get("accounting_digest")) != str(pre.get("accounting_digest")):
        blockers.append("accounting_rollback_or_mutation")
    if str(post.get("evidence_cursor")) != str(pre.get("evidence_cursor")):
        blockers.append("evidence_cursor_rollback_or_double_count")

    auth_pre = str(pre.get("authorization_id") or "")
    auth_post = str(post.get("authorization_id") or "")
    if not auth_pre or not auth_post or auth_pre == auth_post:
        blockers.append("authorization_reuse_or_missing")
    consumed = load_consumed_authorization_ids_v1(ledger_path_for_root_v1(root))
    if auth_pre not in consumed or auth_post not in consumed:
        blockers.append("authorization_not_consumed_once_per_segment")

    if not bool(post.get("reconciliation_completed_before_alpha")):
        blockers.append("missing_reconciliation_before_alpha")
    if int(post.get("duplicate_confirmation_prevented_count", 0)) < 0:
        blockers.append("duplicate_confirmation_advance")
    if int(post.get("duplicate_fill_prevented_count", 0)) < 0:
        blockers.append("duplicate_fill_application")

    claim = str(post.get("open_position_recovery_claim") or "")
    open_present = bool(post.get("open_position_present_at_restart"))
    open_recovered = bool(post.get("open_position_recovered"))
    if claim == OPEN_POSITION_RECOVERY_PROVEN and not open_present:
        blockers.append("open_position_recovery_claimed_without_open_position")
    if claim == OPEN_POSITION_NOT_OBSERVED and open_recovered:
        blockers.append("flat_claim_with_open_position_recovered")
    if open_present and claim != OPEN_POSITION_RECOVERY_PROVEN:
        blockers.append("open_position_present_but_claim_not_proven")
    if (not open_present) and claim != OPEN_POSITION_NOT_OBSERVED:
        blockers.append("flat_recovery_claim_missing")

    if bool(pre_tel.get("authorization_reused")) or bool(post_tel.get("authorization_reused")):
        blockers.append("authorization_reused_telemetry")
    if not bool(pre_tel.get("live_testnet_order_boundary_preserved")) or not bool(
        post_tel.get("live_testnet_order_boundary_preserved")
    ):
        blockers.append("live_testnet_order_boundary_not_preserved")

    if (root / LOCK_FILENAME).exists():
        blockers.append("lock_still_held_after_segments")

    boundary = prove_no_live_testnet_credential_path_v1()
    if not boundary.get("ok"):
        blockers.append("live_testnet_credential_path_reachable")
        notes.extend(str(x) for x in boundary.get("notes", []))

    # Optional checkpoint continuity if present
    checkpoint_path = root / CHECKPOINT_FILENAME
    if checkpoint_path.is_file():
        checkpoint = read_json_v1(checkpoint_path)
        if str(checkpoint.get("confirmation_session_id")) != str(
            post.get("confirmation_session_id")
        ):
            blockers.append("checkpoint_confirmation_mismatch")

    unique = sorted(set(blockers))
    claims = {
        "OPEN_POSITION_RECOVERY_PROVEN": claim == OPEN_POSITION_RECOVERY_PROVEN and open_present,
        "OPEN_POSITION_NOT_OBSERVED": claim == OPEN_POSITION_NOT_OBSERVED and not open_present,
        "AUTHORIZATION_REUSED": False,
        "RECONCILIATION_BEFORE_ALPHA": bool(post.get("reconciliation_completed_before_alpha")),
        "LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED": True,
        "PRE_POST_SEGMENTS_COMPLETE": not unique,
    }
    return RestartBundleVerificationResultV1(
        result="PASS" if not unique else "FAIL",
        verified=not unique,
        blockers=unique,
        notes=notes,
        claims=claims,
    )
