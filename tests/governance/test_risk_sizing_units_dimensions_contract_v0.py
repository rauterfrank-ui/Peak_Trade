"""Static contract: Risk/Sizing units/dimensions declaration v0.

Docs/config/tests-only. Does not authorize live, orders, runtime bridge,
consolidation, authority assignment, or risk/sizing semantic changes.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_units_dimensions_contract_v0.json"
)
CONTRACT_DOC = REPO_ROOT / "docs" / "governance" / "RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md"
OWNER_INVENTORY_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
)
LEGACY_ORDER_INTENT_JSON = (
    REPO_ROOT / "config" / "governance" / "legacy_order_intent_inventory_ssot_v1.json"
)

EXPECTED_PRIMARY_OWNER_COUNT = 5
EXPECTED_COMPANION_EDGE_COUNT = 2
EXPECTED_PRIMARY_OWNER_IDS = (
    "backtest.offline_evaluation_sizing_contract_v1",
    "src.core.position_sizing",
    "src.execution.pipeline.execute_from_signals",
    "src.governance.capital_risk_sizing_v1",
    "src.risk.position_sizer",
)
EXPECTED_CALLABLE_IDS = (
    "core.FixedFractionSizer",
    "core.FixedSizeSizer",
    "core.NoopPositionSizer",
    "core.build_position_sizer_from_config",
    "crs.evaluate_capital_risk_sizing_v1",
    "crs.evaluate_quantity_chain_v1",
    "execution.execute_from_signals",
    "offline.size_offline_evaluation_entry_v1",
    "risk.PositionSizer",
    "risk.calc_position_size",
)
EXPECTED_COMPANION_EDGE_IDS = (
    "COMPANION_LIVE_SESSION_POSITION_FRACTION",
    "COMPANION_SHADOW_POSITION_FRACTION",
)
EXPECTED_DIMENSION_CATALOG = (
    "ACCOUNT_EQUITY_CCY",
    "AVAILABLE_CAPITAL_CCY",
    "RISK_BUDGET_CCY",
    "MAX_NOTIONAL_CCY",
    "POSITION_NOTIONAL_CCY",
    "PRICE_CCY_PER_UNIT",
    "STOP_DISTANCE_CCY_PER_UNIT",
    "STOP_DISTANCE_FRACTION",
    "QUANTITY_BASE_UNITS",
    "SIGNED_QUANTITY_BASE_UNITS",
    "SIGNAL_DIMENSIONLESS_SIGNED",
    "FRACTION_DECIMAL_0_1",
    "PERCENT_0_100",
    "LEVERAGE_MULTIPLIER",
    "LOT_SIZE_BASE_UNITS",
    "POSITION_COUNT_INTEGER",
    "BOOLEAN_GATE",
    "ENUM_POLICY",
    "UNKNOWN_OR_AMBIGUOUS",
)

REQUIRED_CALLABLE_FIELDS = (
    "callable_id",
    "owner_id",
    "source_path",
    "symbol",
    "symbol_kind",
    "domain",
    "inputs",
    "outputs",
    "signedness",
    "numeric_representation",
    "percent_convention",
    "rounding_behavior",
    "ambiguity_notes",
    "runtime_scope",
    "authority_effect",
    "runtime_effect",
)

REQUIRED_DOC_MARKERS = (
    "RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0=true",
    "INVENTORY_ONLY=true",
    "UNITS_DIMENSIONS_DECLARATION_ONLY=true",
    "NO_SIZING_MATH_CHANGE=true",
    "NO_AUTHORITY_ASSIGNMENT=true",
    "CANONICAL_RISK_SIZING_OWNER=UNRESOLVED",
    "CANONICAL_EXECUTION_AUTHORITY_OWNER=UNRESOLVED",
    "AUTHORITY_EFFECT=NONE",
    "RUNTIME_EFFECT=NONE",
    "LIVE_AUTHORIZED=false",
    "ORDERS_ENABLED=false",
    "EXPECTED_PRIMARY_OWNER_COUNT=5",
    "EXPECTED_COMPANION_EDGE_COUNT=2",
)

EXPECTED_DIMENSION_PINS = {
    "crs.evaluate_capital_risk_sizing_v1": {
        "final_quantity": "QUANTITY_BASE_UNITS",
        "leverage_ceiling": "LEVERAGE_MULTIPLIER",
        "account_equity": "ACCOUNT_EQUITY_CCY",
        "per_trade_risk_limit": "RISK_BUDGET_CCY",
    },
    "crs.evaluate_quantity_chain_v1": {
        "final_quantity": "QUANTITY_BASE_UNITS",
        "leverage_ceiling": "LEVERAGE_MULTIPLIER",
        "stop_or_risk_distance": "STOP_DISTANCE_CCY_PER_UNIT",
    },
    "risk.PositionSizer": {
        "risk_pct_config": "PERCENT_0_100",
        "max_position_pct_config": "PERCENT_0_100",
        "size_units": "QUANTITY_BASE_UNITS",
    },
    "risk.calc_position_size": {
        "risk_per_trade": "FRACTION_DECIMAL_0_1",
        "max_position_pct": "FRACTION_DECIMAL_0_1",
        "size": "QUANTITY_BASE_UNITS",
    },
    "core.FixedFractionSizer": {
        "fraction": "FRACTION_DECIMAL_0_1",
        "target_position": "SIGNED_QUANTITY_BASE_UNITS",
        "signal": "SIGNAL_DIMENSIONLESS_SIGNED",
    },
    "core.FixedSizeSizer": {
        "units": "QUANTITY_BASE_UNITS",
        "target_position": "SIGNED_QUANTITY_BASE_UNITS",
    },
    "core.NoopPositionSizer": {
        "signal": "SIGNAL_DIMENSIONLESS_SIGNED",
        "target_position": "SIGNED_QUANTITY_BASE_UNITS",
    },
    "offline.size_offline_evaluation_entry_v1": {
        "risk_per_trade": "FRACTION_DECIMAL_0_1",
        "max_position_pct": "FRACTION_DECIMAL_0_1",
        "size": "QUANTITY_BASE_UNITS",
    },
    "execution.execute_from_signals": {
        "max_position_notional_pct": "UNKNOWN_OR_AMBIGUOUS",
        "target_position": "SIGNED_QUANTITY_BASE_UNITS",
    },
}

EXPECTED_FIELD_PIN_DIMENSIONS = {
    "PositionSizerConfig.risk_pct": "PERCENT_0_100",
    "PositionSizerConfig.max_position_pct": "PERCENT_0_100",
    "calc_position_size.max_position_pct": "FRACTION_DECIMAL_0_1",
    "FixedFractionSizer.fraction": "FRACTION_DECIMAL_0_1",
    "CapitalRiskSizingContextV1.leverage_ceiling": "LEVERAGE_MULTIPLIER",
    "ExecutionPipelineConfig.max_position_notional_pct": "UNKNOWN_OR_AMBIGUOUS",
    "ShadowPaperConfig.position_fraction": "FRACTION_DECIMAL_0_1",
    "LiveSessionConfig.position_fraction": "FRACTION_DECIMAL_0_1",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_contract() -> dict:
    return json.loads(_read(CONTRACT_JSON))


def _ast_symbol_resolves(source_path: Path, symbol_or_callable: str) -> bool:
    """Resolve Class.method or bare function/class via AST — no module import."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    if "." in symbol_or_callable:
        class_name, method_name = symbol_or_callable.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if (
                        isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and item.name == method_name
                    ):
                        return True
        return False
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == symbol_or_callable
        ):
            return True
        if isinstance(node, ast.ClassDef) and node.name == symbol_or_callable:
            return True
    return False


def _ast_has_attribute_assignment_in_method(
    source_path: Path, *, class_method: str, attribute_name: str
) -> bool:
    """Prove Class.method reads/assigns using <something>.attribute_name via AST."""
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    class_name, method_name = class_method.split(".", 1)
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for item in node.body:
            if not (
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == method_name
            ):
                continue
            for sub in ast.walk(item):
                if isinstance(sub, ast.Attribute) and sub.attr == attribute_name:
                    return True
    return False


def _callable_by_id(payload: dict, callable_id: str) -> dict:
    for entry in payload["primary_callables"]:
        if entry["callable_id"] == callable_id:
            return entry
    raise AssertionError(f"missing callable_id: {callable_id}")


def test_contract_doc_markers_present() -> None:
    text = _read(CONTRACT_DOC)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, f"missing doc marker: {marker}"


def test_schema_and_catalog_guard() -> None:
    payload = _load_contract()
    catalog = payload["dimension_catalog_closed"]
    assert tuple(catalog) == EXPECTED_DIMENSION_CATALOG
    assert len(catalog) == len(set(catalog)), "duplicate dimension catalog tokens"

    allowed_numeric = set(payload["allowed_numeric_representations"])
    allowed_percent = set(payload["allowed_percent_conventions"])
    allowed_scopes = set(payload["allowed_runtime_scopes"])
    allowed_signedness = set(payload["allowed_signedness"])
    catalog_set = set(catalog)

    for entry in payload["primary_callables"]:
        for field in REQUIRED_CALLABLE_FIELDS:
            assert field in entry, f"{entry.get('callable_id')}: missing {field}"
        assert entry["inputs"], f"{entry['callable_id']}: empty inputs"
        assert entry["outputs"], f"{entry['callable_id']}: empty outputs"
        assert entry["numeric_representation"] in allowed_numeric
        assert entry["percent_convention"] in allowed_percent
        assert entry["runtime_scope"] in allowed_scopes
        assert entry["signedness"] in allowed_signedness
        assert entry["authority_effect"] == "NONE"
        assert entry["runtime_effect"] == "NONE"
        for dim in (*entry["inputs"].values(), *entry["outputs"].values()):
            assert dim in catalog_set, (
                f"unknown_dimension_token FAIL: {entry['callable_id']} -> {dim}"
            )
        if (
            "UNKNOWN_OR_AMBIGUOUS"
            in (
                *entry["inputs"].values(),
                *entry["outputs"].values(),
            )
            or entry["percent_convention"] == "MIXED_OR_AMBIGUOUS"
        ):
            assert str(entry["ambiguity_notes"]).strip(), (
                f"missing_ambiguity_notes_for_unknown FAIL: {entry['callable_id']}"
            )

    for edge in payload["companion_edges"]:
        assert edge["declared_dimension"] in catalog_set
        assert edge["runtime_usage_dimension"] in catalog_set
        assert edge["authority_effect"] == "NONE"
        assert edge["runtime_effect"] == "NONE"
        assert edge["primary_owner"] is False
        assert edge["bypass_surface_member"] is False
        assert str(edge["ambiguity_notes"]).strip()


def test_primary_owner_completeness_no_add_remove_rename_duplicate() -> None:
    payload = _load_contract()
    owner_ids = tuple(payload["primary_owner_ids_sorted"])
    assert len(owner_ids) == EXPECTED_PRIMARY_OWNER_COUNT
    assert owner_ids == EXPECTED_PRIMARY_OWNER_IDS
    assert len(owner_ids) == len(set(owner_ids)), "owner_duplicate FAIL"
    assert payload["markers"]["EXPECTED_PRIMARY_OWNER_COUNT"] == EXPECTED_PRIMARY_OWNER_COUNT

    callable_owners = {c["owner_id"] for c in payload["primary_callables"]}
    assert callable_owners == set(EXPECTED_PRIMARY_OWNER_IDS)

    # Drift policy pins
    drift = payload["drift_policy"]
    assert drift["primary_owner_addition"] == "FAIL"
    assert drift["primary_owner_removal"] == "FAIL"
    assert drift["primary_owner_rename"] == "FAIL"
    assert drift["primary_owner_duplicate"] == "FAIL"
    assert drift["unresolved_symbol"] == "FAIL"
    assert drift["authority_escalation"] == "FAIL"
    assert drift["companion_edge_addition"] == "FAIL"


def test_primary_callable_set_frozen() -> None:
    payload = _load_contract()
    ids = tuple(sorted(c["callable_id"] for c in payload["primary_callables"]))
    assert ids == EXPECTED_CALLABLE_IDS
    assert len(ids) == len(set(ids)), "callable duplicate FAIL"


def test_symbol_resolution_ast_fail_closed() -> None:
    payload = _load_contract()
    for entry in payload["primary_callables"]:
        path = REPO_ROOT / entry["source_path"]
        assert path.is_file(), f"missing source: {entry['source_path']}"
        assert _ast_symbol_resolves(path, entry["symbol"]), (
            f"unresolved_symbol FAIL: {entry['callable_id']} "
            f"{entry['source_path']}::{entry['symbol']}"
        )
        kind = entry["symbol_kind"]
        if kind == "method":
            assert "." in entry["symbol"]
        elif kind in {"function", "class"}:
            assert "." not in entry["symbol"]
        else:
            raise AssertionError(f"unknown symbol_kind: {kind}")

    for pin in payload["field_pins"]:
        path = REPO_ROOT / pin["source_path"]
        assert path.is_file()
        assert _ast_symbol_resolves(path, pin["symbol"]), (
            f"unresolved_symbol FAIL field pin: {pin['field_id']}"
        )


def test_dimensions_drift_guard_exact_pins() -> None:
    payload = _load_contract()
    for callable_id, pins in EXPECTED_DIMENSION_PINS.items():
        entry = _callable_by_id(payload, callable_id)
        merged = {**entry["inputs"], **entry["outputs"]}
        for key, expected_dim in pins.items():
            assert key in merged, f"{callable_id}: missing pin key {key}"
            assert merged[key] == expected_dim, (
                f"dimensions_drift FAIL: {callable_id}.{key} "
                f"expected={expected_dim} actual={merged[key]}"
            )

    field_pins = {p["field_id"]: p for p in payload["field_pins"]}
    assert set(field_pins) == set(EXPECTED_FIELD_PIN_DIMENSIONS)
    for field_id, expected_dim in EXPECTED_FIELD_PIN_DIMENSIONS.items():
        assert field_pins[field_id]["dimension"] == expected_dim


def test_percent_convention_guard_no_silent_equivalence() -> None:
    payload = _load_contract()
    conflicts = {c["conflict_id"]: c for c in payload["known_percent_conflicts"]}
    assert "POSITION_SIZER_CONFIG_PCT_VS_CALC_FRACTION" in conflicts
    assert "EXECUTE_FROM_SIGNALS_NOTIONAL_PCT_NAME_VS_UNIT_USAGE" in conflicts

    pos_sizer = _callable_by_id(payload, "risk.PositionSizer")
    calc = _callable_by_id(payload, "risk.calc_position_size")
    assert pos_sizer["percent_convention"] == "PERCENT_0_100"
    assert calc["percent_convention"] == "FRACTION_DECIMAL_0_1"
    assert pos_sizer["percent_convention"] != calc["percent_convention"]
    assert pos_sizer["inputs"]["risk_pct_config"] == "PERCENT_0_100"
    assert calc["inputs"]["risk_per_trade"] == "FRACTION_DECIMAL_0_1"
    assert calc["inputs"]["max_position_pct"] == "FRACTION_DECIMAL_0_1"

    exec_entry = _callable_by_id(payload, "execution.execute_from_signals")
    assert exec_entry["inputs"]["max_position_notional_pct"] == "UNKNOWN_OR_AMBIGUOUS"
    assert exec_entry["percent_convention"] == "MIXED_OR_AMBIGUOUS"
    notes = exec_entry["ambiguity_notes"]
    assert "absolute units" in notes.lower()
    assert "FRACTION_DECIMAL_0_1" in notes
    assert len(notes.strip()) > 0

    # Explicit non-equivalence rule
    for conflict in payload["known_percent_conflicts"]:
        left, right = conflict["must_not_equate"]
        assert left != right
        assert {left, right} <= set(EXPECTED_DIMENSION_CATALOG) or {
            left,
            right,
        } <= {"PERCENT_0_100", "FRACTION_DECIMAL_0_1", "QUANTITY_BASE_UNITS"}


def test_companion_edge_guard_exactly_two_not_primary() -> None:
    payload = _load_contract()
    edges = payload["companion_edges"]
    assert len(edges) == EXPECTED_COMPANION_EDGE_COUNT
    ids = tuple(sorted(e["edge_id"] for e in edges))
    assert ids == EXPECTED_COMPANION_EDGE_IDS
    assert payload["markers"]["EXPECTED_COMPANION_EDGE_COUNT"] == EXPECTED_COMPANION_EDGE_COUNT

    for edge in edges:
        assert edge["edge_id"] not in EXPECTED_PRIMARY_OWNER_IDS
        assert edge["primary_owner"] is False
        assert edge["bypass_surface_member"] is False
        path = REPO_ROOT / edge["source_path"]
        assert path.is_file()
        assert _ast_symbol_resolves(path, edge["caller_symbol"]), (
            f"unresolved companion caller: {edge['edge_id']}"
        )
        assert _ast_has_attribute_assignment_in_method(
            path,
            class_method=edge["caller_symbol"],
            attribute_name=edge["assignment_attribute"],
        ), f"companion attribute not found in AST: {edge['edge_id']}"
        assert edge["declared_dimension"] == "FRACTION_DECIMAL_0_1"
        assert edge["runtime_usage_dimension"] == "UNKNOWN_OR_AMBIGUOUS"

    # Must not inflate primary owner count
    assert len(payload["primary_owner_ids_sorted"]) == EXPECTED_PRIMARY_OWNER_COUNT


def test_leverage_ceiling_pass_through_documented() -> None:
    payload = _load_contract()
    crs_eval = _callable_by_id(payload, "crs.evaluate_capital_risk_sizing_v1")
    crs_chain = _callable_by_id(payload, "crs.evaluate_quantity_chain_v1")
    assert crs_eval["inputs"]["leverage_ceiling"] == "LEVERAGE_MULTIPLIER"
    assert crs_chain["inputs"]["leverage_ceiling"] == "LEVERAGE_MULTIPLIER"
    for entry in (crs_eval, crs_chain):
        notes = entry["ambiguity_notes"].lower()
        assert "not applied" in notes or "pass-through" in notes or "pass through" in notes

    pin = next(
        p
        for p in payload["field_pins"]
        if p["field_id"] == "CapitalRiskSizingContextV1.leverage_ceiling"
    )
    assert pin["dimension"] == "LEVERAGE_MULTIPLIER"
    assert "not applied" in pin["note"].lower()


def test_authority_pins_remain_unresolved_none() -> None:
    payload = _load_contract()
    pins = payload["global_authority_pins"]
    assert pins["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert pins["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert pins["AUTHORITY_EFFECT"] == "NONE"
    assert pins["RUNTIME_EFFECT"] == "NONE"
    assert payload["markers"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert payload["markers"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    assert payload["drift_policy"]["authority_escalation"] == "FAIL"


def test_existing_risk_sizing_surface_contract_still_5_5() -> None:
    inventory = json.loads(_read(OWNER_INVENTORY_JSON))
    surface = inventory["risk_sizing_owner_and_bypass_surface_contract"]
    assert surface["expected_owner_count"] == 5
    assert surface["expected_bypass_count"] == 5
    assert len(surface["owners"]) == 5
    assert len(surface["bypasses"]) == 5
    assert surface["global_authority_pins"]["CANONICAL_RISK_SIZING_OWNER"] == "UNRESOLVED"
    assert surface["global_authority_pins"]["CANONICAL_EXECUTION_AUTHORITY_OWNER"] == "UNRESOLVED"
    related = surface["related_but_separate_contracts"]
    assert (
        related["risk_sizing_units_dimensions_contract_v0"]
        == "SEPARATE_UNITS_DIMENSIONS_DECLARATION_ONLY"
    )


def test_legacy_order_intent_contracts_untouched() -> None:
    legacy = json.loads(_read(LEGACY_ORDER_INTENT_JSON))
    assert "direct_submission_surface_contract" in legacy
    assert "decision_owner_surface_contract" in legacy
    assert len(legacy["direct_submission_surface_contract"]["surfaces"]) == 5
    assert len(legacy["decision_owner_surface_contract"]["owners"]) == 3


def test_readme_and_inventory_doc_point_to_units_contract() -> None:
    readme = _read(REPO_ROOT / "docs" / "governance" / "README.md")
    assert "RISK_SIZING_UNITS_DIMENSIONS_CONTRACT_V0.md" in readme
    inventory_doc = _read(
        REPO_ROOT / "docs" / "governance" / "RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md"
    )
    assert "risk_sizing_units_dimensions_contract_v0.json" in inventory_doc
