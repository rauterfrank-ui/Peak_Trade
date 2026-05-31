"""Static contract tests for Shadow 24/7 Futures config/job skeleton (no runtime).

Includes small drift hooks: scheduler placeholder relpath must match ops `wrapper_script`;
preflight status job must stay on the read-only reporter (not the futures wrapper).
Crosslinks `paper_shadow_247_preflight.toml` with `shadow_247_futures_wrapper_skeleton.toml`
for shared default-off / non-authorizing posture (metadata only, not activation approval).
Crosslinks preflight `stop_command` / `emergency_stop_command` to on-disk reporter/snapshot scripts.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[2]
OPS_CONFIG = REPO_ROOT / "config" / "ops" / "shadow_247_futures_wrapper_skeleton.toml"
PAPER_SHADOW_PREFLIGHT_TOML = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"
JOBS_CONFIG = REPO_ROOT / "config" / "scheduler" / "jobs.toml"

PLACEHOLDER_JOB_NAME = "shadow_247_futures_prestart_evidence_drycheck_placeholder_v0"
PREFLIGHT_STATUS_JOB_NAME = "paper_shadow_247_paper_only_preflight_status_v0"
PREFLIGHT_REPORTER_SCRIPT = "scripts/ops/report_paper_shadow_247_preflight_status.py"
RUNTIME_HIGH_VOL_JOB_NAME = "paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0"


def _load_ops_config() -> dict:
    return tomllib.loads(OPS_CONFIG.read_text(encoding="utf-8"))


def _load_paper_shadow_preflight_toml() -> dict:
    return tomllib.loads(PAPER_SHADOW_PREFLIGHT_TOML.read_text(encoding="utf-8"))


def _jobs() -> list[dict]:
    payload = tomllib.loads(JOBS_CONFIG.read_text(encoding="utf-8"))
    return payload.get("job", [])


def _relative_repo_scripts_from_shell_command(cmd: str) -> list[str]:
    """Extract repo-relative `scripts/...py` paths from a shell-ish TOML string (static parse only)."""
    paths: list[str] = []
    for raw in cmd.replace(";", " ").split():
        tok = raw.strip().strip('"').strip("'")
        if tok.startswith("scripts/") and tok.endswith(".py"):
            paths.append(tok)
    return paths


def test_shadow_247_futures_ops_config_file_exists() -> None:
    assert OPS_CONFIG.is_file()


def test_shadow_247_futures_ops_config_schema_and_wrapper_path() -> None:
    cfg = _load_ops_config()
    assert cfg["schema_version"] == "shadow_247_futures_wrapper_skeleton.v0"
    assert cfg["wrapper_script"] == "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
    assert "/tmp/peak_trade_" in cfg["evidence_root_convention"]


def test_shadow_247_futures_ops_config_default_off_core() -> None:
    cfg = _load_ops_config()
    assert cfg["enabled"] is False
    assert cfg["armed"] is False
    assert cfg["dry_run"] is True
    assert cfg["shadow_mode"] is True
    assert cfg["immediate_execution_approved"] is False
    assert cfg["wrapper_daemon_start_allowed"] is False


def test_shadow_247_futures_ops_config_futures_scope_explicit() -> None:
    cfg = _load_ops_config()
    assert cfg["instrument"] == "BTCUSDT"
    assert cfg["market_type"] == "futures"
    assert cfg["perpetual_scope"] is True


def test_shadow_247_futures_ops_config_all_runtime_flags_false() -> None:
    cfg = _load_ops_config()
    for key in (
        "testnet_allowed",
        "live_allowed",
        "paper_allowed",
        "network_allowed",
        "broker_allowed",
        "exchange_allowed",
        "order_submission_allowed",
        "private_exchange_endpoint_allowed",
        "credentials_allowed",
    ):
        assert cfg[key] is False, key


def test_shadow_247_futures_ops_config_future_gates_required_flags() -> None:
    cfg = _load_ops_config()
    assert cfg["supervisor_timeout_future_gate_required"] is True
    assert cfg["abort_stop_criteria_future_gate_required"] is True
    assert cfg["final_operator_confirmation_gate_required"] is True


def test_shadow_247_futures_ops_config_wrapper_modes_include_prestart_only() -> None:
    cfg = _load_ops_config()
    modes = cfg["wrapper_modes_allowed"]
    assert "prestart_evidence_drycheck" in modes
    assert "inspect" in modes
    assert "default_fail_closed" in modes


def test_shadow_247_futures_placeholder_excluded_from_bounded_path_b_preflight_lists_v0() -> None:
    pf = _load_paper_shadow_preflight_toml()
    assert PLACEHOLDER_JOB_NAME not in pf.get("paper_jobs", [])
    assert PLACEHOLDER_JOB_NAME not in pf.get("shadow_jobs", [])


def test_shadow_247_futures_scheduler_placeholder_is_disabled_and_safe() -> None:
    job = next(j for j in _jobs() if j.get("name") == PLACEHOLDER_JOB_NAME)
    assert job["enabled"] is False
    assert job["args"]["script"] == "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
    assert job.get("paper_only") is False
    assert job.get("paper_runtime_job") is False
    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert job[key] is False
    tags = job.get("tags", [])
    assert "disabled_by_default" in tags
    assert "shadow_247_futures" in tags
    assert "prestart_only" in tags


def test_shadow_247_futures_placeholder_job_script_matches_ops_wrapper_path() -> None:
    """Drift hook: scheduler placeholder and ops TOML must reference the same wrapper relpath."""
    cfg = _load_ops_config()
    job = next(j for j in _jobs() if j.get("name") == PLACEHOLDER_JOB_NAME)
    assert job["args"]["script"] == cfg["wrapper_script"]


def test_shadow_247_futures_ops_wrapper_script_file_exists() -> None:
    cfg = _load_ops_config()
    wrapper = REPO_ROOT / cfg["wrapper_script"]
    assert wrapper.is_file()


def test_paper_shadow_247_preflight_status_job_is_readonly_reporter_not_futures_wrapper() -> None:
    """Preflight job may be scheduler-visible but must stay the read-only reporter, not the futures wrapper."""
    job = next(j for j in _jobs() if j.get("name") == PREFLIGHT_STATUS_JOB_NAME)
    assert job["args"]["script"] == PREFLIGHT_REPORTER_SCRIPT
    assert job["args"]["script"] != "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
    tags = job.get("tags", [])
    assert "readonly" in tags
    assert "preflight" in tags
    assert job.get("testnet_authorized") is False
    assert job.get("live_authorized") is False


def test_paper_preflight_job_shape_vs_toml_crosslink_v0() -> None:
    """Crosslink read-only preflight reporter job with paper_shadow_247_preflight.toml (no activation)."""
    pf = _load_paper_shadow_preflight_toml()
    job = next(j for j in _jobs() if j.get("name") == PREFLIGHT_STATUS_JOB_NAME)
    assert PREFLIGHT_STATUS_JOB_NAME in pf.get("paper_jobs", [])
    assert job["args"]["script"] == PREFLIGHT_REPORTER_SCRIPT
    assert job["args"]["script"] != "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
    tags = set(job.get("tags", []))
    assert tags >= {"paper_shadow_247", "preflight", "readonly"}
    assert job.get("paper_only") is True
    assert job.get("dry_run_visible") is True
    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert job.get(key) is False, key
    assert pf["scheduler_execution_authorized"] is False
    assert pf["daemon_activation_authorized"] is False
    assert pf["shadow_runtime_authorized"] is False


def test_paper_shadow_247_preflight_toml_exists_parseable_and_default_off() -> None:
    """Read-only preflight metadata must stay default-off; does not authorize any activation path."""
    assert PAPER_SHADOW_PREFLIGHT_TOML.is_file()
    pf = _load_paper_shadow_preflight_toml()
    assert pf["schema_version"] == "paper_shadow_247_preflight.v0"
    for key in (
        "activation_authorized",
        "daemon_activation_authorized",
        "scheduler_execution_authorized",
        "paper_runtime_authorized",
        "shadow_runtime_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert pf[key] is False, key


def test_paper_shadow247_preflight_toml_and_futures_wrapper_toml_default_off_crosslink() -> None:
    """Both ops TOMLs must agree there is no default activation authority for Shadow-247 / wrapper daemon."""
    pf = _load_paper_shadow_preflight_toml()
    wrap = _load_ops_config()
    assert pf["daemon_activation_authorized"] is False
    assert pf["shadow_runtime_authorized"] is False
    assert wrap["wrapper_daemon_start_allowed"] is False
    assert wrap["immediate_execution_approved"] is False
    assert wrap["enabled"] is False
    assert wrap["armed"] is False
    assert wrap["final_operator_confirmation_gate_required"] is True
    assert wrap["supervisor_timeout_future_gate_required"] is True
    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert pf[key] is False and wrap[key.replace("_authorized", "_allowed")] is False, key


def test_paper_shadow247_runtime_fixture_job_stays_quarantined_v0() -> None:
    """Paper runtime fixture job stays disabled and off wrapper/reporter activation paths."""
    job = next(j for j in _jobs() if j.get("name") == RUNTIME_HIGH_VOL_JOB_NAME)
    assert job["enabled"] is False
    assert job.get("paper_only") is True
    assert job.get("paper_runtime_job") is True
    assert job.get("dry_run_visible") is True
    script = job["args"]["script"]
    assert script == "scripts/aiops/run_paper_trading_session.py"
    assert script != "scripts/ops/shadow_247_futures_start_wrapper_skeleton_v0.py"
    assert script != PREFLIGHT_REPORTER_SCRIPT
    tags = set(job.get("tags", []))
    assert "disabled_by_default" in tags
    assert "paper_runtime" in tags
    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert job.get(key) is False, key
    assert job.get("shadow_247_futures_placeholder") is not True


def test_shadow247_preflight_stop_commands_resolve_v0() -> None:
    """Preflight TOML stop/emergency commands reference existing scripts; stays non-authorizing."""
    pf = _load_paper_shadow_preflight_toml()
    stop_cmd = pf["stop_command"]
    emerg_cmd = pf["emergency_stop_command"]
    assert "report_paper_shadow_247_preflight_status.py" in stop_cmd
    assert "snapshot_operator_stop_signals.py" in emerg_cmd
    for cmd in (stop_cmd, emerg_cmd):
        for rel in _relative_repo_scripts_from_shell_command(cmd):
            assert (REPO_ROOT / rel).is_file(), rel
    assert pf["activation_authorized"] is False
    assert pf["daemon_activation_authorized"] is False
    assert pf["scheduler_execution_authorized"] is False
