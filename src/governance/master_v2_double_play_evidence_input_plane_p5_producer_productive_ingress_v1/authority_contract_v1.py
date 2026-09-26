"""Authority and non-interference checks for P5 producer ingress."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    ContractValidationResultV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.bypass_scan_v1 import (
    scan_producer_class_bypass_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    DIRECT_PRODUCER_TO_B_BYPASS,
    DIRECT_PRODUCER_TO_DP_BYPASS,
    EXTERNAL_EFFECT_AUTHORIZED,
    IMPLEMENTS_P5_PRODUCER_PRODUCTIVE_INGRESS,
    L6_SEMANTIC_AUTHORITY,
    OWNER_DECISION_CONFIG,
    P5_PRODUCER_INTEGRATION_INTRODUCED,
    P5_PACKAGE_PATH_MARKER,
    PRODUCER_TRADING_AUTHORITY,
    PRODUCTIVE_ACTIVATION_AUTHORIZED,
    WORKPACKAGE_ID,
)

_FORBIDDEN_IMPORT_MARKERS: tuple[str, ...] = (
    "current_productive_master_v2_runtime_cycle_v1",
    "src.execution",
    "src.risk",
)


def _fail(*codes: str) -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=False, failure_codes=tuple(dict.fromkeys(codes)))


def _ok() -> ContractValidationResultV1:
    return ContractValidationResultV1(ok=True, failure_codes=())


def validate_p5_owner_decision_config_v1(
    repo_root: Path | None = None,
) -> ContractValidationResultV1:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / OWNER_DECISION_CONFIG
    if not path.is_file():
        return _fail("owner_decision_missing")
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "workpackage_id": WORKPACKAGE_ID,
        "p5_producer_integration_introduced": True,
        "producer_trading_authority": "NONE",
        "direct_producer_to_b_bypass": False,
        "direct_producer_to_dp_bypass": False,
        "productive_activation_authorized": False,
        "external_effect_authorized": False,
        "l6_semantic_authority": "UNCHANGED",
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            return _fail("owner_decision_drift")
    return _ok()


def validate_p5_producer_ingress_authority_contract_v1() -> ContractValidationResultV1:
    failures: list[str] = []
    if not IMPLEMENTS_P5_PRODUCER_PRODUCTIVE_INGRESS:
        failures.append("p5_not_implemented")
    if not P5_PRODUCER_INTEGRATION_INTRODUCED:
        failures.append("p5_integration_flag_missing")
    if PRODUCER_TRADING_AUTHORITY != "NONE":
        failures.append("producer_trading_authority_drift")
    if DIRECT_PRODUCER_TO_B_BYPASS or DIRECT_PRODUCER_TO_DP_BYPASS:
        failures.append("producer_bypass_forbidden")
    if PRODUCTIVE_ACTIVATION_AUTHORIZED or EXTERNAL_EFFECT_AUTHORIZED:
        failures.append("activation_or_external_effect_forbidden")
    if L6_SEMANTIC_AUTHORITY != "UNCHANGED":
        failures.append("l6_semantic_authority_drift")
    if failures:
        return _fail(*failures)
    return _ok()


def scan_p5_package_non_interference_v1(
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    pkg = root / "src" / "governance" / P5_PACKAGE_PATH_MARKER
    hits: list[str] = []
    for py in pkg.rglob("*.py"):
        if py.name in {"authority_contract_v1.py", "bypass_scan_v1.py"}:
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        rel = py.relative_to(root).as_posix()
        for forbidden in (
            "SideState",
            "canonical_order_intent",
            "execution_permit",
            "ENTER_LONG",
            "ENTER_SHORT",
        ):
            if forbidden in text and py.name != "bypass_scan_v1.py":
                hits.append(f"{rel}:{forbidden}")
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(alias.name, rel, hits)
            elif isinstance(node, ast.ImportFrom) and node.module:
                _check_import(node.module, rel, hits)
    bypass_ok, bypass_hits = scan_producer_class_bypass_v1(root)
    if not bypass_ok:
        hits.extend(bypass_hits)
    return (len(hits) == 0, tuple(sorted(set(hits))))


def _check_import(module: str, rel: str, hits: list[str]) -> None:
    for forbidden in _FORBIDDEN_IMPORT_MARKERS:
        if module.startswith(forbidden) or forbidden in module:
            hits.append(f"{rel}:import:{module}")
    if "p4_l6_productive_seam_binding" in module or "p3_input_creator_binder" in module:
        hits.append(f"{rel}:import:{module}")
