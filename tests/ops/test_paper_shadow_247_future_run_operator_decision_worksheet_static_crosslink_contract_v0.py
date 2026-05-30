"""Static crosslink contract tests for Paper-Shadow-247 Future-Run Operator Decision Worksheet v0.

Verifies the charter-hosted worksheet maps Preflight §5 dimensions and §2a.1
hard-gate posture to existing canonical owners without authorizing runtime —
static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
REGISTRY = REPO_ROOT / "docs" / "ops" / "registry"
SCRIPTS = REPO_ROOT / "scripts" / "ops"

CHARTER = RUNBOOKS / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
PREFLIGHT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
DOCS_TRUTH_MAP = REGISTRY / "DOCS_TRUTH_MAP.md"
PRIMARY_EVIDENCE_HELPER = SCRIPTS / "primary_evidence_retention_v0.py"
HARD_GATE_TEST = REPO_ROOT / "tests" / "ops" / "test_run_primary_evidence_retention_hard_gate_v0.py"
THIS_TEST = Path(__file__).resolve().relative_to(REPO_ROOT)

WORKSHEET_SECTION = "## Future-run operator decision worksheet v0"

WORKSHEET_MACHINE_LINES: tuple[str, ...] = (
    "PAPER_SHADOW_247_FUTURE_RUN_OPERATOR_DECISION_WORKSHEET_V0=true",
    "PREFLIGHT_STATUS_REMAINS_BLOCKED=true",
    "STOP_IDLE_PRESERVED=true",
    "WORKSHEET_AUTHORIZES_RUNTIME=false",
    "WORKSHEET_CREATES_EVIDENCE_SURFACE=false",
)

SECTION_5_DIMENSIONS: tuple[str, ...] = (
    "Single owner entrypoint",
    "Canonical job set",
    "Commands",
    "Output paths",
    "Stop and emergency-stop",
    "Dry-run proof",
    "Risk boundaries",
)

HARD_GATE_MACHINE_LINES: tuple[str, ...] = (
    "RUN_PRIMARY_EVIDENCE_RETENTION_HARD_GATE_V0=true",
    "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
)

FORBIDDEN_DUPLICATE_FRAGMENTS: tuple[str, ...] = (
    "PAPER_SHADOW_247_FUTURE_RUN_OPERATOR_DECISION_WORKSHEET_CONTRACT",
    "FUTURE_RUN_OPERATOR_DECISION_WORKSHEET_V1",
    "PAPER_SHADOW_247_OPERATOR_WORKSHEET_RUNBOOK",
)

FORBIDDEN_COMPETING_GLOBS: tuple[str, ...] = (
    "*FUTURE_RUN*OPERATOR*WORKSHEET*RUNBOOK*",
    "*PAPER_SHADOW*247*WORKSHEET*CONTRACT*V1*",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "preflight ready",
    "ready for operator arming",
    "runtime authorized",
    "scheduler authorized",
    "daemon authorized",
    "paper run is approved",
    "shadow run is approved",
    "paper/shadow approved",
    "testnet is approved",
    "live is authorized",
    "aws approved",
    "broker execution is approved",
    "exchange execution is approved",
    "evidence retention complete",
    "operator approval bypassed",
    "gate is passed",
    "blocker is cleared",
    "daemon is authorized",
    "runtime is authorized",
    "preflight grants authority",
    "this worksheet authorizes",
    "worksheet authorizes runtime",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def _lower(path: Path) -> str:
    return _plain(path).lower()


def _worksheet_section() -> str:
    return _plain(CHARTER).split(WORKSHEET_SECTION, 1)[1].split("## Document control", 1)[0]


def test_charter_contains_future_run_operator_decision_worksheet_section_v0() -> None:
    text = _read(CHARTER)
    assert WORKSHEET_SECTION in text
    section = _worksheet_section()
    lowered = section.lower()
    assert "review-only" in lowered
    assert "non-authorizing" in lowered
    assert "stage 0" in lowered or "stop_idle" in lowered
    for line in WORKSHEET_MACHINE_LINES:
        assert line in section, f"missing worksheet machine line: {line!r}"


def test_worksheet_includes_all_seven_preflight_section_5_dimensions_v0() -> None:
    section = _worksheet_section()
    preflight_plain = _plain(PREFLIGHT)
    section_five = preflight_plain.split("## 5. Mandatory preflight dimensions (future)", 1)[
        1
    ].split("## 6. Expected JSON shape", 1)[0]
    for dimension in SECTION_5_DIMENSIONS:
        assert dimension in section_five, f"preflight §5 missing dimension: {dimension!r}"
        assert dimension in section, f"worksheet missing dimension: {dimension!r}"


def test_worksheet_links_preflight_taxonomy_and_primary_evidence_hard_gate_v0() -> None:
    section = _worksheet_section()
    lowered = section.lower()
    assert PREFLIGHT.name in section
    assert TAXONOMY.name in section
    assert "§2a.1" in section or "2a.1" in section
    assert "primary-evidence hard gate" in lowered or "primary evidence hard gate" in lowered
    assert PRIMARY_EVIDENCE_HELPER.name in section
    assert HARD_GATE_TEST.name in section
    assert PRIMARY_EVIDENCE_HELPER.is_file()
    assert HARD_GATE_TEST.is_file()
    assert TAXONOMY.is_file()
    for marker in HARD_GATE_MACHINE_LINES:
        assert marker in _read(PREFLIGHT), f"missing preflight §2a.1 machine line: {marker!r}"
    assert "evidence ≠ approval" in lowered or "evidence = approval" not in lowered


def test_preflight_section_5_reciprocal_pointer_to_charter_worksheet_v0() -> None:
    text = _read(PREFLIGHT)
    section_five = (
        _plain(PREFLIGHT)
        .split("## 5. Mandatory preflight dimensions (future)", 1)[1]
        .split("## 6. Expected JSON shape", 1)[0]
    )
    assert "Future-run operator decision worksheet" in section_five
    assert CHARTER.name in section_five
    assert "non-authorizing" in section_five.lower()
    assert "does **not** change this contract’s **BLOCKED** status" in text or (
        "does **not** change this contract's **BLOCKED** status" in text
    )
    assert "READY_FOR_OPERATOR_ARMING" in section_five


def test_docs_truth_map_records_worksheet_and_test_v0() -> None:
    text = _read(DOCS_TRUTH_MAP)
    assert "Paper-Shadow-247 Future-Run Operator Decision Worksheet v0" in text
    assert CHARTER.name in text
    assert str(THIS_TEST) in text or THIS_TEST.name in text
    assert "PAPER_SHADOW_247_FUTURE_RUN_OPERATOR_DECISION_WORKSHEET_V0=true" in text


def test_worksheet_preserves_blocked_and_stop_idle_posture_v0() -> None:
    section = _worksheet_section()
    charter = _read(CHARTER)
    assert "PREFLIGHT_STATUS_REMAINS_BLOCKED=true" in section
    assert "STOP_IDLE_PRESERVED=true" in section
    assert "Current status: **BLOCKED**." in _read(PREFLIGHT)
    assert "STOP_IDLE" in charter
    assert "not_ready" in charter.lower()


def test_worksheet_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(CHARTER)
    worksheet_lower = _worksheet_section().lower()
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in worksheet_lower, f"forbidden claim in worksheet: {claim!r}"
    for negated in (
        "non-authorizing",
        "does not authorize",
        "blocked",
        "stop_idle",
        "review-only",
    ):
        assert negated in worksheet_lower, f"missing guardrail language: {negated!r}"
    assert "ready for operator arming" not in lowered or "not" in lowered


def test_worksheet_does_not_create_parallel_runbook_or_map_surface_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_FRAGMENTS:
        matches.extend(RUNBOOKS.glob(f"*{fragment}*"))
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate worksheet owner candidates: {matches}"
    for pattern in FORBIDDEN_COMPETING_GLOBS:
        competing = list(RUNBOOKS.glob(pattern))
        competing.extend(SPECS.glob(pattern))
        assert competing == [], f"competing worksheet surfaces: {competing}"
    charter_matches = [
        path for path in RUNBOOKS.glob("*SHADOW*247*GOVERNANCE*CHARTER*") if path != CHARTER
    ]
    assert charter_matches == [], f"unexpected charter duplicates: {charter_matches}"
