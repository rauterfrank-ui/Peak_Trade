"""Test-only patch restoring PE-31 binding coherence in PE-38 default builders."""

from __future__ import annotations

from dataclasses import replace as _orig_replace

import src.ops.bounded_futures_testnet_preflight_execution_readiness_review_lifecycle_integration_contract_v0 as _pe38_mod
from src.ops.bounded_futures_testnet_preflight_execution_readiness_assembly_lifecycle_integration_contract_v0 import (
    PreflightExecutionReadinessAssemblyInput,
    _attach_coherent_pe31_bindings,
)

_PATCHED = False


def apply_pe38_coherent_fixture_patch() -> None:
    global _PATCHED
    if _PATCHED:
        return

    def _replace_with_pe31_coherence(obj, /, **changes):
        result = _orig_replace(obj, **changes)
        if isinstance(result, PreflightExecutionReadinessAssemblyInput):
            if "pe25_operator_closure_proof" in changes and "pe37_traceability_proof" in changes:
                return _attach_coherent_pe31_bindings(result)
        return result

    _pe38_mod.replace = _replace_with_pe31_coherence  # type: ignore[attr-defined]
    _PATCHED = True
