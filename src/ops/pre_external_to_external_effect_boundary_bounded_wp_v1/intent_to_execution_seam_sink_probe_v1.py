"""Forensic sink probes for intent_to_execution seam (no POST, no permit mint)."""

from __future__ import annotations

from typing import Final

from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    FullCoreEnvelopeBoundSendSeamError,
    attempt_envelope_bound_external_effect_send_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    invoke_external_effect_v1,
)

PROBE_OWNER: Final[str] = (
    "ops.pre_external_to_external_effect_boundary_bounded_wp_v1."
    "intent_to_execution_seam_sink_probe_v1"
)


def probe_import_time_invoke_sink_v1() -> str:
    try:
        invoke_external_effect_v1(attempt_post=True)
        return "UNEXPECTED_PASS"
    except FullCoreExternalEffectNotAuthorizedError:
        return "FullCoreExternalEffectNotAuthorizedError"


def probe_envelope_bound_send_seam_without_permit_v1() -> str:
    try:
        attempt_envelope_bound_external_effect_send_v1(
            envelope=None,  # type: ignore[arg-type]
            permit=None,
            store_root=None,
            transport=None,
        )
        return "UNEXPECTED_PASS"
    except FullCoreEnvelopeBoundSendSeamError as exc:
        return str(exc) or type(exc).__name__
    except TypeError:
        return "NO_PERMIT"
