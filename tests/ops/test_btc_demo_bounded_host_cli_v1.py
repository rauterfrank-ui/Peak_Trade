"""The default host command must remain offline preparation."""

import json

import pytest

from scripts.ops import run_btc_demo_bounded_host_v1 as cli
from tests.ops.test_btc_demo_bounded_host_v1 import (
    runtime_case as runtime_case,
    demo_entry as demo_entry,
    no_network as no_network,
    synthetic_active_post_safety_v1 as synthetic_active_post_safety_v1,
)


def test_default_cli_never_opens_signer_or_runtime(runtime_case, monkeypatch, capsys, tmp_path):
    runtime, _, venue = runtime_case
    config = tmp_path / "prepared.json"
    config.write_text(json.dumps(runtime.config))

    def forbidden(*args, **kwargs):
        raise AssertionError("Preparation cannot open credentials or run")

    monkeypatch.setattr(cli, "macos_demo_signer_v1", forbidden)
    monkeypatch.setattr(cli, "BtcDemoRuntimeV1", forbidden)
    assert cli.main(["--config", str(config)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["session_started"] is False and result["credentials_accessed"] is False
    assert result["orders_sent"] == 0 and not runtime.root.exists() and not venue.calls


def test_run_without_explicit_start_never_opens_credentials(runtime_case, monkeypatch, tmp_path):
    runtime, _, venue = runtime_case
    config = tmp_path / "prepared.json"
    config.write_text(json.dumps(runtime.config))

    def forbidden(*args, **kwargs):
        raise AssertionError("No implicit start")

    monkeypatch.setattr(cli, "macos_demo_signer_v1", forbidden)
    with pytest.raises(SystemExit) as caught:
        cli.main(["--config", str(config), "--run"])
    assert caught.value.code == 2 and not runtime.root.exists() and not venue.calls
