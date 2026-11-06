"""Retained cursor publication material inside the existing Exit state owner.

This detects a mixed pair and permits explicit exact cursor publication, without
replaying a decision or claiming a transaction across all decision-path owners.
"""

from dataclasses import asdict
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1
from src.ops.exit_policy_producer_binding_v1.single_writer_v1 import ExitPolicySingleWriterV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    current_productive_cursor_digest_v1,
    load_current_productive_sidestate_confirmation_cursor_v1,
    persist_current_productive_sidestate_confirmation_cursor_v1,
    restore_current_productive_sidestate_confirmation_cursor_v1,
)

SCHEMA = "exit_owned_current_cursor_publication.v1"


def _root(root):
    if root is None or not Path(root).is_absolute():
        raise ValueError("POSITION_EPISODE_CURSOR_ROOT_REQUIRED")
    return str(Path(root).resolve())


def build_current_cursor_publication_v1(*, episode, incoming, outgoing, store_root):
    return {
        "schema": SCHEMA,
        "identity": asdict(episode.identity),
        "cursor_root": _root(store_root),
        "prior_exit_sequence": episode.binding.commit_sequence,
        "incoming_digest": current_productive_cursor_digest_v1(incoming),
        "outgoing_digest": current_productive_cursor_digest_v1(outgoing),
        "outgoing_payload": outgoing.to_dict(),
    }


def _validated_publication(episode, store_root):
    record = episode.binding.current_cursor_publication
    if record is None:
        return None
    expected = {
        "schema",
        "identity",
        "cursor_root",
        "prior_exit_sequence",
        "incoming_digest",
        "outgoing_digest",
        "outgoing_payload",
    }
    if (
        not isinstance(record, dict)
        or set(record) != expected
        or record["schema"] != SCHEMA
        or record["identity"] != asdict(episode.identity)
        or record["cursor_root"] != _root(store_root)
        or type(record["prior_exit_sequence"]) is not int
        or record["prior_exit_sequence"] + 1 != episode.binding.commit_sequence
        or not isinstance(record["incoming_digest"], str)
        or len(record["incoming_digest"]) != 64
        or record["outgoing_digest"]
        != current_productive_cursor_digest_v1(record["outgoing_payload"])
    ):
        raise ValueError("POSITION_EPISODE_CURSOR_BINDING_INVALID")
    restored = restore_current_productive_sidestate_confirmation_cursor_v1(
        record["outgoing_payload"],
        expected_instrument_id=episode.identity.instrument_id,
        expected_venue_native_id=episode.identity.venue_native_id,
        venue_flat=False,
    )
    if (
        restored.disposition.value != "restored"
        or restored.cursor.existing_scope is None
        or restored.cursor.to_dict() != record["outgoing_payload"]
    ):
        raise ValueError("POSITION_EPISODE_CURSOR_PAYLOAD_INVALID")
    return record, restored.cursor


def require_current_cursor_continuity_v1(*, episode, incoming, store_root):
    _root(store_root)
    publication = _validated_publication(episode, store_root)
    if publication is not None and (
        current_productive_cursor_digest_v1(incoming) != publication[0]["outgoing_digest"]
    ):
        raise ValueError("POSITION_EPISODE_CURSOR_RECOVERY_REQUIRED")


def recover_current_cursor_publication_v1(
    *, episode, store_root, expected_scope, writer_session_id
):
    """Explicitly finish only a retained publication; never recalculate a decision.

    Refuses a stale handle, changed/missing current cursor, foreign root/scope or
    invalid retained state. No Exit reset, lifecycle adoption or alpha invocation.
    """
    episode.identity.validate_v1()
    if expected_scope != episode.identity.account_scope:
        raise ValueError("POSITION_EPISODE_ACCOUNT_SCOPE_MISMATCH")
    if episode.binding.alpha_blocked or not episode.binding.state_root:
        raise ValueError("POSITION_EPISODE_EXIT_BINDING_BLOCKED")
    _root(store_root)
    with ExitPolicySingleWriterV1(
        Path(episode.binding.state_root), writer_session_id=writer_session_id
    ):
        state = load_exit_policy_state_v1(
            Path(episode.binding.state_root),
            expected_repository_sha=episode.binding.repository_sha,
            expected_config_digest=episode.binding.config_digest,
            expected_instrument_id=episode.identity.instrument_id,
        )
        if state.to_dict() != episode.binding.to_canonical_state().to_dict():
            raise ValueError("POSITION_EPISODE_RECOVERY_STALE_HANDLE")
        publication = _validated_publication(episode, store_root)
        if publication is None:
            raise ValueError("POSITION_EPISODE_CURSOR_RECOVERY_UNAVAILABLE")
        record, cursor = publication
        current = load_current_productive_sidestate_confirmation_cursor_v1(Path(store_root))
        digest = current_productive_cursor_digest_v1(current)
        if digest == record["outgoing_digest"]:
            return {"status": "ALREADY_PUBLISHED", "cursor_digest": digest}
        if digest != record["incoming_digest"]:
            raise ValueError("POSITION_EPISODE_CURSOR_PUBLICATION_CONFLICT")
        persist_current_productive_sidestate_confirmation_cursor_v1(
            cursor, store_root=Path(store_root), expected_prior_digest=record["incoming_digest"]
        )
        return {"status": "PUBLISHED_RETAINED_CURSOR", "cursor_digest": record["outgoing_digest"]}
