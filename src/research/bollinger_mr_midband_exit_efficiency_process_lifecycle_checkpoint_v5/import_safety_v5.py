"""Explicit evidence that definition import/validation cannot start the V5 runner."""

from __future__ import annotations

from typing import Any

# Import-time side-effect flags (must remain false forever for definition-only safety).
RUNNER_STARTED_AT_IMPORT = False
RUN_SLOT_CLAIMED_AT_IMPORT = False
EVALUATION_EXECUTED_AT_IMPORT = False
PANEL_DATA_ACCESSED_AT_IMPORT = False
HOLDOUT_DATA_ACCESSED_AT_IMPORT = False
PRODUCTION_DATA_ACCESSED_AT_IMPORT = False


def import_safety_attestation_v5() -> dict[str, Any]:
    return {
        "runner_started_at_import": RUNNER_STARTED_AT_IMPORT,
        "run_slot_claimed_at_import": RUN_SLOT_CLAIMED_AT_IMPORT,
        "evaluation_executed_at_import": EVALUATION_EXECUTED_AT_IMPORT,
        "panel_data_accessed_at_import": PANEL_DATA_ACCESSED_AT_IMPORT,
        "holdout_data_accessed_at_import": HOLDOUT_DATA_ACCESSED_AT_IMPORT,
        "production_data_accessed_at_import": PRODUCTION_DATA_ACCESSED_AT_IMPORT,
        "definition_only_import_safe": True,
    }


def assert_no_runner_entrypoint_on_import() -> None:
    attestation = import_safety_attestation_v5()
    for key, value in attestation.items():
        if key == "definition_only_import_safe":
            if value is not True:
                raise RuntimeError("DEFINITION_IMPORT_NOT_SAFE")
            continue
        if value is not False:
            raise RuntimeError(f"IMPORT_SIDE_EFFECT:{key}")
