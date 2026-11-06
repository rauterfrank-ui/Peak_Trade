"""Static crosslink contract tests for Master V2 PRE_LIVE Navigation Read Model (v0).

Machine-anchors docs-only PRE_LIVE navigation governance from
MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md. Verifies
navigation/read-model-only posture without importing runtime modules or
authorizing trading — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

NAV_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md"
ROADMAP = SPECS / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
EXECUTION_SEQUENCE = SPECS / "MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md"
FUTURES_CLASS_A = SPECS / "MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
STRATEGY_INTEGRATION = SPECS / "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
GATE_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"

CONTEXT_READ_ORDER_STEPS: tuple[str, ...] = (
    "| C0 |",
    "| C0b |",
    "| C0c |",
    "| C0d |",
    "| C0e |",
    "| C0f |",
    "| C0f-producer |",
    "| C0g |",
    "| C0h |",
    "| C0i |",
    "| C0j |",
    "| C0k |",
    "| C0-Class-A |",
    "| C1 |",
    "| C1a |",
    "| C2 |",
    "| C3 |",
    "| C4 |",
)

PRE_LIVE_READ_ORDER_STEPS: tuple[str, ...] = tuple(f"| {index} |" for index in range(1, 27))

CLUSTER_MARKERS: tuple[str, ...] = (
    "A — Evidence & inputs",
    "B — Safety & exception intake",
    "C — Candidate & verdict inputs",
    "D — Readiness review chain",
    "E — Exception resolution",
    "F — Signoff & package",
)

SECTION_4_CROSSLINK_FILENAMES: tuple[str, ...] = (
    "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md",
    "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md",
    "MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md",
    "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V1",
    "CANONICAL_PRE_LIVE_NAV",
    "PRE_LIVE_NAVIGATION_READ_MODEL_V1",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live is authorized",
    "testnet is approved",
    "signoff is complete",
    "gate is passed",
    "blocker is cleared",
    "operator approval can be bypassed",
    "broker execution is approved",
    "exchange execution is approved",
    "runtime is wired",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "navigation grants authority",
    "this read model authorizes live",
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


def _pre_live_contract_paths() -> tuple[Path, ...]:
    return tuple(sorted(SPECS.glob("MASTER_V2_FIRST_LIVE_PRE_LIVE_*_CONTRACT_V1.md")))


def test_pre_live_navigation_read_model_exists_with_token_and_non_authorizing_posture_v0() -> None:
    assert NAV_MODEL.is_file()
    text = _read(NAV_MODEL)
    lowered = _lower(NAV_MODEL)
    assert "# Master V2 First Live PRE_LIVE Navigation Read Model v0" in text
    assert 'docs_token: "DOCS_TOKEN_MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0"' in text
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "navigation and read-order read model" in lowered
    assert "index only" in lowered
    assert "does not assert completeness of a live program" in lowered


def test_pre_live_navigation_non_authority_boundary_rejects_approval_surfaces_v0() -> None:
    section = _plain(NAV_MODEL).split("## 3) Non-authority boundary", 1)[1].split("## 4)", 1)[0]
    lowered = section.lower()
    assert "fail-closed by default" in lowered
    assert "authorize live, testnet, paper, or shadow trading" in lowered
    assert "authorize double play selection" in lowered
    assert "constitute evidence, a signoff, a gate closure, or an operator go" in lowered
    assert "gate approval" not in lowered
    assert "signoff complete" not in lowered


def test_pre_live_navigation_read_order_tables_preserve_navigation_only_structure_v0() -> None:
    section = (
        _plain(NAV_MODEL)
        .split("## 4) Suggested read order table", 1)[1]
        .split("## 5) PRE_LIVE cluster map", 1)[0]
    )
    lowered = section.lower()
    assert "reading aid, not a mandate" in lowered
    assert "what it does not authorize" in lowered
    for step in CONTEXT_READ_ORDER_STEPS:
        assert step in section, f"missing context read-order step: {step!r}"
    for step in PRE_LIVE_READ_ORDER_STEPS:
        assert step in section, f"missing pre_live read-order step: {step!r}"
    assert "order-oriented" in lowered
    assert "approval sequence" not in lowered


def test_pre_live_navigation_cluster_map_preserves_thematic_clusters_only_v0() -> None:
    section = _plain(NAV_MODEL).split("## 5) PRE_LIVE cluster map", 1)[1].split("## 6)", 1)[0]
    lowered = section.lower()
    assert "thematic" in lowered and "navigation" in lowered
    for marker in CLUSTER_MARKERS:
        assert marker in section, f"missing cluster marker: {marker!r}"
    assert "not a workflow engine" in lowered
    assert "grants authority" not in lowered


def test_pre_live_navigation_evidence_signoff_gate_boundary_remains_non_authorizing_v0() -> None:
    section = (
        _plain(NAV_MODEL)
        .split("## 7) Evidence / Signoff / Gate boundary", 1)[1]
        .split("## 8)", 1)[0]
    )
    lowered = section.lower()
    assert "not by this index" in lowered
    assert "not by having read this file" in lowered
    assert "gates are not opened by navigation order" in lowered
    assert "create evidence" not in lowered
    assert "gate pass" not in lowered


def test_pre_live_navigation_explicit_non_scope_rejects_runtime_and_evidence_creation_v0() -> None:
    section = _plain(NAV_MODEL).split("## 9) Explicit non-scope", 1)[1].split("## 10)", 1)[0]
    lowered = section.lower()
    assert "change src/" in lowered
    assert "create evidence, out/ artifacts, or signoff records" in lowered
    assert "change master v2 or double play trading logic" in lowered
    assert "dashboard authority" not in lowered


def test_pre_live_navigation_crosslinks_exist_and_referenced_targets_present_v0() -> None:
    text = _read(NAV_MODEL)
    for filename in SECTION_4_CROSSLINK_FILENAMES:
        assert filename in text, f"missing crosslink to {filename!r}"

    for path in (
        STRATEGY_INTEGRATION,
        PURE_STACK_MAP,
        FUTURES_CLASS_A,
        LADDER,
        GATE_INDEX,
    ):
        assert path.is_file(), path

    pre_live_contracts = _pre_live_contract_paths()
    assert len(pre_live_contracts) == 26
    for path in pre_live_contracts:
        assert path.name in text, f"missing PRE_LIVE contract crosslink: {path.name!r}"
        assert path.is_file(), path


def test_pre_live_navigation_peer_owners_reference_navigation_where_expected_v0() -> None:
    """Ladder and Gate Index explicitly peer-link the navigation read model."""
    ladder = _read(LADDER)
    gate_index = _read(GATE_INDEX)
    pure_stack = _read(PURE_STACK_MAP)
    assert NAV_MODEL.name in ladder
    assert NAV_MODEL.name in gate_index
    assert NAV_MODEL.name in pure_stack
    assert "navigation/reading map only" in ladder.lower()
    assert "navigation and read-order read model only" in gate_index.lower()


def test_pre_live_navigation_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(NAV_MODEL)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"

    for negated in (
        "non-authorizing",
        "not a gate schedule",
        "approval, signoff, or evidence",
        "gates are not opened by navigation order",
    ):
        assert negated in lowered


def test_pre_live_navigation_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    navigation_matches = list(SPECS.glob("*PRE_LIVE_NAVIGATION_READ_MODEL*"))
    assert navigation_matches == [NAV_MODEL], (
        f"unexpected PRE_LIVE navigation owner set: {navigation_matches}"
    )

    assert ROADMAP.is_file()
    assert EXECUTION_SEQUENCE.is_file()
