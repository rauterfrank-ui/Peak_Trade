"""Offline characterization tests for required-checks safety-gate surfaces.

These tests intentionally avoid GitHub API calls, workflow mutations, branch
protection changes, and any runtime trading behavior. They pin the repository's
required-checks SSOT and safety wording boundaries as engineering/review
surfaces only.

Related: ``tests/ci/test_required_checks_config.py`` (loader semantics),
``tests/ci/test_pru_required_checks_drift_detector.py`` (legacy retirement).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_CI = _REPO_ROOT / "scripts" / "ci"
sys.path.insert(0, str(_SCRIPTS_CI))
from required_checks_config import load_required_checks_config  # noqa: E402

_REQUIRED_CHECKS_PATH = _REPO_ROOT / "config" / "ci" / "required_status_checks.json"
_RECONCILER_PATH = _REPO_ROOT / "scripts" / "ops" / "reconcile_required_checks_branch_protection.py"
_LEGACY_DRIFT_PATH = _REPO_ROOT / "scripts" / "ci" / "required_checks_drift_detector.py"
_POINTER_SPEC_PATH = (
    _REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0.md"
)


def _markdown_to_plain(text: str) -> str:
    """Strip common md emphasis so phrase assertions work on raw file text."""
    return text.replace("**", "").replace("*", "")


def test_required_checks_ssot_json_is_parseable_with_expected_top_level_shape() -> None:
    data: Any = json.loads(_REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("schema_version")
    assert isinstance(data["required_contexts"], list)
    assert isinstance(data["ignored_contexts"], list)
    assert isinstance(data.get("notes", ""), str)


def test_required_checks_ssot_matches_canonical_loader_semantics() -> None:
    cfg = load_required_checks_config(_REQUIRED_CHECKS_PATH)
    assert cfg["required_contexts"]
    assert cfg["effective_required_contexts"]
    ignored_set = set(cfg["ignored_contexts"])
    for ctx in cfg["effective_required_contexts"]:
        assert ctx not in ignored_set


def test_required_contexts_are_unique_non_empty_strings() -> None:
    data: Any = json.loads(_REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))
    required = data["required_contexts"]
    assert isinstance(required, list)
    assert all(isinstance(x, str) for x in required)
    assert all(x.strip() == x and x for x in required)
    assert len(required) == len(set(required))


def test_ignored_contexts_are_unique_strings() -> None:
    data: Any = json.loads(_REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))
    ignored = data.get("ignored_contexts", [])
    assert isinstance(ignored, list)
    assert all(isinstance(x, str) for x in ignored)
    assert len(ignored) == len(set(ignored))


def test_ssot_allows_overlap_between_required_and_ignored_lists() -> None:
    """Inventory lists may overlap; effective contexts follow loader semantics."""
    data: Any = json.loads(_REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))
    raw_required = set(data["required_contexts"])
    raw_ignored = set(data["ignored_contexts"])
    cfg = load_required_checks_config(_REQUIRED_CHECKS_PATH)
    assert set(cfg["effective_required_contexts"]) == raw_required - raw_ignored


def test_required_context_names_do_not_make_authority_claims() -> None:
    data: Any = json.loads(_REQUIRED_CHECKS_PATH.read_text(encoding="utf-8"))
    serialized = "\n".join(data["required_contexts"]).lower()

    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "autonomous-ready",
        "strategy ready",
        "externally authorized",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in serialized


def test_reconciler_script_is_offline_parseable_and_references_ssot() -> None:
    source = _RECONCILER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert tree.body
    assert "required_status_checks" in source
    assert "branch" in source.lower()
    assert "protection" in source.lower()


def test_reconciler_script_is_not_described_as_trading_authority() -> None:
    source = _RECONCILER_PATH.read_text(encoding="utf-8").lower()

    forbidden_claims = [
        "live authorization granted",
        "signoff complete",
        "gate passed",
        "autonomy ready",
        "strategy ready",
        "trade approved",
    ]

    for claim in forbidden_claims:
        assert claim not in source


def test_legacy_drift_detector_is_not_ssot_and_pointer_index_labels_retired() -> None:
    assert _REQUIRED_CHECKS_PATH.exists()
    assert _LEGACY_DRIFT_PATH.exists()

    legacy_source = _LEGACY_DRIFT_PATH.read_text(encoding="utf-8").lower()
    pointer_spec = _POINTER_SPEC_PATH.read_text(encoding="utf-8").lower()

    assert "required_checks_drift_detector.py" in pointer_spec
    assert "legacy" in pointer_spec or "retired" in pointer_spec
    assert "required_status_checks.json" in pointer_spec
    assert (
        "retired" in legacy_source or "reconcile_required_checks_branch_protection" in legacy_source
    )


def test_pointer_spec_preserves_non_authority_boundary_for_ci_green() -> None:
    raw = _POINTER_SPEC_PATH.read_text(encoding="utf-8")
    pointer_plain = _markdown_to_plain(raw.lower())

    assert "ci green" in pointer_plain
    assert "not live authorization" in pointer_plain
    assert "not trading authority" in pointer_plain or "trading authority" in pointer_plain


@pytest.mark.parametrize(
    "protected",
    [
        _REPO_ROOT / "src" / "trading" / "master_v2",
        _REPO_ROOT / "src" / "ops" / "double_play",
        _REPO_ROOT / "src" / "risk_layer",
        _REPO_ROOT / "src" / "execution",
        _REPO_ROOT / "src" / "live",
    ],
)
def test_characterization_module_does_not_remove_protected_runtime_paths(
    protected: Path,
) -> None:
    assert protected.is_dir(), f"protected path missing from repo: {protected}"
