"""v0 contract: Shadow no-order proof markers stay declarative; canonical env defaults stay safe."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.shadow_no_order_proof import adapter_contract_v0, markers_v0

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Bounded high-risk surfaces only (no whole-repo walk).
_SRC_AUTHORITY_REL_DIRS = (
    "src/execution",
    "src/live",
    "src/ops",
    "src/risk",
    "src/scheduler",
    "src/strategies",
)

# Operational scripts: explicit list + everything under scripts/live/.
_AUTHORITY_SCRIPT_RELPATHS: frozenset[str] = frozenset(
    {
        "scripts/aiops/run_shadow_session.py",
        "scripts/check_live_readiness.py",
        "scripts/ci/shadow_testnet_readiness_scorecard.py",
        "scripts/live_alerts_cli.py",
        "scripts/live_monitor_cli.py",
        "scripts/live_operator_status.py",
        "scripts/ops/p7_ctl.py",
        "scripts/ops/report_paper_shadow_247_preflight_status.py",
        "scripts/ops/review_scheduler_paper_runtime_evidence.py",
        "scripts/ops/run_with_timeout.py",
        "scripts/orchestrate_testnet_runs.py",
        "scripts/orchestrator_dryrun.py",
        "scripts/run_execution_session.py",
        "scripts/run_live_beta_drill.py",
        "scripts/run_scheduler.py",
        "scripts/run_shadow_execution.py",
        "scripts/run_shadow_paper_session.py",
        "scripts/run_testnet_session.py",
        "scripts/serve_live_dashboard.py",
        "scripts/smoke_test_testnet_stack.py",
        "scripts/testnet_orchestrator_cli.py",
    }
)

_SHADOW_NO_ORDER_AUTHORITY_IMPORT: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?m)^\s*from\s+(?:src\.)?shadow_no_order_proof\b"),
    re.compile(r"(?m)^\s*import\s+(?:src\.)?shadow_no_order_proof\b"),
)

# Known mixed-risk Shadow / runtime candidates — may exist; must not claim no-order approval.
_KNOWN_SHADOW_RUNTIME_CANDIDATE_RELPATHS: tuple[str, ...] = (
    "scripts/aiops/run_shadow_session.py",
    "scripts/live/verify_shadow_mode.py",
    "scripts/run_shadow_execution.py",
    "scripts/run_shadow_paper_session.py",
    "scripts/testnet_orchestrator_cli.py",
    "src/live/shadow_session.py",
    "src/ops/p62/run_online_readiness_shadow_session_v1.py",
    "src/ops/p67/shadow_session_scheduler_cli_v1.py",
    "src/ops/p67/shadow_session_scheduler_v1.py",
    "src/ops/p72/run_shadowloop_pack_v1.py",
)

_NO_ORDER_ENTRYPOINT_FORBIDDEN_APPROVAL: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND\s*=\s*(?i:True)"),
        "PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND true",
    ),
    (re.compile(r"SHADOW_MODE_ALLOWED\s*=\s*(?i:True)"), "SHADOW_MODE_ALLOWED true"),
    (re.compile(r"ORDER_SUBMISSION_ALLOWED\s*=\s*(?i:True)"), "ORDER_SUBMISSION_ALLOWED true"),
    (re.compile(r"BROKER_ALLOWED\s*=\s*(?i:True)"), "BROKER_ALLOWED true"),
    (re.compile(r"EXCHANGE_ALLOWED\s*=\s*(?i:True)"), "EXCHANGE_ALLOWED true"),
    (re.compile(r"LIVE_ALLOWED\s*=\s*(?i:True)"), "LIVE_ALLOWED true"),
    (re.compile(r"TESTNET_ALLOWED\s*=\s*(?i:True)"), "TESTNET_ALLOWED true"),
    (re.compile(r"APPROVAL_GRANTED\s*=\s*(?i:True)"), "APPROVAL_GRANTED true"),
    (
        re.compile(r"EXECUTABLE_COMMAND_CREATED\s*=\s*(?i:True)"),
        "EXECUTABLE_COMMAND_CREATED true",
    ),
)

# Workflows must not treat declarative proof metadata as CI/release/execution authority.
_WORKFLOW_FORBIDDEN_SHADOW_NO_ORDER_SUBSTR: tuple[str, ...] = (
    "shadow_no_order_proof",
    "src.shadow_no_order_proof",
)

# Canonical repo config trees — scheduler/runtime wiring must not reference declarative proof.
_CONFIG_AUTHORITY_REL_ROOTS: tuple[str, ...] = ("config",)
_CONFIG_AUTHORITY_FILE_SUFFIXES: frozenset[str] = frozenset(
    {".toml", ".yaml", ".yml", ".json", ".ini", ".cfg"}
)
_CONFIG_FORBIDDEN_SHADOW_NO_ORDER_SUBSTR: tuple[str, ...] = (
    "shadow_no_order_proof",
    "src.shadow_no_order_proof",
    "SHADOW_NO_ORDER_PROOF_V0",
)

_FORBIDDEN_SOURCE_MARKERS = (
    "requests",
    "httpx",
    "urllib.request",
    "socket",
    "subprocess",
    "ccxt",
    "aiohttp",
    "if __name__",
)

# Whole-package guard: declarative surface only (no I/O, CLI, runtime, or trading clients).
_PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src" / "shadow_no_order_proof"
_NO_EXEC_SURFACE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"if\s+__name__\s*==\s*[\"']__main__[\"']"), "__main__ guard"),
    (re.compile(r"\bdef\s+main\s*\("), "def main("),
    (re.compile(r"\b(import|from)\s+argparse\b"), "argparse import"),
    (re.compile(r"argparse\."), "argparse usage"),
    (re.compile(r"\b(import|from)\s+click\b"), "click import"),
    (re.compile(r"click\."), "click usage"),
    (re.compile(r"\b(import|from)\s+typer\b"), "typer import"),
    (re.compile(r"typer\."), "typer usage"),
    (re.compile(r"\buvicorn\b"), "uvicorn"),
    (re.compile(r"\brun_scheduler\b"), "run_scheduler"),
    (re.compile(r"\brun_with_timeout\b"), "run_with_timeout"),
    (re.compile(r"\b(import|from)\s+subprocess\b"), "subprocess import"),
    (re.compile(r"\bsubprocess\."), "subprocess call"),
    (re.compile(r"\bos\.system\s*\("), "os.system"),
    (re.compile(r"\bos\.popen\s*\("), "os.popen"),
    (re.compile(r"\b(import|from)\s+socket\b"), "socket import"),
    (re.compile(r"\bsocket\."), "socket usage"),
    (re.compile(r"\b(import|from)\s+multiprocessing\b"), "multiprocessing import"),
    (re.compile(r"\b(import|from)\s+threading\b"), "threading import"),
    (re.compile(r"\brequests\."), "requests usage"),
    (re.compile(r"\b(import|from)\s+requests\b"), "requests import"),
    (re.compile(r"\bhttpx\."), "httpx usage"),
    (re.compile(r"\b(import|from)\s+httpx\b"), "httpx import"),
    (re.compile(r"\b(import|from)\s+urllib\b"), "urllib import"),
    (re.compile(r"\burllib\.request\b"), "urllib.request"),
    (re.compile(r"\b(import|from)\s+aiohttp\b"), "aiohttp import"),
    (re.compile(r"\baiohttp\."), "aiohttp usage"),
    (re.compile(r"\bwebsocket"), "websocket"),
    (re.compile(r"\bccxt\b"), "ccxt"),
    (re.compile(r"\bcreate_order\b"), "create_order"),
    (re.compile(r"\bplace_order\b"), "place_order"),
    (re.compile(r"\bsend_order\b"), "send_order"),
    (re.compile(r"\bsubmit_order\b"), "submit_order"),
    (re.compile(r"\border_submission\b"), "order_submission"),
    (re.compile(r"\bapi_key\s*="), "api_key assignment"),
    (re.compile(r"\bsecret\s*="), "secret assignment"),
    (re.compile(r"\bprivate_key\s*="), "private_key assignment"),
    (re.compile(r"\bcredential\s*="), "credential assignment"),
    (re.compile(r"SHADOW_MODE_ALLOWED\s*=\s*True"), "SHADOW_MODE_ALLOWED true"),
    (re.compile(r"ORDER_SUBMISSION_ALLOWED\s*=\s*True"), "ORDER_SUBMISSION_ALLOWED true"),
    (re.compile(r"BROKER_ALLOWED\s*=\s*True"), "BROKER_ALLOWED true"),
    (re.compile(r"EXCHANGE_ALLOWED\s*=\s*True"), "EXCHANGE_ALLOWED true"),
    (re.compile(r"LIVE_ALLOWED\s*=\s*True"), "LIVE_ALLOWED true"),
    (re.compile(r"TESTNET_ALLOWED\s*=\s*True"), "TESTNET_ALLOWED true"),
    (re.compile(r"PAPER_ORDER_PATH_ALLOWED\s*=\s*True"), "PAPER_ORDER_PATH_ALLOWED true"),
    (re.compile(r"SCHEDULER_ALLOWED\s*=\s*True"), "SCHEDULER_ALLOWED true"),
    (re.compile(r"RUNTIME_ALLOWED\s*=\s*True"), "RUNTIME_ALLOWED true"),
    (re.compile(r"EXECUTABLE_COMMAND_CREATED\s*=\s*True"), "EXECUTABLE_COMMAND_CREATED true"),
)


def _py_files_under(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts)


def _workflow_files() -> list[Path]:
    d = _REPO_ROOT / ".github" / "workflows"
    if not d.is_dir():
        return []
    return sorted(
        p
        for p in d.rglob("*")
        if p.is_file() and p.suffix.lower() in {".yml", ".yaml"} and "__pycache__" not in p.parts
    )


def _config_authority_surface_files() -> list[Path]:
    paths: list[Path] = []
    for rel in _CONFIG_AUTHORITY_REL_ROOTS:
        root = _REPO_ROOT / rel
        if not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts:
                continue
            suf = p.suffix.lower()
            if suf in _CONFIG_AUTHORITY_FILE_SUFFIXES or p.name.lower().endswith(".env.example"):
                paths.append(p.resolve())
    return sorted(set(paths))


def _authority_surface_files_for_shadow_no_order_import_guard() -> list[Path]:
    paths: list[Path] = []
    for rel in _SRC_AUTHORITY_REL_DIRS:
        root = _REPO_ROOT / rel
        if root.is_dir():
            paths.extend(_py_files_under(root))
    live_scripts = _REPO_ROOT / "scripts" / "live"
    if live_scripts.is_dir():
        paths.extend(_py_files_under(live_scripts))
    for rel in sorted(_AUTHORITY_SCRIPT_RELPATHS):
        p = _REPO_ROOT / rel
        if p.is_file():
            paths.append(p)
    paths.extend(_workflow_files())
    # De-dupe preserving order
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def _shadow_no_order_proof_py_files() -> list[Path]:
    assert _PACKAGE_ROOT.is_dir(), f"missing package: {_PACKAGE_ROOT}"
    paths = sorted(
        p for p in _PACKAGE_ROOT.rglob("*.py") if p.is_file() and "__pycache__" not in p.parts
    )
    assert paths, "expected at least one Python file under shadow_no_order_proof"
    return paths


def test_runtime_authority_surfaces_do_not_import_shadow_no_order_proof() -> None:
    """Static scan: bounded authority paths must not import declarative proof as runtime authority."""
    for path in _authority_surface_files_for_shadow_no_order_import_guard():
        text = path.read_text(encoding="utf-8")
        for pattern in _SHADOW_NO_ORDER_AUTHORITY_IMPORT:
            match = pattern.search(text)
            assert match is None, (
                f"authority surface {path} must not import shadow_no_order_proof "
                f"(matched {match.group(0)!r})"
            )


def test_known_shadow_runtime_candidates_are_not_approved_no_order_entrypoints() -> None:
    """Explicit mixed-risk paths must not embed machine-style approval for no-order entry."""
    checked = 0
    for rel in _KNOWN_SHADOW_RUNTIME_CANDIDATE_RELPATHS:
        path = _REPO_ROOT / rel
        if not path.is_file():
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        for pattern, label in _NO_ORDER_ENTRYPOINT_FORBIDDEN_APPROVAL:
            match = pattern.search(text)
            assert match is None, (
                f"{label!r} must not appear in candidate {path} (matched {match.group(0)!r})"
            )
    assert checked > 0, "expected at least one known shadow/runtime candidate file to exist"


def test_workflows_do_not_reference_shadow_no_order_proof_as_authority() -> None:
    """GitHub Actions YAML must not reference declarative proof as CI/release/execution authority."""
    wf_root = _REPO_ROOT / ".github" / "workflows"
    if not wf_root.is_dir():
        pytest.skip(".github/workflows not present")
    paths = _workflow_files()
    if not paths:
        pytest.skip("no .yml/.yaml workflow files under .github/workflows")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for needle in _WORKFLOW_FORBIDDEN_SHADOW_NO_ORDER_SUBSTR:
            assert needle not in text, (
                f"workflow {path} must not reference {needle!r} "
                "(declarative shadow_no_order_proof is not CI/release authority)"
            )


def test_runtime_scheduler_configs_do_not_reference_shadow_no_order_proof_as_authority() -> None:
    """Bounded config trees must not wire declarative proof as scheduler/runtime authority."""
    paths = _config_authority_surface_files()
    assert paths, "expected at least one config-like file under canonical config roots"
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for needle in _CONFIG_FORBIDDEN_SHADOW_NO_ORDER_SUBSTR:
            assert needle not in text, (
                f"config {path} must not reference {needle!r} "
                "(shadow_no_order_proof is not scheduler/runtime config authority)"
            )


def test_shadow_no_order_proof_package_is_non_execution_surface() -> None:
    """Scan only `src/shadow_no_order_proof/` — no whole-repo walk."""
    for path in _shadow_no_order_proof_py_files():
        text = path.read_text(encoding="utf-8")
        for pattern, label in _NO_EXEC_SURFACE_PATTERNS:
            match = pattern.search(text)
            assert match is None, f"{label!r} matched in {path}: {match.group(0)!r}"


def test_shadow_no_order_markers_are_all_false_and_tagged() -> None:
    assert markers_v0.SHADOW_NO_ORDER_PROOF_V0 == "shadow_no_order_proof_v0"
    assert markers_v0.SHADOW_MODE_ALLOWED is False
    assert markers_v0.ORDER_SUBMISSION_ALLOWED is False
    assert markers_v0.BROKER_ALLOWED is False
    assert markers_v0.EXCHANGE_ALLOWED is False
    assert markers_v0.EXECUTABLE_COMMAND_CREATED is False
    assert markers_v0.LIVE_ALLOWED is False
    assert markers_v0.TESTNET_ALLOWED is False
    assert markers_v0.PAPER_ORDER_PATH_ALLOWED is False
    assert markers_v0.SCHEDULER_ALLOWED is False
    assert markers_v0.RUNTIME_ALLOWED is False


def test_bounded_shadow_adapter_proof_contract_is_declarative_and_all_flags_false() -> None:
    """Bounded adapter proof slice: constants only, no authority to run or trade."""
    assert adapter_contract_v0.BOUNDED_SHADOW_ADAPTER_PROOF_V0 == "bounded_shadow_adapter_proof_v0"
    assert adapter_contract_v0.ADAPTER_KIND == "declarative_no_order_shadow_adapter_proof"
    assert adapter_contract_v0.PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND is False
    assert adapter_contract_v0.EXECUTABLE_COMMAND_CREATED is False
    assert adapter_contract_v0.SHADOW_MODE_ALLOWED is False
    assert adapter_contract_v0.ORDER_SUBMISSION_ALLOWED is False
    assert adapter_contract_v0.BROKER_ALLOWED is False
    assert adapter_contract_v0.EXCHANGE_ALLOWED is False
    assert adapter_contract_v0.RUNTIME_ALLOWED is False
    assert adapter_contract_v0.SCHEDULER_ALLOWED is False
    assert adapter_contract_v0.LIVE_ALLOWED is False
    assert adapter_contract_v0.TESTNET_ALLOWED is False
    assert adapter_contract_v0.PAPER_ALLOWED is False


def test_markers_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(markers_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    for needle in _FORBIDDEN_SOURCE_MARKERS:
        assert needle.lower() not in low, f"unexpected token {needle!r} in {path}"


def test_adapter_contract_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(adapter_contract_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    for needle in _FORBIDDEN_SOURCE_MARKERS:
        assert needle.lower() not in low, f"unexpected token {needle!r} in {path}"


def test_environment_config_defaults_remain_paper_and_gated() -> None:
    """Canonical owner: src.core.environment.EnvironmentConfig defaults."""
    cfg = EnvironmentConfig()
    assert cfg.environment == TradingEnvironment.PAPER
    assert cfg.enable_live_trading is False
    assert cfg.testnet_dry_run is True
    assert cfg.live_mode_armed is False
    assert cfg.live_dry_run_mode is True
