"""Static crosslink contract tests for Master V2 Paper/Testnet Readiness Gap Map (v0).

Machine-anchors docs-only Paper/Testnet readiness gap-map governance from
MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md. Verifies review/readiness
discipline and peer crosslinks without importing runtime modules or authorizing
trading — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"
SCRIPTS = REPO_ROOT / "scripts" / "ops"

GAP_MAP = SPECS / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md"
ROADMAP = SPECS / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
FLAT_PATH_INDEX = SPECS / "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md"
BOUNDED_PILOT_CROSSWALK = SPECS / "MASTER_V2_BOUNDED_PILOT_L1_L5_POINTER_RUNBOOK_CROSSWALK_V0.md"

PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PAPER_TESTNET_STATUS_SCRIPT = SCRIPTS / "report_paper_testnet_readiness_status.py"
PAPER_SHADOW_PREFLIGHT_SCRIPT = SCRIPTS / "report_paper_shadow_247_preflight_status.py"

SECTION_13_RUNBOOKS: tuple[tuple[str, Path], ...] = (
    ("TESTNET_CHECKER", RUNBOOKS / "TESTNET_CHECKER_PREREQUISITES_V0.md"),
    (
        "DAEMON_PAPER_OBSERVATION_GATE",
        RUNBOOKS / "DAEMON_PAPER_24H_PLUS_OBSERVATION_GATE_BEFORE_TESTNET_V0.md",
    ),
    (
        "DAEMON_PAPER_SCOPE_PREFLIGHT",
        RUNBOOKS / "DAEMON_PAPER_24H_PLUS_OPERATOR_SCOPE_PREFLIGHT_V0.md",
    ),
)

GAP_TABLE_ROWS: tuple[str, ...] = (
    "No single Paper/Testnet open-first surface",
    "Source binding intentionally absent",
    "Artifact manifest linkage not selected",
    "Dashboard/cockpit authority risk",
    "Paper/test data protection",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "PAPER_TESTNET_READINESS_GAP_MAP_V1",
    "CANONICAL_READINESS_GAP",
    "MASTER_V2_PAPER_TESTNET_READINESS_V1",
)

FORBIDDEN_COMPETING_GLOBS: tuple[str, ...] = (
    "*PAPER*TESTNET*GAP_MAP*V1*",
    "*CANONICAL*READINESS*GAP*",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "testnet is approved",
    "paper run is approved",
    "shadow run is approved",
    "live is authorized",
    "signoff is complete",
    "gate is passed",
    "blocker is cleared",
    "operator approval can be bypassed",
    "broker execution is approved",
    "exchange execution is approved",
    "runtime is wired",
    "evidence is complete",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "gap map grants authority",
    "this map authorizes live",
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


def test_paper_testnet_gap_map_exists_with_token_and_non_authorizing_posture_v0() -> None:
    assert GAP_MAP.is_file()
    text = _read(GAP_MAP)
    lowered = _lower(GAP_MAP)
    assert "# Master V2 Paper / Testnet Readiness Gap Map V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0" in text
    assert "scope: docs-only" in text
    assert "non-authorizing" in text
    assert "docs-only" in lowered
    assert "read-only" in lowered
    assert "gap map" in lowered
    assert "not live authorization" in lowered
    assert "does not modify" in lowered and "paper" in lowered and "test" in lowered


def test_paper_testnet_gap_map_visible_gaps_remain_blockers_not_approvals_v0() -> None:
    section = (
        _plain(GAP_MAP)
        .split("## 10. Visible Gaps from Repo-Only Review", 1)[1]
        .split("## 11. Authority Boundaries", 1)[0]
    )
    lowered = section.lower()
    assert "repo-visible gaps" in lowered
    assert "without reading real paper/test data" in lowered
    assert "safe next posture" in lowered
    assert "approval" not in lowered
    assert "authorized" not in lowered
    for row in GAP_TABLE_ROWS:
        assert row in section, f"missing gap table row: {row!r}"


def test_paper_testnet_gap_map_authority_boundaries_reject_runtime_and_signoff_v0() -> None:
    section = (
        _plain(GAP_MAP)
        .split("## 11. Authority Boundaries", 1)[1]
        .split("## 12. Safe Follow-Up Candidates", 1)[0]
    )
    lowered = section.lower()
    assert "| Surface | May (informational) | Must not (by this map)" in section
    assert "authorize live trading" in lowered
    assert "complete signoff by itself" in lowered
    assert "place or authorize orders" in lowered
    assert "bypass gates" in lowered
    assert "pass gates by itself" in lowered
    assert "mutate runtime authority" in lowered
    assert "create evidence" not in lowered
    assert "gate passed" not in lowered


def test_paper_testnet_gap_map_risk_section_preserves_fail_closed_separation_v0() -> None:
    section = (
        _plain(GAP_MAP)
        .split("## 7. Risk / KillSwitch / Execution Gate Relevance", 1)[1]
        .split("## 8. Evidence / Registry / Session Review Pack Relevance", 1)[0]
    )
    lowered = section.lower()
    assert "must not override" in lowered
    assert "fail-closed" in lowered
    assert "separation" in lowered and "readiness" in lowered and "authorization" in lowered
    assert "does not assert behavior" in lowered


def test_paper_testnet_gap_map_safe_followups_remain_tests_and_planning_only_v0() -> None:
    section = (
        _plain(GAP_MAP)
        .split("## 12. Safe Follow-Up Candidates", 1)[1]
        .split("## 13. Related pre-Testnet operator runbooks", 1)[0]
    )
    lowered = section.lower()
    assert "tests-only" in lowered
    assert "docs-only" in lowered
    assert "read-only" in lowered
    assert "synthetic fixtures" in lowered
    assert "open-first runbook" in lowered and "only if" in lowered
    assert "avoid" in lowered and "premature" in lowered
    assert "live enablement" in lowered
    assert "runtime start" not in lowered


def test_paper_testnet_gap_map_section_13_runbook_links_exist_and_are_non_authorizing_v0() -> None:
    section = _read(GAP_MAP).split("## 13. Related pre-Testnet operator runbooks", 1)[1]
    section_plain = (
        _plain(GAP_MAP)
        .split("## 13. Related pre-Testnet operator runbooks", 1)[1]
        .split("## 14.", 1)[0]
    )
    lowered = section_plain.lower()
    assert "discoverability" in lowered
    assert "do not approve" in lowered
    assert "do not imply" in lowered and "gate passage" in lowered
    assert "no start commands" in lowered or "planning gate" in lowered
    for label, path in SECTION_13_RUNBOOKS:
        assert path.name in section, f"missing §13 runbook link: {label!r}"
        assert path.is_file(), path


def test_paper_testnet_gap_map_peer_script_and_preflight_owners_exist_v0() -> None:
    for path in (
        PAPER_TESTNET_STATUS_SCRIPT,
        PAPER_SHADOW_PREFLIGHT_SCRIPT,
        PREFLIGHT_CONTRACT,
    ):
        assert path.is_file(), path
    preflight_text = _read(PREFLIGHT_CONTRACT)
    assert "BLOCKED" in preflight_text
    assert "non-authorizing" in preflight_text.lower() or "not" in preflight_text.lower()


def test_paper_testnet_gap_map_reciprocal_peer_crosslinks_from_roadmap_and_flat_path_v0() -> None:
    roadmap = _read(ROADMAP)
    flat_path = _read(FLAT_PATH_INDEX)
    assert GAP_MAP.name in roadmap
    assert "Paper / Testnet Readiness Gap Map" in roadmap
    assert GAP_MAP.name in flat_path
    flat_lower = _lower(FLAT_PATH_INDEX)
    assert "paper/testnet" in flat_lower or "paper" in flat_lower
    assert "characterization" in flat_lower
    assert "not live readiness" in flat_lower


def test_paper_testnet_gap_map_bounded_pilot_crosswalk_peer_exists_v0() -> None:
    assert BOUNDED_PILOT_CROSSWALK.is_file()
    gap_lower = _lower(GAP_MAP)
    assert "bounded pilot" in gap_lower
    assert BOUNDED_PILOT_CROSSWALK.name not in _read(GAP_MAP)


def test_paper_testnet_gap_map_inventory_tables_reference_report_surfaces_v0() -> None:
    text = _plain(GAP_MAP)
    lowered = text.lower()
    assert "scripts/report_live_sessions.py" in text
    assert "bounded pilot" in lowered
    assert "testnet" in lowered
    assert "shadow" in lowered
    assert "not used for" in lowered
    assert "not live authorization" in lowered


def test_paper_testnet_gap_map_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(GAP_MAP)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"
    for negated in (
        "non-authorizing",
        "not live authorization",
        "not live enablement",
        "not imply",
        "gate passage",
    ):
        assert negated in lowered


def test_paper_testnet_gap_map_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    for pattern in FORBIDDEN_COMPETING_GLOBS:
        competing = [path for path in SPECS.glob(pattern) if path != GAP_MAP]
        assert competing == [], f"competing paper/testnet gap map owners: {competing}"

    gap_map_matches = list(SPECS.glob("*PAPER*TESTNET*READINESS*GAP_MAP*"))
    assert gap_map_matches == [GAP_MAP], f"unexpected gap map owner set: {gap_map_matches}"
