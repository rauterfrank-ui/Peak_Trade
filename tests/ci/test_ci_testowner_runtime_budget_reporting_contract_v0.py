"""Reporting-only contract for testowner runtime budget inventory (Stage 2 v0).

Stage 4 extends this owner with runtime_class → TestLayer mapping sourced from
``config/ci/file_category_mapping.yaml``. Pure classification only; does not
alter diff-aware selection, run_matrix, required-check contexts, or enforcement
exit codes.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import pytest
import yaml

SELECTOR = Path("scripts/ops/ci_test_selection_v1.py")
CANONICAL_MAPPING_FILE = Path("config/ci/file_category_mapping.yaml")

NEAR_BUDGET_RATIO = 0.85


class TestLayer(StrEnum):
    L0_STATIC = "L0_STATIC"
    L1_FAST_CORE = "L1_FAST_CORE"
    L2_OWNER_TARGETED = "L2_OWNER_TARGETED"
    L3_INTEGRATION_TARGETED = "L3_INTEGRATION_TARGETED"
    L4_FULL_REGRESSION = "L4_FULL_REGRESSION"
    L5_SCHEDULED_EXTENDED = "L5_SCHEDULED_EXTENDED"


class BudgetStatus(StrEnum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    NEAR_BUDGET = "NEAR_BUDGET"
    OVER_BUDGET = "OVER_BUDGET"
    UNKNOWN_NO_EVIDENCE = "UNKNOWN_NO_EVIDENCE"


LAYER_BUDGET_SECONDS: dict[TestLayer, int] = {
    TestLayer.L0_STATIC: 120,
    TestLayer.L2_OWNER_TARGETED: 480,
    TestLayer.L3_INTEGRATION_TARGETED: 900,
    TestLayer.L4_FULL_REGRESSION: 2400,
}


class RuntimeClassMappingStatus(StrEnum):
    MAPPED = "MAPPED"
    MISSING_RUNTIME_CLASS = "MISSING_RUNTIME_CLASS"
    UNKNOWN_RUNTIME_CLASS = "UNKNOWN_RUNTIME_CLASS"


# Deterministic reporting-only mapping from canonical YAML runtime_class values.
# seconds → NO_OP/static categories; minutes → FOCUSED owner categories;
# full_matrix → FULL regression categories.
RUNTIME_CLASS_TO_TEST_LAYER: dict[str, TestLayer] = {
    "seconds": TestLayer.L0_STATIC,
    "minutes": TestLayer.L2_OWNER_TARGETED,
    "full_matrix": TestLayer.L4_FULL_REGRESSION,
}


@dataclass(frozen=True, slots=True)
class RuntimeClassMappingResult:
    runtime_class: str | None
    test_layer: TestLayer | None
    mapping_status: RuntimeClassMappingStatus
    provenance_source: str
    category: str | None = None
    selection_mode: str | None = None
    reporting_only: bool = True


def map_runtime_class_to_test_layer(
    runtime_class: str | None,
    *,
    category: str | None = None,
    selection_mode: str | None = None,
    provenance_source: str = CANONICAL_MAPPING_FILE.as_posix(),
) -> RuntimeClassMappingResult:
    if runtime_class is None:
        return RuntimeClassMappingResult(
            runtime_class=None,
            test_layer=None,
            mapping_status=RuntimeClassMappingStatus.MISSING_RUNTIME_CLASS,
            provenance_source=provenance_source,
            category=category,
            selection_mode=selection_mode,
        )
    normalized = runtime_class.strip()
    if not normalized:
        return RuntimeClassMappingResult(
            runtime_class=runtime_class,
            test_layer=None,
            mapping_status=RuntimeClassMappingStatus.MISSING_RUNTIME_CLASS,
            provenance_source=provenance_source,
            category=category,
            selection_mode=selection_mode,
        )
    layer = RUNTIME_CLASS_TO_TEST_LAYER.get(normalized)
    if layer is None:
        return RuntimeClassMappingResult(
            runtime_class=normalized,
            test_layer=None,
            mapping_status=RuntimeClassMappingStatus.UNKNOWN_RUNTIME_CLASS,
            provenance_source=provenance_source,
            category=category,
            selection_mode=selection_mode,
        )
    return RuntimeClassMappingResult(
        runtime_class=normalized,
        test_layer=layer,
        mapping_status=RuntimeClassMappingStatus.MAPPED,
        provenance_source=provenance_source,
        category=category,
        selection_mode=selection_mode,
    )


def load_runtime_class_category_rows(
    mapping_path: Path = CANONICAL_MAPPING_FILE,
) -> list[dict[str, Any]]:
    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    categories = data.get("categories", {})
    rows: list[dict[str, Any]] = []
    for category_name in sorted(categories):
        entry = categories[category_name]
        rows.append(
            {
                "category": category_name,
                "runtime_class": entry.get("runtime_class"),
                "selection_mode": entry.get("mode"),
                "provenance_source": mapping_path.as_posix(),
            }
        )
    return rows


def build_runtime_class_test_layer_mapping_report(
    mapping_path: Path = CANONICAL_MAPPING_FILE,
) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for row in load_runtime_class_category_rows(mapping_path):
        mapped = map_runtime_class_to_test_layer(
            row["runtime_class"],
            category=row["category"],
            selection_mode=row["selection_mode"],
            provenance_source=row["provenance_source"],
        )
        report.append(
            {
                "category": mapped.category,
                "runtime_class": mapped.runtime_class,
                "test_layer": mapped.test_layer.value if mapped.test_layer else None,
                "mapping_status": mapped.mapping_status.value,
                "selection_mode": mapped.selection_mode,
                "provenance_source": mapped.provenance_source,
                "reporting_only": mapped.reporting_only,
            }
        )
    return report


def extract_distinct_runtime_class_values(
    mapping_path: Path = CANONICAL_MAPPING_FILE,
) -> tuple[str, ...]:
    values = {
        row["runtime_class"]
        for row in load_runtime_class_category_rows(mapping_path)
        if row["runtime_class"] is not None
    }
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class TestownerRuntimeEvidence:
    testowner: str
    layer: TestLayer
    runtime_seconds: float
    evidence_source: str


@dataclass(frozen=True, slots=True)
class TestownerRuntimeReport:
    testowner: str
    layer: TestLayer
    runtime_seconds: float | None
    budget_seconds: int | None
    budget_status: BudgetStatus
    evidence_source: str | None
    reporting_only: bool = True


ARCHIVED_TESTOWNER_DURATION_EVIDENCE: tuple[TestownerRuntimeEvidence, ...] = (
    TestownerRuntimeEvidence(
        testowner="tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py",
        layer=TestLayer.L0_STATIC,
        runtime_seconds=0.18,
        evidence_source=(
            "archive:planning/systemwide_test_architecture_and_ci_runtime_migration_plan_no_run_v1_20260621T174324Z/"
            "PR4460_POSITIVE_PRECEDENT.md#static-contract-narrow-84-passed-in-0.18s"
        ),
    ),
    TestownerRuntimeEvidence(
        testowner=(
            "tests/ops/test_bounded_futures_testnet_readiness_review_admission_presentation_"
            "lifecycle_bridge_contract_v0.py"
        ),
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=230.0,
        evidence_source=(
            "archive:implementation/pr4464_fast_lane_timeout_diagnose_and_minimal_fix_v1_20260621T191945Z/"
            "VALIDATION.md#33-33-pass-230s-after-fix"
        ),
    ),
    TestownerRuntimeEvidence(
        testowner="tests/ci/test_ci_diff_aware_test_selection_v1.py",
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=464.49,
        evidence_source=(
            "archive:implementation/pe38_pr4457_diagnose_recovery_v1_20260620T101012Z/"
            "CANCELLED_FAST_LANE_LOG.txt#800-passed-in-464.49s"
        ),
    ),
    TestownerRuntimeEvidence(
        testowner=(
            "tests/ops/test_bounded_futures_testnet_readiness_review_admission_presentation_"
            "lifecycle_integration_contract_v0.py"
        ),
        layer=TestLayer.L3_INTEGRATION_TARGETED,
        runtime_seconds=928.81,
        evidence_source=(
            "archive:implementation/pe38_readiness_fixture_recovery_on_clean_main_v1_20260619T070137Z/"
            "FINAL_PE38_REVIEW_FILE_311_RESULT.md#53-passed-in-928.81s"
        ),
    ),
)


def _budget_for_layer(layer: TestLayer) -> int | None:
    return LAYER_BUDGET_SECONDS.get(layer)


def classify_testowner_runtime(
    *,
    testowner: str,
    layer: TestLayer,
    runtime_seconds: float | None,
    evidence_source: str | None,
) -> TestownerRuntimeReport:
    if layer not in LAYER_BUDGET_SECONDS:
        raise ValueError(f"unsupported reporting layer: {layer}")
    if runtime_seconds is None or evidence_source is None:
        return TestownerRuntimeReport(
            testowner=testowner,
            layer=layer,
            runtime_seconds=None,
            budget_seconds=_budget_for_layer(layer),
            budget_status=BudgetStatus.UNKNOWN_NO_EVIDENCE,
            evidence_source=None,
        )
    if runtime_seconds < 0:
        raise ValueError("runtime_seconds must be non-negative")
    budget = _budget_for_layer(layer)
    assert budget is not None
    if runtime_seconds > budget:
        status = BudgetStatus.OVER_BUDGET
    elif runtime_seconds >= budget * NEAR_BUDGET_RATIO:
        status = BudgetStatus.NEAR_BUDGET
    else:
        status = BudgetStatus.WITHIN_BUDGET
    return TestownerRuntimeReport(
        testowner=testowner,
        layer=layer,
        runtime_seconds=runtime_seconds,
        budget_seconds=budget,
        budget_status=status,
        evidence_source=evidence_source,
    )


def build_testowner_cost_inventory(
    evidence_rows: tuple[TestownerRuntimeEvidence, ...] = ARCHIVED_TESTOWNER_DURATION_EVIDENCE,
) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for row in evidence_rows:
        report = classify_testowner_runtime(
            testowner=row.testowner,
            layer=row.layer,
            runtime_seconds=row.runtime_seconds,
            evidence_source=row.evidence_source,
        )
        inventory.append(
            {
                "testowner": report.testowner,
                "layer": report.layer.value,
                "runtime_seconds": report.runtime_seconds,
                "budget_seconds": report.budget_seconds,
                "budget_status": report.budget_status.value,
                "evidence_source": report.evidence_source,
                "reporting_only": report.reporting_only,
            }
        )
    return inventory


def _run_selector(*files: str) -> dict[str, str]:
    cmd = [sys.executable, str(SELECTOR), "--event-name", "pull_request", "--files", *files]
    out = subprocess.check_output(cmd, text=True)
    result: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def test_l0_static_runtime_within_budget() -> None:
    report = classify_testowner_runtime(
        testowner=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[0].testowner,
        layer=TestLayer.L0_STATIC,
        runtime_seconds=0.18,
        evidence_source=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[0].evidence_source,
    )
    assert report.budget_status == BudgetStatus.WITHIN_BUDGET
    assert report.budget_seconds == 120


def test_l2_owner_runtime_within_budget() -> None:
    report = classify_testowner_runtime(
        testowner=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[1].testowner,
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=230.0,
        evidence_source=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[1].evidence_source,
    )
    assert report.budget_status == BudgetStatus.WITHIN_BUDGET
    assert report.budget_seconds == 480


def test_l2_owner_runtime_near_budget() -> None:
    report = classify_testowner_runtime(
        testowner=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[2].testowner,
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=464.49,
        evidence_source=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[2].evidence_source,
    )
    assert report.budget_status == BudgetStatus.NEAR_BUDGET


def test_l3_integration_runtime_over_budget() -> None:
    report = classify_testowner_runtime(
        testowner=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[3].testowner,
        layer=TestLayer.L3_INTEGRATION_TARGETED,
        runtime_seconds=928.81,
        evidence_source=ARCHIVED_TESTOWNER_DURATION_EVIDENCE[3].evidence_source,
    )
    assert report.budget_status == BudgetStatus.OVER_BUDGET
    assert report.budget_seconds == 900


def test_missing_evidence_unknown_no_evidence() -> None:
    report = classify_testowner_runtime(
        testowner="tests/ops/example_missing_evidence_owner.py",
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=None,
        evidence_source=None,
    )
    assert report.budget_status == BudgetStatus.UNKNOWN_NO_EVIDENCE
    assert report.runtime_seconds is None
    assert report.evidence_source is None


def test_negative_runtime_fail_closed() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        classify_testowner_runtime(
            testowner="tests/ci/example.py",
            layer=TestLayer.L0_STATIC,
            runtime_seconds=-1.0,
            evidence_source="archive:invalid-negative",
        )


def test_unknown_layer_fail_closed() -> None:
    with pytest.raises(ValueError, match="unsupported reporting layer"):
        classify_testowner_runtime(
            testowner="tests/ci/example.py",
            layer=TestLayer.L1_FAST_CORE,
            runtime_seconds=10.0,
            evidence_source="archive:unsupported-layer",
        )


def test_provenance_preserved_in_inventory() -> None:
    inventory = build_testowner_cost_inventory()
    assert len(inventory) == 4
    for row in inventory:
        assert row["evidence_source"] is not None
        assert str(row["evidence_source"]).startswith("archive:")
        assert row["reporting_only"] is True


def test_reporting_does_not_change_diff_aware_selection() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    before = _run_selector(reporting_file)
    _ = build_testowner_cost_inventory()
    after = _run_selector(reporting_file)
    assert before == after
    assert before["test_selection_mode"] == "NO_OP"


def test_reporting_does_not_change_run_matrix_semantics() -> None:
    _ = build_testowner_cost_inventory()
    sel = _run_selector(
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py",
    )
    assert sel["tests_execute_no_op"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"


def test_reporting_does_not_change_required_check_contexts() -> None:
    _ = build_testowner_cost_inventory()
    text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "testowner_runtime_budget_reporting" not in text
    assert "testowner_cost_inventory" not in text


def test_reporting_has_no_enforcement_exit_code() -> None:
    inventory = build_testowner_cost_inventory()
    assert all(row["budget_status"] != "PASS" for row in inventory)
    assert all(
        row["budget_status"] in {status.value for status in BudgetStatus} for row in inventory
    )


def test_archived_inventory_unknown_stays_visible_not_pass() -> None:
    inventory = build_testowner_cost_inventory()
    missing = classify_testowner_runtime(
        testowner="tests/ops/untracked_owner.py",
        layer=TestLayer.L2_OWNER_TARGETED,
        runtime_seconds=None,
        evidence_source=None,
    )
    assert missing.budget_status == BudgetStatus.UNKNOWN_NO_EVIDENCE
    assert "PASS" not in missing.budget_status.value
    assert all(
        entry["budget_status"] != BudgetStatus.UNKNOWN_NO_EVIDENCE.value for entry in inventory
    )


def test_selector_static_contract_unchanged_for_ci_reporting_file() -> None:
    sel = _run_selector("tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py")
    assert sel["test_selection_mode"] == "NO_OP"
    assert sel["tests_execute_no_op"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"


# --- Stage 4: runtime_class → TestLayer reporting-only mapping ---


def test_canonical_runtime_class_values_are_seconds_minutes_full_matrix() -> None:
    values = extract_distinct_runtime_class_values()
    assert values == ("full_matrix", "minutes", "seconds")


def test_seconds_maps_to_l0_static() -> None:
    mapped = map_runtime_class_to_test_layer(
        "seconds", category="static_contract", selection_mode="NO_OP"
    )
    assert mapped.mapping_status == RuntimeClassMappingStatus.MAPPED
    assert mapped.test_layer == TestLayer.L0_STATIC


def test_minutes_maps_to_l2_owner_targeted() -> None:
    mapped = map_runtime_class_to_test_layer(
        "minutes", category="tests_focused", selection_mode="FOCUSED"
    )
    assert mapped.mapping_status == RuntimeClassMappingStatus.MAPPED
    assert mapped.test_layer == TestLayer.L2_OWNER_TARGETED


def test_full_matrix_maps_to_l4_full_regression() -> None:
    mapped = map_runtime_class_to_test_layer(
        "full_matrix", category="central_src", selection_mode="FULL"
    )
    assert mapped.mapping_status == RuntimeClassMappingStatus.MAPPED
    assert mapped.test_layer == TestLayer.L4_FULL_REGRESSION


def test_missing_runtime_class_fail_closed() -> None:
    mapped = map_runtime_class_to_test_layer(None, category="unknown")
    assert mapped.mapping_status == RuntimeClassMappingStatus.MISSING_RUNTIME_CLASS
    assert mapped.test_layer is None


def test_empty_runtime_class_fail_closed() -> None:
    mapped = map_runtime_class_to_test_layer("   ", category="unknown")
    assert mapped.mapping_status == RuntimeClassMappingStatus.MISSING_RUNTIME_CLASS
    assert mapped.test_layer is None


def test_unknown_runtime_class_fail_closed() -> None:
    mapped = map_runtime_class_to_test_layer("hours", category="unknown")
    assert mapped.mapping_status == RuntimeClassMappingStatus.UNKNOWN_RUNTIME_CLASS
    assert mapped.test_layer is None
    assert mapped.test_layer != TestLayer.L1_FAST_CORE


def test_unknown_runtime_class_not_classified_as_fast_or_no_op() -> None:
    mapped = map_runtime_class_to_test_layer("fast_lane", category="unknown")
    assert mapped.mapping_status == RuntimeClassMappingStatus.UNKNOWN_RUNTIME_CLASS
    assert mapped.test_layer not in {TestLayer.L0_STATIC, TestLayer.L1_FAST_CORE}


def test_runtime_class_mapping_provenance_preserved() -> None:
    report = build_runtime_class_test_layer_mapping_report()
    assert report
    for row in report:
        assert row["provenance_source"] == CANONICAL_MAPPING_FILE.as_posix()
        assert row["category"] is not None
        assert row["reporting_only"] is True


def test_runtime_class_mapping_covers_all_yaml_categories() -> None:
    report = build_runtime_class_test_layer_mapping_report()
    categories = {row["category"] for row in report}
    yaml_categories = set(
        yaml.safe_load(CANONICAL_MAPPING_FILE.read_text(encoding="utf-8"))["categories"]
    )
    assert categories == yaml_categories
    assert all(row["mapping_status"] == RuntimeClassMappingStatus.MAPPED.value for row in report)


def test_mapped_layers_consumable_by_stage2_budget_model() -> None:
    report = build_runtime_class_test_layer_mapping_report()
    for row in report:
        layer = TestLayer(row["test_layer"])
        if layer in LAYER_BUDGET_SECONDS:
            assert LAYER_BUDGET_SECONDS[layer] > 0


def test_runtime_class_mapping_does_not_change_diff_aware_selection() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    before = _run_selector(reporting_file)
    _ = build_runtime_class_test_layer_mapping_report()
    after = _run_selector(reporting_file)
    assert before == after
    assert before["test_selection_mode"] == "NO_OP"


def test_runtime_class_mapping_does_not_change_run_matrix() -> None:
    _ = build_runtime_class_test_layer_mapping_report()
    sel = _run_selector("tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py")
    assert sel["tests_execute_no_op"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"


def test_runtime_class_mapping_has_no_enforcement_exit_code() -> None:
    report = build_runtime_class_test_layer_mapping_report()
    assert all(row["mapping_status"] != "PASS" for row in report)
    assert all(
        row["mapping_status"] in {status.value for status in RuntimeClassMappingStatus}
        for row in report
    )


def test_stage2_inventory_backward_compatible_after_stage4_extension() -> None:
    inventory = build_testowner_cost_inventory()
    assert len(inventory) == 4
    report = build_runtime_class_test_layer_mapping_report()
    assert len(report) >= 3
