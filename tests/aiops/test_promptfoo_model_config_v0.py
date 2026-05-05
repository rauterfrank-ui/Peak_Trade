from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "evals" / "aiops" / "promptfooconfig.yaml"
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_promptfoo_eval.sh"


def test_promptfoo_config_uses_env_configurable_gpt55_default() -> None:
    config_text = CONFIG.read_text(encoding="utf-8")
    data = yaml.safe_load(config_text)

    assert data["providers"] == ["openai:chat:__PROMPTFOO_OPENAI_MODEL__"]
    assert "openai:gpt-4" not in config_text


def test_promptfoo_runner_exports_model_default_without_secret_values() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")

    assert 'PROMPTFOO_OPENAI_MODEL="${PROMPTFOO_OPENAI_MODEL:-gpt-5.5}"' in runner_text
    assert "export PROMPTFOO_OPENAI_MODEL" in runner_text
    assert "OPENAI_API_KEY" in runner_text
    assert "OpenAI model:" in runner_text


def test_promptfoo_config_change_is_static_only() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")

    assert "promptfoo" in runner_text
    assert "run-shadow" not in runner_text
    assert "run_scheduler" not in runner_text


def test_promptfoo_runner_resolves_config_before_eval() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")

    assert "RESOLVED_CONFIG_PATH=" in runner_text
    assert "__PROMPTFOO_OPENAI_MODEL__" in runner_text
    assert "PROMPTFOO_OPENAI_MODEL" in runner_text
    assert 'eval -c "$RESOLVED_CONFIG_PATH"' in runner_text
