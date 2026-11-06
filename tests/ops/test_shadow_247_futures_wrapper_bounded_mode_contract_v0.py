"""Future Shadow 24/7 Futures wrapper bounded-mode contract — tests-only v0.

Documents the ``--bounded-runtime-contract-check`` slice implemented as a **non-executing**
placeholder in the skeleton wrapper (local evidence only). This module does **not**
approve runtime, daemon, scheduler, paper, shadow, testnet, or live workloads.

Reads repository anchors as **text/TOML** only (offline).
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef, import-not-found]

from tests.ops.test_shadow_247_futures_bounded_runtime_contract_v0 import (
    ABORT_STOP_CRITERIA_REQUIRED,
    BOUNDED_RUNTIME_CONTRACT_APPROVES_EXECUTION,
    BOUNDED_RUNTIME_CONTRACT_VERSION,
    BOUNDED_RUN_REQUIRED_BEFORE_TWENTYFOUR_SEVEN,
    BTCUSDT_FUTURES_PERPETUAL_SCOPE_EXPLICIT_REQUIRED,
    DRY_RUN_SHADOW_ONLY_POSTURE_REQUIRED,
    DURATION_CAP_REQUIRED,
    EVIDENCE_ROOT_CONVENTION_SUBSTRING,
    FINAL_OPERATOR_CONFIRMATION_TOKEN_REQUIRED,
    HEARTBEAT_OR_STEP_EVIDENCE_REQUIRED_IF_RUNTIME_INTRODUCED,
    MANIFEST_FILENAME_REQUIRED,
    MANIFEST_SHA256_FILENAME_REQUIRED,
    MARKDOWN_CLOSEOUT_FILENAME_REQUIRED,
    NEW_72H_BASELINE_REQUIRED_BEFORE_FIRST_BOUNDED_FUTURES_SHADOW,
    NO_BROKER,
    NO_CREDENTIALS,
    NO_EXCHANGE_PRIVATE_ENDPOINT,
    NO_LIVE,
    NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_APPROVED,
    NO_ORDER_SUBMISSION,
    NO_TESTNET_UNLESS_SEPARATELY_APPROVED,
    OLD_EVIDENCE_REUSE_POLICY_V0,
    RECOMMENDED_FIRST_BOUNDED_DURATION_BAND,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

WRAPPER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "shadow_247_futures_start_wrapper_skeleton_v0.py"
OPS_CONFIG = REPO_ROOT / "config" / "ops" / "shadow_247_futures_wrapper_skeleton.toml"
JOBS_CONFIG = REPO_ROOT / "config" / "scheduler" / "jobs.toml"

TEST_OWNER_WRAPPER = (
    REPO_ROOT / "tests" / "ops" / "test_shadow_247_futures_start_wrapper_skeleton_v0.py"
)
TEST_OWNER_CONFIG_JOB = (
    REPO_ROOT / "tests" / "ops" / "test_shadow_247_futures_config_job_skeleton_v0.py"
)
TEST_OWNER_EXECUTABLE_CONTRACT = (
    REPO_ROOT / "tests" / "ops" / "test_shadow_247_futures_executable_start_path_contract_v0.py"
)
TEST_OWNER_BOUNDED_RUNTIME = (
    REPO_ROOT / "tests" / "ops" / "test_shadow_247_futures_bounded_runtime_contract_v0.py"
)

# -----------------------------------------------------------------------------
# Required future bounded-mode contract markers (1–33) — not runtime authority
# -----------------------------------------------------------------------------

# 1 — future CLI entry for bounded contract evidence (implementation deferred).
FUTURE_BOUNDED_MODE_CLI_FLAG = "--bounded-runtime-contract-check"

# 2 — duration must be supplied on the future bounded CLI.
FUTURE_BOUNDED_MODE_DURATION_MINUTES_FLAG = "--duration-minutes"

# 3 — first bounded band aligns with bounded-runtime contract v0.
ALLOWED_FIRST_BOUNDED_DURATION_RANGE = RECOMMENDED_FIRST_BOUNDED_DURATION_BAND

# 4 — imported as ``DURATION_CAP_REQUIRED`` (must remain true).

# 5 — evidence root must follow ``/tmp/peak_trade_*`` operator convention.
FUTURE_BOUNDED_MODE_EVIDENCE_ROOT_CONVENTION = EVIDENCE_ROOT_CONVENTION_SUBSTRING

# 6–7 — canonical relative paths for read-only validation on the future bounded CLI.
FUTURE_BOUNDED_MODE_REQUIRED_OPS_CONFIG_REL = "config/ops/shadow_247_futures_wrapper_skeleton.toml"
FUTURE_BOUNDED_MODE_REQUIRED_JOBS_CONFIG_REL = "config/scheduler/jobs.toml"

# 8–9 — reuse skeleton ``--confirm-token`` + verbatim operator literal (wrapper anchor).
FUTURE_BOUNDED_MODE_CONFIRM_TOKEN_FLAG = "--confirm-token"
FUTURE_FINAL_OPERATOR_TOKEN_LITERAL = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
)

# 10 — this contract never confers execution approval.
WRAPPER_BOUNDED_MODE_CONTRACT_APPROVES_EXECUTION = False

# 11 — skeleton must remain fail-closed until separate gates exist.
BOUNDED_MODE_DEFAULT_FAIL_CLOSED_REQUIRED = True

# 12–23 — required absences for this tests-only bounded-mode slice.
NO_SCHEDULER_START_REQUIRED = True
NO_RUNTIME_START_REQUIRED = True
NO_DAEMON_START_REQUIRED = True
NO_PAPER_RUN_REQUIRED = True
NO_SHADOW_RUN_YET_REQUIRED = True
NO_TESTNET_IN_THIS_MODE_REQUIRED = True
NO_LIVE_IN_THIS_MODE_REQUIRED = True
NO_BROKER_IN_THIS_MODE_REQUIRED = True
NO_EXCHANGE_PRIVATE_ENDPOINT_IN_THIS_MODE_REQUIRED = True
NO_ORDER_SUBMISSION_IN_THIS_MODE_REQUIRED = True
NO_CREDENTIALS_IN_THIS_MODE_REQUIRED = True
NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_LATER_REQUIRED = True

# 24–28 — posture / evidence shape (aligned with bounded-runtime contract v0).
# (24) ``DRY_RUN_SHADOW_ONLY_POSTURE_REQUIRED`` imported.
# (25) ``BTCUSDT_FUTURES_PERPETUAL_SCOPE_EXPLICIT_REQUIRED`` imported.
# (26) prestart drycheck artifact triple — filenames imported from bounded-runtime owner.
# (27) Heartbeat/step evidence only after a future runtime exists.
# (28) ``ABORT_STOP_CRITERIA_REQUIRED`` imported.

# 29–32 — evidence reuse + sequencing (imported / asserted on policy text).
# 33 — ``WRAPPER_BOUNDED_MODE_CONTRACT_APPROVES_EXECUTION`` must stay false.


def _wrapper_source() -> str:
    assert WRAPPER_SCRIPT.is_file()
    return WRAPPER_SCRIPT.read_text(encoding="utf-8", errors="replace")


def _load_ops() -> dict:
    assert OPS_CONFIG.is_file()
    return tomllib.loads(OPS_CONFIG.read_text(encoding="utf-8"))


def test_prerequisite_bounded_mode_repo_surfaces_exist_v0() -> None:
    assert WRAPPER_SCRIPT.is_file()
    assert OPS_CONFIG.is_file()
    assert JOBS_CONFIG.is_file()
    assert TEST_OWNER_BOUNDED_RUNTIME.is_file()
    assert TEST_OWNER_CONFIG_JOB.is_file()
    assert TEST_OWNER_WRAPPER.is_file()
    assert TEST_OWNER_EXECUTABLE_CONTRACT.is_file()


def test_wrapper_source_has_fail_closed_and_prestart_cli_markers_v0() -> None:
    src = _wrapper_source()
    assert "--prestart-evidence-drycheck" in src
    assert "--bounded-shadow-dry-run" in src
    assert "--extended-bounded-shadow-validation" in src
    assert "--extended-confirm-token" in src
    assert "EXTENDED_BOUNDED_SHADOW_CONFIRM_TOKEN_V0" in src
    assert "--candidate-24h-bounded-shadow-validation" in src
    assert "--candidate-24h-confirm-token" in src
    assert "CANDIDATE_24H_BOUNDED_SHADOW_CONFIRM_TOKEN_V0" in src
    assert "--step-interval-seconds" in src
    assert "--evidence-root" in src
    assert "--config" in src
    assert "--jobs-config" in src
    assert FUTURE_BOUNDED_MODE_CONFIRM_TOKEN_FLAG in src
    assert "EXIT_CODE_FAIL_CLOSED" in src or "EXIT_FAIL_CLOSED" in src
    assert "64" in src
    assert "RUN_STARTED=false" in src
    assert "SCHEDULER_STARTED=false" in src
    assert "RUNTIME_STARTED=false" in src
    assert FUTURE_FINAL_OPERATOR_TOKEN_LITERAL in src
    assert MARKDOWN_CLOSEOUT_FILENAME_REQUIRED in src
    assert MANIFEST_FILENAME_REQUIRED in src
    assert MANIFEST_SHA256_FILENAME_REQUIRED in src


def test_future_bounded_mode_contract_constants_internal_consistency_v0() -> None:
    """Markers 1–33: boolean bundle and CLI constants stay internally consistent."""
    assert FUTURE_BOUNDED_MODE_CLI_FLAG.startswith("--")
    assert FUTURE_BOUNDED_MODE_DURATION_MINUTES_FLAG == "--duration-minutes"
    assert ALLOWED_FIRST_BOUNDED_DURATION_RANGE == "10-30min"
    assert DURATION_CAP_REQUIRED is True
    assert FUTURE_BOUNDED_MODE_EVIDENCE_ROOT_CONVENTION == "/tmp/peak_trade_"
    rel_ops = Path(FUTURE_BOUNDED_MODE_REQUIRED_OPS_CONFIG_REL)
    rel_jobs = Path(FUTURE_BOUNDED_MODE_REQUIRED_JOBS_CONFIG_REL)
    assert not rel_ops.is_absolute()
    assert not rel_jobs.is_absolute()
    assert (REPO_ROOT / rel_ops) == OPS_CONFIG
    assert (REPO_ROOT / rel_jobs) == JOBS_CONFIG
    assert FUTURE_BOUNDED_MODE_CONFIRM_TOKEN_FLAG == "--confirm-token"
    assert FINAL_OPERATOR_CONFIRMATION_TOKEN_REQUIRED is True
    assert WRAPPER_BOUNDED_MODE_CONTRACT_APPROVES_EXECUTION is False
    assert BOUNDED_RUNTIME_CONTRACT_APPROVES_EXECUTION is False
    assert BOUNDED_MODE_DEFAULT_FAIL_CLOSED_REQUIRED is True

    assert NO_SCHEDULER_START_REQUIRED is True
    assert NO_RUNTIME_START_REQUIRED is True
    assert NO_DAEMON_START_REQUIRED is True
    assert NO_PAPER_RUN_REQUIRED is True
    assert NO_SHADOW_RUN_YET_REQUIRED is True
    assert NO_TESTNET_IN_THIS_MODE_REQUIRED is True
    assert NO_LIVE_IN_THIS_MODE_REQUIRED is True
    assert NO_BROKER_IN_THIS_MODE_REQUIRED is True
    assert NO_EXCHANGE_PRIVATE_ENDPOINT_IN_THIS_MODE_REQUIRED is True
    assert NO_ORDER_SUBMISSION_IN_THIS_MODE_REQUIRED is True
    assert NO_CREDENTIALS_IN_THIS_MODE_REQUIRED is True
    assert NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_LATER_REQUIRED is True

    assert DRY_RUN_SHADOW_ONLY_POSTURE_REQUIRED is True
    assert BTCUSDT_FUTURES_PERPETUAL_SCOPE_EXPLICIT_REQUIRED is True
    assert MARKDOWN_CLOSEOUT_FILENAME_REQUIRED.endswith(".md")
    assert MANIFEST_FILENAME_REQUIRED == "manifest.json"
    assert MANIFEST_SHA256_FILENAME_REQUIRED == "MANIFEST.sha256"
    assert HEARTBEAT_OR_STEP_EVIDENCE_REQUIRED_IF_RUNTIME_INTRODUCED is True
    assert ABORT_STOP_CRITERIA_REQUIRED is True

    assert NEW_72H_BASELINE_REQUIRED_BEFORE_FIRST_BOUNDED_FUTURES_SHADOW is False
    assert BOUNDED_RUN_REQUIRED_BEFORE_TWENTYFOUR_SEVEN is True

    low = OLD_EVIDENCE_REUSE_POLICY_V0.lower()
    assert "scheduler" in low
    assert "hygiene" in low
    assert "not" in low
    assert "instrument" in low or "scope" in low
    assert "wrapper" in low and "runtime" in low


def test_future_bounded_mode_aligned_with_bounded_runtime_contract_v0() -> None:
    """Reuse bounded-runtime contract v0 without widening execution authority."""
    assert BOUNDED_RUNTIME_CONTRACT_VERSION == "shadow_247_futures_bounded_runtime_contract.v0"
    assert ALLOWED_FIRST_BOUNDED_DURATION_RANGE == RECOMMENDED_FIRST_BOUNDED_DURATION_BAND
    assert NO_LIVE is True
    assert NO_TESTNET_UNLESS_SEPARATELY_APPROVED is True
    assert NO_BROKER is True
    assert NO_EXCHANGE_PRIVATE_ENDPOINT is True
    assert NO_ORDER_SUBMISSION is True
    assert NO_CREDENTIALS is True
    assert NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_APPROVED is True


def test_ops_skeleton_matches_bounded_mode_btcusdt_futures_perp_posture_v0() -> None:
    cfg = _load_ops()
    assert cfg["instrument"] == "BTCUSDT"
    assert cfg["market_type"] == "futures"
    assert cfg["perpetual_scope"] is True
    assert cfg["dry_run"] is True
    assert cfg["shadow_mode"] is True


def test_wrapper_source_declares_bounded_runtime_contract_check_cli_v0() -> None:
    """Contract flag is present in wrapper source (placeholder implementation)."""
    assert FUTURE_BOUNDED_MODE_CLI_FLAG in _wrapper_source()
    assert FUTURE_BOUNDED_MODE_DURATION_MINUTES_FLAG in _wrapper_source()
    assert "BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES" in _wrapper_source()
    assert "bounded_runtime_contract_check" in _wrapper_source()
    assert BOUNDED_RUNTIME_CONTRACT_VERSION in _wrapper_source()
