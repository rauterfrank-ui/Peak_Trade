"""Static readiness-peer crosslink contract tests for Paper/Shadow 247 Preflight (v0).

Machine-anchors BLOCKED preflight governance from
PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md. Verifies readiness ledger, gate
snapshot, primary evidence retention, taxonomy, charter, and blocker-register
peer discipline without importing runtime modules or authorizing trading —
static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
SCRIPTS = REPO_ROOT / "scripts" / "ops"

PREFLIGHT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
CHARTER = RUNBOOKS / "SHADOW_247_GOVERNANCE_CHARTER_V0.md"
TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
GAP_MAP = SPECS / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md"
BOUNDED_PILOT_CROSSWALK = SPECS / "MASTER_V2_BOUNDED_PILOT_L1_L5_POINTER_RUNBOOK_CROSSWALK_V0.md"

PEER_SCRIPTS: tuple[tuple[str, Path], ...] = (
    ("preflight_status", SCRIPTS / "report_paper_shadow_247_preflight_status.py"),
    ("readiness_ledger", SCRIPTS / "build_readiness_evidence_ledger_v0.py"),
    ("gate_snapshot", SCRIPTS / "report_readiness_gate_snapshot_v0.py"),
    ("ledger_preflight_mirror", SCRIPTS / "report_readiness_ledger_preflight_mirror_v0.py"),
    ("primary_evidence_retention", SCRIPTS / "primary_evidence_retention_v0.py"),
)

HARD_GATE_MACHINE_LINES: tuple[str, ...] = (
    "RUN_PRIMARY_EVIDENCE_RETENTION_HARD_GATE_V0=true",
    "FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true",
    "TMP_ONLY_EVIDENCE_INVALID=true",
    "MANIFEST_VERIFY_REQUIRED=true",
    "CLOSEOUT_REFERENCE_REQUIRED=true",
    "RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
)

BLOCKED_STATUS_MARKERS: tuple[str, ...] = (
    "PRE_FLIGHT_BLOCKED_LIFTED=false",
    "READY_FOR_START=false",
    "PREFLIGHT_MAY_REMAIN_BLOCKED_AFTER_RUN=true",
)

FORBIDDEN_DUPLICATE_FRAGMENTS: tuple[str, ...] = (
    "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V1",
    "CANONICAL_PAPER_SHADOW_PREFLIGHT",
    "247_PREFLIGHT_CONTRACT_V1",
)

FORBIDDEN_COMPETING_GLOBS: tuple[str, ...] = (
    "*PAPER_SHADOW*PREFLIGHT*V1*",
    "*247_PREFLIGHT*CONTRACT*V1*",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "daemon is authorized",
    "runtime is authorized",
    "paper run is approved",
    "shadow run is approved",
    "testnet is approved",
    "live is authorized",
    "broker execution is approved",
    "exchange execution is approved",
    "gate is passed",
    "blocker is cleared",
    "signoff is complete",
    "operator approval can be bypassed",
    "evidence authorizes runtime",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "preflight grants authority",
    "this contract authorizes live",
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


def test_paper_shadow_247_preflight_exists_blocked_and_non_authorizing_v0() -> None:
    assert PREFLIGHT.is_file()
    text = _read(PREFLIGHT)
    lowered = _lower(PREFLIGHT)
    assert "# Paper/Shadow 24/7 Preflight Contract v0" in text
    assert "Current status: **BLOCKED**." in text
    assert "does **not** authorize activation" in text
    assert "does **not** start a daemon" in text
    assert "non-authorizing" in lowered
    assert "must not be interpreted as daemon activation" in lowered
    assert "stop — do not activate paper/shadow 24/7" in lowered


def test_paper_shadow_247_preflight_section_2a1_hard_gate_machine_lines_fail_closed_v0() -> None:
    section = (
        _plain(PREFLIGHT)
        .split("## 2a.1 Future-run primary evidence hard gate v0", 1)[1]
        .split("**Scoped preflight exception (U3 pattern) v0:**", 1)[0]
    )
    lowered = section.lower()
    for marker in HARD_GATE_MACHINE_LINES:
        assert marker in section, f"missing hard-gate machine line: {marker!r}"
    assert "evidence ≠ approval" in lowered or "evidence = approval" not in lowered
    assert "fail closed" in lowered or "fail-closed" in lowered
    assert "does not clear preflight blocked" in lowered
    for marker in BLOCKED_STATUS_MARKERS:
        assert marker in _read(PREFLIGHT), f"missing blocked-status marker: {marker!r}"


def test_paper_shadow_247_preflight_readiness_ledger_gate_snapshot_review_input_only_v0() -> None:
    text = _read(PREFLIGHT)
    lowered = _lower(PREFLIGHT)
    assert "Readiness ledger and gate snapshot (review-input-only)" in text
    assert "build_readiness_evidence_ledger_v0.py" in text
    assert "report_readiness_gate_snapshot_v0.py" in text
    assert "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE" in text
    assert "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE" in text
    assert "completeness and consistency signals only" in lowered
    assert "do not clear preflight blocked" in lowered
    assert "do not authorize runtime" in lowered
    assert "glb-014" in lowered
    assert "glb-015" in lowered


def test_paper_shadow_247_preflight_declared_peer_scripts_exist_v0() -> None:
    text = _read(PREFLIGHT)
    for label, path in PEER_SCRIPTS:
        assert path.is_file(), f"missing peer script: {label!r} -> {path}"
    assert "report_paper_shadow_247_preflight_status.py" in text
    assert "primary_evidence_retention_v0.py" in text


def test_paper_shadow_247_preflight_taxonomy_charter_blocker_peer_linkage_v0() -> None:
    text = _read(PREFLIGHT)
    lowered = _lower(PREFLIGHT)
    assert TAXONOMY.name in text
    assert CHARTER.name in text
    assert BLOCKER_REGISTER.name in text
    assert TAXONOMY.is_file()
    assert CHARTER.is_file()
    assert BLOCKER_REGISTER.is_file()
    assert "glb-015" in lowered
    assert "§6.5" in text
    assert "non-authorizing" in lowered
    assert "governance-only" in lowered or "governance only" in lowered
    taxonomy = _read(TAXONOMY)
    assert PREFLIGHT.name in taxonomy
    assert "report_readiness_ledger_preflight_mirror_v0.py" in taxonomy


def test_paper_shadow_247_preflight_gap_map_and_crosswalk_peers_exist_v0() -> None:
    assert GAP_MAP.is_file()
    assert BOUNDED_PILOT_CROSSWALK.is_file()
    assert GAP_MAP.name not in _read(PREFLIGHT)
    assert BOUNDED_PILOT_CROSSWALK.name not in _read(PREFLIGHT)


def test_paper_shadow_247_preflight_primary_evidence_and_blocked_lift_semantics_v0() -> None:
    text = _plain(PREFLIGHT)
    lowered = text.lower()
    assert "primary_evidence_required_for_every_run=true" in lowered
    assert "primary evidence retention invariant" in lowered
    assert "forbidden as primary evidence" in lowered
    assert "/tmp-only" in lowered or "/tmp" in lowered
    assert "not complete" in lowered
    assert "blocked" in lowered
    assert "pre_flight_blocked_lifted=false" in lowered


def test_paper_shadow_247_preflight_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(PREFLIGHT)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"
    for negated in (
        "blocked",
        "non-authorizing",
        "does not authorize",
        "evidence ≠ approval",
        "not trading authority",
    ):
        assert negated in lowered


def test_paper_shadow_247_preflight_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_FRAGMENTS:
        matches.extend(RUNBOOKS.glob(f"*{fragment}*"))
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    for pattern in FORBIDDEN_COMPETING_GLOBS:
        competing = [path for path in RUNBOOKS.glob(pattern) if path != PREFLIGHT]
        competing.extend(path for path in SPECS.glob(pattern))
        assert competing == [], f"competing preflight owner candidates: {competing}"

    preflight_matches = list(RUNBOOKS.glob("*PAPER_SHADOW*247*PREFLIGHT*CONTRACT*"))
    assert preflight_matches == [PREFLIGHT], (
        f"unexpected paper/shadow 247 preflight owner set: {preflight_matches}"
    )
