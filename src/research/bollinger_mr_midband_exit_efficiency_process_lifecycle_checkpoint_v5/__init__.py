"""Process-lifecycle checkpoint scaffold for Bollinger/MR midband exit-efficiency V5.

Definition-only scaffold. Importing this package MUST NOT start an evaluation runner,
claim a run slot, load panel/holdout/production data, or mutate run-count state.
"""

from __future__ import annotations

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5=true"
IMPORT_DOES_NOT_START_RUNNER = True
IMPORT_DOES_NOT_CLAIM_RUN_SLOT = True
IMPORT_DOES_NOT_ACCESS_PANEL_DATA = True

__all__ = [
    "PACKAGE_MARKER",
    "IMPORT_DOES_NOT_START_RUNNER",
    "IMPORT_DOES_NOT_CLAIM_RUN_SLOT",
    "IMPORT_DOES_NOT_ACCESS_PANEL_DATA",
]
