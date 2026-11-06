from __future__ import annotations

import json
from pathlib import Path

from scripts import run_scheduler


def test_write_scheduler_heartbeat_freshness_is_non_authorizing(tmp_path: Path) -> None:
    heartbeat = tmp_path / "runtime_out" / "scheduler_heartbeat_freshness_v0.json"

    run_scheduler.write_scheduler_heartbeat_freshness(
        heartbeat,
        config_path=Path("config/scheduler/jobs.toml"),
        poll_interval=30,
        include_tags={"paper_runtime"},
        exclude_tags=None,
        dry_run=False,
        once=False,
        iteration=7,
        due_jobs_count=0,
        jobs_dispatched_total=1,
        reason="idle_no_due_jobs",
    )

    payload = json.loads(heartbeat.read_text(encoding="utf-8"))
    assert payload["version"] == "scheduler_heartbeat_freshness_v0"
    assert payload["heartbeat_only"] is True
    assert payload["does_not_authorize_trading"] is True
    assert payload["live_authority_changed"] is False
    assert payload["testnet_started"] is False
    assert payload["real_orders_started"] is False
    assert payload["include_tags"] == ["paper_runtime"]
    assert payload["reason"] == "idle_no_due_jobs"
