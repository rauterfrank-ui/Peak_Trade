"""Static crosslink contract tests for Strategy to Master V2 Integration (v0).

Machine-anchors docs-only strategy governance from
STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md. Verifies strategy integration
remains subordinate to Master V2 governance without importing runtime strategy
modules or authorizing execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

CONTRACT = SPECS / "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md"
DECISION_AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
COCKPIT_NON_AUTHORITY = SPECS / "OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md"
TIERING_DUAL_SOURCE = SPECS / "STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md"
DOUBLE_PLAY_RUNBOOK = RUNBOOKS / "double_play.md"

CONTRACT_SECTION_3_CROSSLINKS: tuple[str, ...] = (
    "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
    "OPS_COCKPIT_MASTER_V2_NON_AUTHORITY_CONTRACT_V1.md",
    "double_play.md",
)

RELATED_STRATEGY_GOVERNANCE_OWNERS: tuple[Path, ...] = (
    DECISION_AUTHORITY_MAP,
    COCKPIT_NON_AUTHORITY,
    TIERING_DUAL_SOURCE,
    DOUBLE_PLAY_RUNBOOK,
)

CORE_RULE_FORBIDDEN_GRANTS: tuple[str, ...] = (
    "live trading authority",
    "broker or exchange order authority",
    "testnet execution authority",
    "promotion authority",
    "gate authority",
    "Master V2 readiness authority",
    "Double Play decision authority",
)

REGISTRY_METADATA_ROWS: tuple[str, ...] = (
    "strategy_id",
    "tier",
    "is_live_ready",
    "allowed_environments",
)

CLASSIFICATION_LABELS: tuple[str, ...] = (
    "research-only",
    "candidate",
    "paper-observable",
    "shadow-observable",
    "testnet-blocked",
    "live-blocked",
    "double-play-observable",
    "double-play-candidate",
    "vetoed",
    "deprecated",
    "unknown",
)

ANTI_PATTERN_LITERALS: tuple[str, ...] = (
    '`tier="production"` implies live readiness',
    "`allowed_environments` including `live` implies order permission",
    "`is_live_ready` bypasses Master V2 readiness",
    "Double Play reads raw strategy metadata as final authority",
    "Strategy registry changes unlock execution paths",
    "Backtest success is treated as promotion",
    "Strategy profile output is treated as live approval",
)

NON_SCOPE_LITERALS: tuple[str, ...] = (
    "edit `src/strategies/registry.py`",
    "authorize execution",
    "promote any strategy",
    "alter Master V2",
    "alter Double Play",
    "alter gates",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V1",
    "CANONICAL_STRATEGY_LIVE_GATE",
    "STRATEGY_LIVE_AUTHORITY_MAP",
    "STRATEGY_LIVE_GATE_MAP",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "live is authorized",
    "approved for live trading",
    "strategy is ready for live",
    "registry grants execution",
    "strategy can bypass master v2",
    "strategy can bypass operator approval",
    "broker execution is approved",
    "exchange execution is approved",
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


def test_strategy_integration_contract_exists_with_token_and_docs_only_posture_v0() -> None:
    assert CONTRACT.is_file()
    text = _read(CONTRACT)
    lowered = text.lower()
    assert "# Strategy to Master V2 Integration Contract v0" in text
    assert "docs_token: DOCS_TOKEN_STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0" in text
    assert "scope: docs-only strategy governance contract" in text
    assert "docs-only governance contract" in text
    assert "does not change runtime behavior" in text
    assert "does not authorize execution" not in lowered
    assert "authorize execution" in lowered


def test_strategy_integration_core_rule_subordinates_strategies_to_master_v2_v0() -> None:
    section = _read(CONTRACT).split("## 2. Core rule", 1)[1].split("## 3.", 1)[0]
    lowered = section.lower()
    for grant in CORE_RULE_FORBIDDEN_GRANTS:
        assert grant in section, f"missing forbidden grant: {grant!r}"
    assert "must not independently grant" in lowered
    assert "master v2 remains the governance boundary" in lowered
    assert "readiness, gating, veto, promotion" in lowered


def test_strategy_integration_registry_metadata_table_is_informational_only_v0() -> None:
    text = _read(CONTRACT)
    assert "## 4. Registry metadata interpretation" in text
    section = text.split("## 4.", 1)[1].split("## 5.", 1)[0]
    assert "| Field / concept | Safe interpretation | Unsafe interpretation |" in section
    assert "catalog and compatibility metadata" in section
    for row in REGISTRY_METADATA_ROWS:
        assert row in section, f"missing registry metadata row: {row!r}"
    assert "Authority to trade" in section
    assert "Standalone live enablement" in section
    assert "Broker/exchange order permission" in section


def test_strategy_integration_classification_semantics_remain_non_authorizing_v0() -> None:
    text = _read(CONTRACT)
    assert "## 5. Master V2 compatible strategy classification" in text
    section = text.split("## 5.", 1)[1].split("## 6.", 1)[0]
    assert "non-authorizing categories" in section
    for label in CLASSIFICATION_LABELS:
        assert f"`{label}`" in section, f"missing classification label: {label!r}"
    assert "Requires explicit Master V2 readiness contract" in section
    assert DECISION_AUTHORITY_MAP.name in _read(CONTRACT) or "Master V2" in section


def test_strategy_integration_double_play_rule_rejects_raw_registry_authority_v0() -> None:
    section = _read(CONTRACT).split("## 6. Strategy-to-Double-Play rule", 1)[1].split("## 7.", 1)[0]
    assert "must not consume raw strategy registry metadata as authority" in section.lower()
    assert "non-authority label" in section.lower()


def test_strategy_integration_anti_patterns_and_non_scope_guardrails_v0() -> None:
    text = _read(CONTRACT)
    anti = text.split("## 9. Dangerous anti-patterns", 1)[1].split("## 10.", 1)[0]
    non_scope = text.split("## 11. Non-scope", 1)[1].split("## 12.", 1)[0]
    for literal in ANTI_PATTERN_LITERALS:
        assert literal in anti, f"missing anti-pattern: {literal!r}"
    for literal in NON_SCOPE_LITERALS:
        assert literal in non_scope, f"missing non-scope literal: {literal!r}"
    assert "operator-review gates" in anti.lower() or "operator review" in anti.lower()


def test_strategy_integration_section_3_crosslinks_exist_and_targets_present_v0() -> None:
    text = _read(CONTRACT)
    for filename in CONTRACT_SECTION_3_CROSSLINKS:
        assert filename in text, f"missing §3 crosslink to {filename!r}"
    for path in RELATED_STRATEGY_GOVERNANCE_OWNERS:
        assert path.is_file(), path


def test_strategy_integration_related_tiering_owner_exists_without_parallel_authority_spec_v0() -> (
    None
):
    """Tiering dual-source is ecosystem owner; integration contract §3 links DAM/cockpit/runbook."""
    assert TIERING_DUAL_SOURCE.is_file()
    tiering = _read(TIERING_DUAL_SOURCE)
    assert CONTRACT.name in tiering
    assert "non-authorizing" in tiering.lower() or "does not grant" in tiering.lower()


def test_strategy_integration_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(CONTRACT)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"
    for negated in (
        "must not independently grant",
        "does not perform or require those checks",
        "this contract does not:",
        "authorize execution",
        "promote any strategy",
    ):
        assert negated in lowered


def test_strategy_integration_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    integration_matches = list(SPECS.glob("*STRATEGY_TO_MASTER_V2_INTEGRATION*"))
    assert integration_matches == [CONTRACT], (
        f"unexpected strategy integration owner set: {integration_matches}"
    )
