from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"


def test_operator_python_environment_note_documents_uv_run_preference() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "Operator Python Environment Note v0" in text
    assert "`uv run python`" in text
    assert "not a system Python such as `/usr/bin/python3`" in text
    assert "`prometheus_client` is available in the project-managed environment" in text
    assert "Apple Command Line Tools Python may not include it" in text
    assert "optional warning `prometheus_client not installed`" in text
    assert "non-fatal for the current Paper-only evidence gates" in text
    assert "reduces observability quality" in text


def test_operator_python_environment_note_is_non_authorizing() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "This note does **not** change runtime authorization." in text
    assert "It does not authorize daemon execution" in text
    assert "scheduler execution" in text
    assert "Paper runtime" in text
    assert "Shadow runtime" in text
    assert "Testnet" in text
    assert "Live" in text
    assert "broker" in text
    assert "exchange" in text
    assert "order submission" in text
