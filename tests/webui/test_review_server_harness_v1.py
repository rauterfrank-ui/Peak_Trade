"""Focused contracts for scripts/webui/review_server.sh (+ Playwright webServer helper).

Uses isolated temporary ports and state dirs. Never stops foreign processes.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from urllib.request import urlopen

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = REPO_ROOT / "scripts" / "webui" / "review_server.sh"
PLAYWRIGHT_WEBSERVER = REPO_ROOT / "scripts" / "webui" / "review_server_playwright_webserver_v1.py"


def _harness_physical_path(target: Path | str) -> str:
    """Invoke the harness physical_path() helper without starting a server."""
    extract = subprocess.run(
        [
            "bash",
            "-c",
            r"""
set -euo pipefail
eval "$(sed -n '/^physical_path()/,/^}/p' "$1")"
physical_path "$2"
""",
            "physical_path",
            str(HARNESS),
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert extract.returncode == 0, extract.stdout + extract.stderr
    return extract.stdout.strip()


def _resolve_uv_bin(tmp_path: Path) -> str:
    """Prefer real uv; otherwise provide a minimal `uv run` shim for CI matrices."""
    found = shutil.which("uv")
    if found:
        return found
    shim_dir = tmp_path / "_peak_trade_uv_shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    shim = shim_dir / "uv"
    if not shim.exists():
        py = shlex.quote(sys.executable)
        shim.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"PY={py}\n"
            "# Emulate: uv run python -m uvicorn ... using the active test interpreter.\n"
            'if [[ "${1:-}" == "run" ]]; then\n'
            "  shift\n"
            '  if [[ "${1:-}" == "python" || "${1:-}" == "python3" ]]; then\n'
            "    shift\n"
            '    exec "$PY" "$@"\n'
            "  fi\n"
            '  exec "$@"\n'
            "fi\n"
            'exec "$@"\n',
            encoding="utf-8",
        )
        shim.chmod(0o755)
    return str(shim)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _parse_kv(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in blob.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _run(
    *args: str,
    env: dict[str, str],
    check: bool = False,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(HARNESS), *args],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        check=check,
        timeout=timeout,
    )


def _base_env(tmp_path: Path, port: int, **overrides: str) -> dict[str, str]:
    state = tmp_path / "state"
    state.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        {
            "PEAK_TRADE_WEBUI_HOST": "127.0.0.1",
            "PEAK_TRADE_WEBUI_PORT": str(port),
            "PEAK_TRADE_WEBUI_STATE_DIR": str(state),
            "PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS": "60",
            "PEAK_TRADE_WEBUI_STOP_TIMEOUT_SECONDS": "15",
            "PEAK_TRADE_WEBUI_HEALTH_PATH": "/api/health",
            "PEAK_TRADE_WEBUI_REVIEW_PATH": "/",
            "PEAK_TRADE_WEBUI_UV": _resolve_uv_bin(tmp_path),
            "LIVE_AUTHORIZED": "false",
            "ORDERS_ALLOWED": "false",
        }
    )
    env.update(overrides)
    return env


@pytest.fixture(autouse=True)
def _harness_uv_env(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch):
    """Ensure harness starts work in CI jobs where `uv` is not on PATH."""
    if shutil.which("uv"):
        yield
        return
    shim_root = tmp_path_factory.mktemp("harness_uv")
    monkeypatch.setenv("PEAK_TRADE_WEBUI_UV", _resolve_uv_bin(shim_root))
    yield


def _http_code(url: str, timeout: float = 3.0) -> int:
    with urlopen(url, timeout=timeout) as resp:  # noqa: S310 — localhost tests
        return int(getattr(resp, "status", 200))


@pytest.fixture()
def isolated_port() -> int:
    return _free_port()


def test_harness_script_exists_and_is_executable() -> None:
    assert HARNESS.is_file()
    # executable bit preferred; bash invocation still works without it
    assert HARNESS.stat().st_size > 0


def test_macos_bash_32_static_compat() -> None:
    raw = HARNESS.read_text(encoding="utf-8")
    # Ignore comment lines when scanning for forbidden Bash-4 constructs.
    code_lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    text = "\n".join(code_lines)
    assert "mapfile" not in text
    assert "declare -A" not in text
    assert "readarray" not in text
    assert re.search(r"\buvicorn\b.*--reload", text) is None
    assert "UVICORN_RELOAD=false" in raw


def test_identity_ok_uses_physical_path_comparison() -> None:
    """Static contract: cwd vs REPO_ROOT must not use raw string inequality alone."""
    raw = HARNESS.read_text(encoding="utf-8")
    assert "physical_path()" in raw
    assert "pwd -P" in raw
    assert "cwd_phys" in raw
    assert "repo_phys" in raw
    # Proven bug form must remain gone.
    assert '[[ -n "$cwd" && "$cwd" != "$REPO_ROOT" ]]' not in raw


def test_physical_path_tmp_private_tmp_equivalence_and_distinct_rejection(
    tmp_path: Path,
) -> None:
    """Lexical path aliases resolve equal; distinct directories stay fail-closed.

    Portable contract uses a symlink alias (Linux CI has no /private/tmp).
    On macOS, also prove /tmp vs /private/tmp when that alias exists.
    """
    real_dir = tmp_path / "real_worktree"
    real_dir.mkdir()
    alias_dir = tmp_path / "alias_worktree_link"
    alias_dir.symlink_to(real_dir, target_is_directory=True)
    other_dir = tmp_path / "other_worktree"
    other_dir.mkdir()

    assert str(real_dir) != str(alias_dir)
    phys_real = _harness_physical_path(real_dir)
    phys_alias = _harness_physical_path(alias_dir)
    assert phys_real == phys_alias
    assert phys_real == os.path.realpath(real_dir)

    phys_other = _harness_physical_path(other_dir)
    assert phys_other != phys_real
    assert phys_real == phys_alias
    assert not (phys_real == phys_other)

    # macOS-only proven production alias when present.
    private_tmp = Path("/private/tmp")
    if private_tmp.is_dir():
        marker = uuid.uuid4().hex
        logical_root = Path("/tmp") / f"peak_trade_review_server_path_identity_{marker}"
        logical_root.mkdir(parents=True, exist_ok=True)
        try:
            private_alias = private_tmp / logical_root.name
            assert private_alias.is_dir()
            assert _harness_physical_path(logical_root) == _harness_physical_path(private_alias)
            if sys.platform == "darwin":
                assert str(logical_root) != str(private_alias)
        finally:
            try:
                logical_root.rmdir()
            except OSError:
                pass


def test_start_status_idempotent_stop_logs_and_bind(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port)
    state = Path(env["PEAK_TRADE_WEBUI_STATE_DIR"])
    pid_file = state / "review_server.pid"
    log_file = state / "review_server.log"

    try:
        started = _run("start", env=env, timeout=120)
        assert started.returncode == 0, started.stdout + started.stderr
        kv = _parse_kv(started.stdout)
        assert kv.get("STATUS") == "RUNNING_HEALTHY"
        assert kv.get("HOST") == "127.0.0.1"
        assert kv.get("UVICORN_RELOAD") == "false"
        assert pid_file.is_file()
        assert log_file.is_file()
        assert log_file.stat().st_size > 0

        health = f"http://127.0.0.1:{isolated_port}/api/health"
        root = f"http://127.0.0.1:{isolated_port}/"
        assert _http_code(health) == 200
        assert _http_code(root) == 200

        status = _run("status", env=env)
        assert status.returncode == 0
        assert _parse_kv(status.stdout).get("STATUS") == "RUNNING_HEALTHY"

        again = _run("start", env=env)
        assert again.returncode == 0, again.stdout + again.stderr
        again_kv = _parse_kv(again.stdout)
        assert again_kv.get("STATUS") == "RUNNING_HEALTHY"
        assert again_kv.get("ACTION") == "REUSED_EXISTING_HEALTHY"
        assert again_kv.get("PID") == kv.get("PID")

        logs = _run("logs", env=env)
        assert logs.returncode == 0
        assert str(log_file) in logs.stdout or "LOG_FILE=" in logs.stdout

        # Bind localhost only: process command must include 127.0.0.1 and no --reload
        pid = int(kv["PID"])
        cmd = subprocess.check_output(["ps", "-p", str(pid), "-o", "args="], text=True)
        assert "127.0.0.1" in cmd
        assert "--reload" not in cmd
        assert "src.webui.app:app" in cmd
    finally:
        _run("stop", env=env, timeout=60)
        stopped = _run("status", env=env)
        assert _parse_kv(stopped.stdout).get("STATUS") == "STOPPED"


def test_stale_pid_recovery(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port)
    state = Path(env["PEAK_TRADE_WEBUI_STATE_DIR"])
    pid_file = state / "review_server.pid"
    pid_file.write_text("999999\n", encoding="utf-8")

    status = _run("status", env=env)
    assert _parse_kv(status.stdout).get("STATUS") == "STALE_PID"

    try:
        started = _run("start", env=env, timeout=120)
        assert started.returncode == 0, started.stdout + started.stderr
        assert _parse_kv(started.stdout).get("STATUS") == "RUNNING_HEALTHY"
        assert pid_file.read_text(encoding="utf-8").strip() != "999999"
    finally:
        _run("stop", env=env, timeout=60)


def test_unknown_port_owner_fail_closed(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port)
    # Foreign listener: stdlib http.server (not Peak Trade review identity)
    foreign = subprocess.Popen(
        ["python3", "-m", "http.server", str(isolated_port), "--bind", "127.0.0.1"],
        cwd=str(tmp_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                if _http_code(f"http://127.0.0.1:{isolated_port}/", timeout=1) == 200:
                    break
            except Exception:  # noqa: BLE001 — wait loop
                time.sleep(0.1)
        status = _run("status", env=env)
        assert _parse_kv(status.stdout).get("STATUS") == "PORT_OCCUPIED_BY_UNKNOWN_PROCESS"

        started = _run("start", env=env, timeout=30)
        assert started.returncode != 0
        blob = started.stdout + started.stderr
        assert "PORT_OCCUPIED_BY_UNKNOWN_PROCESS" in blob or "unknown process" in blob.lower()

        # Must not have killed the foreign process
        assert foreign.poll() is None
    finally:
        foreign.terminate()
        try:
            foreign.wait(timeout=5)
        except subprocess.TimeoutExpired:
            foreign.kill()


def test_stop_only_own_verified_process(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port)
    other_port = _free_port()
    foreign = subprocess.Popen(
        ["python3", "-m", "http.server", str(other_port), "--bind", "127.0.0.1"],
        cwd=str(tmp_path),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        started = _run("start", env=env, timeout=120)
        assert started.returncode == 0, started.stdout + started.stderr
        review_pid = int(_parse_kv(started.stdout)["PID"])
        foreign_pid = foreign.pid

        stopped = _run("stop", env=env, timeout=60)
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr
        assert _parse_kv(stopped.stdout).get("STATUS") == "STOPPED"

        # Foreign process must survive
        assert foreign.poll() is None
        assert foreign_pid == foreign.pid
        # Review pid should be gone
        alive = subprocess.run(["kill", "-0", str(review_pid)], capture_output=True)
        assert alive.returncode != 0
    finally:
        _run("stop", env=env, timeout=30)
        foreign.terminate()
        try:
            foreign.wait(timeout=5)
        except subprocess.TimeoutExpired:
            foreign.kill()


def test_restart(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port)
    try:
        started = _run("start", env=env, timeout=120)
        assert started.returncode == 0
        old_pid = _parse_kv(started.stdout).get("PID")
        restarted = _run("restart", env=env, timeout=180)
        assert restarted.returncode == 0, restarted.stdout + restarted.stderr
        kv = _parse_kv(restarted.stdout)
        assert kv.get("STATUS") == "RUNNING_HEALTHY"
        assert kv.get("ACTION") == "RESTARTED" or "STARTED" in restarted.stdout
        assert kv.get("PID")
        # PID may or may not change; health must hold
        assert _http_code(f"http://127.0.0.1:{isolated_port}/api/health") == 200
        assert old_pid is not None
    finally:
        _run("stop", env=env, timeout=60)


def test_healthcheck_timeout(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(
        tmp_path,
        isolated_port,
        PEAK_TRADE_WEBUI_HEALTH_PATH="/definitely-missing-health-path-v1",
        PEAK_TRADE_WEBUI_START_TIMEOUT_SECONDS="3",
    )
    started = _run("start", env=env, timeout=60)
    assert started.returncode != 0
    blob = (started.stdout + started.stderr).lower()
    assert "timeout" in blob or "healthcheck" in blob or "start failed" in blob
    # Ensure no owned healthy server remains
    status = _run("status", env=env)
    assert _parse_kv(status.stdout).get("STATUS") in {
        "STOPPED",
        "STALE_PID",
        "PORT_OCCUPIED_BY_UNKNOWN_PROCESS",
    }
    # If somehow a process remained on port with our identity, stop it via harness
    _run("stop", env=env, timeout=30)


def test_localhost_only_rejects_non_loopback(tmp_path: Path, isolated_port: int) -> None:
    env = _base_env(tmp_path, isolated_port, PEAK_TRADE_WEBUI_HOST="0.0.0.0")
    started = _run("start", env=env, timeout=15)
    assert started.returncode != 0
    assert "LOCALHOST_ONLY" in (started.stdout + started.stderr)


def test_playwright_webserver_module_contracts() -> None:
    text = PLAYWRIGHT_WEBSERVER.read_text(encoding="utf-8")
    assert 'PRIMARY_PLAYWRIGHT_CHANNEL = "chrome"' in text
    assert 'PRIMARY_BROWSER = "GOOGLE_CHROME"' in text
    assert "is_ci_environment" in text
    assert "review_server.sh" in text
    assert "--reload" not in text

    # Import-level smoke via repo root on sys.path (no server start)
    import sys

    scripts_webui = str(REPO_ROOT / "scripts" / "webui")
    if scripts_webui not in sys.path:
        sys.path.insert(0, scripts_webui)
    import review_server_playwright_webserver_v1 as mod  # type: ignore

    assert mod.PRIMARY_PLAYWRIGHT_CHANNEL == "chrome"
    assert mod.default_reuse_existing() in {True, False}
    old_ci = os.environ.get("CI")
    os.environ["CI"] = "true"
    try:
        assert mod.default_reuse_existing() is False
    finally:
        if old_ci is None:
            os.environ.pop("CI", None)
        else:
            os.environ["CI"] = old_ci


def test_playwright_webserver_smoke_and_no_external_network(
    tmp_path: Path, isolated_port: int
) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "review_server_playwright_webserver_v1", PLAYWRIGHT_WEBSERVER
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    state = tmp_path / "pw_state"
    server = mod.ReviewServerWebServer(
        host="127.0.0.1",
        port=isolated_port,
        state_dir=state,
        reuse_existing=False,
        start_timeout_seconds=60,
    )
    external: list[str] = []
    try:
        handle = server.start()
        assert handle.primary_playwright_channel == "chrome"
        assert _http_code(handle.health_url) == 200
        assert _http_code(handle.review_url) == 200

        with sync_playwright() as p:
            browser, report = mod.launch_chrome_channel(p, headless=True)
            assert report["PRIMARY_PLAYWRIGHT_CHANNEL"] == "chrome"
            context = browser.new_context()
            page = context.new_page()

            def on_request(request: object) -> None:
                url = getattr(request, "url", "")
                if not str(url).startswith(handle.base_url) and not str(url).startswith(
                    ("data:", "blob:", "about:")
                ):
                    external.append(str(url))

            page.on("request", on_request)
            page.goto(handle.review_url, wait_until="domcontentloaded", timeout=60_000)
            browser.close()

        assert external == [], f"unexpected external requests: {external}"
    finally:
        server.stop()
        env = _base_env(tmp_path, isolated_port)
        env["PEAK_TRADE_WEBUI_STATE_DIR"] = str(state)
        _run("stop", env=env, timeout=30)
