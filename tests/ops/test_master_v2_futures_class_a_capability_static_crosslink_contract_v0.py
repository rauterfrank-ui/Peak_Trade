"""Static crosslink contract tests for Master V2 Futures Class A Capability (v0).

Machine-anchors docs-only Futures Class A capability governance from
MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md. Verifies HOLD / non-authorizing
posture without importing execution runtime modules or authorizing trading — static
file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

CONTRACT = SPECS / "MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md"
ROADMAP = SPECS / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
EXECUTION_SEQUENCE = SPECS / "MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md"
PRE_LIVE_NAV = SPECS / "MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md"
FUTURES_INSTRUMENT_METADATA = SPECS / "FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md"
FUTURES_MARKET_DATA_PROVENANCE = SPECS / "FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md"
FUTURES_CAPABILITY_SPEC = SPECS / "FUTURES_CAPABILITY_SPEC_V0.md"
FUTURES_INPUT_READ_MODEL = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md"
FUTURES_INPUT_PRODUCER = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"

CONTRACT_SECTION_9_CROSSLINKS: tuple[str, ...] = (
    "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md",
    "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md",
    "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md",
    "FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md",
    "FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md",
    "FUTURES_CAPABILITY_SPEC_V0.md",
    "MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md",
)

CAPABILITY_TABLE_MARKERS: tuple[str, ...] = (
    "SPOT_ONLY",
    "RUNTIME_NOT_WIRED",
    "PURE_DTO_READY",
    "SPOT_SIM_ONLY",
    "SPOT_PUBLIC_ONLY",
)

GAP_MAP_NUMBERED_ITEMS: tuple[str, ...] = tuple(f"{index}." for index in range(1, 11))

NON_CLAIMS_LITERALS: tuple[str, ...] = (
    "futures or perp / swap readiness",
    "testnet or live readiness",
    "pure dto ready",
    "trading authority",
)

WP1B_HOLD_LITERALS: tuple[str, ...] = (
    "no paperexecutionengine wiring on main",
    "no testnet or live permission",
    "no futures class a readiness from documentation or pure tests alone",
    "not wired to futures accounting v0 today",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "MASTER_V2_FUTURES_CLASS_A_CAPABILITY_V1",
    "CANONICAL_FUTURES_CLASS_A",
    "FUTURES_CLASS_A_READINESS",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "futures are ready",
    "perps are ready",
    "testnet is approved",
    "live is authorized",
    "runtime is wired",
    "broker execution is approved",
    "exchange execution is approved",
    "spot class-a proves perp readiness",
    "operator approval can be bypassed",
    "ai can authorize trades",
    "autonomy can authorize trades",
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


def test_futures_class_a_capability_exists_with_token_and_non_authorizing_posture_v0() -> None:
    assert CONTRACT.is_file()
    text = _read(CONTRACT)
    plain = _plain(CONTRACT)
    lowered = plain.lower()
    assert "# Master V2 Futures Class A Capability Contract v0" in text
    assert 'docs_token: "DOCS_TOKEN_MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0"' in text
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "does not enable testnet or live" in lowered
    assert "does not call exchanges" in lowered


def test_futures_class_a_capability_table_preserves_hold_posture_markers_v0() -> None:
    section = (
        _plain(CONTRACT).split("## 3. Capability classification table", 1)[1].split("## 4.", 1)[0]
    )
    lowered = section.lower()
    assert "| Layer | Classification |" in section
    for marker in CAPABILITY_TABLE_MARKERS:
        assert marker in section, f"missing capability marker: {marker!r}"
    assert "pure dto ready" in lowered
    assert "runtime not wired" in lowered
    assert "execution approval" not in lowered


def test_futures_class_a_gap_map_lists_ten_open_prerequisites_v0() -> None:
    section = _plain(CONTRACT).split("## 4. Futures Class A gap map", 1)[1].split("## 5.", 1)[0]
    lowered = section.lower()
    assert "top 10" in lowered
    assert "prerequisites remain open" in lowered
    for item in GAP_MAP_NUMBERED_ITEMS:
        assert item in section, f"missing gap map item {item!r}"
    assert "order is not a priority ranking" in lowered


def test_futures_class_a_non_claims_reject_spot_and_dto_misinterpretation_v0() -> None:
    section = (
        _plain(CONTRACT)
        .split("## 5. Non-claims / prohibited interpretations", 1)[1]
        .split("## 6.", 1)[0]
    )
    lowered = section.lower()
    assert "futures or perp / swap readiness" in lowered
    assert "testnet or live readiness" in lowered
    assert "pure dto ready" in lowered and "runtime not wired" in lowered
    assert "btc/eur class a" in lowered
    assert "must not treat" in lowered


def test_futures_class_a_wp1b_hold_posture_remains_unwired_on_main_v0() -> None:
    plain = _plain(CONTRACT)
    hold_section = plain.split("### 7.5 Explicit non-claims", 1)[1].split("## 8.", 1)[0]
    wiring_section = plain.split("### 7.4 Preconditions before any wiring", 1)[1].split(
        "### 7.5", 1
    )[0]
    assert "SPOT_SIM_ONLY" in plain
    assert "not wired to the class a runner or wp1b hot path" in plain.lower()
    assert "no live/testnet approval" in wiring_section.lower()
    assert "no paperexecutionengine wiring on main" in hold_section.lower()
    assert "no testnet or live permission" in hold_section.lower()
    assert (
        "no futures class a readiness from documentation or pure tests alone"
        in hold_section.lower()
    )
    assert "not wired to futures accounting v0 today" in plain.lower()


def test_futures_class_a_section_9_crosslinks_exist_and_targets_present_v0() -> None:
    text = _read(CONTRACT)
    for filename in CONTRACT_SECTION_9_CROSSLINKS:
        assert filename in text, f"missing §9 crosslink to {filename!r}"

    for path in (
        FUTURES_INPUT_READ_MODEL,
        FUTURES_INPUT_PRODUCER,
        PURE_STACK_MAP,
        FUTURES_INSTRUMENT_METADATA,
        FUTURES_MARKET_DATA_PROVENANCE,
        FUTURES_CAPABILITY_SPEC,
        PRE_LIVE_NAV,
    ):
        assert path.is_file(), path


def test_futures_class_a_related_first_live_owners_reference_capability_contract_v0() -> None:
    """Roadmap and execution sequence are ecosystem peers; capability §9 links PRE_LIVE nav."""
    roadmap = _read(ROADMAP)
    pre_live = _read(PRE_LIVE_NAV)
    assert CONTRACT.name in roadmap
    assert CONTRACT.name in pre_live
    assert ROADMAP.is_file()
    assert EXECUTION_SEQUENCE.is_file()


def test_futures_class_a_peer_specs_do_not_claim_execution_authority_v0() -> None:
    for path in (
        FUTURES_INSTRUMENT_METADATA,
        FUTURES_MARKET_DATA_PROVENANCE,
        FUTURES_CAPABILITY_SPEC,
    ):
        text = _lower(path)
        assert "docs-only" in text
        assert "does not permit" in text or "does not grant" in text


def test_futures_class_a_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(CONTRACT)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"

    for negated in (
        "does not enable testnet or live",
        "non-authorizing",
        "runtime not wired",
        "does not close",
        "not evidence of completion",
    ):
        assert negated in lowered


def test_futures_class_a_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    capability_matches = list(SPECS.glob("*FUTURES_CLASS_A_CAPABILITY*"))
    assert capability_matches == [CONTRACT], (
        f"unexpected futures class-a capability owner set: {capability_matches}"
    )
