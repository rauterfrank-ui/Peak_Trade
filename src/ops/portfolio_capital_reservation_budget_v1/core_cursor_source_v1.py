"""Original Core cursor lineage and current KILL_ALL veto, never a fresh decision."""

from pathlib import Path

from .durable_store_v1 import digest

SCHEMA = "portfolio_original_core_cursor_source.v1"
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
    return cursor, original.current_productive_cursor_digest_v1(payload)


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
    _, checksum = _read_original_cursor(root, instrument_id=parent.instrument_id, native_id=native)
    payload = dict(
        schema=SCHEMA,
        cursor_root=root,
        instrument_id=parent.instrument_id,
        native_id=native,
        decision_id=parent.decision_id,
        core_parent_digest=parent.semantic_digest,
        trading_epoch=parent.trading_epoch,
        source_cursor_digest=checksum,
    )
    return {**payload, "digest": digest(payload)}


def validate_core_cursor_source_v1(source, *, intent, native_id):
    if (
        not isinstance(source, dict)
        or set(source) != _FIELDS
        or source["schema"] != SCHEMA
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


def inspect_current_core_cursor_v1(source):
    from trading.master_v2.double_play_state import SideState

    cursor, checksum = _read_original_cursor(
        source["cursor_root"], instrument_id=source["instrument_id"], native_id=source["native_id"]
    )
    # This is the original Core replay's explicit KILL_ALL predicate. Other
    # current Core, scope, market and numerical-risk predicates are not renewed.
    if cursor.side_state is SideState.KILL_ALL:
        raise ValueError("CURRENT_CORE_CURSOR_KILL_ALL")
    return dict(
        scope="CURRENT_ORIGINAL_CORE_KILL_ALL_VETO_ONLY",
        cursor_digest=checksum,
        source_cursor_digest=source["source_cursor_digest"],
        runtime_authorization_effect="NONE",
    )
