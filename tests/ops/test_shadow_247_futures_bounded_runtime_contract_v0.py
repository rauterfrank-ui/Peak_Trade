"""Bounded Shadow 24/7 Futures runtime contract — tests-only surface v0.

Defines **documentation-grade** constants that any future bounded Futures Shadow runtime
implementation must satisfy before separate operator approval gates. This module **does not**
approve execution, daemon start, scheduler enablement, broker/exchange/network/order paths,
nor paper/shadow/testnet/live workloads.

Prefer reading repo anchors as **text/TOML** (offline); avoid subprocess/network here.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

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

PLACEHOLDER_JOB_NAME = "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"

# -----------------------------------------------------------------------------
# Bounded-runtime contract markers (future governance — not runtime authority)
# -----------------------------------------------------------------------------

BOUNDED_RUNTIME_CONTRACT_VERSION = "shadow_247_futures_bounded_runtime_contract.v0"

DURATION_CAP_REQUIRED = True
RECOMMENDED_FIRST_BOUNDED_DURATION_BAND = "10-30min"
NEW_72H_BASELINE_REQUIRED_BEFORE_FIRST_BOUNDED_FUTURES_SHADOW = False
BOUNDED_RUN_REQUIRED_BEFORE_TWENTYFOUR_SEVEN = True

EVIDENCE_ROOT_CONVENTION_SUBSTRING = "/tmp/peak_trade_"
MANIFEST_FILENAME_REQUIRED = "manifest.json"
MANIFEST_SHA256_FILENAME_REQUIRED = "MANIFEST.sha256"
MARKDOWN_CLOSEOUT_FILENAME_REQUIRED = "SHADOW_247_FUTURES_PRESTART_EVIDENCE_DRYCHECK.md"

HEARTBEAT_OR_STEP_EVIDENCE_REQUIRED_IF_RUNTIME_INTRODUCED = True
ABORT_STOP_CRITERIA_REQUIRED = True

NO_LIVE = True
NO_TESTNET_UNLESS_SEPARATELY_APPROVED = True
NO_BROKER = True
NO_EXCHANGE_PRIVATE_ENDPOINT = True
NO_ORDER_SUBMISSION = True
NO_CREDENTIALS = True
NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_APPROVED = True

DRY_RUN_SHADOW_ONLY_POSTURE_REQUIRED = True
BTCUSDT_FUTURES_PERPETUAL_SCOPE_EXPLICIT_REQUIRED = True

FINAL_OPERATOR_CONFIRMATION_TOKEN_REQUIRED = True

OLD_EVIDENCE_REUSE_POLICY_V0 = (
    "Historical evidence may reduce repeated short-duration ladder probes only for "
    "scheduler-shape visibility / disconnect-no-trade / evidence-pack hygiene — "
    "**not** as approval for Futures instrument scope changes nor for any new bounded "
    "wrapper runtime path."
)

BOUNDED_RUNTIME_CONTRACT_APPROVES_EXECUTION = False


def _wrapper_source() -> str:
    assert WRAPPER_SCRIPT.is_file()
    return WRAPPER_SCRIPT.read_text(encoding="utf-8", errors="replace")


def _load_ops() -> dict:
    assert OPS_CONFIG.is_file()
    return tomllib.loads(OPS_CONFIG.read_text(encoding="utf-8"))


def _placeholder_job() -> dict:
    assert JOBS_CONFIG.is_file()
    rows = tomllib.loads(JOBS_CONFIG.read_text(encoding="utf-8")).get("job", [])
    return next(j for j in rows if j.get("name") == PLACEHOLDER_JOB_NAME)


def test_bounded_runtime_contract_marker_consistency_v0() -> None:
    """Internal consistency — contract bundle cannot silently approve runtime."""
    assert BOUNDED_RUNTIME_CONTRACT_APPROVES_EXECUTION is False
    assert DURATION_CAP_REQUIRED is True
    assert NEW_72H_BASELINE_REQUIRED_BEFORE_FIRST_BOUNDED_FUTURES_SHADOW is False
    assert BOUNDED_RUN_REQUIRED_BEFORE_TWENTYFOUR_SEVEN is True
    assert ABORT_STOP_CRITERIA_REQUIRED is True
    assert HEARTBEAT_OR_STEP_EVIDENCE_REQUIRED_IF_RUNTIME_INTRODUCED is True
    assert NO_LIVE is True
    assert NO_TESTNET_UNLESS_SEPARATELY_APPROVED is True
    assert NO_BROKER is True
    assert NO_EXCHANGE_PRIVATE_ENDPOINT is True
    assert NO_ORDER_SUBMISSION is True
    assert NO_CREDENTIALS is True
    assert NO_NETWORK_UNLESS_EXPLICIT_PUBLIC_SOURCE_SCOPE_APPROVED is True
    assert DRY_RUN_SHADOW_ONLY_POSTURE_REQUIRED is True
    assert BTCUSDT_FUTURES_PERPETUAL_SCOPE_EXPLICIT_REQUIRED is True
    assert FINAL_OPERATOR_CONFIRMATION_TOKEN_REQUIRED is True
    assert EVIDENCE_ROOT_CONVENTION_SUBSTRING in "/tmp/peak_trade_shadow_evidence_example"
    assert MANIFEST_FILENAME_REQUIRED.endswith(".json")
    assert MANIFEST_SHA256_FILENAME_REQUIRED.startswith("MANIFEST")
    assert MARKDOWN_CLOSEOUT_FILENAME_REQUIRED.endswith(".md")
    assert len(OLD_EVIDENCE_REUSE_POLICY_V0) > 80


def test_prerequisite_bounded_runtime_repo_surfaces_exist_v0() -> None:
    assert WRAPPER_SCRIPT.is_file()
    assert OPS_CONFIG.is_file()
    assert JOBS_CONFIG.is_file()
    assert TEST_OWNER_WRAPPER.is_file()
    assert TEST_OWNER_CONFIG_JOB.is_file()
    assert TEST_OWNER_EXECUTABLE_CONTRACT.is_file()


def test_wrapper_supports_prestart_drycheck_evidence_contract_v0() -> None:
    src = _wrapper_source()
    assert "--prestart-evidence-drycheck" in src
    assert "--evidence-root" in src
    assert "tomllib" in src
    assert MANIFEST_FILENAME_REQUIRED in src
    assert MANIFEST_SHA256_FILENAME_REQUIRED in src
    assert MARKDOWN_CLOSEOUT_FILENAME_REQUIRED in src
    assert EVIDENCE_ROOT_CONVENTION_SUBSTRING in src or "peak_trade_" in src


def test_wrapper_includes_future_operator_confirmation_anchor_v0() -> None:
    src = _wrapper_source()
    token = "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
    assert token in src
    assert "FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0" in src


def test_ops_skeleton_reflects_bounded_contract_defaults_v0() -> None:
    cfg = _load_ops()
    assert cfg["instrument"] == "BTCUSDT"
    assert cfg["market_type"] == "futures"
    assert cfg["perpetual_scope"] is True
    assert cfg["dry_run"] is True
    assert cfg["shadow_mode"] is True
    assert cfg["immediate_execution_approved"] is False
    assert cfg["enabled"] is False
    assert cfg["armed"] is False
    assert cfg["abort_stop_criteria_future_gate_required"] is True
    assert cfg["final_operator_confirmation_gate_required"] is True


def test_scheduler_placeholder_remains_default_off_v0() -> None:
    job = _placeholder_job()
    assert job["enabled"] is False
    assert job["args"]["script"] == "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
