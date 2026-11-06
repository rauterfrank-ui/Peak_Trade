"""Focused tests: PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from src.ops.pre_economic_zero_order_evidence_session_contract_v1 import (
    evaluate_pre_economic_zero_order_evidence_session_contract_v1,
    PreEconomicZeroOrderEvidenceSessionOverridesV1,
    REQUIRED_DECISION_LOGIC_BINDINGS,
)
from src.ops.pre_economic_zero_order_evidence_session_runner_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
    PRODUCTION_SESSION_DURATION_SECONDS,
    AbortReason,
    ControllableClock,
    PreEconomicSessionRunnerError,
    TelemetryLedgerV1,
    TelemetryState,
    atomic_write_text,
    forbid_order_attempt,
    load_session_config_v1,
    redact_mapping,
    resolve_output_root,
    run_pre_economic_zero_order_evidence_session_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_verifier_v1 import (
    RESULT_IMPLEMENTATION_READINESS_PASS,
    RESULT_SESSION_NOT_AUTHORIZED,
    RESULT_SHADOW_ACTIVATION_INELIGIBLE,
    evaluate_implementation_readiness_binding_v1,
    verify_session_evidence_root_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_SRC = REPO_ROOT / "src/ops/pre_economic_zero_order_evidence_session_runner_v1.py"
VERIFIER_SRC = REPO_ROOT / "src/ops/pre_economic_zero_order_evidence_session_verifier_v1.py"
CLI = REPO_ROOT / "scripts/ops/run_pre_economic_zero_order_evidence_session_v1.py"
CONFIG = REPO_ROOT / "config/ops/pre_economic_zero_order_evidence_session_v1.toml"
CONTRACT_DOC = REPO_ROOT / "docs/ops/runbooks/PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1.md"
SHADOW_TOML = REPO_ROOT / "config/ops/shadow_preparation_readiness_gate_v0.toml"
SHADOW_CONTRACT = REPO_ROOT / "docs/ops/runbooks/SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
STEP29U_ELIGIBILITY = (
    REPO_ROOT / "docs/ops/runbooks/STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0.md"
)
STEP29U_INVENTORY = (
    REPO_ROOT / "docs/ops/runbooks/STEP_29U_CANONICAL_BINDING_AND_IMPLEMENTATION_INVENTORY_V0.md"
)
CHARTER = REPO_ROOT / "docs/ops/runbooks/SHADOW_247_GOVERNANCE_CHARTER_V0.md"
PROGRESS = REPO_ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
RUNBOOK = REPO_ROOT / "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.orders",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.webui",
)


@pytest.fixture()
def unique_out(request):
    """Unique output namespace under repo out/ for path-safety checks."""
    base = REPO_ROOT / "out" / "ops" / "_pez_tests" / f"{request.node.name}_{uuid.uuid4().hex[:10]}"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    yield base
    shutil.rmtree(base, ignore_errors=True)


def test_package_marker_and_defaults() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID == "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1"
    cfg = load_session_config_v1(repo_root=REPO_ROOT)
    assert cfg.implementation_enabled is False
    assert cfg.session_execution_authorized is False
    assert cfg.operator_go_required is True
    assert cfg.dry_run is True
    assert cfg.zero_order_enforced is True
    assert cfg.runtime_authority == "NONE"
    assert cfg.orders_allowed is False
    assert cfg.production_session_duration_seconds == 21600
    assert cfg.maximum_test_runtime_seconds < 21600


def test_happy_path_dry_run_implementation_readiness(unique_out: Path) -> None:
    session_id = "happy_path"
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    cfg = load_session_config_v1(repo_root=REPO_ROOT)
    # Use a throwaway config with redirected output_root.
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if line.startswith("output_root"):
            lines.append(f'output_root = "{out_rel}"')
        else:
            lines.append(line)
    tmp_cfg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)

    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id=session_id,
        clock=ControllableClock(10.0),
        max_cycles=3,
        allow_implementation_dry_run=True,
        operator_go_present=False,
        head_sha="deadbeef",
        evidence_subdir=session_id,
    )
    assert result.terminal_state == TelemetryState.COMPLETED.value
    assert result.orders_attempted == 0
    assert result.orders_submitted == 0
    assert result.zero_order_enforced is True
    assert result.runtime_authority == "NONE"
    assert result.operator_go_present is False
    assert result.heartbeat_count == 3
    assert result.integrity_status == "PASS"
    assert result.completeness == "COMPLETE"
    assert result.consumer_eligibility is False
    assert result.implementation_readiness == RESULT_IMPLEMENTATION_READINESS_PASS
    assert result.session_evidence_status == RESULT_SESSION_NOT_AUTHORIZED
    assert result.shadow_activation_eligible is False

    evidence_root = REPO_ROOT / result.evidence_root
    verification = verify_session_evidence_root_v1(
        evidence_root=evidence_root,
        repo_root=REPO_ROOT,
    )
    assert verification.implementation_readiness == RESULT_IMPLEMENTATION_READINESS_PASS
    assert verification.session_evidence == RESULT_SESSION_NOT_AUTHORIZED
    assert verification.economic_validity == "ECONOMIC_GATE_UNCHANGED"
    assert verification.shadow_activation == RESULT_SHADOW_ACTIVATION_INELIGIBLE
    assert verification.consumer_eligibility is False

    binding = evaluate_implementation_readiness_binding_v1(
        repo_root=REPO_ROOT,
        evidence_root=evidence_root,
    )
    assert binding["implementation_readiness"] == RESULT_IMPLEMENTATION_READINESS_PASS
    assert binding["six_hour_session_ready"] is False
    assert binding["session_admissible"] is False
    assert binding["contract_six_hour_session_ready"] is False
    assert "EXPLICIT_OPERATOR_GO_ABSENT" in binding["contract_blockers"]


def test_order_attempt_fail_closed(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="order_attempt",
        clock=ControllableClock(0.0),
        allow_implementation_dry_run=True,
        order_attempt=True,
        evidence_subdir="order_attempt",
    )
    assert result.orders_attempted == 1
    assert result.orders_submitted == 0
    assert result.abort_reason == AbortReason.ORDER_ATTEMPT_FORBIDDEN.value
    assert result.terminal_state == TelemetryState.ABORTED.value
    assert result.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"
    with pytest.raises(PreEconomicSessionRunnerError):
        forbid_order_attempt("unit")


def test_production_duration_without_go_blocked(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="dur21600",
        clock=ControllableClock(0.0),
        requested_duration_seconds=PRODUCTION_SESSION_DURATION_SECONDS,
        allow_implementation_dry_run=True,
        operator_go_present=False,
        evidence_subdir="dur21600",
    )
    assert result.abort_reason == AbortReason.PRODUCTION_DURATION_BLOCKED.value
    assert result.terminal_state == TelemetryState.ABORTED.value
    assert result.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"


def test_missing_operator_authorization_blocks_non_dry_run(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="nondry",
        clock=ControllableClock(0.0),
        dry_run_override=False,
        allow_implementation_dry_run=True,
        evidence_subdir="nondry",
    )
    assert result.abort_reason == AbortReason.SESSION_NOT_AUTHORIZED.value


def test_unknown_config_fields_fail_closed(tmp_path: Path) -> None:
    text = CONFIG.read_text(encoding="utf-8") + "\nunexpected_field = true\n"
    path = tmp_path / "bad.toml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PreEconomicSessionRunnerError, match="UNKNOWN_CONFIG_FIELDS"):
        load_session_config_v1(repo_root=REPO_ROOT, config_path=path)


def test_unsafe_config_combinations_fail_closed(tmp_path: Path) -> None:
    text = CONFIG.read_text(encoding="utf-8")
    text = text.replace(
        "session_execution_authorized = false", "session_execution_authorized = true"
    )
    text = text.replace("dry_run = true", "dry_run = false")
    path = tmp_path / "unsafe.toml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PreEconomicSessionRunnerError, match="CONFIG_UNSAFE"):
        load_session_config_v1(repo_root=REPO_ROOT, config_path=path)


def test_path_traversal_rejected() -> None:
    with pytest.raises(PreEconomicSessionRunnerError, match="OUTPUT_PATH_ESCAPE"):
        resolve_output_root(repo_root=REPO_ROOT, output_root="../outside")
    with pytest.raises(PreEconomicSessionRunnerError, match="OUTPUT_PATH_ESCAPE"):
        resolve_output_root(repo_root=REPO_ROOT, output_root="/tmp/abs")


def test_symlink_output_forbidden(unique_out: Path) -> None:
    target = unique_out / "real_dir"
    target.mkdir(parents=True, exist_ok=True)
    link = unique_out / "link_out"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(PreEconomicSessionRunnerError, match="SYMLINK"):
        resolve_output_root(
            repo_root=REPO_ROOT,
            output_root=link.relative_to(REPO_ROOT).as_posix(),
        )


def test_missing_manifest_and_terminal_invalid(unique_out: Path) -> None:
    evidence = unique_out / "incomplete"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "session_manifest.json").write_text(
        json.dumps(
            {
                "session_id": "x",
                "evidence_schema_version": "v1",
                "contract_version": "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1",
                "runtime_authority": "NONE",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    verification = verify_session_evidence_root_v1(evidence_root=evidence, repo_root=REPO_ROOT)
    assert verification.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"
    assert "MISSING_ARTIFACTS" in ",".join(verification.blockers)


def test_tampered_file_digest_invalid(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="tamper",
        clock=ControllableClock(0.0),
        max_cycles=2,
        allow_implementation_dry_run=True,
        evidence_subdir="tamper",
    )
    evidence_root = REPO_ROOT / result.evidence_root
    terminal = evidence_root / "terminal_result.json"
    payload = json.loads(terminal.read_text(encoding="utf-8"))
    payload["orders_attempted"] = 99
    terminal.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verification = verify_session_evidence_root_v1(
        evidence_root=evidence_root,
        repo_root=REPO_ROOT,
    )
    assert verification.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"
    assert any("DIGEST_MISMATCH" in b for b in verification.blockers)


def test_session_id_mismatch_blocked(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="sid_ok",
        clock=ControllableClock(0.0),
        max_cycles=2,
        allow_implementation_dry_run=True,
        evidence_subdir="sid_ok",
    )
    evidence_root = REPO_ROOT / result.evidence_root
    # Bypass integrity by rewriting both file and manifest entry is hard; instead
    # mutate after clearing manifests to isolate semantic mismatch path.
    terminal = json.loads((evidence_root / "terminal_result.json").read_text(encoding="utf-8"))
    terminal["session_id"] = "other"
    # Recompute digests for verifier content checks by rewriting all tracked files
    # consistently except lifecycle keeps original id — create mismatch.
    (evidence_root / "terminal_result.json").write_text(
        json.dumps(terminal, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Refresh manifest digests so integrity passes but semantic mismatch remains.
    lines = []
    for name in sorted(p.name for p in evidence_root.iterdir() if p.is_file()):
        if name == "evidence_manifest.sha256":
            continue
        digest = __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (evidence_root / "evidence_manifest.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    integrity = json.loads((evidence_root / "integrity_manifest.json").read_text(encoding="utf-8"))
    files = {}
    for name in integrity.get("files", {}):
        files[name] = __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
    integrity["files"] = files
    (evidence_root / "integrity_manifest.json").write_text(
        json.dumps(integrity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Update manifest again after integrity rewrite.
    lines = []
    for name in sorted(p.name for p in evidence_root.iterdir() if p.is_file()):
        if name == "evidence_manifest.sha256":
            continue
        digest = __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (evidence_root / "evidence_manifest.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    verification = verify_session_evidence_root_v1(
        evidence_root=evidence_root,
        repo_root=REPO_ROOT,
    )
    assert any("SESSION_ID_MISMATCH" in b for b in verification.blockers)
    assert verification.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"


def test_duplicate_terminal_and_event_after_terminal() -> None:
    clock = ControllableClock(0.0)
    ledger = TelemetryLedgerV1(session_id="t")
    ledger.events.append(
        __import__(
            "src.ops.pre_economic_zero_order_evidence_session_runner_v1",
            fromlist=["TelemetryEventV1"],
        ).TelemetryEventV1(
            sequence=1,
            state=TelemetryState.INITIALIZING.value,
            elapsed_seconds=0.0,
            timestamp=0.0,
        )
    )
    ledger.current_state = TelemetryState.INITIALIZING
    ledger.transition(to_state=TelemetryState.READY, clock=clock, start_ts=0.0)
    ledger.transition(to_state=TelemetryState.RUNNING, clock=clock, start_ts=0.0)
    ledger.transition(to_state=TelemetryState.COMPLETED, clock=clock, start_ts=0.0)
    with pytest.raises(PreEconomicSessionRunnerError, match="EVENT_AFTER_TERMINAL"):
        ledger.transition(to_state=TelemetryState.HEARTBEAT, clock=clock, start_ts=0.0)


def test_non_monotone_sequence_and_time() -> None:
    clock = ControllableClock(0.0)
    ledger = TelemetryLedgerV1(session_id="t")
    TelemetryEventV1 = __import__(
        "src.ops.pre_economic_zero_order_evidence_session_runner_v1",
        fromlist=["TelemetryEventV1"],
    ).TelemetryEventV1
    ledger.events.append(
        TelemetryEventV1(
            sequence=1,
            state=TelemetryState.INITIALIZING.value,
            elapsed_seconds=0.0,
            timestamp=0.0,
        )
    )
    ledger.current_state = TelemetryState.INITIALIZING
    ledger.transition(to_state=TelemetryState.READY, clock=clock, start_ts=0.0)
    # Force non-monotone by injecting bad last elapsed then advancing negatively via hack
    ledger.events[-1].elapsed_seconds = 99.0
    with pytest.raises(PreEconomicSessionRunnerError, match="NON_MONOTONE_TIME"):
        ledger.transition(to_state=TelemetryState.RUNNING, clock=clock, start_ts=0.0)


def test_signal_abort_and_exception(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)

    signal_result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="sig",
        clock=ControllableClock(0.0),
        max_cycles=5,
        allow_implementation_dry_run=True,
        force_abort=AbortReason.SIGNAL_ABORT,
        evidence_subdir="sig",
    )
    assert signal_result.abort_reason == AbortReason.SIGNAL_ABORT.value
    assert signal_result.terminal_state == TelemetryState.ABORTED.value

    exc_result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="exc",
        clock=ControllableClock(0.0),
        max_cycles=5,
        allow_implementation_dry_run=True,
        inject_exception=RuntimeError("boom"),
        evidence_subdir="exc",
    )
    assert exc_result.abort_reason == AbortReason.UNEXPECTED_EXCEPTION.value
    assert exc_result.terminal_state == TelemetryState.ABORTED.value


def test_heartbeat_staleness_blocks_consumption(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)
    result = run_pre_economic_zero_order_evidence_session_v1(
        repo_root=REPO_ROOT,
        config=cfg,
        session_id="stale",
        clock=ControllableClock(0.0),
        max_cycles=2,
        allow_implementation_dry_run=True,
        evidence_subdir="stale",
    )
    evidence_root = REPO_ROOT / result.evidence_root
    hb = json.loads((evidence_root / "heartbeat_summary.json").read_text(encoding="utf-8"))
    hb["stale"] = True
    (evidence_root / "heartbeat_summary.json").write_text(
        json.dumps(hb, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    # Refresh digests
    lines = []
    for name in sorted(p.name for p in evidence_root.iterdir() if p.is_file()):
        if name == "evidence_manifest.sha256":
            continue
        digest = __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (evidence_root / "evidence_manifest.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    integrity = json.loads((evidence_root / "integrity_manifest.json").read_text(encoding="utf-8"))
    integrity["files"] = {
        name: __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
        for name in integrity.get("files", {})
    }
    (evidence_root / "integrity_manifest.json").write_text(
        json.dumps(integrity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = []
    for name in sorted(p.name for p in evidence_root.iterdir() if p.is_file()):
        if name == "evidence_manifest.sha256":
            continue
        digest = __import__("hashlib").sha256((evidence_root / name).read_bytes()).hexdigest()
        lines.append(f"{digest}  {name}")
    (evidence_root / "evidence_manifest.sha256").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    verification = verify_session_evidence_root_v1(
        evidence_root=evidence_root,
        repo_root=REPO_ROOT,
    )
    assert "HEARTBEAT_STALE" in verification.blockers
    assert verification.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"


def test_secret_redaction_and_atomic_write(tmp_path: Path) -> None:
    payload = {"api_key": "supersecret", "nested": {"token": "abc", "ok": 1}}
    redacted = redact_mapping(payload)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["ok"] == 1
    path = tmp_path / "x.json"
    digest = atomic_write_text(path=path, text='{"a":1}\n')
    assert path.read_text(encoding="utf-8") == '{"a":1}\n'
    assert len(digest) == 64


def test_old_schema_version_blocked(unique_out: Path) -> None:
    evidence = unique_out / "old_schema"
    evidence.mkdir(parents=True, exist_ok=True)
    for name in (
        "session_manifest.json",
        "lifecycle_events.json",
        "heartbeat_summary.json",
        "abort_summary.json",
        "terminal_result.json",
        "integrity_manifest.json",
        "effective_config_snapshot.json",
    ):
        (evidence / name).write_text("{}\n", encoding="utf-8")
    (evidence / "session_manifest.json").write_text(
        json.dumps(
            {
                "session_id": "old",
                "evidence_schema_version": "v0",
                "contract_version": "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_V1",
                "runtime_authority": "NONE",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "evidence_manifest.sha256").write_text("", encoding="utf-8")
    verification = verify_session_evidence_root_v1(evidence_root=evidence, repo_root=REPO_ROOT)
    assert "INCOMPATIBLE_EVIDENCE_SCHEMA_VERSION" in verification.blockers
    assert verification.implementation_readiness == "IMPLEMENTATION_READINESS_BLOCKED"


def test_determinism_same_inputs(unique_out: Path) -> None:
    out_rel = unique_out.relative_to(REPO_ROOT).as_posix()
    tmp_cfg = unique_out / "cfg.toml"
    text = CONFIG.read_text(encoding="utf-8").replace(
        'output_root = "out/ops/pre_economic_zero_order_evidence_session_v1"',
        f'output_root = "{out_rel}"',
    )
    tmp_cfg.write_text(text, encoding="utf-8")
    cfg = load_session_config_v1(repo_root=REPO_ROOT, config_path=tmp_cfg)

    def _once(sid: str):
        return run_pre_economic_zero_order_evidence_session_v1(
            repo_root=REPO_ROOT,
            config=cfg,
            session_id=sid,
            clock=ControllableClock(0.0),
            max_cycles=2,
            allow_implementation_dry_run=True,
            head_sha="abc",
            evidence_subdir=sid,
        )

    a = _once("det_a")
    b = _once("det_b")
    assert a.config_digest == b.config_digest
    assert a.implementation_digest == b.implementation_digest
    assert a.heartbeat_count == b.heartbeat_count
    assert a.terminal_state == b.terminal_state
    assert a.elapsed_seconds == b.elapsed_seconds


def test_contract_still_blocks_six_hour_without_go() -> None:
    result = evaluate_pre_economic_zero_order_evidence_session_contract_v1(
        overrides=PreEconomicZeroOrderEvidenceSessionOverridesV1(
            operator_go_present=False,
            decision_logic_bound={k: True for k in REQUIRED_DECISION_LOGIC_BINDINGS},
            implementation_readiness_passed=True,
        )
    )
    assert result.six_hour_session_ready is False
    assert "EXPLICIT_OPERATOR_GO_ABSENT" in result.blockers


def test_no_forbidden_imports() -> None:
    for src in (RUNNER_SRC, VERIFIER_SRC):
        tree = ast.parse(src.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        for mod in imported:
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not mod.startswith(prefix), f"{src.name}:{mod}"


def test_docs_and_shadow_surfaces_reconciled() -> None:
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_IMPLEMENTATION_READINESS_V1" in doc
    assert "IMPLEMENTATION_READINESS" in doc
    assert "SIX_HOUR_SESSION_EXECUTED=false" in doc or "SIX_HOUR_SESSION_READY=false" in doc
    assert "SESSION_EXECUTION_AUTHORIZED=false" in doc

    toml = SHADOW_TOML.read_text(encoding="utf-8")
    assert "pre_economic_zero_order_evidence_implementation_readiness" in toml
    assert "economic_validity_offline_gate_pass = false" in toml
    assert "shadow_activation_authorized = false" in toml

    for path in (
        SHADOW_CONTRACT,
        STEP29U_ELIGIBILITY,
        STEP29U_INVENTORY,
        CHARTER,
        PROGRESS,
        RUNBOOK,
    ):
        text = path.read_text(encoding="utf-8")
        assert "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE" in text
        assert "IMPLEMENTATION_READINESS" in text or "implementation readiness" in text.lower()


def test_cli_dry_run_and_reject(unique_out: Path) -> None:
    # CLI uses canonical output root; use unique session ids to avoid collisions.
    sid = f"cli_{unique_out.name}"
    # Clean target if present
    target = REPO_ROOT / "out/ops/pre_economic_zero_order_evidence_session_v1" / sid
    if target.exists():
        for p in sorted(target.rglob("*"), reverse=True):
            if p.is_file() or p.is_symlink():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        target.rmdir()

    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "dry-run",
            "--allow-implementation-dry-run",
            "--session-id",
            sid,
            "--max-cycles",
            "2",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["implementation_readiness"] == RESULT_IMPLEMENTATION_READINESS_PASS
    assert payload["orders_attempted"] == 0

    proc2 = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "reject-production-duration",
            "--json",
            "--session-id",
            f"{sid}_reject",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    payload2 = json.loads(proc2.stdout)
    assert payload2["abort_reason"] in {
        "PRODUCTION_DURATION_BLOCKED",
        "SESSION_NOT_AUTHORIZED",
        "TIME_BUDGET_EXCEEDED",
    }
