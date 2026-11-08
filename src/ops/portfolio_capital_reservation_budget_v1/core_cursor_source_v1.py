"""Original Core cursor and current entry-state vetoes, never a fresh decision."""

from pathlib import Path

from .durable_store_v1 import digest

SCHEMA = "portfolio_original_core_cursor_source.v1"
C3_SCHEMA = "portfolio_original_core_cursor_source.v2"
_FIELDS = {
    "schema",
    "cursor_root",
    "instrument_id",
    "native_id",
    "decision_id",
    "core_parent_digest",
    "trading_epoch",
    "source_cursor_digest",
    "digest",
}


def _read_original_cursor(root, *, instrument_id, native_id):
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_sidestate_confirmation_cursor_v1 as original,
    )

    payload = original.load_current_productive_sidestate_confirmation_cursor_v1(Path(root))
    if payload is None:
        raise ValueError("CURRENT_CORE_CURSOR_MISSING")
    cursor = original.parse_current_productive_sidestate_confirmation_cursor_v1(payload)
    if (
        cursor.schema_name != original.CURSOR_SCHEMA_NAME
        or cursor.schema_version != original.CURSOR_SCHEMA_VERSION
        or cursor.lineage_id != original.CURSOR_LINEAGE_ID
        or cursor.instrument_id != instrument_id
        or cursor.venue_native_id != native_id
        or cursor.confirmation_epochs != original.CANONICAL_CONFIRMATION_EPOCHS
        or (
            cursor.existing_scope is not None
            and cursor.existing_scope.instrument_id != instrument_id
        )
        or (
            cursor.cap61_confirmation_state is not None
            and cursor.cap61_confirmation_state.instrument_id != instrument_id
        )
    ):
        raise ValueError("CURRENT_CORE_CURSOR_IDENTITY_MISMATCH")
    # Original cursor's internal structural constraints, without inventing a
    # new wall-clock age, epoch-equality or venue-flat assertion.
    if (
        cursor.trading_epoch < 1
        or not 0 <= cursor.last_evaluated_trading_epoch < cursor.trading_epoch
        or cursor.now_tick < 1
        or not 0
        <= cursor.scope_confirmation.last_evaluated_trading_epoch
        <= cursor.last_evaluated_trading_epoch
    ):
        raise ValueError("CURRENT_CORE_CURSOR_STATE_UNPROVEN")
    return cursor, original.current_productive_cursor_digest_v1(payload), payload


def bind_core_cursor_source_v1(parent, cursor_root, intent):
    from trading.master_v2.canonical_trading_decision_evidence_v1 import (
        CanonicalTradingDecisionEvidenceV1,
        compute_canonical_trading_decision_evidence_semantic_digest,
    )

    if (
        type(parent) is not CanonicalTradingDecisionEvidenceV1
        or parent.semantic_digest
        != compute_canonical_trading_decision_evidence_semantic_digest(parent)
        or parent.decision_id != intent.decision_id
        or parent.instrument_id != intent.instrument_id
        or type(parent.trading_epoch) is not int
        or intent.trading_epoch != str(parent.trading_epoch)
        or parent.order_intent_ref != intent.semantic_digest
        or parent.execution_eligible is not False
        or parent.adapter_compatible is not False
        or parent.authority_effect != "NONE"
        or parent.runtime_effect != "NONE"
        or parent.order_effect != "NONE"
    ):
        raise ValueError("ORIGINAL_CORE_CURSOR_DECISION_PARENT_MISMATCH")
    if not isinstance(cursor_root, (str, Path)) or not str(cursor_root):
        raise ValueError("ORIGINAL_CORE_CURSOR_ROOT_REQUIRED")
    root = str(Path(cursor_root).resolve())
    # Native identity comes from the original cursor; the plan validator binds
    # it independently to the unchanged native envelope before any write.
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_sidestate_confirmation_cursor_v1 as original,
    )

    raw = original.load_current_productive_sidestate_confirmation_cursor_v1(Path(root))
    if raw is None:
        raise ValueError("CURRENT_CORE_CURSOR_MISSING")
    native = raw.get("venue_native_id")
    cursor, checksum, _ = _read_original_cursor(
        root, instrument_id=parent.instrument_id, native_id=native
    )
    from .core_confirmation_source_v1 import bind_core_confirmation_lineage_v1

    payload = dict(
        schema=C3_SCHEMA,
        cursor_root=root,
        instrument_id=parent.instrument_id,
        native_id=native,
        decision_id=parent.decision_id,
        core_parent_digest=parent.semantic_digest,
        trading_epoch=parent.trading_epoch,
        source_cursor_digest=checksum,
        confirmation_lineage=bind_core_confirmation_lineage_v1(cursor),
    )
    return {**payload, "digest": digest(payload)}


def validate_core_cursor_source_v1(source, *, intent, native_id):
    if (
        not isinstance(source, dict)
        or source.get("schema") not in {SCHEMA, C3_SCHEMA}
        or set(source)
        != _FIELDS | ({"confirmation_lineage"} if source.get("schema") == C3_SCHEMA else set())
        or source["digest"] != digest({k: v for k, v in source.items() if k != "digest"})
        or any(
            type(source[k]) is not str or not source[k] or source[k] != source[k].strip()
            for k in _FIELDS - {"trading_epoch"}
        )
        or not Path(source["cursor_root"]).is_absolute()
        or str(Path(source["cursor_root"]).resolve()) != source["cursor_root"]
        or source["decision_id"] != intent.decision_id
        or source["instrument_id"] != intent.instrument_id
        or source["native_id"] != native_id
        or type(source["trading_epoch"]) is not int
        or str(source["trading_epoch"]) != intent.trading_epoch
        or any(
            len(source[k]) != 64 or any(c not in "0123456789abcdef" for c in source[k])
            for k in ["core_parent_digest", "source_cursor_digest"]
        )
    ):
        raise ValueError("ORIGINAL_CORE_CURSOR_SOURCE_INVALID")
    if source["schema"] == C3_SCHEMA:
        from .core_confirmation_source_v1 import validate_core_confirmation_lineage_v1

        validate_core_confirmation_lineage_v1(
            source["confirmation_lineage"], instrument_id=intent.instrument_id
        )


def inspect_current_core_cursor_v1(source, *, intent_side):
    from trading.master_v2.double_play_state import SideState
    from trading.master_v2.double_play_entry_exit_policy_v0 import (
        EntryExitDirectionState,
        _direction_armed_for_entry,
    )
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        _side_state_to_entry_exit_direction,
    )
    from trading.master_v2.chop_scope_event_policy_binding_v1 import (
        project_composition_chop_guard_from_scope_policy_v1,
    )
    from trading.master_v2.double_play_composition_matrix_v1 import CompositionChopGuardStatus

    cursor, checksum, raw = _read_original_cursor(
        source["cursor_root"], instrument_id=source["instrument_id"], native_id=source["native_id"]
    )
    # Preserve the previous explicit KILL_ALL veto's precedence.
    if cursor.side_state is SideState.KILL_ALL:
        raise ValueError("CURRENT_CORE_CURSOR_KILL_ALL")
    runtime_scope = raw.get("runtime_scope_state")
    if not isinstance(runtime_scope, dict) or type(runtime_scope.get("chop_latched")) is not bool:
        # The general restore adapter's bool conversion is not proof that an
        # absent/null/numeric/string value means an inactive current CHOP latch.
        raise ValueError("CURRENT_CORE_SCOPE_POLICY_UNPROVEN")
    chop = project_composition_chop_guard_from_scope_policy_v1(
        chop_latched=runtime_scope["chop_latched"]
    )
    if chop == CompositionChopGuardStatus.CHOP_GUARD_BLOCK.value:
        raise ValueError("CURRENT_CORE_SCOPE_CHOP_BLOCK")
    direction = _side_state_to_entry_exit_direction(cursor.side_state)
    if not _direction_armed_for_entry(direction):
        raise ValueError("CURRENT_CORE_ENTRY_DIRECTION_NOT_ARMED")
    if intent_side not in {"LONG", "SHORT"}:
        raise ValueError("CURRENT_CORE_ORIGINAL_ENTRY_SIDE_UNPROVEN")
    expected = (
        EntryExitDirectionState.LONG_ARMED
        if intent_side == "LONG"
        else EntryExitDirectionState.SHORT_ARMED
    )
    if direction is not expected:
        raise ValueError("CURRENT_CORE_ENTRY_DIRECTION_MISMATCH")
    confirmation = {"scope": "LEGACY_ORIGINAL_C3_NOT_ASSESSED"}
    if source["schema"] == C3_SCHEMA:
        from .core_confirmation_source_v1 import inspect_current_core_confirmation_v1

        confirmation = inspect_current_core_confirmation_v1(
            source["confirmation_lineage"], cursor=cursor, raw=raw, intent_side=intent_side
        )
    return dict(
        scope="CURRENT_ORIGINAL_CORE_ENTRY_STATE_VETOES_ONLY",
        current_side_state=cursor.side_state.value,
        direction_state=direction.value,
        original_intent_side=intent_side,
        chop_guard_status=chop,
        cursor_digest=checksum,
        source_cursor_digest=source["source_cursor_digest"],
        confirmation=confirmation,
        runtime_authorization_effect="NONE",
    )
