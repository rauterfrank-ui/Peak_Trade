"""Constants for generic evaluation-runner lifecycle observability v1."""

from __future__ import annotations

SCHEMA_VERSION = "evaluation_runner_lifecycle_observability.v1"
HEARTBEAT_FILENAME = "runner_lifecycle_heartbeat.json"
PROGRESS_FILENAME = "runner_lifecycle_progress.json"
TERMINAL_DIAGNOSTICS_FILENAME = "runner_lifecycle_terminal_diagnostics.json"
EXCEPTION_FILENAME = "runner_lifecycle_exception.json"

RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE = "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
INCONCLUSIVE_INFRASTRUCTURE_FAILURE = RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE

PHASE_INIT = "init"
PHASE_MEMBER = "member"
PHASE_PERSIST = "persist"
PHASE_COMPLETE = "complete"
PHASE_TERMINAL_FAILURE = "terminal_failure"

MAX_TRACEBACK_CHARS = 4000
MAX_EXCEPTION_MESSAGE_CHARS = 512
MAX_MEMBER_ID_CHARS = 128

# No automatic resume / rerun under this observability surface.
AUTO_RERUN_ALLOWED = False
AUTO_RESUME_ALLOWED = False
