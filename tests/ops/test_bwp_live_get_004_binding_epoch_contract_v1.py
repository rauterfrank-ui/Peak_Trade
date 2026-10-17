"""Parser contract for the productive live-C1 launcher binding epoch.

No venue I/O and no Keychain session. The consumer path stops at the existing
selection-budget fail-closed gate, which is before inventory acquisition.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import urllib.request
from pathlib import Path
from types import ModuleType

import pytest

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    MAY_POST as K1_MAY_POST,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PATH = (
    REPO_ROOT
    / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)
_UTC_SENTINEL = "2099-01-01T00:00:00Z"
_EXPLICIT_EPOCH = "2026-01-02T03:04:05Z"


class _StopAfterParse(Exception):
    """Abort after the real ArgumentParser returns, before any later effect."""


def _load_launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "bwp_live_get_004_policy_governed_launcher_v1",
        LAUNCHER_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("LAUNCHER_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _refuse_http(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("VENUE_HTTP_FORBIDDEN")


def _invoke(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    extra: list[str],
    *,
    stop_after_parse: bool,
) -> tuple[argparse.Namespace, list[str], int | None, str]:
    module = _load_launcher()
    captured: dict[str, argparse.Namespace] = {}
    utc_calls: list[str] = []
    real_parse = argparse.ArgumentParser.parse_args

    def _wrapped_parse(
        self: argparse.ArgumentParser,
        args: list[str] | None = None,
        namespace: argparse.Namespace | None = None,
    ) -> argparse.Namespace:
        parsed = real_parse(self, args=args, namespace=namespace)
        if "ns" not in captured:
            captured["ns"] = parsed
            if stop_after_parse:
                raise _StopAfterParse()
        return parsed

    def _utc_iso() -> str:
        utc_calls.append(_UTC_SENTINEL)
        return _UTC_SENTINEL

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", _wrapped_parse)
    monkeypatch.setattr(module, "_utc_iso", _utc_iso)
    monkeypatch.setattr(urllib.request, "urlopen", _refuse_http)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(LAUNCHER_PATH),
            "--evidence-root",
            str(tmp_path / "evidence"),
            "--lane-state-root",
            str(tmp_path / "lane"),
            "--productivity-root",
            str(tmp_path / "productivity"),
            "--wp-branch-evidence-run",
            *extra,
        ],
    )
    if stop_after_parse:
        with pytest.raises(_StopAfterParse):
            module._main()
        return captured["ns"], utc_calls, None, ""
    rc = module._main()
    return captured["ns"], utc_calls, rc, ""


def test_default_binding_epoch_parses_as_none(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    namespace, _calls, rc, _out = _invoke(monkeypatch, tmp_path, [], stop_after_parse=True)
    assert rc is None
    assert namespace.binding_epoch is None


def test_explicit_binding_epoch_is_adopted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    namespace, _calls, _rc, _out = _invoke(
        monkeypatch,
        tmp_path,
        ["--binding-epoch", _EXPLICIT_EPOCH],
        stop_after_parse=True,
    )
    assert namespace.binding_epoch == _EXPLICIT_EPOCH


def test_omitted_binding_epoch_uses_utc_iso_fallback_before_http(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace, calls, rc, _out = _invoke(monkeypatch, tmp_path, [], stop_after_parse=False)
    payload = json.loads(capsys.readouterr().out)
    assert namespace.binding_epoch is None
    assert calls == [_UTC_SENTINEL]
    assert rc == 2
    assert payload["status"] == "FAIL"
    assert payload["blocker"] == "SELECTION_GET_BUDGET_EXPLICIT_REQUIRED"
    assert (namespace.binding_epoch or calls[0]) == _UTC_SENTINEL


def test_explicit_binding_epoch_skips_utc_fallback_on_consumer_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace, calls, rc, _out = _invoke(
        monkeypatch,
        tmp_path,
        ["--binding-epoch", _EXPLICIT_EPOCH],
        stop_after_parse=False,
    )
    payload = json.loads(capsys.readouterr().out)
    assert namespace.binding_epoch == _EXPLICIT_EPOCH
    assert calls == []
    assert rc == 2
    assert payload["blocker"] == "SELECTION_GET_BUDGET_EXPLICIT_REQUIRED"
    assert (namespace.binding_epoch or "UNUSED") == _EXPLICIT_EPOCH


def test_selection_get_budget_flag_default_and_explicit_value_unchanged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    omitted, _calls, _rc, _out = _invoke(monkeypatch, tmp_path, [], stop_after_parse=True)
    explicit, _calls, _rc, _out = _invoke(
        monkeypatch,
        tmp_path,
        ["--selection-max-total-get-attempts", "6"],
        stop_after_parse=True,
    )
    assert omitted.selection_max_total_get_attempts is None
    assert explicit.selection_max_total_get_attempts == 6
    text = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert text.index("SELECTION_GET_BUDGET_EXPLICIT_REQUIRED") < text.index(
        "acquire_eea_universe_inventory_v1("
    )


def test_consumer_path_does_not_raise_attribute_error_for_binding_epoch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _namespace, _calls, rc, _out = _invoke(monkeypatch, tmp_path, [], stop_after_parse=False)
    captured = capsys.readouterr()
    assert rc == 2
    assert "AttributeError" not in captured.err
    assert "binding_epoch" not in captured.err
    payload = json.loads(captured.out)
    assert payload["blocker"] == "SELECTION_GET_BUDGET_EXPLICIT_REQUIRED"


def test_optional_binding_epoch_does_not_weaken_safety_invariants() -> None:
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert K1_MAY_POST is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    text = LAUNCHER_PATH.read_text(encoding="utf-8")
    assert "LIVE_TRADING_AUTHORIZED = True" not in text
    assert "POST_ALLOWED = True" not in text
    assert "K1_MAY_POST = True" not in text
    assert "REAL_VENUE_POST_ALLOWED = True" not in text
    assert "EXTERNAL_EFFECT_AUTHORIZED = True" not in text
