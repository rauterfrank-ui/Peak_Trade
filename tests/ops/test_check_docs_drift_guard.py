"""Tests for scripts/ops/check_docs_drift_guard.py (deterministic mapping logic)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "check_docs_drift_guard.py"

_spec = importlib.util.spec_from_file_location("check_docs_drift_guard", _SCRIPT)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
evaluate = _mod.evaluate

_FIXTURE_MAP: dict = {
    "version": 1,
    "rules": [
        {
            "id": "execution-layer",
            "sensitive": ["src/execution/"],
            "required_docs": [
                "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
                "docs/PEAK_TRADE_V1_KNOWN_LIMITATIONS.md",
            ],
        },
        {
            "id": "governance-doc",
            "sensitive": ["docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md"],
            "required_docs": ["docs/ops/registry/DOCS_TRUTH_MAP.md"],
        },
    ],
}


def test_no_sensitive_change_ok() -> None:
    changed = ["README.md", "src/foo.py"]
    assert evaluate(changed, _FIXTURE_MAP) == []


def test_execution_change_with_governance_doc_ok() -> None:
    changed = [
        "src/execution/pipeline.py",
        "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
        "docs/ops/registry/DOCS_TRUTH_MAP.md",
    ]
    assert evaluate(changed, _FIXTURE_MAP) == []


def test_execution_change_without_doc_fails() -> None:
    changed = ["src/execution/pipeline.py"]
    v = evaluate(changed, _FIXTURE_MAP)
    assert len(v) == 1
    assert v[0][0] == "execution-layer"
    assert "src/execution/pipeline.py" in v[0][1]


def test_governance_doc_change_requires_truth_map() -> None:
    changed = ["docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md"]
    v = evaluate(changed, _FIXTURE_MAP)
    assert len(v) == 1
    assert v[0][0] == "governance-doc"


def test_governance_plus_truth_map_ok() -> None:
    changed = [
        "docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md",
        "docs/ops/registry/DOCS_TRUTH_MAP.md",
    ]
    v = evaluate(changed, _FIXTURE_MAP)
    assert not any(x[0] == "governance-doc" for x in v)


def test_script_exists() -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "ops" / "check_docs_drift_guard.py"
    assert script.is_file()
