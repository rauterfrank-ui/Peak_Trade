"""v0 contract: Shadow no-order proof markers stay declarative; canonical env defaults stay safe."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import fields
from pathlib import Path

import pytest

from src.core.environment import EnvironmentConfig, TradingEnvironment
from src.shadow_no_order_proof import (
    adapter_contract_v0,
    bounded_adapter_v0,
    markers_v0,
    observation_harness_v0,
)

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

# Workflows/configs must not wire bounded adapter plan symbols as CI/runtime/approval authority.
_WORKFLOW_CONFIG_BOUNDED_ADAPTER_FORBIDDEN_SUBSTR: tuple[str, ...] = (
    "bounded_adapter_v0",
    "BoundedShadowAdapterPlan",
    "build_bounded_shadow_adapter_plan_v0",
    "BOUNDED_SHADOW_ADAPTER_PROOF_V0",
    "declarative_no_order_shadow_adapter_proof",
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


def _workflow_and_config_authority_surface_files() -> list[Path]:
    """Union of workflow YAML and canonical config trees (deduped)."""
    paths = _workflow_files() + _config_authority_surface_files()
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


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


def test_workflows_and_configs_do_not_reference_bounded_adapter_as_authority() -> None:
    """Workflows and bounded config trees must not treat bounded adapter plans as wiring authority."""
    paths = _workflow_and_config_authority_surface_files()
    if not paths:
        pytest.skip("no workflow or config authority surface files to scan")
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for needle in _WORKFLOW_CONFIG_BOUNDED_ADAPTER_FORBIDDEN_SUBSTR:
            assert needle not in text, (
                f"{path} must not reference {needle!r} "
                "(bounded adapter plan is not workflow/config execution authority)"
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


def test_bounded_shadow_adapter_plan_is_declarative_non_executable_not_approved() -> None:
    """Implementation slice: frozen plan only; no authority flags; no allowed actions."""
    p1 = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0()
    p2 = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source="bounded_adapter_build_v0")
    assert p1 == p2
    custom = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source="contract_test_source")
    assert custom.source == "contract_test_source"
    assert custom.adapter_kind == adapter_contract_v0.ADAPTER_KIND
    assert custom.proof_version == f"{adapter_contract_v0.BOUNDED_SHADOW_ADAPTER_PROOF_V0}_impl_v0"
    assert custom.allowed_actions == ()
    assert custom.evidence_required is True
    assert custom.proven_shadow_no_order_entrypoint_found is False
    assert custom.executable_command_created is False
    assert "not an executable command" in custom.not_executable_declaration.lower()
    assert (
        "not approved" in custom.not_approved_declaration.lower()
        or "approved by this plan" in custom.not_approved_declaration.lower()
    )
    assert custom.shadow_mode_allowed is False
    assert custom.order_submission_allowed is False
    assert custom.broker_allowed is False
    assert custom.exchange_allowed is False
    assert custom.runtime_allowed is False
    assert custom.scheduler_allowed is False
    assert custom.live_allowed is False
    assert custom.testnet_allowed is False
    assert custom.paper_allowed is False
    assert "intent_order_flow_submit" in custom.forbidden_actions
    assert "intent_order_flow_place" in custom.forbidden_actions


def test_bounded_adapter_plan_has_no_order_like_allowed_actions() -> None:
    """No permitted action bucket may admit trading, runtime, or mixed-risk entry scripts."""
    plan = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0()
    assert not plan.allowed_actions
    risky_tokens = (
        "order",
        "broker",
        "exchange",
        "runtime",
        "scheduler",
        "live",
        "testnet",
        "shadow_mode",
        "credential",
        "api_key",
    )
    for action in plan.allowed_actions:
        low = action.lower()
        assert not any(tok in low for tok in risky_tokens), (
            f"unexpected risky allowed_action {action!r}"
        )


def test_bounded_adapter_module_isolates_from_mixed_risk_scripts_and_runtime_packages() -> None:
    path = Path(bounded_adapter_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    for needle in ("scripts/run_shadow_execution.py", "scripts/testnet_orchestrator_cli.py"):
        assert needle not in text, f"{path} must not reference mixed-risk script path {needle!r}"
    for pattern in (
        re.compile(
            r"(?m)^\s*from\s+src\.(strategies|execution|live|scheduler|ops|data|orders|backtest)\b"
        ),
        re.compile(
            r"(?m)^\s*import\s+src\.(strategies|execution|live|scheduler|ops|data|orders|backtest)\b"
        ),
    ):
        assert pattern.search(text) is None, f"{path} must not import runtime-like src packages"


def test_bounded_adapter_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(bounded_adapter_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    for needle in _FORBIDDEN_SOURCE_MARKERS:
        assert needle.lower() not in low, f"unexpected token {needle!r} in {path}"


def test_shadow_observation_input_snapshot_has_only_safe_fields() -> None:
    """Contract: snapshot carries symbol/time/source/payload only — no broker/exchange/client fields."""
    expected = {"symbol", "observed_at_utc", "source", "payload"}
    assert {
        f.name for f in fields(observation_harness_v0.ShadowObservationInputSnapshot)
    } == expected
    forbidden_substrings = ("exchange", "broker", "client", "credential")
    for f in fields(observation_harness_v0.ShadowObservationInputSnapshot):
        lower = f.name.lower()
        for sub in forbidden_substrings:
            assert sub not in lower, f"field {f.name!r} must not contain {sub!r}"


def test_shadow_observation_evidence_record_shapes_and_safety_flags() -> None:
    """Contract: evidence record mirrors plan metadata; operational safety flags stay false."""
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="TEST",
        observed_at_utc="2026-01-02T00:00:00Z",
        source="contract_observation_v0",
        payload={"mid": 1.0},
    )
    plan = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source=snapshot.source)
    rec = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=snapshot, plan=plan
    )
    assert rec.evidence_version == observation_harness_v0.OBSERVATION_EVIDENCE_SCHEMA_V0
    assert rec.adapter_kind == plan.adapter_kind
    assert rec.source == snapshot.source
    assert rec.observed_at_utc == snapshot.observed_at_utc
    assert rec.evidence_id == rec.evidence_hash
    assert len(rec.evidence_id) == 64
    assert rec.proof_version == plan.proof_version
    assert rec.allowed_actions == ()
    assert rec.evidence_required is True
    assert rec.proven_shadow_no_order_entrypoint_found is False
    assert rec.executable_command_created is False
    must_be_false = (
        rec.broker_touched,
        rec.exchange_touched,
        rec.credentials_touched,
        rec.order_intent_created,
        rec.order_submission_allowed,
        rec.runtime_started,
        rec.scheduler_started,
        rec.shadow_mode_allowed,
        rec.live_allowed,
        rec.testnet_allowed,
        rec.paper_allowed,
        rec.broker_allowed,
        rec.exchange_allowed,
        rec.runtime_allowed,
        rec.scheduler_allowed,
    )
    assert not any(must_be_false), f"expected all operational flags false, got {must_be_false!r}"


def test_shadow_observation_evidence_is_deterministic_for_same_inputs() -> None:
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="AAA",
        observed_at_utc="2026-05-16T12:00:00Z",
        source="det_test",
        payload={"a": 1, "nested": {"z": 3, "y": 2}},
    )
    plan = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source="det_test")
    r1 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=snapshot, plan=plan
    )
    r2 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=snapshot, plan=plan
    )
    assert r1.evidence_id == r2.evidence_id


def test_shadow_observation_evidence_id_changes_when_snapshot_or_plan_differs() -> None:
    base_snap = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="BBB",
        observed_at_utc="2026-05-16T12:00:00Z",
        source="id_change",
        payload={"k": 1},
    )
    plan_a = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source="id_change")
    plan_b = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source="other_source")
    rid1 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=base_snap, plan=plan_a
    ).evidence_id
    rid2 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="BBB",
            observed_at_utc="2026-05-16T12:00:01Z",
            source="id_change",
            payload={"k": 1},
        ),
        plan=plan_a,
    ).evidence_id
    rid3 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="BBB",
            observed_at_utc="2026-05-16T12:00:00Z",
            source="id_change",
            payload={"k": 2},
        ),
        plan=plan_a,
    ).evidence_id
    rid4 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="BBB",
            observed_at_utc="2026-05-16T12:00:00Z",
            source="other",
            payload={"k": 1},
        ),
        plan=plan_a,
    ).evidence_id
    rid5 = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=base_snap, plan=plan_b
    ).evidence_id
    assert len({rid1, rid2, rid3, rid4, rid5}) == 5


def test_shadow_observation_harness_emits_no_order_like_allowed_actions() -> None:
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="CCC",
        observed_at_utc="2026-05-16T12:00:00Z",
        source="no_order_actions",
        payload={},
    )
    plan = bounded_adapter_v0.build_bounded_shadow_adapter_plan_v0(source=snapshot.source)
    rec = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=snapshot, plan=plan
    )
    assert not rec.allowed_actions
    for action in rec.allowed_actions:
        low = action.lower()
        assert "order" not in low


def test_run_shadow_observation_one_shot_v0_returns_same_as_default_plan_build() -> None:
    """One-shot entry is sugar over evidence build with plan derived from snapshot.source."""
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="ONE",
        observed_at_utc="2026-05-16T14:00:00Z",
        source="one_shot_equiv",
        payload={"x": 1},
    )
    via_one_shot = observation_harness_v0.run_shadow_observation_one_shot_v0(snapshot)
    via_build = observation_harness_v0.build_shadow_observation_evidence_record_v0(
        snapshot=snapshot, plan=None
    )
    assert via_one_shot == via_build
    assert isinstance(via_one_shot, observation_harness_v0.ShadowObservationEvidenceRecord)


def test_run_shadow_observation_one_shot_v0_is_deterministic() -> None:
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="TWO",
        observed_at_utc="2026-05-16T14:01:00Z",
        source="one_shot_det",
        payload={"n": 2},
    )
    a = observation_harness_v0.run_shadow_observation_one_shot_v0(snapshot)
    b = observation_harness_v0.run_shadow_observation_one_shot_v0(snapshot)
    assert a.evidence_id == b.evidence_id


def test_run_shadow_observation_one_shot_v0_hash_changes_when_snapshot_changes() -> None:
    base = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="THR",
        observed_at_utc="2026-05-16T14:02:00Z",
        source="one_shot_hash",
        payload={"p": 0},
    )
    rid0 = observation_harness_v0.run_shadow_observation_one_shot_v0(base).evidence_id
    rid1 = observation_harness_v0.run_shadow_observation_one_shot_v0(
        observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="THR",
            observed_at_utc="2026-05-16T14:02:00Z",
            source="one_shot_hash",
            payload={"p": 1},
        )
    ).evidence_id
    assert rid0 != rid1


def test_run_shadow_observation_one_shot_v0_preserves_no_order_safety_flags() -> None:
    snapshot = observation_harness_v0.ShadowObservationInputSnapshot(
        symbol="FOU",
        observed_at_utc="2026-05-16T14:03:00Z",
        source="one_shot_flags",
        payload={},
    )
    rec = observation_harness_v0.run_shadow_observation_one_shot_v0(snapshot)
    assert rec.allowed_actions == ()
    assert rec.evidence_required is True
    assert rec.proven_shadow_no_order_entrypoint_found is False
    assert rec.executable_command_created is False
    must_be_false = (
        rec.broker_touched,
        rec.exchange_touched,
        rec.credentials_touched,
        rec.order_intent_created,
        rec.order_submission_allowed,
        rec.runtime_started,
        rec.scheduler_started,
        rec.shadow_mode_allowed,
        rec.live_allowed,
        rec.testnet_allowed,
        rec.paper_allowed,
        rec.broker_allowed,
        rec.exchange_allowed,
        rec.runtime_allowed,
        rec.scheduler_allowed,
    )
    assert not any(must_be_false), f"expected all operational flags false, got {must_be_false!r}"


def _snap(
    symbol: str, source: str, payload: dict[str, object]
) -> observation_harness_v0.ShadowObservationInputSnapshot:
    return observation_harness_v0.ShadowObservationInputSnapshot(
        symbol=symbol,
        observed_at_utc="2026-05-16T15:00:00Z",
        source=source,
        payload=payload,
    )


def test_run_shadow_observation_batch_v0_one_record_per_snapshot_ordered() -> None:
    snaps = (
        _snap("A", "batch_src", {"i": 0}),
        _snap("B", "batch_src", {"i": 1}),
    )
    records = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    assert len(records) == 2
    assert records[0] == observation_harness_v0.run_shadow_observation_one_shot_v0(snaps[0])
    assert records[1] == observation_harness_v0.run_shadow_observation_one_shot_v0(snaps[1])


def test_run_shadow_observation_batch_v0_empty_is_deterministic() -> None:
    r1 = observation_harness_v0.run_shadow_observation_batch_v0(())
    r2 = observation_harness_v0.run_shadow_observation_batch_v0(())
    assert r1 == () == r2
    s1 = observation_harness_v0.build_shadow_observation_batch_summary_v0(r1)
    s2 = observation_harness_v0.build_shadow_observation_batch_summary_v0(r2)
    assert s1 == s2
    assert s1.record_count == 0
    assert s1.evidence_ids == ()
    assert len(s1.batch_hash) == 64


def test_shadow_observation_batch_summary_same_order_same_hash() -> None:
    snaps = (
        _snap("X", "batch_hash", {"k": 1}),
        _snap("Y", "batch_hash", {"k": 2}),
    )
    recs_a = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    recs_b = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    su_a = observation_harness_v0.build_shadow_observation_batch_summary_v0(recs_a)
    su_b = observation_harness_v0.build_shadow_observation_batch_summary_v0(recs_b)
    assert su_a.batch_hash == su_b.batch_hash
    assert su_a.evidence_ids == su_b.evidence_ids


def test_shadow_observation_batch_hash_changes_when_snapshot_changes() -> None:
    snaps1 = (
        _snap("X", "bh", {"k": 1}),
        _snap("Y", "bh", {"k": 2}),
    )
    snaps2 = (
        _snap("X", "bh", {"k": 1}),
        _snap("Y", "bh", {"k": 99}),
    )
    h1 = observation_harness_v0.build_shadow_observation_batch_summary_v0(
        observation_harness_v0.run_shadow_observation_batch_v0(snaps1)
    ).batch_hash
    h2 = observation_harness_v0.build_shadow_observation_batch_summary_v0(
        observation_harness_v0.run_shadow_observation_batch_v0(snaps2)
    ).batch_hash
    assert h1 != h2


def test_shadow_observation_batch_hash_order_sensitive() -> None:
    s1 = _snap("P", "ord", {"n": 1})
    s2 = _snap("Q", "ord", {"n": 2})
    h_forward = observation_harness_v0.build_shadow_observation_batch_summary_v0(
        observation_harness_v0.run_shadow_observation_batch_v0((s1, s2))
    ).batch_hash
    h_reverse = observation_harness_v0.build_shadow_observation_batch_summary_v0(
        observation_harness_v0.run_shadow_observation_batch_v0((s2, s1))
    ).batch_hash
    assert h_forward != h_reverse


def test_shadow_observation_batch_records_remain_no_order() -> None:
    snaps = (
        _snap("N1", "no_order_batch", {}),
        _snap("N2", "no_order_batch", {"z": 3}),
    )
    for rec in observation_harness_v0.run_shadow_observation_batch_v0(snaps):
        assert rec.allowed_actions == ()
        must_be_false = (
            rec.broker_touched,
            rec.exchange_touched,
            rec.credentials_touched,
            rec.order_intent_created,
            rec.order_submission_allowed,
            rec.runtime_started,
            rec.scheduler_started,
            rec.shadow_mode_allowed,
            rec.live_allowed,
            rec.testnet_allowed,
            rec.paper_allowed,
            rec.broker_allowed,
            rec.exchange_allowed,
            rec.runtime_allowed,
            rec.scheduler_allowed,
        )
        assert not any(must_be_false)


def test_shadow_observation_batch_summary_flags_safe_for_nonempty() -> None:
    snaps = (_snap("S1", "sum_safe", {}), _snap("S2", "sum_safe", {"a": 1}))
    summary = observation_harness_v0.build_shadow_observation_batch_summary_v0(
        observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    )
    assert summary.all_no_order is True
    assert summary.all_broker_touched_false is True
    assert summary.all_exchange_touched_false is True
    assert summary.all_credentials_touched_false is True
    assert summary.all_order_intent_created_false is True
    assert summary.all_runtime_started_false is True
    assert summary.all_scheduler_started_false is True
    assert summary.all_shadow_mode_allowed_false is True
    assert summary.proven_shadow_no_order_entrypoint_found is False
    assert summary.executable_command_created is False


def _timed_meta() -> dict[str, object]:
    return {
        "started_at_utc": "2026-05-16T16:00:00Z",
        "ended_at_utc": "2026-05-16T17:00:00Z",
        "cadence_seconds": 60,
        "max_observations": 10,
    }


def test_build_shadow_observation_timed_summary_v0_accepts_records_and_metadata() -> None:
    snaps = (
        _snap("T1", "timed", {"i": 0}),
        _snap("T2", "timed", {"i": 1}),
    )
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    meta = _timed_meta()
    summary = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs,
        started_at_utc=str(meta["started_at_utc"]),
        ended_at_utc=str(meta["ended_at_utc"]),
        cadence_seconds=int(meta["cadence_seconds"]),
        max_observations=int(meta["max_observations"]),
    )
    assert summary.timed_version == observation_harness_v0.TIMED_OBSERVATION_SUMMARY_SCHEMA_V0
    assert summary.record_count == 2
    assert summary.observed_at_utc_values == tuple(r.observed_at_utc for r in recs)
    assert len(summary.timed_hash) == 64
    assert summary.cadence_source == "caller_provided"


def test_shadow_observation_timed_summary_same_inputs_same_hash() -> None:
    snaps = (_snap("S", "th", {"k": 1}),)
    recs_a = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    recs_b = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    meta = _timed_meta()
    kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": int(meta["max_observations"]),
    }
    t_a = observation_harness_v0.build_shadow_observation_timed_summary_v0(recs_a, **kw)
    t_b = observation_harness_v0.build_shadow_observation_timed_summary_v0(recs_b, **kw)
    assert t_a.timed_hash == t_b.timed_hash
    assert t_a.batch_hash == t_b.batch_hash


def test_shadow_observation_timed_hash_changes_when_cadence_metadata_changes() -> None:
    snaps = (_snap("C", "cad", {}),)
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    base = _timed_meta()
    kw1 = {
        "started_at_utc": str(base["started_at_utc"]),
        "ended_at_utc": str(base["ended_at_utc"]),
        "cadence_seconds": 60,
        "max_observations": int(base["max_observations"]),
    }
    kw2 = {**kw1, "cadence_seconds": 120}
    h1 = observation_harness_v0.build_shadow_observation_timed_summary_v0(recs, **kw1).timed_hash
    h2 = observation_harness_v0.build_shadow_observation_timed_summary_v0(recs, **kw2).timed_hash
    assert h1 != h2


def test_shadow_observation_timed_hash_changes_when_cadence_source_changes() -> None:
    snaps = (_snap("CS", "cads", {}),)
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    meta = _timed_meta()
    kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": int(meta["max_observations"]),
    }
    a = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs, cadence_source="caller_provided", **kw
    )
    b = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs, cadence_source="fixture", **kw
    )
    assert a.timed_hash != b.timed_hash


def test_shadow_observation_timed_hash_changes_when_started_ended_change() -> None:
    snaps = (_snap("E", "se", {}),)
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    h1 = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs,
        started_at_utc="2026-05-16T12:00:00Z",
        ended_at_utc="2026-05-16T13:00:00Z",
        cadence_seconds=30,
        max_observations=5,
    ).timed_hash
    h2 = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs,
        started_at_utc="2026-05-16T12:00:01Z",
        ended_at_utc="2026-05-16T13:00:00Z",
        cadence_seconds=30,
        max_observations=5,
    ).timed_hash
    assert h1 != h2


def test_shadow_observation_timed_hash_order_sensitive() -> None:
    s1 = _snap("O1", "ordt", {"n": 1})
    s2 = _snap("O2", "ordt", {"n": 2})
    meta = _timed_meta()
    kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": int(meta["max_observations"]),
    }
    fwd = observation_harness_v0.run_shadow_observation_batch_v0((s1, s2))
    rev = observation_harness_v0.run_shadow_observation_batch_v0((s2, s1))
    assert (
        observation_harness_v0.build_shadow_observation_timed_summary_v0(fwd, **kw).timed_hash
        != observation_harness_v0.build_shadow_observation_timed_summary_v0(rev, **kw).timed_hash
    )


def test_shadow_observation_timed_summary_empty_is_deterministic() -> None:
    empty: tuple[observation_harness_v0.ShadowObservationEvidenceRecord, ...] = ()
    meta = _timed_meta()
    kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": int(meta["max_observations"]),
    }
    a = observation_harness_v0.build_shadow_observation_timed_summary_v0(empty, **kw)
    b = observation_harness_v0.build_shadow_observation_timed_summary_v0(empty, **kw)
    assert a == b
    assert a.record_count == 0
    assert a.observed_at_utc_values == ()
    assert len(a.timed_hash) == 64


def test_shadow_observation_timed_summary_flags_safe_for_nonempty() -> None:
    snaps = (_snap("F1", "tsafe", {}), _snap("F2", "tsafe", {"a": 1}))
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    meta = _timed_meta()
    t = observation_harness_v0.build_shadow_observation_timed_summary_v0(
        recs,
        started_at_utc=str(meta["started_at_utc"]),
        ended_at_utc=str(meta["ended_at_utc"]),
        cadence_seconds=int(meta["cadence_seconds"]),
        max_observations=int(meta["max_observations"]),
    )
    assert t.all_no_order is True
    assert t.proven_shadow_no_order_entrypoint_found is False
    assert t.executable_command_created is False
    assert t.all_broker_touched_false is True
    assert t.all_exchange_touched_false is True
    assert t.all_credentials_touched_false is True
    assert t.all_order_intent_created_false is True
    assert t.all_runtime_started_false is True
    assert t.all_scheduler_started_false is True
    assert t.all_shadow_mode_allowed_false is True


def test_shadow_observation_timed_summary_rejects_negative_cadence_or_max() -> None:
    snaps = (_snap("V", "neg", {}),)
    recs = observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    meta = _timed_meta()
    base_kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "max_observations": int(meta["max_observations"]),
    }
    with pytest.raises(ValueError, match="cadence_seconds"):
        observation_harness_v0.build_shadow_observation_timed_summary_v0(
            recs, cadence_seconds=-1, **base_kw
        )
    with pytest.raises(ValueError, match="max_observations"):
        observation_harness_v0.build_shadow_observation_timed_summary_v0(
            recs,
            cadence_seconds=1,
            max_observations=-3,
            started_at_utc=str(meta["started_at_utc"]),
            ended_at_utc=str(meta["ended_at_utc"]),
        )


def _local_run_kw(
    run_id: str = "run-1",
    *,
    source: str = "caller_provided",
    cadence_source: str = "caller_provided",
) -> dict[str, object]:
    meta = _timed_meta()
    return {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": int(meta["max_observations"]),
        "run_id": run_id,
        "source": source,
        "cadence_source": cadence_source,
    }


def test_run_shadow_observation_local_v0_composes_records_batch_and_timed() -> None:
    snaps = (
        _snap("L1", "loc", {"i": 0}),
        _snap("L2", "loc", {"i": 1}),
    )
    kw = _local_run_kw()
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    assert run.run_version == observation_harness_v0.LOCAL_OBSERVATION_RUN_RESULT_SCHEMA_V0
    assert run.record_count == 2
    assert run.records == observation_harness_v0.run_shadow_observation_batch_v0(snaps)
    assert run.batch_summary == observation_harness_v0.build_shadow_observation_batch_summary_v0(
        run.records
    )
    assert run.timed_summary == observation_harness_v0.build_shadow_observation_timed_summary_v0(
        run.records,
        started_at_utc=str(kw["started_at_utc"]),
        ended_at_utc=str(kw["ended_at_utc"]),
        cadence_seconds=int(kw["cadence_seconds"]),
        max_observations=int(kw["max_observations"]),
        cadence_source=str(kw["cadence_source"]),
    )
    assert len(run.run_hash) == 64


def test_shadow_observation_local_run_same_inputs_same_run_hash() -> None:
    snaps = (_snap("X", "lrh", {"k": 1}),)
    kw = _local_run_kw()
    a = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    b = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    assert a.run_hash == b.run_hash


def test_shadow_observation_local_run_hash_changes_when_snapshot_payload_changes() -> None:
    kw = _local_run_kw()
    r1 = observation_harness_v0.run_shadow_observation_local_v0((_snap("P", "ch", {"k": 1}),), **kw)
    r2 = observation_harness_v0.run_shadow_observation_local_v0((_snap("P", "ch", {"k": 2}),), **kw)
    assert r1.run_hash != r2.run_hash


def test_shadow_observation_local_run_hash_changes_when_run_id_or_sources_or_timing_change() -> (
    None
):
    snaps = (_snap("Q", "meta", {}),)
    base = _local_run_kw()
    h0 = observation_harness_v0.run_shadow_observation_local_v0(snaps, **base).run_hash
    assert (
        observation_harness_v0.run_shadow_observation_local_v0(
            snaps, **{**base, "run_id": "other-run"}
        ).run_hash
        != h0
    )
    assert (
        observation_harness_v0.run_shadow_observation_local_v0(
            snaps, **{**base, "source": "fixture_provenance"}
        ).run_hash
        != h0
    )
    assert (
        observation_harness_v0.run_shadow_observation_local_v0(
            snaps, **{**base, "cadence_source": "fixture"}
        ).run_hash
        != h0
    )
    assert (
        observation_harness_v0.run_shadow_observation_local_v0(
            snaps,
            **{
                **base,
                "started_at_utc": "2026-05-16T10:00:00Z",
            },
        ).run_hash
        != h0
    )


def test_shadow_observation_local_run_hash_order_sensitive() -> None:
    s1 = _snap("A", "lord", {"n": 1})
    s2 = _snap("B", "lord", {"n": 2})
    kw = _local_run_kw()
    h_fwd = observation_harness_v0.run_shadow_observation_local_v0((s1, s2), **kw).run_hash
    h_rev = observation_harness_v0.run_shadow_observation_local_v0((s2, s1), **kw).run_hash
    assert h_fwd != h_rev


def test_shadow_observation_local_run_empty_is_deterministic() -> None:
    snaps: tuple[observation_harness_v0.ShadowObservationInputSnapshot, ...] = ()
    kw = _local_run_kw()
    a = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    b = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    assert a == b
    assert a.record_count == 0
    assert len(a.run_hash) == 64


def test_shadow_observation_local_run_flags_remain_not_approved() -> None:
    snaps = (_snap("Z1", "nap", {}), _snap("Z2", "nap", {"x": 1}))
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **_local_run_kw())
    assert run.local_observation_run_approved is False
    assert run.proven_shadow_no_order_entrypoint_found is False
    assert run.executable_command_created is False
    assert run.shadow_mode_allowed is False
    assert run.runtime_allowed is False
    assert run.scheduler_allowed is False
    assert run.order_submission_allowed is False
    assert run.all_no_order is True
    assert run.all_shadow_mode_allowed_false is True


def test_shadow_observation_local_run_rejects_snapshot_count_over_max() -> None:
    snaps = (
        _snap("M0", "cap", {}),
        _snap("M1", "cap", {}),
        _snap("M2", "cap", {}),
    )
    meta = _timed_meta()
    kw = {
        "started_at_utc": str(meta["started_at_utc"]),
        "ended_at_utc": str(meta["ended_at_utc"]),
        "cadence_seconds": int(meta["cadence_seconds"]),
        "max_observations": 2,
        "run_id": "x",
        "source": "caller_provided",
        "cadence_source": "caller_provided",
    }
    with pytest.raises(ValueError, match="snapshot count exceeds"):
        observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)


def test_build_shadow_observation_local_evidence_bundle_v0_is_deterministic() -> None:
    snaps = (_snap("E1", "evb", {"n": 1}),)
    kw = _local_run_kw(run_id="evidence-run-1")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    a = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run)
    b = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run)
    assert a == b
    assert (
        hashlib.sha256(a.local_run_result_json_bytes).hexdigest()
        == hashlib.sha256(b.local_run_result_json_bytes).hexdigest()
    )


def test_evidence_bundle_manifest_reflects_payload_hash_and_schema() -> None:
    snaps = (_snap("E2", "evm", {}),)
    kw = _local_run_kw(run_id="manifest-run")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    bundle = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run)
    payload_hash = hashlib.sha256(bundle.local_run_result_json_bytes).hexdigest()
    manifest = json.loads(bundle.manifest_json_bytes.decode("utf-8"))
    assert manifest["schema"] == observation_harness_v0.LOCAL_OBSERVATION_EVIDENCE_OUTPUT_SCHEMA_V0
    assert manifest["created_by"] == "shadow_observation_harness_v0"
    assert manifest["run_id"] == run.run_id
    assert manifest["run_hash"] == run.run_hash
    assert manifest["files"] == [
        {
            "path": "local_run_result.json",
            "sha256": payload_hash,
            "bytes": len(bundle.local_run_result_json_bytes),
        }
    ]


def test_evidence_bundle_bytes_change_when_local_run_payload_changes() -> None:
    kw = _local_run_kw(run_id="delta-run")
    r1 = observation_harness_v0.run_shadow_observation_local_v0(
        (_snap("D", "evd", {"k": 1}),), **kw
    )
    r2 = observation_harness_v0.run_shadow_observation_local_v0(
        (_snap("D", "evd", {"k": 2}),), **kw
    )
    b1 = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(r1)
    b2 = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(r2)
    assert b1.local_run_result_json_bytes != b2.local_run_result_json_bytes
    assert b1.manifest_json_bytes != b2.manifest_json_bytes


def test_write_shadow_observation_local_evidence_writes_three_files(tmp_path: Path) -> None:
    snaps = (_snap("W1", "wrt", {}),)
    kw = _local_run_kw(run_id="write-run-a")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    receipt = observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run,
        output_dir=tmp_path / "evidence_root",
        overwrite=False,
    )
    root = Path(receipt.output_root)
    names = {p.name for p in root.iterdir()}
    assert names == {
        "local_run_result.json",
        "manifest.json",
        "MANIFEST.sha256",
    }
    bundle = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run)
    assert (root / "local_run_result.json").read_bytes() == bundle.local_run_result_json_bytes
    assert (root / "manifest.json").read_bytes() == bundle.manifest_json_bytes
    digest = (root / "MANIFEST.sha256").read_bytes().decode("utf-8")
    assert digest == hashlib.sha256(bundle.manifest_json_bytes).hexdigest() + "\n"
    assert (
        receipt.local_run_result_sha256
        == hashlib.sha256(bundle.local_run_result_json_bytes).hexdigest()
    )
    assert receipt.manifest_sha256 == hashlib.sha256(bundle.manifest_json_bytes).hexdigest()
    assert (
        receipt.manifest_body_sha256_hex == hashlib.sha256(bundle.manifest_json_bytes).hexdigest()
    )


def test_write_shadow_observation_local_evidence_refuses_overwrite(tmp_path: Path) -> None:
    snaps = (_snap("W2", "novr", {}),)
    kw = _local_run_kw(run_id="write-run-b")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    out = tmp_path / "out_b"
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=False
    )
    with pytest.raises(FileExistsError):
        observation_harness_v0.write_shadow_observation_local_evidence_v0(
            run, output_dir=out, overwrite=False
        )


def test_write_shadow_observation_local_evidence_overwrite_true_replaces(tmp_path: Path) -> None:
    snaps = (_snap("W3", "ovr", {}),)
    kw = _local_run_kw(run_id="write-run-c")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    out = tmp_path / "out_c"
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=False
    )
    first_payload = (Path(out) / run.run_id / "local_run_result.json").read_bytes()
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=True
    )
    second_payload = (Path(out) / run.run_id / "local_run_result.json").read_bytes()
    assert first_payload == second_payload


def test_write_shadow_observation_local_evidence_overwrite_preserves_extra_files(
    tmp_path: Path,
) -> None:
    snaps = (_snap("W4", "xtra", {}),)
    kw = _local_run_kw(run_id="write-run-d")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    out = tmp_path / "out_d"
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=False
    )
    dest = Path(out) / run.run_id
    (dest / "extra.txt").write_text("keep", encoding="utf-8")
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=True
    )
    assert (dest / "extra.txt").read_text(encoding="utf-8") == "keep"


def test_evidence_output_receipt_authority_flags_remain_false(tmp_path: Path) -> None:
    snaps = (_snap("W5", "rcp", {}), _snap("W6", "rcp", {"z": 9}))
    kw = _local_run_kw(run_id="receipt-run")
    run = observation_harness_v0.run_shadow_observation_local_v0(snaps, **kw)
    receipt = observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run,
        output_dir=tmp_path / "out_e",
        overwrite=False,
    )
    assert receipt.local_observation_evidence_output_approved is False
    assert receipt.local_observation_run_approved is False
    assert receipt.proven_shadow_no_order_entrypoint_found is False
    assert receipt.executable_command_created is False
    assert receipt.shadow_mode_allowed is False
    assert receipt.runtime_allowed is False
    assert receipt.scheduler_allowed is False
    assert receipt.order_submission_allowed is False


def test_write_evidence_rejects_unsafe_run_id(tmp_path: Path) -> None:
    snaps = (_snap("U", "unsafe", {}),)
    meta = _timed_meta()
    run = observation_harness_v0.run_shadow_observation_local_v0(
        snaps,
        started_at_utc=str(meta["started_at_utc"]),
        ended_at_utc=str(meta["ended_at_utc"]),
        cadence_seconds=int(meta["cadence_seconds"]),
        max_observations=int(meta["max_observations"]),
        run_id="trick/../../../escape",
        source="caller_provided",
        cadence_source="caller_provided",
    )
    with pytest.raises(ValueError, match="run_id"):
        observation_harness_v0.write_shadow_observation_local_evidence_v0(
            run,
            output_dir=tmp_path / "bad",
            overwrite=False,
        )


def _fixture_pkg_snaps() -> tuple[observation_harness_v0.ShadowObservationInputSnapshot, ...]:
    """Synthetic in-test snapshots — no repo fixture files, no market data."""
    return (
        observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="FIXTURE-OBS",
            observed_at_utc="2026-01-01T00:00:00Z",
            source="fixture_static",
            payload={"price": "100.00", "state": "synthetic", "idx": 0},
        ),
        observation_harness_v0.ShadowObservationInputSnapshot(
            symbol="FIXTURE-OBS",
            observed_at_utc="2026-01-01T00:01:00Z",
            source="fixture_static",
            payload={"price": "100.01", "state": "synthetic", "idx": 1},
        ),
    )


def _fixture_pkg_local_run_kw() -> dict[str, object]:
    return {
        "started_at_utc": "2026-01-01T00:00:00Z",
        "ended_at_utc": "2026-01-01T01:00:00Z",
        "cadence_seconds": 60,
        "max_observations": 10,
        "run_id": "fixture-pkg-run-v0",
        "source": "fixture_static",
        "cadence_source": "fixture_static",
    }


def test_fixture_evidence_package_builds_local_run_from_fixture_snapshots() -> None:
    kw = _fixture_pkg_local_run_kw()
    run = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    assert run.run_version == observation_harness_v0.LOCAL_OBSERVATION_RUN_RESULT_SCHEMA_V0
    assert run.run_id == "fixture-pkg-run-v0"
    assert run.source == "fixture_static"
    assert run.record_count == 2
    assert run.local_observation_run_approved is False
    assert run.all_no_order is True
    assert run.proven_shadow_no_order_entrypoint_found is False


def test_fixture_evidence_package_writes_bounded_output_under_tmp_path(tmp_path: Path) -> None:
    kw = _fixture_pkg_local_run_kw()
    run = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    receipt = observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run,
        output_dir=tmp_path / "fixture_pkg_out",
        overwrite=False,
    )
    root = Path(receipt.output_root)
    assert {p.name for p in root.iterdir()} == {
        "local_run_result.json",
        "manifest.json",
        "MANIFEST.sha256",
    }
    bundle = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run)
    assert (root / "local_run_result.json").read_bytes() == bundle.local_run_result_json_bytes
    assert (root / "manifest.json").read_bytes() == bundle.manifest_json_bytes
    digest = (root / "MANIFEST.sha256").read_bytes().decode("utf-8")
    assert digest == hashlib.sha256(bundle.manifest_json_bytes).hexdigest() + "\n"


def test_fixture_evidence_package_generation_is_deterministic() -> None:
    kw = _fixture_pkg_local_run_kw()
    run_a = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    run_b = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    assert run_a == run_b
    b_a = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run_a)
    b_b = observation_harness_v0.build_shadow_observation_local_evidence_bundle_v0(run_b)
    assert b_a == b_b


def test_fixture_evidence_package_overwrite_behavior_explicit(tmp_path: Path) -> None:
    kw = _fixture_pkg_local_run_kw()
    run = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    out = tmp_path / "fpkg_ov"
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=False
    )
    with pytest.raises(FileExistsError):
        observation_harness_v0.write_shadow_observation_local_evidence_v0(
            run, output_dir=out, overwrite=False
        )
    observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run, output_dir=out, overwrite=True
    )


def test_fixture_evidence_package_safety_flags_false_and_no_run_approval(tmp_path: Path) -> None:
    kw = _fixture_pkg_local_run_kw()
    run = observation_harness_v0.run_shadow_observation_local_v0(_fixture_pkg_snaps(), **kw)
    assert run.local_observation_run_approved is False
    assert run.shadow_mode_allowed is False
    receipt = observation_harness_v0.write_shadow_observation_local_evidence_v0(
        run,
        output_dir=tmp_path / "fpkg_flags",
        overwrite=False,
    )
    assert receipt.local_observation_evidence_output_approved is False
    assert receipt.local_observation_run_approved is False


def test_observation_harness_has_no_sleep_or_datetime_now_tokens() -> None:
    path = Path(observation_harness_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    assert "time.sleep" not in text
    assert "datetime.now" not in text


def test_observation_harness_module_isolates_from_mixed_risk_scripts_and_runtime_packages() -> None:
    path = Path(observation_harness_v0.__file__).resolve()
    text = path.read_text(encoding="utf-8")
    for needle in ("scripts/run_shadow_execution.py", "scripts/testnet_orchestrator_cli.py"):
        assert needle not in text, f"{path} must not reference mixed-risk script path {needle!r}"
    for pattern in (
        re.compile(
            r"(?m)^\s*from\s+src\.(strategies|execution|live|scheduler|ops|data|orders|backtest)\b"
        ),
        re.compile(
            r"(?m)^\s*import\s+src\.(strategies|execution|live|scheduler|ops|data|orders|backtest)\b"
        ),
    ):
        assert pattern.search(text) is None, f"{path} must not import runtime-like src packages"


def test_observation_harness_module_source_has_no_execution_or_network_tokens() -> None:
    path = Path(observation_harness_v0.__file__).resolve()
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
