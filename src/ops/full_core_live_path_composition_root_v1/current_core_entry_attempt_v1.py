"""Fence retained Entries during a new durable Core evaluation, never advance Core."""

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from . import current_productive_sidestate_confirmation_cursor_v1 as original
from .current_core_entry_assessment_frame_v1 import UNCOMMITTED_ATTEMPT_SCHEMA


def begin_current_core_entry_attempt_v1(
    *, bound_instrument, store_root, cycle_id, incoming_cursor_override=None
):
    """Publish negative admission in the original cursor before invoking Core.

    Return the exact CAS predecessor for the final publication. Missing or
    invalid original state is not fabricated or repaired here: the existing
    restore/consumer contracts retain their original refusal behavior.
    """
    root = Path(store_root)
    raw = original.load_current_productive_sidestate_confirmation_cursor_v1(root)
    predecessor = original.current_productive_cursor_digest_v1(raw)
    if raw is None:
        return predecessor
    if (
        incoming_cursor_override is not None
        and original.current_productive_cursor_digest_v1(incoming_cursor_override) != predecessor
    ):
        raise original.CurrentProductiveCursorError("CURSOR_PUBLICATION_CONFLICT")
    restored = original.restore_current_productive_sidestate_confirmation_cursor_v1(
        raw,
        expected_instrument_id=bound_instrument.instrument_id,
        expected_venue_native_id=bound_instrument.venue_native_id,
        venue_flat=False,
    )
    if restored.cursor is None:
        return predecessor
    if type(cycle_id) is not str or not cycle_id.strip():
        raise ValueError("CURRENT_CORE_ENTRY_ATTEMPT_ID_REQUIRED")
    marker = dict(
        schema=UNCOMMITTED_ATTEMPT_SCHEMA,
        instrument_id=restored.cursor.instrument_id,
        venue_native_id=restored.cursor.venue_native_id,
        cycle_id=cycle_id,
        attempt_id=uuid4().hex,
        prior_cursor_digest=predecessor,
        status="EVALUATION_NOT_COMMITTED",
        runtime_authorization_effect="NONE",
    )
    pending = replace(restored.cursor, entry_assessment_frame=marker)
    original.persist_current_productive_sidestate_confirmation_cursor_v1(
        pending, store_root=root, expected_prior_digest=predecessor
    )
    return original.current_productive_cursor_digest_v1(pending)
