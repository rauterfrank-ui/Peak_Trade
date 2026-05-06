import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
JOBS_CONFIG = REPO_ROOT / "config" / "scheduler" / "jobs.toml"
PREFLIGHT_CONFIG = REPO_ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"


def _jobs() -> list[dict]:
    payload = tomllib.loads(JOBS_CONFIG.read_text(encoding="utf-8"))
    return payload.get("job", [])


def _runtime_min_job() -> dict:
    return next(
        job for job in _jobs() if job.get("name") == "paper_shadow_247_paper_only_runtime_min_v0"
    )


def test_paper_only_runtime_min_scheduler_job_is_present_disabled_and_non_authorizing() -> None:
    target = _runtime_min_job()

    assert target["enabled"] is False
    assert target["schedule_type"] == "once"
    assert target["command"] == "python"
    assert target["paper_only"] is True
    assert target["paper_runtime_job"] is True
    assert target["dry_run_visible"] is True
    assert target["runtime_fixture"] == "tests/fixtures/p7/paper_run_min_v0.json"
    assert target["runtime_outdir_template"] == "out/paper_shadow_247/runtime/min/{timestamp}"

    assert "paper_shadow_247" in target["tags"]
    assert "paper_runtime" in target["tags"]
    assert "paper_runtime_min" in target["tags"]
    assert "disabled_by_default" in target["tags"]

    for key in (
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert target[key] is False


def test_paper_only_runtime_min_scheduler_job_command_shape_is_fixture_bound_and_not_live() -> None:
    target = _runtime_min_job()
    args = target["args"]

    assert args["script"] == "scripts/aiops/run_paper_trading_session.py"
    assert args["spec"] == "tests/fixtures/p7/paper_run_min_v0.json"
    assert args["outdir"] == "out/paper_shadow_247/runtime/min/__DRY_RUN_PLACEHOLDER__"

    command_blob = f"{target['command']} {args}".lower()

    assert "run_paper_trading_session.py" in command_blob
    assert "paper_run_min_v0.json" in command_blob

    for forbidden in (
        "--live",
        "--testnet",
        "p7_ctl.py run-shadow",
        "run_shadow_session.py",
        "submit_order",
        "real_order",
        "broker_connect",
        "exchange_connect",
        "api_key",
        "secret",
    ):
        assert forbidden not in command_blob


def test_paper_only_runtime_min_scheduler_job_is_referenced_by_preflight_metadata() -> None:
    payload = tomllib.loads(PREFLIGHT_CONFIG.read_text(encoding="utf-8"))

    assert "paper_shadow_247_paper_only_runtime_min_v0" in payload["paper_jobs"]


def test_paper_only_runtime_min_scheduler_job_is_not_enabled_in_default_job_set() -> None:
    enabled_names = {job["name"] for job in _jobs() if job.get("enabled") is True}

    assert "paper_shadow_247_paper_only_runtime_min_v0" not in enabled_names
    assert "paper_shadow_247_paper_only_preflight_status_v0" in enabled_names
