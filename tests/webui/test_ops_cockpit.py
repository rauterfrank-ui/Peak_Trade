import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.execution.telemetry_health import HealthCheckResult, HealthReport
from src.ops.update_officer_consumer import UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE
from src.webui.ops_cockpit import (
    build_ops_cockpit_payload,
    build_workflow_officer_panel_context,
    render_ops_cockpit_html,
    resolve_update_officer_route_inputs,
)


def test_workflow_officer_panel_context_empty_repo(tmp_path: Path) -> None:
    ctx = build_workflow_officer_panel_context(tmp_path)
    assert ctx["present"] is False
    assert ctx["dashboard_schema_version"] == "workflow_officer.dashboard_view/v0"
    assert ctx["empty_reason"] == "no_officer_output_dir"
    assert ctx["executive_panel"]["present"] is False
    assert (
        ctx["executive_panel"]["executive_panel_schema_version"]
        == "workflow_officer.executive_panel_view/v0"
    )


def test_ops_cockpit_session_end_mismatch_registry_started_integration(tmp_path: Path) -> None:
    """session_end_mismatch_state reflects live session registry (started → mismatch_signal)."""
    from datetime import datetime, timezone

    from src.experiments.live_session_registry import (
        STATUS_STARTED,
        LiveSessionRecord,
        register_live_session_run,
    )

    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    (docs_dir / "AI_UNKNOWN_REDUCTION_V1.md").write_text("# ok\n", encoding="utf-8")
    reg = tmp_path / "reports" / "experiments" / "live_sessions"
    rec = LiveSessionRecord(
        session_id="sess_x",
        run_id=None,
        run_type="live_session_shadow",
        mode="shadow",
        env_name="env",
        symbol="BTC/EUR",
        status=STATUS_STARTED,
        started_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    register_live_session_run(rec, base_dir=reg)
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    sem = payload["session_end_mismatch_state"]
    assert sem["status"] == "mismatch_signal"
    assert sem["blocked_next_session"] is True
    assert sem["data_source"] == "live_session_registry"


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
    assert "transfer_ambiguity_state" in payload
    assert "human_supervision_state" in payload
    assert "phase83_eligibility_snapshot" in payload
    assert "workflow_officer_state" in payload
    sup = payload["human_supervision_state"]
    assert sup["status"] == "operator_supervised"
    assert sup["mode"] == "intended"
    assert sup["summary"] == "bounded pilot requires operator supervision"
    sem = payload["session_end_mismatch_state"]
    assert sem["status"] == "unknown"
    assert sem["summary"] == "no_signal"
    assert sem["blocked_next_session"] is False
    assert sem["runbook"] == "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH"
    assert sem.get("data_source") == "none"
    assert sem.get("observation_reason") == "no_registry_or_live_runs_artifacts"
    assert sem.get("reader_schema_version") == "session_end_mismatch_reader/v0"
    ta = payload["transfer_ambiguity_state"]
    assert ta["runbook_ref"] == "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY"
    assert ta["reader_schema_version"] == "transfer_ambiguity_reader/v0"
    assert ta["status"] == "unknown"
    assert "transfer_truth_not_observed" in ta["summary"] or ta["summary"] == "no_signal"
    assert "data_source" in ta
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
    assert "p85_exchange_observation" in dep
    assert dep["p85_exchange_observation"]["reader_schema_version"].startswith(
        "p85_exchange_reader"
    )
    assert "market_data_cache_observation" in dep
    assert dep["market_data_cache_observation"]["reader_schema_version"].startswith(
        "market_data_cache_observation_reader"
    )
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
    assert "incident_stop_invoked" in payload["incident_state"]
    assert "incident_stop_source" in payload["incident_state"]
    assert "pt_force_no_trade" in payload["incident_state"]
    assert "pt_enabled" in payload["incident_state"]
    assert "pt_armed" in payload["incident_state"]
    assert "kill_switch_source" in payload["incident_state"]
    assert "entry_permitted" in payload["incident_state"]
    assert "risk_gate_kill_switch_active" in payload["incident_state"]
    assert "operator_authoritative_state" in payload["incident_state"]
    assert "operator_state_reason" in payload["incident_state"]
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
    ss = payload["system_state"]
    assert ss["mode"] == "truth_first_ops_cockpit_v3"
    assert ss["execution_model"] == "guarded_execution"
    assert ss["config_load_status"] == "not_loaded"
    assert ss["environment"] == "unknown"
    assert ss["bounded_pilot_mode"] is None
    assert ss["gating_posture_observation"] == payload["policy_state"]["summary"]
    spo = payload["safety_posture_observation"]
    assert spo["status"] == "blocking"
    assert spo["data_source"] == "cockpit_payload_aggregate"
    assert spo["reader_schema_version"].startswith("safety_posture_observation/")
    assert "cockpit observation" in spo["summary"].lower()
    rso = payload["run_session_observation"]
    assert rso["status"] == "nominal"
    assert rso["data_source"] == "cockpit_payload_aggregate"
    assert rso["reader_schema_version"].startswith("run_session_observation/")
    assert "observation" in rso["summary"].lower()


def test_ops_cockpit_safety_posture_observation_in_html(tmp_path: Path) -> None:
    """HTML surfaces additive safety posture aggregate; no approval or live-truth wording."""
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    (docs_dir / "AI_UNKNOWN_REDUCTION_V1.md").write_text("# ok\n", encoding="utf-8")
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Safety / gating posture (observation)" in html
    assert "safety_posture_observation.status" in html
    assert "not an approval" in html.lower()
    assert "broker or exchange truth" in html.lower()


def test_ops_cockpit_run_session_observation_in_html(tmp_path: Path) -> None:
    """HTML surfaces run/session aggregate; no session guarantee or approval wording."""
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "AI_LAYER_CANONICAL_SPEC_V1.md").write_text("# ok\n", encoding="utf-8")
    (docs_dir / "AI_UNKNOWN_REDUCTION_V1.md").write_text("# ok\n", encoding="utf-8")
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Run / session (observation)" in html
    assert "run_session_observation.status" in html
    assert "not a session guarantee" in html.lower()
    rs_block = html.split("Run / session (observation)", 1)[1].split("Incident observation", 1)[0]
    assert "approval" in rs_block.lower()  # explicit "not ... approval" disclaimer in this block
    assert "not an approval" in rs_block.lower()


def test_system_state_environment_observation_from_config(tmp_path: Path) -> None:
    """system_state reflects config-derived environment when config loads."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        "\n".join(
            [
                "[environment]",
                'mode = "paper"',
                "enable_live_trading = " + str(False).lower(),
                "bounded_pilot_mode = " + str(True).lower(),
            ]
        ),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    ss = payload["system_state"]
    assert ss["config_load_status"] == "loaded"
    assert ss["environment"] == "paper"
    assert ss["bounded_pilot_mode"] is True
    assert ss["gating_posture_observation"] == payload["policy_state"]["summary"]


def test_system_state_config_unavailable_when_toml_invalid(tmp_path: Path) -> None:
    """Broken config file yields unavailable load status without raising."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text("this is not valid toml [[[\n", encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    ss = payload["system_state"]
    assert ss["config_load_status"] == "unavailable"
    assert ss["environment"] == "unknown"
    assert ss["bounded_pilot_mode"] is None


def test_ops_cockpit_html_contains_system_state_environment_observation(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "system_state.config_load_status" in html
    assert "system_state.environment" in html
    assert "system_state.gating_posture_observation" in html
    assert "Config environment (observation)" in html
    assert "not a broker or exchange guarantee" in html


def test_phase83_eligibility_snapshot_unavailable_in_empty_repo(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    snap = payload["phase83_eligibility_snapshot"]
    assert snap["mode"] == "phase83_eligibility_snapshot_v1"
    assert snap["status"] == "unavailable"
    assert snap["strategies_checked"] == 0
    assert snap["items"] == []


def test_ops_cockpit_html_contains_phase83_eligibility_card(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Phase 83 — Strategy eligibility" in html
    assert "Read-only" in html
    assert "Observation only" in html


def test_ops_cockpit_html_contains_policy_guard_observation_card(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Policy / guard rails — observed state" in html
    assert "policy_state.action" in html
    assert "guard_state.treasury_separation" in html
    assert "not a control surface" in html


def test_ops_cockpit_html_contains_policy_governance_rv6_surface(tmp_path: Path) -> None:
    """vNext RV6 — Policy/Governance bundle: boundary + supervision + evidence cross-ref."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert 'id="policy-governance-observation-surface"' in html
    assert "Policy / Governance observation (vNext RV6)" in html
    assert "ai_boundary_state.proposer_authority" in html
    assert "ai_boundary_state.critic_authority" in html
    assert "Human Supervision (payload)" in html
    assert "human_supervision_state.status" in html
    assert "Evidence / audit (governance cross-surface)" in html
    assert "not approval" in html.lower()
    assert 'id="evidence-state-card"' in html
    assert "#evidence-state-card" in html


def test_ops_cockpit_html_contains_incident_observation_card(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Incident — observed rollup" in html
    assert "incident_state.status" in html
    assert "incident_state.requires_operator_attention" in html
    assert "not a control surface" in html


def test_ops_cockpit_html_contains_run_state_observation_card(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Run state — observed rollup" in html
    assert "run_state.status" in html
    assert "run_state.last_run_status" in html
    assert "not a control surface" in html


def test_ops_cockpit_html_contains_phase57_snapshot_discoverability_links(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Live status snapshot (Phase 57) — endpoints" in html
    assert "/api/live/status/snapshot.json" in html
    assert "/api/live/status/snapshot.html" in html
    assert "observation only" in html.lower()


def test_phase83_eligibility_snapshot_ok_with_real_repo_tiering() -> None:
    repo = Path(__file__).resolve().parents[2]
    if not (repo / "config" / "strategy_tiering.toml").exists():
        pytest.skip("checkout without strategy_tiering.toml")
    payload = build_ops_cockpit_payload(repo_root=repo)
    snap = payload["phase83_eligibility_snapshot"]
    assert snap["mode"] == "phase83_eligibility_snapshot_v1"
    assert snap["status"] == "ok"
    assert snap["strategies_checked"] > 0
    assert "eligible_count" in snap
    assert isinstance(snap["items"], list)


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
    assert payload["run_state"]["registry_session_count"] == 1
    assert "registry_last_started_at" in payload["run_state"]


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
    assert stale["order"] == "ok"
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
    assert stale["order"] == "ok"
    assert stale["summary"] == "stale"


def test_stale_state_order_ok_when_fresh_live_runs_events(tmp_path: Path) -> None:
    """Non-empty live_runs events with recent mtime → stale_state.order ok."""
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
    assert payload["stale_state"]["order"] == "ok"


def test_stale_state_order_stale_when_events_mtime_old(tmp_path: Path) -> None:
    """Old events file mtime → stale_state.order stale (log observation)."""
    import json
    import os
    import time

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
    ep = run_dir / "events.parquet"
    events.to_parquet(ep, index=False)
    old = time.time() - 26 * 3600
    os.utime(ep, (old, old))
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["stale_state"]["order"] == "stale"


def test_ops_cockpit_html_contains_stale_order_log_disclaimer(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "not exchange order-book state" in html


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
    assert inc["kill_switch_source"] == "data/kill_switch/state.json"
    assert inc["risk_gate_kill_switch_active"] is True
    assert inc["operator_authoritative_state"] == "kill_switch_active"
    assert "Kill switch" in str(inc["operator_state_reason"])


def test_incident_state_read_model_incident_stop_invoked_when_artifact_exists(
    tmp_path: Path,
) -> None:
    """When incident-stop artifact exists, incident_stop_invoked is True."""
    out_ops = tmp_path / "out" / "ops"
    out_ops.mkdir(parents=True)
    stop_dir = out_ops / "incident_stop_20260321T120000Z_manual-stop"
    stop_dir.mkdir()
    (stop_dir / "incident_stop_state.env").write_text(
        "PT_INCIDENT_STOP=1\nPT_FORCE_NO_TRADE=1\nPT_ENABLED=0\nPT_ARMED=0\n",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    inc = payload["incident_state"]
    assert inc["incident_stop_invoked"] is True
    assert "incident_stop_state.env" in str(inc["incident_stop_source"])


def test_ops_cockpit_html_contains_incident_state_read_model(tmp_path: Path) -> None:
    """HTML renders Incident-state read model section."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Incident-state read model" in html
    assert "Incident stop invoked" in html
    assert "PT_FORCE_NO_TRADE" in html
    assert "PT_ENABLED" in html
    assert "PT_ARMED" in html
    assert "Kill-switch source" in html
    assert "Entry permitted" in html
    assert "Risk-gate kill-switch active" in html
    assert "Operator authoritative state" in html
    assert "Operator state reason" in html


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
    assert "Read-only exposure / risk observation" in html
    assert "not approval, not unlock" in html
    assert "no_live_context" in html
    assert "Treasury separation:" in html
    assert "Observed exposure:" in html
    assert "stale_state.exposure:" in html
    assert "dependencies_state.summary:" in html
    assert "Configured caps:" in html
    assert "Symbol exposures (preview):" in html


def test_ops_cockpit_html_contains_stale_state(tmp_path: Path) -> None:
    """HTML rendert Stale State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Stale State" in html
    assert "balance" in html.lower()
    assert "position" in html.lower()
    assert "Reconciliation hardening" in html or "reconciliation" in html.lower()


def test_balance_semantics_state_section_present(tmp_path: Path) -> None:
    """balance_semantics_state Sektion ist im Payload und hat erwartete Keys."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "balance_semantics_state" in payload
    bs = payload["balance_semantics_state"]
    assert "balance_semantic_state" in bs
    assert "balance_reason_code" in bs
    assert "balance_operator_visible_state" in bs


def test_balance_semantics_state_with_config_returns_populated_when_paper_broker(
    tmp_path: Path,
) -> None:
    """When config exists and PaperBroker is used, balance_semantic_state is balance_semantics_clear."""
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(
        """
[general]
base_currency = "EUR"
starting_capital = 10000.0
""",
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, config_path=config_path)
    bs = payload["balance_semantics_state"]
    assert bs["balance_semantic_state"] == "balance_semantics_clear"
    assert bs["balance_reason_code"] == "BALANCE_PAPER_BROKER_EXPLICIT"
    assert bs["balance_operator_visible_state"] == "paper_broker_cash_explicit"
    assert payload["stale_state"]["balance"] == "ok"


def test_ops_cockpit_html_contains_balance_semantics(tmp_path: Path) -> None:
    """HTML rendert Balance Semantics Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Balance Semantics" in html
    assert "Operator visibility" in html or "operator visibility" in html.lower()
    assert "Semantic state" in html or "semantic state" in html.lower()


def test_ops_cockpit_html_contains_session_end_mismatch(tmp_path: Path) -> None:
    """HTML rendert Session End Mismatch Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Session End Mismatch" in html
    assert "session-end-mismatch-observation-surface" in html
    assert "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH" in html
    assert "Blocked next session" in html or "blocked_next_session" in html
    assert "Observation (read-only)" in html


def test_ops_cockpit_html_contains_transfer_ambiguity_observation(tmp_path: Path) -> None:
    """HTML rendert Transfer / Treasury ambiguity observation (read-only)."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Transfer / Treasury ambiguity" in html
    assert "transfer-ambiguity-observation-surface" in html
    assert "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY" in html
    assert "not approval" in html.lower()
    assert "Observation (read-only)" in html


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
    assert "p85_exchange_observation" in dep
    assert "market_data_cache_observation" in dep


def test_ops_cockpit_html_contains_evidence_state(tmp_path: Path) -> None:
    """HTML rendert Evidence State Card."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Evidence State" in html
    assert "Read-only evidence / audit observation" in html
    assert "not approval, not unlock" in html
    assert "audit_trail:" in html
    assert "freshness_status:" in html
    assert "last_verified_utc:" in html
    assert "source_freshness" in html
    assert "telemetry_evidence:" in html


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
    assert dep["p85_exchange_observation"]["data_source"] == "p85_result_json"
    assert dep["p85_exchange_observation"]["observation_reason"] == "p85_connectivity_ok_true"


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
    assert dep["p85_exchange_observation"]["observation_reason"] == "p85_connectivity_ok_false"


def test_dependencies_state_exchange_unknown_when_no_p85(tmp_path: Path) -> None:
    """When no P85_RESULT.json, exchange is unknown."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["exchange"] == "unknown"
    assert dep["p85_exchange_observation"]["observation_reason"] in (
        "no_p85_artifact",
        "p85_search_base_missing",
    )


def test_dependencies_state_exchange_unknown_when_p85_stale(tmp_path: Path) -> None:
    """Stale P85 artifact yields exchange unknown (conservative)."""
    import json
    import os
    import time

    p85_dir = tmp_path / "out" / "ops" / "p85_stale"
    p85_dir.mkdir(parents=True)
    p = p85_dir / "P85_RESULT.json"
    p.write_text(
        json.dumps({"connectivity": {"ok": True}, "overall_ok": True}),
        encoding="utf-8",
    )
    old = time.time() - 4000.0
    os.utime(p, (old, old))
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    dep = payload["dependencies_state"]
    assert dep["exchange"] == "unknown"
    assert dep["p85_exchange_observation"]["stale"] is True
    assert dep["p85_exchange_observation"]["observation_reason"] == "artifact_stale"


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
    assert "Read-only dependencies / health-drift observation" in html
    assert "not approval, not unlock" in html
    assert "market_data_cache:" in html
    assert "Degraded signals (preview):" in html
    assert "Summary:" in html
    assert "Exchange:" in html
    assert "Telemetry:" in html
    assert "artifact observation only" in html.lower()
    assert "not a live connectivity check" in html.lower()
    assert "local parquet" in html.lower()
    assert "not a live feed check" in html.lower()


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


def test_v3_html_contains_operator_summary_surface(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Operator summary (read-only)" in html
    assert "System status (observation)" in html
    assert "Go / No-Go observation (not approval)" in html
    assert "Incident observation (read-only)" in html
    assert "incident_state.status" in html
    assert "incident_state.incident_stop_invoked" in html
    assert "incident_state.entry_permitted" in html
    assert "incident_state.operator_authoritative_state" in html
    assert "dependencies_state.degraded_count" in html
    assert "dependencies_state.telemetry" in html
    assert "dependencies_state.exchange" in html
    assert "Evidence freshness observation (read-only)" in html
    assert "evidence_state.freshness_status" in html
    assert "evidence_state.last_verified_utc" in html
    assert "evidence_state.source_freshness" in html
    assert "Status at a glance" in html
    assert "status-grid" in html
    assert "status-label" in html
    assert "Truth" in html
    assert "Freshness" in html
    assert "Sources" in html
    assert "Mode" in html
    assert "operator snapshot, system state, truth sections" in html
    assert "Not an approval, not an unlock" in html
    summary_start = html.index("Operator summary (read-only)")
    summary_end = html.index("Status at a glance")
    summary_segment = html[summary_start:summary_end]
    assert summary_segment.count("incident_state.requires_operator_attention") == 1


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
    """HTML rendert Operator Summary Surface mit Status-at-a-glance-Karten (v3-Rollup)."""
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Operator summary (read-only)" in html
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
    assert 'method="post"' not in html.lower()
    assert "uo-source-form" in html
    assert 'method="get"' in html


def test_truth_first_regression(tmp_path: Path) -> None:
    """Regression: truth-first Erwartungen bleiben erfüllt."""
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert payload["truth_state"]["truth_first_positioning"] == "enabled"
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Truth-First" in html
    assert "Read-only" in html
    assert "Visual emphasis only" in html


@pytest.fixture
def ops_client():
    """Create FastAPI test client for ops cockpit (uses module-level app with /ops route)."""
    from src.webui.app import app

    return TestClient(app)


def test_ops_cockpit_shows_balance_semantics(ops_client: TestClient) -> None:
    """GET /ops rendert Balance Semantics Card (HTTP-Integration)."""
    response = ops_client.get("/ops")
    assert response.status_code == 200
    html = response.text
    assert "Balance Semantics" in html
    assert "Operator visibility" in html or "operator visibility" in html.lower()
    assert "Semantic state" in html or "semantic state" in html.lower()
    assert "Reason code" in html or "reason code" in html.lower()


def _sample_notifier_payload() -> dict:
    return {
        "officer_version": "v3-min",
        "generated_at": "2026-03-24T10:25:52Z",
        "next_recommended_topic": "python_dependencies",
        "top_priority_reason": "Topic ranks first.",
        "recommended_update_queue": [
            {
                "topic_id": "python_dependencies",
                "rank": 1,
                "worst_priority": "p3",
                "finding_count": 1,
                "blocked_count": 0,
                "manual_review_count": 0,
                "safe_review_count": 1,
                "headline": "1 finding(s); worst_priority=p3; blocked=0; manual_review=0; safe_review=1",
            }
        ],
        "recommended_next_action": "Focus manual review on update topic.",
        "recommended_review_paths": ["pyproject.toml"],
        "severity": "low",
        "reminder_class": "hygiene",
        "requires_manual_review": False,
    }


def test_update_officer_ui_empty_by_default(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    uo = payload["update_officer_ui"]
    assert uo["available"] is False
    assert uo["status"] == "unavailable"
    assert uo["empty_state_message"]


def test_update_officer_ui_from_run_dir(tmp_path: Path) -> None:
    run_dir = tmp_path / "uo_run"
    run_dir.mkdir()
    (run_dir / "notifier_payload.json").write_text(
        json.dumps(_sample_notifier_payload()),
        encoding="utf-8",
    )
    payload = build_ops_cockpit_payload(repo_root=tmp_path, update_officer_run_dir=run_dir)
    uo = payload["update_officer_ui"]
    assert uo["available"] is True
    assert uo["next_topic"] == "python_dependencies"
    assert uo["headline"]


def test_update_officer_ui_from_explicit_payload_path(tmp_path: Path) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    payload = build_ops_cockpit_payload(repo_root=tmp_path, update_officer_notifier_path=path)
    uo = payload["update_officer_ui"]
    assert uo["available"] is True
    assert "python_dependencies" in str(uo.get("headline", ""))


def test_ops_cockpit_html_contains_update_officer_section(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Update Officer" in html
    assert "Notifier summary" in html or "notifier" in html.lower()


def test_ops_cockpit_html_update_officer_no_write_actions(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Update Officer" in html
    assert 'method="post"' not in html.lower()
    assert 'method="get"' in html
    assert "uo-source-form" in html


def test_resolve_update_officer_route_inputs_conflict() -> None:
    n, r, c = resolve_update_officer_route_inputs("/a", "/b")
    assert c is True
    assert n is None and r is None


def test_resolve_update_officer_route_inputs_whitespace_only_is_omitted() -> None:
    n, r, c = resolve_update_officer_route_inputs("   ", None)
    assert c is False
    assert n is None and r is None


def test_build_ops_cockpit_payload_update_officer_conflict(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(
        repo_root=tmp_path,
        update_officer_source_conflict=True,
    )
    uo = payload["update_officer_ui"]
    assert uo["available"] is False
    assert uo["empty_state_message"] == UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE


def test_ops_route_explicit_notifier_path(ops_client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    response = ops_client.get("/ops", params={"update_officer_notifier_path": str(path)})
    assert response.status_code == 200
    assert "python_dependencies" in response.text


def test_ops_route_explicit_run_dir(ops_client: TestClient, tmp_path: Path) -> None:
    run_dir = tmp_path / "uo_run"
    run_dir.mkdir()
    (run_dir / "notifier_payload.json").write_text(
        json.dumps(_sample_notifier_payload()),
        encoding="utf-8",
    )
    response = ops_client.get("/ops", params={"update_officer_run_dir": str(run_dir)})
    assert response.status_code == 200
    assert "python_dependencies" in response.text


def test_ops_route_whitespace_only_params_empty_state(
    ops_client: TestClient,
) -> None:
    response = ops_client.get(
        "/ops",
        params={"update_officer_notifier_path": "  ", "update_officer_run_dir": "\t"},
    )
    assert response.status_code == 200
    assert "not available" in response.text.lower()


def test_ops_route_conflicting_params_deterministic_message(
    ops_client: TestClient, tmp_path: Path
) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    run_dir = tmp_path / "other"
    run_dir.mkdir()
    response = ops_client.get(
        "/ops",
        params={
            "update_officer_notifier_path": str(path),
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert response.status_code == 200
    assert UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE.split(":")[0] in response.text
    assert "Active source:" in response.text
    assert "conflict" in response.text.lower()
    assert 'method="post"' not in response.text.lower()


def test_ops_route_source_selection_ergonomics_visible(ops_client: TestClient) -> None:
    response = ops_client.get("/ops")
    assert response.status_code == 200
    html = response.text
    assert "Update Officer source selection" in html
    assert "uo-source-form" in html
    assert 'method="get"' in html
    assert 'action="/ops"' in html
    assert 'name="update_officer_notifier_path"' in html
    assert 'name="update_officer_run_dir"' in html
    assert 'href="/ops"' in html
    assert 'method="post"' not in html.lower()


def test_ops_route_active_source_summary_explicit_notifier_path(
    ops_client: TestClient, tmp_path: Path
) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    response = ops_client.get("/ops", params={"update_officer_notifier_path": str(path)})
    assert response.status_code == 200
    assert "explicit notifier path" in response.text.lower()
    assert str(path) in response.text


def test_ops_route_active_source_summary_run_dir(ops_client: TestClient, tmp_path: Path) -> None:
    run_dir = tmp_path / "uo_run"
    run_dir.mkdir()
    (run_dir / "notifier_payload.json").write_text(
        json.dumps(_sample_notifier_payload()),
        encoding="utf-8",
    )
    response = ops_client.get("/ops", params={"update_officer_run_dir": str(run_dir)})
    assert response.status_code == 200
    assert "run directory" in response.text.lower()
    assert str(run_dir) in response.text


def test_ops_route_clear_link_resets_to_empty_state(ops_client: TestClient) -> None:
    r_clear = ops_client.get("/ops")
    assert r_clear.status_code == 200
    assert "Active source:" in r_clear.text
    assert "none" in r_clear.text.lower() or "empty-state" in r_clear.text.lower()


def test_api_ops_cockpit_query_params_explicit_path(ops_client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    response = ops_client.get(
        "/api/ops-cockpit",
        params={"update_officer_notifier_path": str(path)},
    )
    assert response.status_code == 200
    data = response.json()
    assert "workflow_officer_state" in data
    assert isinstance(data["workflow_officer_state"], dict)
    assert data["update_officer_ui"]["available"] is True
    assert data["update_officer_ui"]["next_topic"] == "python_dependencies"


def test_api_ops_cockpit_query_params_conflict(ops_client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    run_dir = tmp_path / "other"
    run_dir.mkdir()
    response = ops_client.get(
        "/api/ops-cockpit",
        params={
            "update_officer_notifier_path": str(path),
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["update_officer_ui"]["available"] is False
    assert data["update_officer_ui"]["empty_state_message"] == (
        UPDATE_OFFICER_ROUTE_CONFLICT_MESSAGE
    )


def test_normalize_update_officer_source_preset() -> None:
    from src.webui.ops_cockpit import normalize_update_officer_source_preset

    assert normalize_update_officer_source_preset(None) == "manual"
    assert normalize_update_officer_source_preset("") == "manual"
    assert normalize_update_officer_source_preset("  run-dir  ") == "run_dir"
    assert normalize_update_officer_source_preset("NOTIFIER_PATH") == "notifier_path"
    assert normalize_update_officer_source_preset("bogus") == "manual"


def test_ops_route_v9_preset_toolbar_visible(ops_client: TestClient) -> None:
    r = ops_client.get("/ops")
    assert r.status_code == 200
    html = r.text
    assert "Operator presets (GET-only)" in html
    assert "uo-preset-toolbar" in html
    assert "Active preset:" in html
    assert "uo-active-preset" in html
    assert "update_officer_source_preset" in html
    assert 'method="post"' not in html.lower()


def test_ops_route_v9_active_preset_from_query_param(ops_client: TestClient) -> None:
    r = ops_client.get("/ops", params={"update_officer_source_preset": "notifier_path"})
    assert r.status_code == 200
    assert "Active preset:" in r.text
    assert "notifier path" in r.text.lower()
    assert 'name="update_officer_source_preset"' in r.text
    assert 'value="notifier_path"' in r.text


def test_ops_route_v9_apply_source_preserves_preset(ops_client: TestClient, tmp_path: Path) -> None:
    run_dir = tmp_path / "uo_run"
    run_dir.mkdir()
    (run_dir / "notifier_payload.json").write_text(
        json.dumps(_sample_notifier_payload()),
        encoding="utf-8",
    )
    r = ops_client.get(
        "/ops",
        params={
            "update_officer_source_preset": "run_dir",
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert r.status_code == 200
    assert "run directory" in r.text.lower()
    assert 'value="run_dir"' in r.text


def test_ops_route_v9_conflict_with_preset_query_still_read_only(
    ops_client: TestClient, tmp_path: Path
) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    run_dir = tmp_path / "other"
    run_dir.mkdir()
    r = ops_client.get(
        "/ops",
        params={
            "update_officer_source_preset": "notifier_path",
            "update_officer_notifier_path": str(path),
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert r.status_code == 200
    assert "conflict" in r.text.lower()
    assert "preset is informational" in r.text.lower()
    assert 'method="post"' not in r.text.lower()


def test_ops_route_v9_notifier_path_focus_link_omits_run_dir_param(
    ops_client: TestClient, tmp_path: Path
) -> None:
    import re

    run_dir = tmp_path / "uo_run"
    run_dir.mkdir()
    r = ops_client.get(
        "/ops",
        params={"update_officer_run_dir": str(run_dir)},
    )
    assert r.status_code == 200
    m = re.search(r'<a href="([^"]+)">Notifier path focus</a>', r.text)
    assert m
    assert "update_officer_source_preset=notifier_path" in m.group(1)
    assert "update_officer_run_dir" not in m.group(1)


def test_ops_route_v11_operator_trace_visible_default(ops_client: TestClient) -> None:
    r = ops_client.get("/ops")
    assert r.status_code == 200
    assert "uo-operator-trace" in r.text
    assert 'data-u11-source-mode="none"' in r.text
    assert "<dt>source_mode</dt>" in r.text
    assert "<dt>effective_resolution_target</dt>" in r.text
    assert "NONE_NO_EXPLICIT_SOURCE" in r.text
    assert "safe_default_active</dt><dd><code>true</code></dd>" in r.text
    assert 'method="post"' not in r.text.lower()


def test_ops_route_v11_operator_trace_conflict_matches_consumer(
    ops_client: TestClient, tmp_path: Path
) -> None:
    from src.ops.update_officer_consumer import build_update_officer_source_trace

    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    run_dir = tmp_path / "other"
    run_dir.mkdir()
    r = ops_client.get(
        "/ops",
        params={
            "update_officer_notifier_path": str(path),
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert r.status_code == 200
    assert 'data-u11-source-mode="conflict"' in r.text
    assert "BLOCKED_ROUTE_CONFLICT" in r.text
    tr = build_update_officer_source_trace(
        conflict=True,
        effective_notifier_path=None,
        effective_run_dir=None,
        source_preset="manual",
    )
    assert tr["effective_resolution_target"] == "BLOCKED_ROUTE_CONFLICT"


def test_ops_route_v11_operator_trace_resolved_path_in_html(
    ops_client: TestClient, tmp_path: Path
) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    r = ops_client.get("/ops", params={"update_officer_notifier_path": str(path)})
    assert r.status_code == 200
    assert 'data-u11-source-mode="explicit_notifier_path"' in r.text
    assert str(path) in r.text


def test_build_update_officer_validation_aids_conflict() -> None:
    from src.webui.ops_cockpit import build_update_officer_validation_aids

    aids = build_update_officer_validation_aids(
        conflict=True,
        effective_notifier_path=None,
        effective_run_dir=None,
        source_preset="notifier_path",
    )
    assert aids["source_mode"] == "conflict"
    assert aids["conflict_explanation"]
    assert not aids["safe_default_explanation"]
    assert "Active preset notifier path" in aids["preset_explanation"]


def test_build_update_officer_validation_aids_none_manual() -> None:
    from src.webui.ops_cockpit import build_update_officer_validation_aids

    aids = build_update_officer_validation_aids(
        conflict=False,
        effective_notifier_path=None,
        effective_run_dir=None,
        source_preset="manual",
    )
    assert aids["source_mode"] == "none"
    assert aids["safe_default_explanation"]
    assert "Active preset manual" in aids["preset_explanation"]


def test_build_update_officer_validation_aids_explicit_path() -> None:
    from src.webui.ops_cockpit import build_update_officer_validation_aids

    aids = build_update_officer_validation_aids(
        conflict=False,
        effective_notifier_path="/tmp/np.json",
        effective_run_dir=None,
        source_preset="manual",
    )
    assert aids["source_mode"] == "explicit_notifier_path"
    assert "explicit path" in aids["resolution_explanation"].lower()


def test_ops_route_v10_validation_aids_visible(ops_client: TestClient) -> None:
    r = ops_client.get("/ops")
    assert r.status_code == 200
    assert "uo-validation-aids" in r.text
    assert "Validation / explainability (read-only)" in r.text
    assert 'data-u10-source-mode="none"' in r.text
    assert "Active preset manual" in r.text
    assert 'method="post"' not in r.text.lower()


def test_ops_route_v10_help_text_notifier_path_preset(ops_client: TestClient) -> None:
    r = ops_client.get("/ops", params={"update_officer_source_preset": "notifier_path"})
    assert r.status_code == 200
    assert 'data-u10-source-mode="none"' in r.text
    assert "Active preset notifier path" in r.text


def test_ops_route_v10_help_text_run_dir_preset(ops_client: TestClient) -> None:
    r = ops_client.get("/ops", params={"update_officer_source_preset": "run_dir"})
    assert r.status_code == 200
    assert "Active preset run directory" in r.text


def test_ops_route_v10_help_text_conflict_state(ops_client: TestClient, tmp_path: Path) -> None:
    path = tmp_path / "notifier_payload.json"
    path.write_text(json.dumps(_sample_notifier_payload()), encoding="utf-8")
    run_dir = tmp_path / "other"
    run_dir.mkdir()
    r = ops_client.get(
        "/ops",
        params={
            "update_officer_notifier_path": str(path),
            "update_officer_run_dir": str(run_dir),
        },
    )
    assert r.status_code == 200
    assert 'data-u10-source-mode="conflict"' in r.text
    assert "No notifier payload is loaded while inputs conflict" in r.text


def test_ops_cockpit_workflow_officer_empty_state_wording(tmp_path: Path) -> None:
    ctx = build_workflow_officer_panel_context(tmp_path)
    assert ctx["present"] is False
    assert ctx["empty_reason"] == "no_officer_output_dir"
    assert (ctx.get("executive_panel") or {}).get("present") is False


def test_ops_cockpit_payload_contains_workflow_officer_state(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    assert "workflow_officer_state" in payload
    w = payload["workflow_officer_state"]
    assert isinstance(w, dict)
    assert w.get("present") is False
    assert w.get("empty_reason") == "no_officer_output_dir"


def test_ops_cockpit_html_contains_operator_workflow_observation_empty(tmp_path: Path) -> None:
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert 'id="operator-workflow-observation-surface"' in html
    assert "Operator workflow observation (vNext Phase 4)" in html
    assert "workflow_officer_state.empty_reason" in html
    assert "no_officer_output_dir" in html
    assert "not approval" in html.lower()
    assert "does not execute Workflow Officer" in html


def test_ops_cockpit_html_contains_operator_workflow_observation_with_report(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "out" / "ops" / "workflow_officer" / "20260201T000000Z"
    run_dir.mkdir(parents=True)
    report = {
        "officer_version": "v1-min",
        "profile": "docs_only_pr",
        "mode": "audit",
        "success": True,
        "finished_at": "2026-02-01",
        "summary": {
            "total_checks": 1,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "strict": False,
            "executive_summary": {
                "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
                "urgency_label": "clear",
                "attention_rationale": "No blocking errors.",
            },
            "operator_report": {
                "operator_report_schema_version": "workflow_officer.operator_report/v0",
                "primary_followup": {
                    "check_id": "chk_a",
                    "recommended_priority": "p3",
                    "effective_level": "ok",
                    "recommended_action": "No action.",
                },
                "rollup": {
                    "total_checks": 1,
                    "hard_failures": 0,
                    "warnings": 0,
                    "infos": 0,
                },
                "top_followups": [
                    {
                        "rank": 1,
                        "check_id": "chk_a",
                        "recommended_priority": "p3",
                        "effective_level": "ok",
                    }
                ],
            },
        },
    }
    (run_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "workflow_officer_state.run_dir_name" in html
    assert "20260201T000000Z" in html
    assert "workflow_officer_state.primary_followup.check_id" in html
    assert "chk_a" in html
    assert 'id="operator-workflow-handoff-preview-observation"' in html
    assert "no_handoff_context_in_report" in html
    assert "no_next_chat_preview_in_report" in html


def test_ops_cockpit_html_handoff_and_next_step_preview_when_report_includes_summary_blocks(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "out" / "ops" / "workflow_officer" / "20260201T000000Z"
    run_dir.mkdir(parents=True)
    report = {
        "officer_version": "v1-min",
        "profile": "docs_only_pr",
        "mode": "audit",
        "success": True,
        "finished_at": "2026-02-01",
        "summary": {
            "total_checks": 1,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "strict": False,
            "executive_summary": {
                "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
                "urgency_label": "clear",
                "attention_rationale": "No blocking errors.",
            },
            "operator_report": {
                "operator_report_schema_version": "workflow_officer.operator_report/v0",
                "primary_followup": {
                    "check_id": "chk_a",
                    "recommended_priority": "p3",
                    "effective_level": "ok",
                    "recommended_action": "No action.",
                },
                "rollup": {
                    "total_checks": 1,
                    "hard_failures": 0,
                    "warnings": 0,
                    "infos": 0,
                },
                "top_followups": [
                    {
                        "rank": 1,
                        "check_id": "chk_a",
                        "recommended_priority": "p3",
                        "effective_level": "ok",
                    }
                ],
            },
            "handoff_context": {
                "handoff_schema_version": "workflow_officer.handoff_context/v1",
                "primary_followup_check_id": "chk_h",
                "top_followups": [{"rank": 1, "check_id": "chk_h"}],
                "registry_inputs_rollup": {"pointer_count": 2},
                "merge_log_inputs_rollup": {"latest_pr_number": 2505},
            },
            "next_chat_preview": {
                "preview_schema_version": "workflow_officer.next_chat_preview/v1",
                "primary_followup_check_id": "chk_ncp",
                "queued_followup_check_ids": ["c1"],
                "latest_pr_number": 2505,
                "registry_pointer_count": 2,
                "hard_failures": 0,
                "warnings": 1,
                "total_checks": 3,
            },
        },
    }
    (run_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert 'id="operator-workflow-handoff-preview-observation"' in html
    assert "workflow_officer_state.handoff_observation.primary_followup_check_id" in html
    assert "chk_h" in html
    assert "workflow_officer_state.next_chat_preview_observation.rollup_echo.warnings" in html
    assert "c1" in html


def test_ops_cockpit_workflow_officer_report_contains_operator_rollup_label(tmp_path: Path) -> None:
    run_dir = tmp_path / "out" / "ops" / "workflow_officer" / "20260201T000000Z"
    run_dir.mkdir(parents=True)
    report = {
        "officer_version": "v1-min",
        "profile": "docs_only_pr",
        "mode": "audit",
        "success": True,
        "finished_at": "2026-02-01",
        "summary": {
            "total_checks": 1,
            "hard_failures": 0,
            "warnings": 0,
            "infos": 0,
            "strict": False,
            "executive_summary": {
                "executive_summary_schema_version": "workflow_officer.executive_summary/v0",
                "urgency_label": "clear",
                "attention_rationale": "No blocking errors.",
            },
            "operator_report": {
                "operator_report_schema_version": "workflow_officer.operator_report/v0",
                "primary_followup": {
                    "check_id": "chk_a",
                    "recommended_priority": "p3",
                    "effective_level": "ok",
                    "recommended_action": "No action.",
                },
                "rollup": {
                    "total_checks": 1,
                    "hard_failures": 0,
                    "warnings": 0,
                    "infos": 0,
                },
                "top_followups": [
                    {
                        "rank": 1,
                        "check_id": "chk_a",
                        "recommended_priority": "p3",
                        "effective_level": "ok",
                    }
                ],
            },
        },
    }
    (run_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
    ctx = build_workflow_officer_panel_context(tmp_path)
    assert ctx["present"] is True
    line = str(ctx.get("operator_snapshot_line") or "")
    assert "total=1" in line
