"""Static and behavioral tests for bounded review durable-run-root hardening v0."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
SHARED_HELPER = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
SHADOW_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_shadow_bounded_observation_evidence_v0.py"
TESTNET_REVIEW = REPO_ROOT / "scripts" / "ops" / "review_testnet_bounded_observation_evidence_v0.py"
SHADOW_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_shadow_bounded_observation_adapter_v0.py"
TESTNET_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
MANDATORY_CLOSEOUT_WIRING_TOKEN = "DURABLE_PRIMARY_EVIDENCE_MANDATORY_CLOSEOUT_WIRING_V0=true"
CLOSEOUT_HELPER = REPO_ROOT / "scripts" / "ops" / "durable_closeout_copy_verify_v0.py"
PAPER_ADAPTER = REPO_ROOT / "scripts" / "ops" / "run_paper_only_bounded_observation_adapter_v0.py"
MANDATORY_CLOSEOUT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_mandatory_durable_closeout_contract_v0.py"
)
HARD_GATE_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
)


# SLICE-PE-4: bounded observation / pilot / scheduler-completion closeout wiring guard matrix.
class Pe4BoundedCloseoutLane(NamedTuple):
    lane_id: str
    anchor: str
    bounded_observation: bool


PE4_BOUNDED_CLOSEOUT_LANE_MATRIX: tuple[Pe4BoundedCloseoutLane, ...] = (
    Pe4BoundedCloseoutLane(
        "shadow",
        "review_shadow_bounded_observation_evidence_v0.py",
        True,
    ),
    Pe4BoundedCloseoutLane(
        "testnet",
        "review_testnet_bounded_observation_evidence_v0.py",
        True,
    ),
    Pe4BoundedCloseoutLane(
        "paper_bounded",
        "run_paper_only_bounded_observation_adapter_v0.py",
        True,
    ),
    Pe4BoundedCloseoutLane(
        "bounded_pilot",
        "bounded observation/pilot",
        True,
    ),
    Pe4BoundedCloseoutLane(
        "scheduler_completion",
        "scheduler_completion_closeout_v0.json",
        False,
    ),
)

PE4_COMPLETION_CONTRACT_MARKERS = (
    "PE4_BOUNDED_OBSERVATION_MANDATORY_CLOSEOUT_WIRING_GUARD_V0=true",
    "MANDATORY_DURABLE_CLOSEOUT_REQUIRED=true",
    "CHECKSUM_VERIFY_REQUIRED=true",
    "PRIMARY_EVIDENCE_REQUIRED_FOR_RUN_COMPLETION=true",
    "RUN_COMPLETION_INVALID_WITHOUT_DURABLE_PRIMARY_EVIDENCE=true",
    "TMP_ONLY_EVIDENCE_INVALID=true",
    "MANIFEST_VERIFY_REQUIRED=true",
    "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true",
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "GAP2A1_PRIMARY_EVIDENCE_ENFORCED=false",
)

INVARIANT_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_primary_evidence_retention_invariant_contract_v0.py"
)
U3_CONTRACT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_preflight_scoped_exception_contract_u3_v0.py"
)


def _preflight_section_2a1() -> str:
    return PREFLIGHT.read_text(encoding="utf-8").split("## 2a.1", 1)[1].split("## 2b.", 1)[0]


def _load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_shadow_staging_bundle(staging: Path) -> None:
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "SHADOW_247_FUTURES_BOUNDED_SHADOW_DRY_RUN.md").write_text(
        "NO_BROKER\nNO_NETWORK\nNO_ORDER_SUBMISSION\n",
        encoding="utf-8",
    )
    (evidence / "steps.jsonl").write_text('{"step_index": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "shadow_247_futures_bounded_shadow_dry_run.v0",
                "NO_BROKER": True,
                "NO_NETWORK": True,
                "NO_ORDER_SUBMISSION": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("stderr\n", encoding="utf-8")


def _write_testnet_staging_bundle(staging: Path) -> None:
    evidence = staging / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    proof_doc = "docs/ops/specs/FUTURES_TESTNET_DRY_RUN_PROOF_CONTRACT_V0.md"
    (evidence / "TESTNET_BOUNDED_OBSERVATION.md").write_text(
        "\n".join(
            [
                "TESTNET_SANDBOX_ONLY",
                "NO_PRODUCTION_FALLBACK",
                "NO_LIVE_ORDER_SUBMISSION",
                proof_doc,
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence / "steps.jsonl").write_text('{"step_index": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "testnet_bounded_dry_run.v0",
                "TESTNET_SANDBOX_ONLY": True,
                "NO_PRODUCTION_FALLBACK": True,
                "NO_LIVE_ORDER_SUBMISSION": True,
                "broker_connected": False,
                "production_fallback": False,
                "proof_contract_doc": proof_doc,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = staging / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("stderr\n", encoding="utf-8")


def _write_durable_bounded_bundle(durable: Path, *, lane: str) -> None:
    if lane == "shadow":
        _write_shadow_staging_bundle(durable)
    else:
        _write_testnet_staging_bundle(durable)
    (durable / "RUN_METADATA.json").write_text('{"run_id": "test"}\n', encoding="utf-8")
    review_dir = durable / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "REVIEW_RESULT.json").write_text(
        json.dumps({"verdict": "PASS"}) + "\n",
        encoding="utf-8",
    )
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(durable)


@pytest.fixture(autouse=True)
def _cleanup_durable_archive_dirs():
    yield
    archive_roots = REPO_ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def test_shadow_review_cli_accepts_optional_durable_run_root() -> None:
    text = SHADOW_REVIEW.read_text(encoding="utf-8")
    assert "--durable-run-root" in text
    assert "validate_durable_primary_evidence_root" in text


def test_testnet_review_cli_accepts_optional_durable_run_root() -> None:
    text = TESTNET_REVIEW.read_text(encoding="utf-8")
    assert "--durable-run-root" in text
    assert "validate_durable_primary_evidence_root" in text


def test_preflight_section_2a_references_review_durable_run_root_anchor() -> None:
    section = PREFLIGHT.read_text(encoding="utf-8").split("## 2a.1", 1)[0]
    assert "review_shadow_bounded_observation_evidence_v0.py" in section
    assert "review_testnet_bounded_observation_evidence_v0.py" in section
    assert "--durable-run-root" in section
    assert "validate_durable_primary_evidence_root()" in section
    assert "default off" in section.lower() or "Default off" in section


def test_shared_helper_exposes_validate_durable_primary_evidence_root() -> None:
    text = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def validate_durable_primary_evidence_root" in text
    assert "VALIDATE_DURABLE_PRIMARY_EVIDENCE_ROOT_V0=true" in text


def test_shadow_review_omitted_durable_flag_preserves_staging_only(tmp_path: Path) -> None:
    review_mod = _load_module(
        SHADOW_REVIEW, "review_shadow_bounded_observation_evidence_v0_staging_only"
    )
    staging = Path("/tmp") / f"peak_trade_shadow_review_staging_{tmp_path.name}"
    staging.mkdir(parents=True, exist_ok=True)
    _write_shadow_staging_bundle(staging)
    result = review_mod.review_evidence(staging)
    assert result["verdict"] == review_mod.PASS
    assert "durable_run_root" not in result
    assert "durable_checks" not in result


def test_testnet_review_omitted_durable_flag_preserves_staging_only(tmp_path: Path) -> None:
    review_mod = _load_module(
        TESTNET_REVIEW, "review_testnet_bounded_observation_evidence_v0_staging_only"
    )
    staging = Path("/tmp") / f"peak_trade_testnet_review_staging_{tmp_path.name}"
    staging.mkdir(parents=True, exist_ok=True)
    _write_testnet_staging_bundle(staging)
    result = review_mod.review_evidence(staging)
    assert result["verdict"] == review_mod.PASS
    assert "durable_run_root" not in result


def test_shadow_review_durable_run_root_passes_with_valid_archive(tmp_path: Path) -> None:
    review_mod = _load_module(
        SHADOW_REVIEW, "review_shadow_bounded_observation_evidence_v0_durable_pass"
    )
    staging = Path("/tmp") / f"peak_trade_shadow_review_staging_pass_{tmp_path.name}"
    staging.mkdir(parents=True, exist_ok=True)
    durable = _durable_root(tmp_path)
    _write_shadow_staging_bundle(staging)
    _write_durable_bounded_bundle(durable, lane="shadow")
    result = review_mod.review_evidence(staging, durable_run_root=durable)
    assert result["verdict"] == review_mod.PASS
    assert result["checks"]["durable_primary_evidence_valid"] is True
    assert result["durable_checks"]["manifest_sha256_verify"] is True


def test_testnet_review_durable_run_root_passes_with_valid_archive(tmp_path: Path) -> None:
    review_mod = _load_module(
        TESTNET_REVIEW, "review_testnet_bounded_observation_evidence_v0_durable_pass"
    )
    staging = Path("/tmp") / f"peak_trade_testnet_review_staging_pass_{tmp_path.name}"
    staging.mkdir(parents=True, exist_ok=True)
    durable = _durable_root(tmp_path)
    _write_testnet_staging_bundle(staging)
    _write_durable_bounded_bundle(durable, lane="testnet")
    result = review_mod.review_evidence(staging, durable_run_root=durable)
    assert result["verdict"] == review_mod.PASS
    assert result["checks"]["durable_primary_evidence_valid"] is True


def test_shadow_review_durable_run_root_fails_closed_under_tmp(tmp_path: Path) -> None:
    review_mod = _load_module(
        SHADOW_REVIEW, "review_shadow_bounded_observation_evidence_v0_durable_tmp"
    )
    staging = Path("/tmp") / f"peak_trade_shadow_review_staging_tmp_{tmp_path.name}"
    staging.mkdir(parents=True, exist_ok=True)
    durable = Path("/tmp") / f"peak_trade_shadow_review_durable_tmp_{tmp_path.name}"
    durable.mkdir(parents=True, exist_ok=True)
    _write_shadow_staging_bundle(staging)
    _write_durable_bounded_bundle(durable, lane="shadow")
    result = review_mod.review_evidence(staging, durable_run_root=durable)
    assert result["verdict"] == review_mod.REVIEW_REQUIRED
    assert result["checks"]["durable_primary_evidence_valid"] is False
    assert any("outside /tmp" in issue for issue in result["issues"])


def test_validate_durable_primary_evidence_root_fails_on_manifest_mismatch(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.ops.primary_evidence_retention_v0 import validate_durable_primary_evidence_root

    durable = _durable_root(tmp_path)
    _write_durable_bounded_bundle(durable, lane="shadow")
    tampered = durable / "RUN_METADATA.json"
    tampered.write_text('{"run_id": "tampered"}\n', encoding="utf-8")
    ok, reason, detail = validate_durable_primary_evidence_root(durable)
    assert ok is False
    assert "checksum mismatch" in reason or any("checksum mismatch" in i for i in detail["issues"])


def test_section_2a1_contains_mandatory_closeout_wiring_token() -> None:
    section = _preflight_section_2a1()
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert "Mandatory durable closeout wiring" in section


def test_section_2a1_anchors_bounded_shadow_testnet_mandatory_closeout_wiring() -> None:
    section = _preflight_section_2a1()
    assert "review_shadow_bounded_observation_evidence_v0.py" in section
    assert "review_testnet_bounded_observation_evidence_v0.py" in section
    assert "--durable-run-root" in section
    assert "validate_durable_primary_evidence_root()" in section
    assert "MANIFEST.sha256" in section
    collapsed = section.lower()
    assert "shadow" in collapsed
    assert "testnet" in collapsed
    assert "closeout" in collapsed


def test_section_2a1_preserves_durable_run_root_opt_in_default_off() -> None:
    section = _preflight_section_2a1()
    collapsed = section.lower()
    assert "default off" in collapsed or "opt-in (default off)" in collapsed
    assert "not default-on review behavior" in collapsed
    section_2a = PREFLIGHT.read_text(encoding="utf-8").split("## 2a.1", 1)[0]
    assert "default off" in section_2a.lower() or "Default off" in section_2a


def test_section_2a1_mandatory_wiring_does_not_authorize_runtime() -> None:
    section = _preflight_section_2a1()
    collapsed = section.replace("**", "").lower()
    assert "evidence ≠ approval" in section or "evidence = approval" not in collapsed
    assert "non-authorizing" in collapsed
    assert "does not authorize runtime" in collapsed
    assert "does not clear preflight blocked" in collapsed
    for forbidden in ("live", "broker", "exchange", "scheduler"):
        assert forbidden in collapsed


def test_pr3631_review_gate_preserved_without_adapter_execute_change() -> None:
    for review in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review.read_text(encoding="utf-8")
        assert "--durable-run-root" in text
        assert "validate_durable_primary_evidence_root" in text
        assert "default=True" not in text
        assert 'default="on"' not in text.lower()
    helper = SHARED_HELPER.read_text(encoding="utf-8")
    assert "def validate_durable_primary_evidence_root" in helper
    for adapter in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "verify_manifest_sha256" in text


def test_mandatory_wiring_slice_reuses_canonical_preflight_owner_only() -> None:
    canonical = (
        REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    )
    assert canonical == PREFLIGHT
    parallel_preflight = REPO_ROOT / "docs" / "ops" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
    assert not parallel_preflight.is_file()
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in _preflight_section_2a1()


def test_bounded_review_owner_crosslinks_invariant_contract_module() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    invariant_text = INVARIANT_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert INVARIANT_CONTRACT_TESTS.name in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in invariant_text
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in invariant_text


def test_bounded_review_invariant_owners_share_mandatory_closeout_wiring_anchor() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    invariant_text = INVARIANT_CONTRACT_TESTS.read_text(encoding="utf-8")
    section = _preflight_section_2a1()
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in invariant_text
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        assert review_path.name in section
        assert "--durable-run-root" in review_path.read_text(encoding="utf-8")


def test_bounded_review_invariant_reciprocal_chain_preserves_durable_run_root_opt_in_default_off() -> (
    None
):
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        assert "--durable-run-root" in text
        assert "default=None" in text
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "durable_run_root" not in text
    collapsed = _preflight_section_2a1().replace("**", "").lower()
    assert "opt-in (default off)" in collapsed or "default off" in collapsed


def test_bounded_review_invariant_reciprocal_chain_preserves_non_authorizing_boundary() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8").lower()
    invariant_text = INVARIANT_CONTRACT_TESTS.read_text(encoding="utf-8").lower()
    section = _preflight_section_2a1().replace("**", "").lower()
    assert "non-authorizing" in owner_text or "does not authorize runtime" in section
    assert "non-authorizing" in invariant_text or "evidence" in invariant_text
    assert "blocked" in section
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        collapsed = review_path.read_text(encoding="utf-8").lower()
        assert "non-authorizing" in collapsed or "does not claim readiness" in collapsed
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        assert "live_allowed=false" in adapter_path.read_text(encoding="utf-8").lower()


def test_bounded_review_owner_crosslinks_u3_contract_module() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    u3_text = U3_CONTRACT_TESTS.read_text(encoding="utf-8")
    assert U3_CONTRACT_TESTS.name in owner_text
    assert Path(__file__).name in u3_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in u3_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in owner_text
    assert "SCOPED_PREFLIGHT_EXCEPTION_U3_V0=true" in u3_text


def test_bounded_review_u3_reciprocal_chain_preserves_durable_run_root_opt_in_default_off() -> None:
    u3_text = U3_CONTRACT_TESTS.read_text(encoding="utf-8")
    section = _preflight_section_2a1().replace("**", "").lower()
    for review_path in (SHADOW_REVIEW, TESTNET_REVIEW):
        text = review_path.read_text(encoding="utf-8")
        assert "--durable-run-root" in text
        assert "default=None" in text
    for adapter_path in (SHADOW_ADAPTER, TESTNET_ADAPTER):
        text = adapter_path.read_text(encoding="utf-8")
        assert "--durable-run-root" not in text
        assert "durable_run_root" not in text
    assert "default off" in section or "opt-in (default off)" in section
    assert SHADOW_ADAPTER.name in u3_text
    assert "does not start scheduler" in section


def test_pe4_bounded_closeout_lane_matrix_covers_required_lanes_v0() -> None:
    lane_ids = {row.lane_id for row in PE4_BOUNDED_CLOSEOUT_LANE_MATRIX}
    assert lane_ids >= frozenset(
        {"shadow", "testnet", "paper_bounded", "bounded_pilot", "scheduler_completion"}
    )


@pytest.mark.parametrize(
    "row",
    PE4_BOUNDED_CLOSEOUT_LANE_MATRIX,
    ids=lambda row: row.lane_id,
)
def test_pe4_bounded_observation_mandatory_closeout_completion_contract_row_v0(
    row: Pe4BoundedCloseoutLane,
) -> None:
    section = _preflight_section_2a1()
    owner = PREFLIGHT.read_text(encoding="utf-8")

    assert row.anchor in section or row.anchor in owner
    for token in PE4_COMPLETION_CONTRACT_MARKERS:
        assert token in section
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in section
    assert "durable_closeout_copy_verify_v0.py" in section
    assert "/tmp`-only" in section or "TMP_ONLY_EVIDENCE_INVALID" in section
    assert "MANIFEST.sha256" in section
    assert "verify_manifest_sha256" in section or "checksum" in section.lower()
    assert "not complete" in section.lower() or "incomplete" in section.lower()
    collapsed = section.replace("**", "").lower()
    assert "does not authorize runtime" in collapsed
    assert "enforcement remains opt-in" in collapsed or "default off" in collapsed
    if row.bounded_observation:
        assert "bounded" in collapsed or "observation" in collapsed


def test_pe4_bounded_observation_mandatory_closeout_wiring_guard_reciprocal_owners_v0() -> None:
    owner_text = Path(__file__).read_text(encoding="utf-8")
    mandatory_text = MANDATORY_CLOSEOUT_TESTS.read_text(encoding="utf-8")
    hard_gate_text = HARD_GATE_TESTS.read_text(encoding="utf-8")
    assert "PE4_BOUNDED_CLOSEOUT_LANE_MATRIX" in owner_text
    assert MANDATORY_CLOSEOUT_WIRING_TOKEN in mandatory_text
    assert Path(__file__).name in hard_gate_text or "bounded_observation_review" in hard_gate_text
    assert CLOSEOUT_HELPER.is_file()
    assert "durable_closeout_copy_verify_v0.py" in _preflight_section_2a1()
