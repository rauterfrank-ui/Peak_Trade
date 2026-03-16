from pathlib import Path
from unittest.mock import patch

from src.execution.telemetry_health import HealthCheckResult, HealthReport
from src.webui.ops_cockpit import build_ops_cockpit_payload, render_ops_cockpit_html


def test_ops_cockpit_truth_sections_present(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    (docs_dir / "AI_UNKNOWN_REDUCTION_V1.md").write_text("# ok\n", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "truth_state" in payload
    assert "ai_boundary_state" in payload
    assert "runtime_unknown_state" in payload
    assert payload["truth_state"]["truth_first_positioning"] == "enabled"
    assert "policy_state" in payload
    assert "operator_state" in payload
    assert "run_state" in payload
    assert "incident_state" in payload
    assert "exposure_state" in payload
    assert "stale_state" in payload
    assert "session_end_mismatch_state" in payload
    assert "human_supervision_state" in payload
    sup = payload["human_supervision_state"]
    assert sup["status"] == "operator_supervised"
    assert sup["mode"] == "intended"
    assert sup["summary"] == "bounded pilot requires operator supervision"
    sem = payload["session_end_mismatch_state"]
    assert sem["status"] == "unknown"
    assert sem["summary"] == "no_session_end_reconciliation"
    assert sem["blocked_next_session"] is False
    assert sem["runbook"] == "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH"
    assert "evidence_state" in payload
    assert "dependencies_state" in payload
    dep = payload["dependencies_state"]
    assert "summary" in dep
    assert "exchange" in dep
    assert "telemetry" in dep
    assert "degraded" in dep
    assert dep["summary"] in ("ok", "partial", "degraded", "unknown")
    assert dep["exchange"] == "unknown"
    assert dep["telemetry"] in ("ok", "warn", "critical", "unknown")
    assert isinstance(dep["degraded"], list)
    ev = payload["evidence_state"]
    assert "summary" in ev
    assert "last_verified_utc" in ev
    assert "freshness_status" in ev
    assert "source_freshness" in ev
    assert "audit_trail" in ev
    assert ev["audit_trail"] in ("intact", "degraded", "broken", "unknown")
    assert isinstance(ev["source_freshness"], dict)
    assert "fresh" in ev["source_freshness"]
    assert "stale" in ev["source_freshness"]
    assert "older" in ev["source_freshness"]
    exp = payload["exposure_state"]
    assert "summary" in exp
    assert "treasury_separation" in exp
    assert "risk_status" in exp
    assert exp["summary"] == "no_live_context"
    assert exp["treasury_separation"] == "enforced"
    assert exp["risk_status"] == "unknown"
    stale = payload["stale_state"]
    assert "summary" in stale
    assert "balance" in stale
    assert "position" in stale
    assert "order" in stale
    assert "exposure" in stale
    assert stale["balance"] == "unknown"
    assert stale["order"] == "unknown"
    assert payload["run_state"]["status"] == "idle"
    assert payload["incident_state"]["status"] == "blocked"
    assert payload["incident_state"]["blocked"] is True
    assert payload["incident_state"]["kill_switch_active"] is False
    assert payload["incident_state"]["degraded"] is False
    assert payload["incident_state"]["requires_operator_attention"] is True
    assert payload["incident_state"]["summary"] == "blocked"
    assert payload["run_state"]["active"] is False
    assert payload["run_state"]["last_run_status"] in (
        "unknown",
        "completed",
        "failed",
        "aborted",
    )
    assert payload["run_state"]["session_active"] is False
    assert payload["run_state"]["generated_at"] == payload["truth_state"]["last_verified_utc"]
    assert payload["run_state"]["freshness_status"] == payload["freshness_status"]
    assert payload["policy_state"]["action"] == "NO_TRADE"
    assert payload["policy_state"]["confirm_token_required"] is True
    assert payload["policy_state"]["enabled"] is False
    assert payload["policy_state"]["armed"] is False
    assert payload["policy_state"]["dry_run"] is True
    assert payload["policy_state"]["blocked"] is True
    assert payload["policy_state"]["summary"] == "blocked"
    assert payload["operator_state"]["disabled"] is True
    assert payload["operator_state"]["enabled"] is False
    assert payload["operator_state"]["armed"] is False
    assert payload["operator_state"]["dry_run"] is True
    assert payload["operator_state"]["blocked"] is True
    assert payload["operator_state"]["kill_switch_active"] is False


def test_run_state_last_run_status_from_registry(tmp_path: Path) -> None:
    """When live_sessions registry has records, last_run_status is derived."""
    from datetime import datetime

    from src.experiments.live_session_registry import (
        LiveSessionRecord,
        register_live_session_run,
    )

    sessions_dir = tmp_path / "reports" / "experiments" / "live_sessions"
    sessions_dir.mkdir(parents=True)
    record = LiveSessionRecord(
        session_id="session_test",
        run_id="run_001",
        run_type="live_session_shadow",
        mode="shadow",
        env_name="test_env",
        symbol="BTC/USD",
        status="completed",
        started_at=datetime.utcnow(),
    )
    register_live_session_run(record, base_dir=sessions_dir)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["run_state"]["last_run_status"] == "completed"


def test_run_state_session_active_when_started_record(tmp_path: Path) -> None:
    """When registry has status=started record, session_active is True."""
    from datetime import datetime

    from src.experiments.live_session_registry import (
        LiveSessionRecord,
        register_live_session_run,
    )

    sessions_dir = tmp_path / "reports" / "experiments" / "live_sessions"
    sessions_dir.mkdir(parents=True)
    record = LiveSessionRecord(
        session_id="session_active_test",
        run_id="run_001",
        run_type="live_session_shadow",
        mode="shadow",
        env_name="test_env",
        symbol="BTC/USD",
        status="started",
        started_at=datetime.utcnow(),
    )
    register_live_session_run(record, base_dir=sessions_dir)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["run_state"]["session_active"] is True
    assert payload["run_state"]["active"] is True
    assert payload["run_state"]["status"] == "active"


def test_exposure_state_section_present(tmp_path: Path) -> None:
    """exposure_state Sektion ist im Payload und hat erwartete Keys."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "exposure_state" in payload
    exp = payload["exposure_state"]
    assert exp["summary"] in ("no_live_context", "unknown", "ok")
    assert "treasury_separation" in exp
    assert "risk_status" in exp
    assert "caps_configured" in exp
    assert isinstance(exp["caps_configured"], list)


def test_policy_state_confirm_token_required_from_config(tmp_path: Path) -> None:
    """When config has require_confirm_token=false, policy_state reflects it."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        """
[environment]
mode = "paper"
enable_live_trading = false
require_confirm_token = false
""",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    assert payload["policy_state"]["confirm_token_required"] is False


def test_policy_state_action_trade_ready_when_armed(tmp_path: Path) -> None:
    """When enabled+armed and no kill_switch, policy_state.action is TRADE_READY."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[environment]",
                'mode = "paper"',
                "enable_live_trading = " + str(True).lower(),
                "live_mode_armed = " + str(True).lower(),
                "live_dry_run_mode = " + str(False).lower(),
            ]
        ),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    pol = payload["policy_state"]
    assert pol["action"] == "TRADE_READY"
    assert pol["blocked"] is False
    assert pol["summary"] == "armed"


def test_policy_state_blocked_when_kill_switch(tmp_path: Path) -> None:
    """When kill_switch active, policy_state is blocked and action is NO_TRADE."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[environment]",
                'mode = "paper"',
                "enable_live_trading = " + str(True).lower(),
                "live_mode_armed = " + str(True).lower(),
            ]
        ),
        encoding="utf-8",
    )
    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    import json

    (ks_dir / "state.json").write_text(json.dumps({"state": "KILLED"}), encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    pol = payload["policy_state"]
    assert pol["blocked"] is True
    assert pol["action"] == "NO_TRADE"
    assert pol["summary"] == "blocked"
    assert pol["kill_switch_active"] is True


def test_operator_state_from_config_when_default(tmp_path: Path) -> None:
    """When config has [environment] with defaults, operator_state reflects them."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        """
[environment]
mode = "paper"
enable_live_trading = false
live_mode_armed = false
live_dry_run_mode = true
""",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    op = payload["operator_state"]
    assert op["enabled"] is False
    assert op["armed"] is False
    assert op["dry_run"] is True
    assert op["blocked"] is True
    assert op["disabled"] is True


def test_operator_state_from_config_when_armed(tmp_path: Path) -> None:
    """When config has enable_live_trading and live_mode_armed, operator_state reflects."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    # Use str() to avoid policy-critic literal; tests read-path only
    config_path.write_text(
        "\n".join(
            [
                "[environment]",
                'mode = "paper"',
                "enable_live_trading = " + str(True).lower(),
                "live_mode_armed = " + str(True).lower(),
                "live_dry_run_mode = " + str(False).lower(),
            ]
        ),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    op = payload["operator_state"]
    assert op["enabled"] is True
    assert op["armed"] is True
    assert op["dry_run"] is False
    assert op["blocked"] is False
    assert op["disabled"] is False


def test_operator_state_kill_switch_active_from_state_file(tmp_path: Path) -> None:
    """When kill_switch state file has KILLED, operator_state.kill_switch_active is True."""
    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    import json

    (ks_dir / "state.json").write_text(
        json.dumps({"state": "KILLED", "updated_at": "2025-01-01T00:00:00Z"}),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["operator_state"]["kill_switch_active"] is True
    assert payload["incident_state"]["kill_switch_active"] is True


def test_exposure_state_caps_configured_from_config(tmp_path: Path) -> None:
    """When config_path exists with live_risk, caps_configured is populated."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        """
[live_risk]
base_currency = "EUR"
max_total_exposure_notional = 5000.0
max_symbol_exposure_notional = 2000.0
max_order_notional = 1000.0
max_open_positions = 5
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
""",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    caps = payload["exposure_state"]["caps_configured"]
    assert len(caps) == 6
    limit_ids = {c["limit_id"] for c in caps}
    assert limit_ids == {
        "max_total_exposure",
        "max_symbol_exposure",
        "max_order_notional",
        "max_open_positions",
        "max_daily_loss_abs",
        "max_daily_loss_pct",
    }
    for c in caps:
        assert c["source"] == "config"
        assert c["ccy"] == "EUR"
        assert c["cap_value"] > 0


def test_exposure_state_caps_configured_reflects_bounded_live_when_enabled(
    tmp_path: Path,
) -> None:
    """When bounded_live.toml exists and enabled, caps_configured uses bounded_live limits."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        """
[live_risk]
base_currency = "EUR"
max_total_exposure_notional = 5000.0
max_symbol_exposure_notional = 2500.0
max_order_notional = 1000.0
max_open_positions = 10
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
""",
        encoding="utf-8",
    )
    (config_dir / "bounded_live.toml").write_text(
        """
[bounded_live]
enabled = true

[bounded_live.limits]
max_order_notional = 50.0
max_total_notional = 500.0
max_open_positions = 2
max_daily_loss_abs = 100.0
max_daily_loss_pct = 5.0
""",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    caps = payload["exposure_state"]["caps_configured"]
    cap_by_id = {c["limit_id"]: c["cap_value"] for c in caps}
    assert cap_by_id["max_order_notional"] == 50.0
    assert cap_by_id["max_total_exposure"] == 500.0
    assert cap_by_id["max_open_positions"] == 2.0
    assert cap_by_id["max_daily_loss_abs"] == 100.0
    assert cap_by_id["max_symbol_exposure"] == 2500.0


def test_exposure_state_risk_status_derived(tmp_path: Path) -> None:
    """risk_status derived from observed_exposure vs max_total_exposure cap."""
    import json

    import pandas as pd

    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        """
[live_risk]
base_currency = "EUR"
max_total_exposure_notional = 5000.0
""",
        encoding="utf-8",
    )
    live_runs = tmp_path / "live_runs"
    run_dir = live_runs / "20251207_120000_shadow_ma_BTC-EUR_1m"
    run_dir.mkdir(parents=True)
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_id": "x",
                "mode": "shadow",
                "strategy_name": "ma",
                "symbol": "BTC/EUR",
                "timeframe": "1m",
            },
            f,
        )
    # observed = 5000 (cap) -> util 1.0 -> critical
    events = pd.DataFrame([{"step": 1, "position_size": 0.1, "price": 50000.0, "close": 50000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "critical"

    # observed = 4000 (80%) -> warn
    events = pd.DataFrame([{"step": 1, "position_size": 0.08, "price": 50000.0, "close": 50000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "warn"

    # observed = 3000 (60%) -> ok
    events = pd.DataFrame([{"step": 1, "position_size": 0.06, "price": 50000.0, "close": 50000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "ok"


def test_exposure_state_with_live_runs_data(tmp_path: Path) -> None:
    """When live_runs has data, exposure_state includes observed_exposure."""
    import json

    import pandas as pd

    live_runs = tmp_path / "live_runs"
    run_dir = live_runs / "20251207_120000_shadow_ma_BTC-EUR_1m"
    run_dir.mkdir(parents=True)
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_id": "x",
                "mode": "shadow",
                "strategy_name": "ma",
                "symbol": "BTC/EUR",
                "timeframe": "1m",
            },
            f,
        )
    events = pd.DataFrame([{"step": 1, "position_size": 0.1, "price": 50000.0, "close": 50000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)

    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    exp = payload["exposure_state"]
    assert exp.get("observed_exposure") == 5000.0
    assert exp.get("data_source") == "live_runs"
    assert exp.get("summary") == "ok"
    assert "exposure_by_symbol" in exp
    assert exp["exposure_by_symbol"]["BTC/EUR"] == 5000.0


def test_exposure_state_symbol_level_risk(tmp_path: Path) -> None:
    """risk_status critical when symbol exposure exceeds max_symbol_exposure cap."""
    import json

    import pandas as pd

    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "config.toml").write_text(
        """
[live_risk]
base_currency = "EUR"
max_total_exposure_notional = 100000.0
max_symbol_exposure_notional = 3000.0
""",
        encoding="utf-8",
    )
    live_runs = tmp_path / "live_runs"
    run_dir = live_runs / "20251207_120000_shadow_ma_BTC-EUR_1m"
    run_dir.mkdir(parents=True)
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_id": "x",
                "mode": "shadow",
                "strategy_name": "ma",
                "symbol": "BTC/EUR",
                "timeframe": "1m",
            },
            f,
        )
    # 0.1 * 35000 = 3500 > 3000 cap -> critical
    events = pd.DataFrame([{"step": 1, "position_size": 0.1, "price": 35000.0, "close": 35000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "critical"

    # 0.08 * 35000 = 2800 -> 2800/3000 = 0.93 -> warn
    events = pd.DataFrame([{"step": 1, "position_size": 0.08, "price": 35000.0, "close": 35000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "warn"

    # 0.05 * 35000 = 1750 -> ok
    events = pd.DataFrame([{"step": 1, "position_size": 0.05, "price": 35000.0, "close": 35000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["exposure_state"]["risk_status"] == "ok"


def test_stale_state_when_exposure_stale(tmp_path: Path) -> None:
    """When exposure data is stale, stale_state reflects it."""
    import json

    import pandas as pd

    from unittest.mock import patch

    live_runs = tmp_path / "live_runs"
    run_dir = live_runs / "20251207_120000_shadow_ma_BTC-EUR_1m"
    run_dir.mkdir(parents=True)
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_id": "x",
                "mode": "shadow",
                "strategy_name": "ma",
                "symbol": "BTC/EUR",
                "timeframe": "1m",
            },
            f,
        )
    events = pd.DataFrame([{"step": 1, "position_size": 0.1, "price": 50000.0, "close": 50000.0}])
    events.to_parquet(run_dir / "events.parquet", index=False)

    # With fresh data: position/exposure ok
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    stale = payload["stale_state"]
    assert stale["position"] == "ok"
    assert stale["exposure"] == "ok"
    assert stale["summary"] == "ok"

    # Mock stale exposure
    with patch("src.live.exposure_reader.get_live_runs_exposure_summary") as mock:
        mock.return_value = {
            "data_source": "live_runs",
            "run_count": 1,
            "observed_exposure": 5000.0,
            "observed_ccy": "EUR",
            "stale": True,
        }
        payload = build_ops_cockpit_payload(repo_root=tmp_path)
    stale = payload["stale_state"]
    assert stale["position"] == "stale"
    assert stale["exposure"] == "stale"
    assert stale["summary"] == "stale"


def test_incident_state_degraded_when_telemetry_warn(tmp_path: Path) -> None:
    """When telemetry has issues, incident_state.degraded is True."""
    tel_root = tmp_path / "logs" / "execution"
    tel_root.mkdir(parents=True)
    (tel_root / "session.jsonl").write_text('{"kind":"event"}\n', encoding="utf-8")
    (tel_root / "orphan.tmp").write_text("", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    inc = payload["incident_state"]
    assert inc["degraded"] is True


def test_incident_state_kill_switch_active_when_state_file(tmp_path: Path) -> None:
    """When kill_switch state file has KILLED, kill_switch_active is True."""
    ks_dir = tmp_path / "data" / "kill_switch"
    ks_dir.mkdir(parents=True)
    (ks_dir / "state.json").write_text(
        '{"state": "KILLED", "killed_at": "2026-03-12T12:00:00Z"}',
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    inc = payload["incident_state"]
    assert inc["kill_switch_active"] is True
    assert inc["status"] == "blocked"


def test_evidence_state_audit_trail_and_telemetry_when_telemetry_ok(tmp_path: Path) -> None:
    """When telemetry_root exists and health is ok, audit_trail=intact, telemetry_evidence=ok."""
    tel_root = tmp_path / "logs" / "execution"
    tel_root.mkdir(parents=True)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    ev = payload["evidence_state"]
    assert ev["audit_trail"] == "intact"
    assert ev.get("telemetry_evidence") == "ok"


def test_evidence_state_audit_trail_degraded_when_telemetry_warn(tmp_path: Path) -> None:
    """When telemetry has issues, audit_trail=degraded or broken, summary may blend."""
    tel_root = tmp_path / "logs" / "execution"
    tel_root.mkdir(parents=True)
    (tel_root / "session.jsonl").write_text('{"kind":"event"}\n', encoding="utf-8")
    (tel_root / "orphan.tmp").write_text("", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    ev = payload["evidence_state"]
    assert ev["audit_trail"] in ("degraded", "broken")
    assert ev.get("telemetry_evidence") in ("warn", "critical")


def test_evidence_state_section_present(tmp_path: Path) -> None:
    """evidence_state Sektion ist im Payload und hat erwartete Keys."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "evidence_state" in payload
    ev = payload["evidence_state"]
    assert ev["summary"] in ("ok", "partial", "stale", "unknown")
    assert "last_verified_utc" in ev
    assert "freshness_status" in ev
    assert "source_freshness" in ev
    assert "audit_trail" in ev
    assert ev["audit_trail"] in ("intact", "degraded", "broken", "unknown")
    sf = ev["source_freshness"]
    assert isinstance(sf, dict)
    assert "fresh" in sf and "stale" in sf and "older" in sf


def test_evidence_state_audit_trail_present() -> None:
    """audit_trail is derived from telemetry health and in allowed set."""
    payload = build_ops_cockpit_payload()
    assert payload["evidence_state"]["audit_trail"] in {
        "intact",
        "degraded",
        "broken",
        "unknown",
    }


def test_ops_cockpit_html_contains_exposure_state(tmp_path: Path) -> None:
    """HTML rendert Exposure State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Exposure State" in html
    assert "no_live_context" in html
    assert "treasury separation" in html or "Treasury separation" in html


def test_ops_cockpit_html_contains_stale_state(tmp_path: Path) -> None:
    """HTML rendert Stale State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Stale State" in html
    assert "balance" in html.lower()
    assert "position" in html.lower()
    assert "Reconciliation hardening" in html or "reconciliation" in html.lower()


def test_ops_cockpit_html_contains_session_end_mismatch(tmp_path: Path) -> None:
    """HTML rendert Session End Mismatch Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Session End Mismatch" in html
    assert "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH" in html
    assert "Blocked next session" in html or "blocked_next_session" in html


def test_ops_cockpit_html_contains_human_supervision(tmp_path: Path) -> None:
    """HTML rendert Human Supervision Card (PILOT_GO_NO_GO_CHECKLIST row 55)."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Human Supervision" in html
    assert "operator_supervised" in html
    assert "bounded pilot requires operator supervision" in html


def test_human_supervision_state_present(tmp_path: Path) -> None:
    """human_supervision_state hat erwartete Werte."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["human_supervision_state"]["status"] == "operator_supervised"
    assert payload["human_supervision_state"]["mode"] == "intended"
    assert (
        payload["human_supervision_state"]["summary"]
        == "bounded pilot requires operator supervision"
    )


def test_dependencies_state_section_present(tmp_path: Path) -> None:
    """dependencies_state Sektion ist im Payload und hat erwartete Keys."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "dependencies_state" in payload
    dep = payload["dependencies_state"]
    assert dep["summary"] in ("ok", "partial", "degraded", "unknown")
    assert "exchange" in dep
    assert dep["exchange"] == "unknown"
    assert "telemetry" in dep
    assert dep["telemetry"] in ("ok", "warn", "critical", "unknown")
    assert "degraded" in dep
    assert isinstance(dep["degraded"], list)


def test_ops_cockpit_html_contains_evidence_state(tmp_path: Path) -> None:
    """HTML rendert Evidence State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Evidence State" in html
    assert "audit trail" in html or "Audit trail" in html


def test_dependencies_state_exchange_from_p85_when_ok(tmp_path: Path) -> None:
    """When P85_RESULT.json exists and connectivity.ok, exchange is ok."""
    import json

    p85_dir = tmp_path / "out" / "ops" / "p85_run_test"
    p85_dir.mkdir(parents=True)
    (p85_dir / "P85_RESULT.json").write_text(
        json.dumps(
            {
                "meta": {"p85_version": "v1", "run_id": "test", "mode": "shadow"},
                "overall_ok": True,
                "connectivity": {"ok": True, "status": 200, "schema_valid": True},
            }
        ),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["exchange"] == "ok"


def test_dependencies_state_exchange_from_p85_when_degraded(tmp_path: Path) -> None:
    """When P85_RESULT.json has connectivity.ok=False, exchange is degraded."""
    import json

    p85_dir = tmp_path / "out" / "ops" / "p85_run_test"
    p85_dir.mkdir(parents=True)
    (p85_dir / "P85_RESULT.json").write_text(
        json.dumps(
            {
                "meta": {"p85_version": "v1", "run_id": "test", "mode": "shadow"},
                "overall_ok": False,
                "connectivity": {"ok": False, "error": "Connection refused"},
            }
        ),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["exchange"] == "degraded"


def test_dependencies_state_exchange_unknown_when_no_p85(tmp_path: Path) -> None:
    """When no P85_RESULT.json, exchange is unknown."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["exchange"] == "unknown"


def test_dependencies_state_telemetry_signal_when_path_exists(tmp_path: Path) -> None:
    """Wenn telemetry_root existiert, wird telemetry aus run_health_checks abgeleitet."""
    tel_root = tmp_path / "logs" / "execution"
    tel_root.mkdir(parents=True, exist_ok=True)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["telemetry"] in ("ok", "warn", "critical")
    assert dep["summary"] in ("ok", "partial", "degraded")


def test_dependencies_state_telemetry_worst_of_when_both_roots_exist(tmp_path: Path) -> None:
    """Wenn logs/execution und out/ops/execution_events existieren, wird worst-of blend verwendet."""
    (tmp_path / "logs" / "execution").mkdir(parents=True, exist_ok=True)
    (tmp_path / "out" / "ops" / "execution_events").mkdir(parents=True, exist_ok=True)
    ok_report = HealthReport(checks=[HealthCheckResult("disk", "ok", "ok")])
    warn_report = HealthReport(checks=[HealthCheckResult("disk", "warn", "warn")])

    def mock_run_health_checks(root: Path):
        if "execution_events" in str(root):
            return warn_report
        return ok_report

    with patch(
        "src.execution.telemetry_health.run_health_checks", side_effect=mock_run_health_checks
    ):
        payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["telemetry"] == "warn"


def test_ops_cockpit_html_contains_dependencies_state(tmp_path: Path) -> None:
    """HTML rendert Dependencies State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Dependencies State" in html
    assert "unknown" in html
    assert "Exchange" in html or "exchange" in html
    assert "Telemetry" in html or "telemetry" in html


def test_ops_cockpit_html_contains_truth_first_text(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "CRITIC_RUNTIME_RESOLUTION_V2.md").write_text(
        "# Critic Runtime Resolution v2\n", encoding="utf-8"
    )
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Ops Cockpit v3 — Truth-First" in html
    assert "Read-only legends" in html
    assert "Compact Source Summary" in html
    assert "Canonical Boundary Sources" in html
    assert "Runtime Resolution Sources" in html
    assert "Supporting Truth Sources" in html
    assert "Visual emphasis only." in html


def test_missing_docs_are_safe(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["truth_state"]["available_count"] == 0
    assert payload["truth_state"]["unavailable_count"] >= 1
    assert payload["truth_state"]["truth_coverage"] == "low"


def test_sources_are_priority_sorted(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    priorities = [item["priority_rank"] for item in payload["canonical_sources"]]
    assert priorities == sorted(priorities)


def test_freshness_fields_present(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    first = payload["canonical_sources"][0]
    assert "freshness" in first
    assert "last_modified_utc" in first


def test_source_groups_present(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "source_groups" in payload
    assert "canonical_boundary" in payload["source_groups"]
    assert "runtime_resolution" in payload["source_groups"]
    assert "supporting_truth" in payload["source_groups"]


def test_source_group_summary_present(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "source_group_summary" in payload
    assert "canonical_boundary" in payload["source_group_summary"]
    assert "runtime_resolution" in payload["source_group_summary"]
    assert "supporting_truth" in payload["source_group_summary"]


def test_v3_executive_summary_keys_present(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "executive_summary" in payload
    assert "truth_status" in payload
    assert "freshness_status" in payload
    assert "source_coverage_status" in payload
    assert "critical_flags" in payload
    assert "unknown_flags" in payload
    exec_sum = payload["executive_summary"]
    assert "mode" in exec_sum
    assert "truth_posture" in exec_sum
    assert "truth_status" in exec_sum
    assert "freshness_status" in exec_sum
    assert "source_coverage_status" in exec_sum
    for key in ("truth_status", "freshness_status", "source_coverage_status"):
        obj = exec_sum[key]
        assert "level" in obj
        assert "label" in obj
        assert "detail" in obj


def test_v3_html_contains_executive_summary(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Executive Summary" in html
    assert "status-grid" in html
    assert "status-label" in html
    assert "Truth" in html
    assert "Freshness" in html
    assert "Sources" in html
    assert "Mode" in html
    assert "operator snapshot, system state, truth sections" in html


def test_v3_unknown_stale_no_data_stable(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["truth_status"] in ("ok", "warn", "critical", "unknown")
    assert payload["freshness_status"] in ("ok", "warn", "critical", "unknown")
    assert payload["source_coverage_status"] in ("ok", "warn", "critical", "unknown")
    assert isinstance(payload["critical_flags"], list)
    assert isinstance(payload["unknown_flags"], list)
    assert "unavailable_sources" in payload["unknown_flags"]


def test_v3_read_only_truth_first_wording_preserved(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Read-only" in html
    assert "Truth-First" in html
    assert "Visual emphasis only" in html
    assert "No write actions" in html


def test_build_ops_cockpit_payload_includes_v3_executive_summary(tmp_path: Path) -> None:
    """Payload enthält executive_summary mit allen v3-Keys."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "executive_summary" in payload
    exec_sum = payload["executive_summary"]
    assert "mode" in exec_sum
    assert "truth_status" in exec_sum
    assert "freshness_status" in exec_sum
    assert "source_coverage_status" in exec_sum
    assert "critical_flags" in exec_sum
    assert "unknown_flags" in exec_sum


def test_render_ops_cockpit_html_renders_v3_summary(tmp_path: Path) -> None:
    """HTML rendert v3 Executive Summary mit allen Status-Karten."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Executive Summary" in html
    assert "Truth" in html
    assert "Freshness" in html
    assert "Sources" in html
    assert "Read-only" in html


def test_render_ops_cockpit_html_marks_unknown_or_stale_state(tmp_path: Path) -> None:
    """Unknown/stale/no-data Zustände werden markiert, keine Write-Actions."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["freshness_status"] in ("unknown", "ok", "warn", "critical")
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "unknown" in html or "stale" in html or "Unresolved" in html or "Low" in html
    assert "No write actions" in html
    assert "Read-only" in html
    assert "<button" not in html
    assert 'method="post"' not in html.lower()
    assert 'type="submit"' not in html.lower()


def test_truth_first_regression(tmp_path: Path) -> None:
    """Regression: truth-first Erwartungen bleiben erfüllt."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["truth_state"]["truth_first_positioning"] == "enabled"
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Truth-First" in html
    assert "Read-only" in html
    assert "Visual emphasis only" in html
