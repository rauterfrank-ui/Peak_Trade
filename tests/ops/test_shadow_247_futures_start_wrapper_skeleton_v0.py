"""Static/offline guards for Shadow 247 Futures default-off start-wrapper skeleton v0."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "shadow_247_futures_start_wrapper_skeleton_v0.py"
SRC_TEXT = SCRIPT.read_text(encoding="utf-8")

_FUTURE_CONFIRM_TOKEN = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
)


def test_shadow_247_futures_wrapper_skeleton_script_exists() -> None:
    assert SCRIPT.is_file(), "expected skeleton under scripts/ops/"


@pytest.mark.parametrize(
    "forbidden_snippet",
    [
        "ccxt",
        "requests",
        "aiohttp",
        "websocket",
        "binance",
        "subprocess",
        "os.system",
        "Popen",
        "urllib.request",
        "socket",
    ],
)
def test_shadow_247_futures_wrapper_skeleton_source_has_no_blocked_substrings(
    forbidden_snippet: str,
) -> None:
    assert forbidden_snippet not in SRC_TEXT.lower()


@pytest.mark.parametrize(
    "marker",
    [
        "BOUNDARY_NO_LIVE",
        "BOUNDARY_NO_TESTNET_UNLESS_APPROVED",
        "BOUNDARY_NO_BROKER",
        "BOUNDARY_NO_PRIVATE_EXCHANGE",
        "NO_EXCHANGE",
        "EXIT_CODE_FAIL_CLOSED",
        "BOUNDARY_NO_ORDER_SUBMISSION",
        "BOUNDARY_NO_NETWORK",
        "BOUNDARY_FUTURES_PERP_SCOPE",
        "/tmp/peak_trade",
        "NO_ORDER_SUBMISSION",
        "PRESTART_SCHEMA_V0",
        "--bounded-runtime-contract-check",
        "--duration-minutes",
        "BOUNDED_RUNTIME_CONTRACT_DURATION_CAP_MINUTES",
    ],
)
def test_shadow_247_futures_wrapper_skeleton_has_boundary_constants(marker: str) -> None:
    assert marker in SRC_TEXT


def test_shadow_247_futures_wrapper_skeleton_import_has_no_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PYTHONINSPECT", raising=False)

    spec = importlib.util.spec_from_file_location(
        "_skel_under_test_shadow_247",
        SCRIPT,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert hasattr(mod, "main")
    assert mod.EXIT_FAIL_CLOSED_DEFAULT == 64


def test_shadow_247_futures_wrapper_skeleton_default_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64
    combo = proc.stderr + proc.stdout
    assert "FAIL-CLOSED" in combo or "fail-closed" in combo.lower() or "SKELETON" in combo
    assert "RUN_STARTED=false" in combo


def test_shadow_247_futures_wrapper_skeleton_correct_token_still_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    token = "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--confirm-token", token],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_futures_wrapper_skeleton_evidence_root_invalid_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-root",
            "/var/tmp/forbidden_peak_trade_fake",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64
    assert "peak_trade" in (proc.stderr + proc.stdout)


def test_shadow_247_futures_wrapper_skeleton_evidence_root_valid_prefix_still_returns_64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--evidence-root",
            "/tmp/peak_trade_shadow_247_skeleton_probe",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_futures_wrapper_skeleton_future_token_marker_in_source_only() -> None:
    marker = "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
    assert marker in SRC_TEXT
    assert "FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0" in SRC_TEXT


def test_shadow_247_futures_wrapper_skeleton_machine_lines_include_flags() -> None:
    monkeypatch_locals = subprocess.run(
        [sys.executable, str(SCRIPT), "--inspect"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    combo = monkeypatch_locals.stdout + monkeypatch_locals.stderr
    assert monkeypatch_locals.returncode == 64
    assert "BOUNDARY_NO_LIVE" in combo
    assert "RUN_STARTED=false" in combo
    assert "SCHEDULER_STARTED=false" in combo


_DRY_ART_MD = "SHADOW_247_FUTURES_PRESTART_EVIDENCE_DRYCHECK.md"
_DRY_MANIFEST_JSON = "manifest.json"
_DRY_SHA = "MANIFEST.sha256"


def _drycheck_machine_needles() -> tuple[str, ...]:
    return (
        "RUN_STARTED=false",
        "SCHEDULER_STARTED=false",
        "RUNTIME_STARTED=false",
        "NETWORK_USED=false",
        "BROKER_USED=false",
        "EXCHANGE_USED=false",
        "ORDER_SUBMISSION_USED=false",
        "READY_TO_START_FUTURES_SHADOW_247_DAEMON=false",
    )


def test_shadow_247_prestart_evidence_drycheck_writes_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ev_", dir="/tmp")
    root = Path(root_str)
    assert str(root).startswith("/tmp/peak_trade_")
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--prestart-evidence-drycheck",
            "--evidence-root",
            str(root),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    try:
        assert proc.returncode == 0
        combo = proc.stderr + proc.stdout
        for ln in _drycheck_machine_needles():
            assert ln in combo
        assert "READONLY_OPS_OR_JOBS_CONFIG_VALIDATED=false" in combo
        assert "READONLY_CONFIG_VALIDATION_OK=skipped" in combo
        assert _DRY_ART_MD in {p.name for p in root.iterdir()}
        manifest_path = root / _DRY_MANIFEST_JSON
        manifest_bytes = manifest_path.read_bytes()
        got_hex = hashlib.sha256(manifest_bytes).hexdigest()
        sha_file = root / _DRY_SHA
        assert sha_file.read_text(encoding="utf-8").strip() == got_hex
        md_txt = (root / _DRY_ART_MD).read_text(encoding="utf-8")
        for ln in _drycheck_machine_needles():
            assert ln in md_txt
        assert "## Read-only config validation" in md_txt
        assert "skipped" in md_txt.lower()
        doc = json.loads(manifest_bytes.decode("utf-8"))
        ms = doc["verbatim_machine_summary"]
        for ln in _drycheck_machine_needles():
            assert ln in ms
        blk = doc["readonly_local_config_skeleton_validation"]
        assert blk["ops_config_provided"] is False
        assert blk["jobs_config_provided"] is False
        assert blk["combined_validation_ok"] is True
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_prestart_evidence_drycheck_repeat_overwrites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_repeat_", dir="/tmp")
    cli = [
        sys.executable,
        str(SCRIPT),
        "--prestart-evidence-drycheck",
        "--evidence-root",
        root_str,
    ]
    try:
        first = subprocess.run(
            cli, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=10
        )
        second = subprocess.run(
            cli, cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=10
        )
        assert first.returncode == 0 and second.returncode == 0
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_prestart_evidence_drycheck_requires_strict_tmp_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--prestart-evidence-drycheck",
            "--evidence-root",
            "/tmp/does_not_start_with_peak_trade_convention_xx",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_prestart_evidence_drycheck_rejects_repo_internal_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    inner = REPO_ROOT / "_utest_inside_repo_peak_evidence_drychk"
    inner.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(inner.resolve()),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
    finally:
        shutil.rmtree(inner, ignore_errors=True)


def test_shadow_247_prestart_evidence_drycheck_rejects_nonempty_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_nonempty_", dir="/tmp")
    root_path = Path(root_str)
    (root_path / "unexpected.txt").write_text("junk", encoding="utf-8")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                root_str,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_prestart_evidence_drycheck_rejects_paper_named_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    parent_str = tempfile.mkdtemp(prefix="peak_trade_utest_paren_", dir="/tmp")
    paper_nested = Path(parent_str) / "paper_trade_only"
    paper_nested.mkdir(parents=True)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(paper_nested.resolve()),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
    finally:
        shutil.rmtree(parent_str, ignore_errors=True)


def test_shadow_247_prestart_evidence_drycheck_mutually_exclusive_with_inspect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_mutex_", dir="/tmp")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--inspect",
                "--prestart-evidence-drycheck",
                "--evidence-root",
                root_str,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        combo = (proc.stderr + proc.stdout).lower()
        assert "not allowed" in combo or "at most one of --inspect" in combo
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_bounded_runtime_contract_check_mutually_exclusive_with_inspect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_bmutex_i_", dir="/tmp")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--inspect",
                "--bounded-runtime-contract-check",
                "--evidence-root",
                root_str,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert "one of --inspect" in (proc.stderr + proc.stdout).lower()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_bounded_runtime_contract_check_mutually_exclusive_with_prestart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_bmutex_p_", dir="/tmp")
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--bounded-runtime-contract-check",
                "--evidence-root",
                root_str,
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert "one of --inspect" in (proc.stderr + proc.stdout).lower()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_bounded_runtime_contract_check_writes_placeholder_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_bchk_", dir="/tmp")
    root = Path(root_str)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--bounded-runtime-contract-check",
            "--evidence-root",
            str(root),
            "--duration-minutes",
            "10",
            "--confirm-token",
            _FUTURE_CONFIRM_TOKEN,
            "--config",
            "config/ops/shadow_247_futures_wrapper_skeleton.toml",
            "--jobs-config",
            "config/scheduler/jobs.toml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    try:
        assert proc.returncode == 0
        combo = proc.stderr + proc.stdout
        assert "BOUNDED_RUNTIME_CONTRACT_CHECK_WRITTEN=true" in combo
        assert "PRESTART_EVIDENCE_DRYCHECK_WRITTEN=true" in combo
        doc = json.loads((root / _DRY_MANIFEST_JSON).read_text(encoding="utf-8"))
        assert doc.get("bounded_runtime_contract_check") is True
        assert doc.get("duration_minutes_requested") == 10
        assert doc.get("duration_minutes_cap_enforced") == 30
        assert (
            doc.get("bounded_runtime_contract_version")
            == "shadow_247_futures_bounded_runtime_contract.v0"
        )
        assert doc.get("run_started") is False
        md_txt = (root / _DRY_ART_MD).read_text(encoding="utf-8")
        assert "Bounded runtime contract check" in md_txt
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_bounded_runtime_contract_check_rejects_missing_jobs_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_bcfg_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--bounded-runtime-contract-check",
                "--evidence-root",
                str(root),
                "--duration-minutes",
                "10",
                "--confirm-token",
                _FUTURE_CONFIRM_TOKEN,
                "--config",
                "config/ops/shadow_247_futures_wrapper_skeleton.toml",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        combo = (proc.stderr + proc.stdout).lower()
        assert "requires both" in combo or "jobs-config" in combo
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_bounded_runtime_contract_check_duration_out_of_range(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_bdur_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--bounded-runtime-contract-check",
                "--evidence-root",
                str(root),
                "--duration-minutes",
                "99",
                "--confirm-token",
                _FUTURE_CONFIRM_TOKEN,
                "--config",
                "config/ops/shadow_247_futures_wrapper_skeleton.toml",
                "--jobs-config",
                "config/scheduler/jobs.toml",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert "duration-minutes" in (proc.stderr + proc.stdout).lower()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_wrapper_config_validate_requires_prestart_drycheck(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--config",
            "config/ops/shadow_247_futures_wrapper_skeleton.toml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64
    assert "drycheck" in (proc.stderr + proc.stdout).lower()


def test_shadow_247_wrapper_inspect_rejects_paired_config_args(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--inspect",
            "--config",
            "config/ops/shadow_247_futures_wrapper_skeleton.toml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert proc.returncode == 64


def test_shadow_247_prestart_drycheck_with_valid_ops_config_writes_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_cfg_", dir="/tmp")
    root = Path(root_str)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--prestart-evidence-drycheck",
            "--evidence-root",
            str(root),
            "--config",
            "config/ops/shadow_247_futures_wrapper_skeleton.toml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    try:
        assert proc.returncode == 0
        combo = proc.stderr + proc.stdout
        assert "READONLY_OPS_OR_JOBS_CONFIG_VALIDATED=true" in combo
        assert "READONLY_CONFIG_VALIDATION_OK=true" in combo
        md_txt = (root / _DRY_ART_MD).read_text(encoding="utf-8")
        assert "**PASS**" in md_txt
        doc = json.loads((root / _DRY_MANIFEST_JSON).read_text(encoding="utf-8"))
        blk = doc["readonly_local_config_skeleton_validation"]
        assert blk["ops_config_provided"] is True
        assert blk["jobs_config_provided"] is False
        assert blk["combined_validation_ok"] is True
        assert not blk["ops_validation_errors"]
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def test_shadow_247_prestart_drycheck_with_ops_and_scheduler_jobs_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_dual_", dir="/tmp")
    root = Path(root_str)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--prestart-evidence-drycheck",
            "--evidence-root",
            str(root),
            "--config",
            "config/ops/shadow_247_futures_wrapper_skeleton.toml",
            "--jobs-config",
            "config/scheduler/jobs.toml",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    try:
        assert proc.returncode == 0
        doc = json.loads((root / _DRY_MANIFEST_JSON).read_text(encoding="utf-8"))
        blk = doc["readonly_local_config_skeleton_validation"]
        assert blk["ops_config_provided"] is True
        assert blk["jobs_config_provided"] is True
        assert blk["combined_validation_ok"] is True
        tail = Path(blk["jobs_config_absolute"]).as_posix()
        assert tail.endswith("config/scheduler/jobs.toml")
        assert not blk["ops_validation_errors"] and not blk["jobs_validation_errors"]
    finally:
        shutil.rmtree(root_str, ignore_errors=True)


def _mutate_ops_fixture(text: str, rel_name: str) -> Path:
    mut_dir = REPO_ROOT / "_utest_shadow_247_ops_cfg_mut"
    mut_dir.mkdir(exist_ok=True)
    p = mut_dir / rel_name
    p.write_text(text, encoding="utf-8")
    return p.relative_to(REPO_ROOT)


def test_shadow_247_prestart_drycheck_mutated_ops_config_fail_closed_no_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    good = (REPO_ROOT / "config/ops/shadow_247_futures_wrapper_skeleton.toml").read_text(
        encoding="utf-8",
    )
    bad = good.replace("enabled = false", "enabled = true", 1)
    rel = _mutate_ops_fixture(bad, "unsafe_enabled_true.toml")
    mut_dir = REPO_ROOT / "_utest_shadow_247_ops_cfg_mut"
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_bad_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(root),
                "--config",
                str(rel),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        combo = proc.stderr + proc.stdout
        assert "validation failed" in combo.lower()
        assert not (root / _DRY_ART_MD).exists()
        assert "READY_TO_START_FUTURES_SHADOW_247_DAEMON=true" not in combo
    finally:
        shutil.rmtree(root_str, ignore_errors=True)
        shutil.rmtree(mut_dir, ignore_errors=True)


def test_shadow_247_prestart_drycheck_mutated_live_allowed_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    good = (REPO_ROOT / "config/ops/shadow_247_futures_wrapper_skeleton.toml").read_text(
        encoding="utf-8",
    )
    bad = good.replace("live_allowed = false", "live_allowed = true", 1)
    rel = _mutate_ops_fixture(bad, "unsafe_live.toml")
    mut_dir = REPO_ROOT / "_utest_shadow_247_ops_cfg_mut"
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_bad2_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(root),
                "--config",
                str(rel),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert not (root / _DRY_ART_MD).exists()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)
        shutil.rmtree(mut_dir, ignore_errors=True)


def test_shadow_247_prestart_drycheck_mutated_order_submission_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    good = (REPO_ROOT / "config/ops/shadow_247_futures_wrapper_skeleton.toml").read_text(
        encoding="utf-8",
    )
    bad = good.replace(
        "order_submission_allowed = false",
        "order_submission_allowed = true",
        1,
    )
    rel = _mutate_ops_fixture(bad, "unsafe_orders.toml")
    mut_dir = REPO_ROOT / "_utest_shadow_247_ops_cfg_mut"
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_bad3_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(root),
                "--config",
                str(rel),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert not (root / _DRY_ART_MD).exists()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)
        shutil.rmtree(mut_dir, ignore_errors=True)


def test_shadow_247_prestart_drycheck_mutated_instrument_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    good = (REPO_ROOT / "config/ops/shadow_247_futures_wrapper_skeleton.toml").read_text(
        encoding="utf-8",
    )
    bad = good.replace('instrument = "BTCUSDT"', 'instrument = "ETHUSDT"', 1)
    rel = _mutate_ops_fixture(bad, "unsafe_instrument.toml")
    mut_dir = REPO_ROOT / "_utest_shadow_247_ops_cfg_mut"
    root_str = tempfile.mkdtemp(prefix="peak_trade_utest_ro_bad4_", dir="/tmp")
    root = Path(root_str)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--prestart-evidence-drycheck",
                "--evidence-root",
                str(root),
                "--config",
                str(rel),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert proc.returncode == 64
        assert not (root / _DRY_ART_MD).exists()
    finally:
        shutil.rmtree(root_str, ignore_errors=True)
        shutil.rmtree(mut_dir, ignore_errors=True)
