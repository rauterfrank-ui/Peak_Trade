from pathlib import Path

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
    assert payload["run_state"]["status"] == "idle"
    assert payload["incident_state"]["status"] == "blocked"
    assert payload["incident_state"]["blocked"] is True
    assert payload["incident_state"]["kill_switch_active"] is False
    assert payload["incident_state"]["degraded"] is False
    assert payload["incident_state"]["requires_operator_attention"] is True
    assert payload["incident_state"]["summary"] == "blocked"
    assert payload["run_state"]["active"] is False
    assert payload["run_state"]["last_run_status"] == "unknown"
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
