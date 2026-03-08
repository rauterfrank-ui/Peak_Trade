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


def test_ops_cockpit_html_contains_truth_first_text(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs" / "governance" / "ai"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "CRITIC_RUNTIME_RESOLUTION_V2.md").write_text(
        "# Critic Runtime Resolution v2\n", encoding="utf-8"
    )
    html = render_ops_cockpit_html(repo_root=tmp_path)
    assert "Ops Cockpit v2.3 — Truth-First" in html
    assert "AI Boundary State" in html
    assert "Runtime Unknown State" in html
    assert "Truth coverage" in html
    assert "Priority buckets" in html


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


def test_priority_counts_present(tmp_path: Path) -> None:
    payload = build_ops_cockpit_payload(repo_root=tmp_path)
    counts = payload["truth_state"]["priority_counts"]
    assert "canonical_boundary" in counts
    assert "runtime_resolution" in counts
    assert "supporting_truth" in counts
