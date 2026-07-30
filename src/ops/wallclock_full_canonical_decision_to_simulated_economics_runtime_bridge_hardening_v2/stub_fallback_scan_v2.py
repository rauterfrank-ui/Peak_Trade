"""Automated stub/fallback scan — fail-closed acceptance gate."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CANONICAL_FILL_LEDGER_ATTR,
    DEFAULT_HOLD_FALLBACK_ACTIVE,
    DEFAULT_REGIME_FALLBACK_ACTIVE,
    DEFAULT_ZERO_QUANTITY_FALLBACK_ACTIVE,
    ECONOMICS_PLACEHOLDER_WRITERS_ACTIVE,
    FORCED_FIXTURE_WALLCLOCK_REACHABLE,
    HARDCODED_HOLD_PRESENT,
    OWNER,
    PRODUCTIVE_WALLCLOCK_REQUIRED_APPEND_STREAMS,
)

SCAN_ID = f"{OWNER}.stub_fallback_scan_v2"

BRIDGE_PKG = "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
HARDENING_PKG = (
    "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
)
WALLCLOCK_RUNTIME = (
    "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
    "session_runtime_v1.py"
)
FORCED_WIRING_MODULE_MARKER = "forced_wiring_fixture_v2"


@dataclass
class StubFallbackScanResultV2:
    ok: bool
    scan_id: str
    blockers: list[str] = field(default_factory=list)
    findings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(repo_root: Path, rel: str) -> str:
    return (repo_root / rel).read_text(encoding="utf-8")


def run_stub_fallback_scan_v2(*, repo_root: Path) -> StubFallbackScanResultV2:
    root = Path(repo_root)
    blockers: list[str] = []
    findings: dict[str, Any] = {
        "hardcoded_hold_present": HARDCODED_HOLD_PRESENT,
        "default_hold_fallback_active": DEFAULT_HOLD_FALLBACK_ACTIVE,
        "default_zero_quantity_fallback_active": DEFAULT_ZERO_QUANTITY_FALLBACK_ACTIVE,
        "default_regime_fallback_active": DEFAULT_REGIME_FALLBACK_ACTIVE,
        "economics_placeholder_writers_active": ECONOMICS_PLACEHOLDER_WRITERS_ACTIVE,
        "forced_fixture_wallclock_reachable": FORCED_FIXTURE_WALLCLOCK_REACHABLE,
        "canonical_fill_ledger_attr": CANONICAL_FILL_LEDGER_ATTR,
    }

    # Regime default scan in feature pipelines.
    for rel in (
        f"{BRIDGE_PKG}/feature_regime_pipeline_v1.py",
        f"{HARDENING_PKG}/feature_regime_pipeline_v2.py",
    ):
        text = _read(root, rel)
        if 'regime_id = "trending"  # default' in text or "default known suitability" in text:
            blockers.append(f"DEFAULT_REGIME_FALLBACK_IN_SOURCE:{rel}")
        if "REGIME_UNCLASSIFIED_FAIL_CLOSED" not in text and "hardening" in rel:
            blockers.append(f"MISSING_UNCLASSIFIED_FAIL_CLOSED:{rel}")

    # fills_ledger typo must be absent in bridge owners.
    for rel in (
        f"{BRIDGE_PKG}/decision_economics_cycle_bridge_v1.py",
        f"{BRIDGE_PKG}/wallclock_binding_adapter_v1.py",
        WALLCLOCK_RUNTIME,
        "scripts/ops/run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py",
        f"{HARDENING_PKG}/hardening_cycle_bridge_v2.py",
    ):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "fills_ledger" in text:
            blockers.append(f"NONCANONICAL_FILLS_LEDGER_ATTR:{rel}")

    # Wallclock must not import forced wiring fixture.
    runtime = _read(root, WALLCLOCK_RUNTIME)
    if FORCED_WIRING_MODULE_MARKER in runtime:
        blockers.append("FORCED_FIXTURE_IMPORTED_BY_WALLCLOCK")
        findings["forced_fixture_wallclock_reachable"] = True

    # Observation adapter must not expose silent HOLD / qty=0 defaults.
    adapter = _read(
        root,
        "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "observation_cycle_adapter_v1.py",
    )
    if 'intended_side: str = "HOLD"' in adapter:
        blockers.append("DEFAULT_HOLD_ADAPTER_PARAMETER_PRESENT")
        findings["default_hold_fallback_active"] = True
    if 'intended_quantity: Decimal = Decimal("0")' in adapter:
        blockers.append("DEFAULT_ZERO_QUANTITY_ADAPTER_PARAMETER_PRESENT")
        findings["default_zero_quantity_fallback_active"] = True
    if "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE" not in runtime:
        blockers.append("DEFAULT_HOLD_ADAPTER_REACHABLE_WITHOUT_BRIDGE_GUARD")

    # Productive wallclock must bind runbook evidence streams (not only offline probes).
    evidence_writer = _read(
        root,
        "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "wallclock_evidence_v1.py",
    )
    if "append_productive_cycle_evidence_streams_v2" not in runtime:
        blockers.append("PRODUCTIVE_EVIDENCE_STREAM_BINDER_NOT_CALLED")
    for stream in PRODUCTIVE_WALLCLOCK_REQUIRED_APPEND_STREAMS:
        if stream not in evidence_writer:
            blockers.append(f"PRODUCTIVE_APPEND_STREAM_MISSING:{stream}")
    if "completion_verdict.json" not in runtime:
        blockers.append("COMPLETION_VERDICT_NOT_WRITTEN_BY_WALLCLOCK")
    auth_runtime = _read(
        root,
        "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1/"
        "authorization_consumption_runtime_v1.py",
    )
    if "authorization_consumption.json" not in auth_runtime and (
        "authorization_consumption.json" not in runtime
    ):
        blockers.append("AUTHORIZATION_CONSUMPTION_JSON_NOT_WRITTEN")

    # Placeholder economics writers: require stub=False path and bridge-required guard.
    if "BRIDGE_REQUIRED_FOR_FULL_SYSTEM_EVIDENCE" not in runtime:
        blockers.append("ECONOMICS_PLACEHOLDER_WRITER_UNGUARDED")
    if '"stub": True' in runtime and "quality_fail = True" not in runtime:
        blockers.append("ECONOMICS_STUB_WRITER_WITHOUT_QUALITY_FAIL")

    # AST: no place_order / submit_order calls in hardening package.
    pkg = root / HARDENING_PKG
    for path in pkg.glob("*.py"):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = None
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in {"place_order", "submit_order", "create_order", "cancel_order"}:
                    blockers.append(f"ORDER_CALL_IN_HARDENING:{path.name}:{name}")
            if isinstance(node, ast.ImportFrom) and node.module:
                if "private" in node.module.lower():
                    blockers.append(f"PRIVATE_IMPORT:{path.name}:{node.module}")
                if node.module.startswith("src.execution.venue"):
                    blockers.append(f"VENUE_EXEC_IMPORT:{path.name}:{node.module}")

    if DEFAULT_REGIME_FALLBACK_ACTIVE:
        blockers.append("CONSTANT_DEFAULT_REGIME_FALLBACK_ACTIVE_TRUE")
    if HARDCODED_HOLD_PRESENT:
        blockers.append("CONSTANT_HARDCODED_HOLD_PRESENT_TRUE")
    if FORCED_FIXTURE_WALLCLOCK_REACHABLE:
        blockers.append("CONSTANT_FORCED_FIXTURE_WALLCLOCK_REACHABLE_TRUE")

    return StubFallbackScanResultV2(
        ok=not blockers,
        scan_id=SCAN_ID,
        blockers=blockers,
        findings=findings,
    )
