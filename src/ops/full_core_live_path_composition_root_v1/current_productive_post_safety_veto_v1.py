"""Current original FILEGATE veto for the explicit direct POST path.

This is a new read-only consumer of the existing durable reader, not a new
kill-state writer, send authorization, signed recovery or global claim ledger.
The selected original path and exact envelope stay pinned throughout a call.
Every check reads again; a previous ACTIVE read never authorizes a later send.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    read_durable_filegate_join_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.ops.managed_filegate_v1 import managed_filegate_configured_v1, read_configured_filegate_v1


class CurrentPostSafetyVetoError(ValueError):
    pass


@dataclass(frozen=True)
class CurrentPostSafetyContextV1:
    """References only: the exact original envelope and selected durable path."""

    envelope: FinalOrderEnvelopeV1
    state_path: str
    _managed_release: str | None = field(init=False, repr=False, compare=False, default=None)

    def __post_init__(self):
        if isinstance(self.state_path, str) and managed_filegate_configured_v1(self.state_path):
            current = read_configured_filegate_v1(self.state_path) or {}
            object.__setattr__(self, "_managed_release", current.get("filegate_release_sha256"))

    def inspect_v1(self, *, stage):
        assert_envelope_unmodified_v1(self.envelope)
        try:
            return self._inspect_current_v1(stage=stage)
        except OSError as exc:
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_READ_UNPROVEN:{stage}") from exc

    def _inspect_current_v1(self, *, stage):
        if (
            not isinstance(self.state_path, str)
            or str(Path(canonical_kill_switch_state_path()).resolve()) != self.state_path
        ):
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_SOURCE_CHANGED:{stage}")
        if os.environ.get("PEAK_KILL_SWITCH") == "1":
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_EMERGENCY_DENY:{stage}")
        evidence = read_durable_filegate_join_evidence_v1(state_path=self.state_path)
        if str(Path(canonical_kill_switch_state_path()).resolve()) != self.state_path:
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_SOURCE_CHANGED:{stage}")
        if os.environ.get("PEAK_KILL_SWITCH") == "1":
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_EMERGENCY_DENY:{stage}")
        if not (
            evidence.evidence_status == DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value
            and evidence.blocked is False
            and evidence.boolean_reader_blocked is False
            and evidence.state_name == "ACTIVE"
            and evidence.contradictory is False
            and evidence.env_overlay_used_as_durable_evidence is False
        ):
            raise CurrentPostSafetyVetoError(
                f"POST_SAFETY_DURABLE_VETO:{stage}:{evidence.evidence_status}:{evidence.state_name}"
            )
        if self._managed_release is not None or managed_filegate_configured_v1(self.state_path):
            current = read_configured_filegate_v1(self.state_path)
            if (
                current is None
                or self._managed_release is None
                or current.get("filegate_release_sha256") != self._managed_release
            ):
                raise CurrentPostSafetyVetoError(f"POST_SAFETY_FILEGATE_REVISION_CHANGED:{stage}")
        return evidence

    def inspect_wire_v1(self, *, payload, stage, envelope_id=None, envelope_digest=None):
        # Reuse the original exact envelope/body projection. Import here avoids
        # coupling the HTTP module's import initialization back to its own seam.
        from .envelope_bound_external_effect_send_seam_v1 import _payload_from_envelope_v1

        if (
            (envelope_id is not None and envelope_id != self.envelope.envelope_id)
            or (envelope_digest is not None and envelope_digest != self.envelope.envelope_digest)
            or dict(payload) != _payload_from_envelope_v1(self.envelope)
        ):
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_ENVELOPE_MISMATCH:{stage}")
        return self.inspect_v1(stage=stage)


def resolve_current_post_safety_context_v1(envelope, context=None, *, stage):
    assert_envelope_unmodified_v1(envelope)
    if context is None:
        try:
            context = CurrentPostSafetyContextV1(
                envelope=envelope,
                state_path=str(Path(canonical_kill_switch_state_path()).resolve()),
            )
        except OSError as exc:
            raise CurrentPostSafetyVetoError(f"POST_SAFETY_SOURCE_UNPROVEN:{stage}") from exc
    if type(context) is not CurrentPostSafetyContextV1 or context.envelope != envelope:
        raise CurrentPostSafetyVetoError(f"POST_SAFETY_CONTEXT_MISMATCH:{stage}")
    context.inspect_v1(stage=stage)
    return context
