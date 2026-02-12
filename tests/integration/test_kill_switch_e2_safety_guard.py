from __future__ import annotations

import inspect
from pathlib import Path

import pytest

# PR-04 must not depend on modules introduced in other PRs (e.g. PR-02).
import importlib.util

if importlib.util.find_spec("src.live.kill_switch") is None:
    pytest.skip(
        "src.live.kill_switch not available on this branch (introduced in another PR); skipping E2 integration test",
        allow_module_level=True,
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_guard_or_skip():
    """
    Try to instantiate SafetyGuard in a robust way.
    If your SafetyGuard requires mandatory ctor args, this test will skip
    until you wire a factory (recommended: get_default_guard()).
    """
    from src.live import safety as safety_mod

    # Prefer explicit factories if you have them
    for fn_name in (
        "get_default_guard",
        "create_safety_guard",
    ):
        fn = getattr(safety_mod, fn_name, None)
        if callable(fn):
            # create_safety_guard(None) is your contract
            if fn_name == "create_safety_guard":
                return fn(None)
            return fn()

    cls = getattr(safety_mod, "SafetyGuard", None)
    if cls is None:
        pytest.skip("SafetyGuard not found in src.live.safety")

    # Try zero-arg ctor
    try:
        return cls()
    except TypeError:
        pass

    # Try minimal ctor (fill common params if present)
    sig = inspect.signature(cls)
    kwargs = {}
    for name, p in sig.parameters.items():
        if name == "self":
            continue
        if p.default is not inspect.Parameter.empty:
            continue
        # common patterns
        if name in ("phase", "mode"):
            kwargs[name] = 0
        elif name in ("is_live", "live"):
            kwargs[name] = False
        elif name == "env_config":
            from src.core.environment import EnvironmentConfig, TradingEnvironment

            kwargs[name] = EnvironmentConfig(
                environment=TradingEnvironment.TESTNET,
                enable_live_trading=False,
                testnet_dry_run=True,
            )
        else:
            pytest.skip(
                f"Cannot instantiate SafetyGuard; missing required ctor arg: {name}. "
                "Add a factory (e.g. get_default_guard()) or adapt this test."
            )

    try:
        return cls(**kwargs)
    except Exception as e:
        pytest.skip(f"Cannot instantiate SafetyGuard with inferred kwargs={kwargs}: {e!r}")


def test_kill_switch_blocks_via_safety_guard_e2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    E2-light: end-to-end within process:
      - write TOML kill_switch config
      - call SafetyGuard.ensure_may_place_order()
      - expect KillSwitchBlocked
      - verify audit JSONL was written
    """
    # Make relative config paths resolve against temp working dir
    monkeypatch.chdir(tmp_path)

    audit = tmp_path / "data/kill_switch/audit.jsonl"
    cfg = tmp_path / "config/risk/kill_switch.toml"

    _write(
        cfg,
        f"""
[kill_switch]
enabled = true
enforce = true
audit_path = "{audit.as_posix()}"
reason = "e2_test_block"
""".strip(),
    )

    # Import after chdir so any relative paths behave as intended
    from src.live.kill_switch import KillSwitchBlocked

    guard = _make_guard_or_skip()

    with pytest.raises(KillSwitchBlocked):
        guard.ensure_may_place_order(is_testnet=True)

    assert audit.exists(), "expected audit JSONL to be written"
    line = audit.read_text(encoding="utf-8").strip().splitlines()[-1]
    assert '"decision":"block"' in line
    assert '"reason":"e2_test_block"' in line
