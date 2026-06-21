"""Reporting-only contract for testowner runtime budget inventory (Stage 2 v0).

Stage 4 extends this owner with runtime_class → TestLayer mapping sourced from
``config/ci/file_category_mapping.yaml``. Stage 5A adds testowner → category →
runtime_class → TestLayer provenance reporting reusing the canonical selector
``categorize()`` semantics and YAML mapping rows. Stage 5B adds a bounded
reporting-only batch inventory join that routes multiple testowners through the
Stage 5A provenance chain and joins archived runtime evidence with Stage 2 budget
status. Pure classification only; does not alter diff-aware selection, run_matrix,
required-check contexts, or enforcement exit codes.
"""

from __future__ import annotations

import fnmatch
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
import yaml

from scripts.ops.ci_test_selection_v1 import categorize

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


class ProvenanceResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNKNOWN_NO_MATCH = "UNKNOWN_NO_MATCH"
    UNKNOWN_MISSING_RUNTIME_CLASS = "UNKNOWN_MISSING_RUNTIME_CLASS"
    UNKNOWN_RUNTIME_CLASS = "UNKNOWN_RUNTIME_CLASS"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"


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


def normalize_testowner_path(path: str) -> str:
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    if normalized.startswith("/"):
        raise ValueError("absolute paths are not valid testowner identities")
    if ".." in PurePosixPath(normalized).parts:
        raise ValueError("parent segments are not valid in testowner paths")
    return normalized.removeprefix("./")


def load_category_mapping_categories(
    mapping_path: Path = CANONICAL_MAPPING_FILE,
) -> dict[str, Any]:
    data = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    return data.get("categories", {})


def yaml_glob_matches(pattern: str, path: str) -> bool:
    pattern = pattern.replace("\\", "/")
    path = path.replace("\\", "/")
    if pattern == path:
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path == prefix or path.startswith(f"{prefix}/")
    if pattern == "**/*.md":
        return path.endswith(".md")
    if pattern == "**/conftest.py":
        return path == "conftest.py" or path.endswith("/conftest.py")
    if pattern.endswith("*/**"):
        head = pattern[:-4]
        head_prefix = head.split("*", 1)[0]
        if not path.startswith(head_prefix):
            return False
        remainder = path[len(head_prefix) :]
        return fnmatch.fnmatch(remainder, head[len(head_prefix) :] + "/**")
    return fnmatch.fnmatch(path, pattern)


def find_yaml_matching_categories(
    path: str,
    categories: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    mapping = categories if categories is not None else load_category_mapping_categories()
    matches: list[dict[str, Any]] = []
    for category_name in sorted(mapping):
        entry = mapping[category_name]
        matched_globs = [glob for glob in entry.get("globs", []) if yaml_glob_matches(glob, path)]
        if matched_globs:
            matches.append(
                {
                    "category": category_name,
                    "runtime_class": entry.get("runtime_class"),
                    "selection_mode": entry.get("mode"),
                    "matched_globs": tuple(sorted(matched_globs)),
                }
            )
    return matches


def _selector_rule_id(category: str) -> str:
    return f"selector.categorize:{category}"


def _resolve_provenance_status(
    *,
    selector_category: str,
    yaml_matches: list[dict[str, Any]],
    mapping_status: RuntimeClassMappingStatus,
) -> ProvenanceResolutionStatus:
    distinct_runtime_classes = {
        match["runtime_class"] for match in yaml_matches if match.get("runtime_class") is not None
    }
    if (
        len(yaml_matches) > 1
        and len(distinct_runtime_classes) > 1
        and selector_category == "unknown"
    ):
        return ProvenanceResolutionStatus.AMBIGUOUS_MATCH
    if selector_category == "unknown":
        return ProvenanceResolutionStatus.UNKNOWN_NO_MATCH
    if mapping_status == RuntimeClassMappingStatus.MISSING_RUNTIME_CLASS:
        return ProvenanceResolutionStatus.UNKNOWN_MISSING_RUNTIME_CLASS
    if mapping_status == RuntimeClassMappingStatus.UNKNOWN_RUNTIME_CLASS:
        return ProvenanceResolutionStatus.UNKNOWN_RUNTIME_CLASS
    return ProvenanceResolutionStatus.RESOLVED


def _optional_budget_report_for_testowner(
    testowner_path: str,
    test_layer: TestLayer | None,
) -> dict[str, Any] | None:
    if test_layer is None or test_layer not in LAYER_BUDGET_SECONDS:
        return None
    normalized = normalize_testowner_path(testowner_path)
    for row in ARCHIVED_TESTOWNER_DURATION_EVIDENCE:
        if normalize_testowner_path(row.testowner) != normalized:
            continue
        report = classify_testowner_runtime(
            testowner=normalized,
            layer=test_layer,
            runtime_seconds=row.runtime_seconds,
            evidence_source=row.evidence_source,
        )
        return {
            "testowner": report.testowner,
            "layer": report.layer.value,
            "runtime_seconds": report.runtime_seconds,
            "budget_seconds": report.budget_seconds,
            "budget_status": report.budget_status.value,
            "evidence_source": report.evidence_source,
            "reporting_only": report.reporting_only,
        }
    return None


@dataclass(frozen=True, slots=True)
class TestownerCategoryProvenanceReport:
    testowner_path: str
    matched_category: str | None
    matched_pattern: str | None
    runtime_class: str | None
    test_layer: TestLayer | None
    provenance_source: str
    resolution_status: ProvenanceResolutionStatus
    selection_mode: str | None = None
    budget_report: dict[str, Any] | None = None
    reporting_only: bool = True


def build_testowner_category_provenance_report(
    testowner_path: str,
    *,
    mapping_path: Path = CANONICAL_MAPPING_FILE,
    categories: dict[str, Any] | None = None,
) -> TestownerCategoryProvenanceReport:
    normalized = normalize_testowner_path(testowner_path)
    selector_category = categorize(normalized)
    mapping = (
        categories if categories is not None else load_category_mapping_categories(mapping_path)
    )
    yaml_matches = find_yaml_matching_categories(normalized, mapping)
    matched_pattern: str | None = None
    runtime_class: str | None = None
    selection_mode: str | None = None
    provenance_source = f"scripts/ops/ci_test_selection_v1.py:categorize+{mapping_path.as_posix()}"

    if selector_category != "unknown" and selector_category in mapping:
        entry = mapping[selector_category]
        runtime_class = entry.get("runtime_class")
        selection_mode = entry.get("mode")
        category_globs = [
            glob for glob in entry.get("globs", []) if yaml_glob_matches(glob, normalized)
        ]
        if category_globs:
            matched_pattern = sorted(category_globs)[0]
        else:
            matched_pattern = _selector_rule_id(selector_category)
    elif selector_category != "unknown":
        matched_pattern = _selector_rule_id(selector_category)
    elif yaml_matches:
        matched_pattern = yaml_matches[0]["matched_globs"][0]

    mapped = map_runtime_class_to_test_layer(
        runtime_class,
        category=selector_category if selector_category != "unknown" else None,
        selection_mode=selection_mode,
        provenance_source=provenance_source,
    )
    resolution_status = _resolve_provenance_status(
        selector_category=selector_category,
        yaml_matches=yaml_matches,
        mapping_status=mapped.mapping_status,
    )
    test_layer = (
        mapped.test_layer if resolution_status == ProvenanceResolutionStatus.RESOLVED else None
    )
    budget_report = _optional_budget_report_for_testowner(normalized, test_layer)

    return TestownerCategoryProvenanceReport(
        testowner_path=normalized,
        matched_category=None if selector_category == "unknown" else selector_category,
        matched_pattern=matched_pattern,
        runtime_class=mapped.runtime_class,
        test_layer=test_layer,
        provenance_source=provenance_source,
        resolution_status=resolution_status,
        selection_mode=selection_mode,
        budget_report=budget_report,
    )


def build_testowner_category_provenance_report_dict(
    testowner_path: str,
    *,
    mapping_path: Path = CANONICAL_MAPPING_FILE,
    categories: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_testowner_category_provenance_report(
        testowner_path,
        mapping_path=mapping_path,
        categories=categories,
    )
    payload: dict[str, Any] = {
        "testowner_path": report.testowner_path,
        "matched_category": report.matched_category,
        "matched_pattern": report.matched_pattern,
        "runtime_class": report.runtime_class,
        "test_layer": report.test_layer.value if report.test_layer else None,
        "provenance_source": report.provenance_source,
        "resolution_status": report.resolution_status.value,
        "selection_mode": report.selection_mode,
        "reporting_only": report.reporting_only,
    }
    if report.budget_report is not None:
        payload["budget_report"] = report.budget_report
    return payload


@dataclass(frozen=True, slots=True)
class TestownerBudgetInventoryRow:
    testowner_path: str
    matched_category: str | None
    matched_pattern: str | None
    runtime_class: str | None
    test_layer: TestLayer | None
    runtime_seconds: float | None
    runtime_evidence_source: str | None
    budget_seconds: int | None
    budget_status: BudgetStatus
    resolution_status: ProvenanceResolutionStatus
    provenance: str
    reporting_only: bool = True


def parse_runtime_seconds(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("runtime_seconds must be numeric")
    numeric = float(value)
    if numeric < 0:
        raise ValueError("runtime_seconds must be non-negative")
    return numeric


def _deduplicate_testowner_paths(testowner_paths: list[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    unique: list[str] = []
    duplicate_count = 0
    for path in testowner_paths:
        normalized = normalize_testowner_path(path)
        if normalized in seen:
            duplicate_count += 1
            continue
        seen.add(normalized)
        unique.append(path)
    return unique, duplicate_count


def _resolve_budget_fields_for_inventory_row(
    provenance_report: TestownerCategoryProvenanceReport,
) -> tuple[float | None, str | None, int | None, BudgetStatus]:
    if provenance_report.resolution_status != ProvenanceResolutionStatus.RESOLVED:
        return None, None, None, BudgetStatus.UNKNOWN_NO_EVIDENCE
    if provenance_report.budget_report is None:
        budget_seconds = (
            _budget_for_layer(provenance_report.test_layer)
            if provenance_report.test_layer is not None
            else None
        )
        return None, None, budget_seconds, BudgetStatus.UNKNOWN_NO_EVIDENCE
    budget_report = provenance_report.budget_report
    return (
        budget_report["runtime_seconds"],
        budget_report["evidence_source"],
        budget_report["budget_seconds"],
        BudgetStatus(budget_report["budget_status"]),
    )


def build_testowner_budget_inventory_row(
    testowner_path: str,
    *,
    mapping_path: Path = CANONICAL_MAPPING_FILE,
    categories: dict[str, Any] | None = None,
) -> TestownerBudgetInventoryRow:
    provenance_report = build_testowner_category_provenance_report(
        testowner_path,
        mapping_path=mapping_path,
        categories=categories,
    )
    runtime_seconds, evidence_source, budget_seconds, budget_status = (
        _resolve_budget_fields_for_inventory_row(provenance_report)
    )
    return TestownerBudgetInventoryRow(
        testowner_path=provenance_report.testowner_path,
        matched_category=provenance_report.matched_category,
        matched_pattern=provenance_report.matched_pattern,
        runtime_class=provenance_report.runtime_class,
        test_layer=provenance_report.test_layer,
        runtime_seconds=runtime_seconds,
        runtime_evidence_source=evidence_source,
        budget_seconds=budget_seconds,
        budget_status=budget_status,
        resolution_status=provenance_report.resolution_status,
        provenance=provenance_report.provenance_source,
    )


def testowner_budget_inventory_row_to_dict(row: TestownerBudgetInventoryRow) -> dict[str, Any]:
    return {
        "testowner_path": row.testowner_path,
        "matched_category": row.matched_category,
        "matched_pattern": row.matched_pattern,
        "runtime_class": row.runtime_class,
        "test_layer": row.test_layer.value if row.test_layer else None,
        "runtime_seconds": row.runtime_seconds,
        "runtime_evidence_source": row.runtime_evidence_source,
        "budget_seconds": row.budget_seconds,
        "budget_status": row.budget_status.value,
        "resolution_status": row.resolution_status.value,
        "provenance": row.provenance,
        "reporting_only": row.reporting_only,
    }


def build_testowner_budget_inventory_summary(
    rows: list[TestownerBudgetInventoryRow],
    *,
    duplicate_testowner_skipped_count: int = 0,
) -> dict[str, int]:
    summary: dict[str, int] = {
        "total_rows": len(rows),
        "resolved_rows": 0,
        "unknown_provenance_rows": 0,
        "ambiguous_match_rows": 0,
        "within_budget_rows": 0,
        "near_budget_rows": 0,
        "over_budget_rows": 0,
        "unknown_no_evidence_rows": 0,
        "duplicate_testowner_skipped_count": duplicate_testowner_skipped_count,
    }
    positive_budget_statuses = {
        BudgetStatus.WITHIN_BUDGET,
        BudgetStatus.NEAR_BUDGET,
        BudgetStatus.OVER_BUDGET,
    }
    for row in rows:
        if row.resolution_status == ProvenanceResolutionStatus.RESOLVED:
            summary["resolved_rows"] += 1
        elif row.resolution_status == ProvenanceResolutionStatus.AMBIGUOUS_MATCH:
            summary["ambiguous_match_rows"] += 1
            summary["unknown_provenance_rows"] += 1
        elif row.resolution_status != ProvenanceResolutionStatus.RESOLVED:
            summary["unknown_provenance_rows"] += 1
        if row.budget_status == BudgetStatus.WITHIN_BUDGET:
            summary["within_budget_rows"] += 1
        elif row.budget_status == BudgetStatus.NEAR_BUDGET:
            summary["near_budget_rows"] += 1
        elif row.budget_status == BudgetStatus.OVER_BUDGET:
            summary["over_budget_rows"] += 1
        elif row.budget_status == BudgetStatus.UNKNOWN_NO_EVIDENCE:
            summary["unknown_no_evidence_rows"] += 1
        if row.resolution_status != ProvenanceResolutionStatus.RESOLVED:
            assert row.budget_status not in positive_budget_statuses
    return summary


def build_testowner_budget_inventory(
    testowner_paths: list[str],
    *,
    mapping_path: Path = CANONICAL_MAPPING_FILE,
    categories: dict[str, Any] | None = None,
) -> dict[str, Any]:
    unique_paths, duplicate_count = _deduplicate_testowner_paths(testowner_paths)
    rows = [
        build_testowner_budget_inventory_row(
            path,
            mapping_path=mapping_path,
            categories=categories,
        )
        for path in unique_paths
    ]
    rows.sort(key=lambda row: row.testowner_path)
    summary = build_testowner_budget_inventory_summary(
        rows,
        duplicate_testowner_skipped_count=duplicate_count,
    )
    return {
        "rows": [testowner_budget_inventory_row_to_dict(row) for row in rows],
        "summary": summary,
        "reporting_only": True,
    }


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


# --- Stage 5A: testowner → category → runtime_class → TestLayer provenance ---


def test_stage5_known_testowner_resolves_static_contract_chain() -> None:
    testowner = "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py"
    report = build_testowner_category_provenance_report(testowner)
    assert report.testowner_path == testowner
    assert report.matched_category == "static_contract"
    assert report.matched_pattern == "tests/ci/**"
    assert report.runtime_class == "seconds"
    assert report.test_layer == TestLayer.L0_STATIC
    assert report.resolution_status == ProvenanceResolutionStatus.RESOLVED
    assert report.provenance_source.endswith(CANONICAL_MAPPING_FILE.as_posix())
    assert report.budget_report is not None
    assert report.budget_report["layer"] == TestLayer.L0_STATIC.value


def test_stage5_report_preserves_original_testowner_path() -> None:
    report = build_testowner_category_provenance_report(
        "./tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )
    assert report.testowner_path == (
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )


def test_stage5_no_category_match_fail_closed_unknown() -> None:
    report = build_testowner_category_provenance_report("not/a/known/repo/path.xyz")
    assert report.matched_category is None
    assert report.resolution_status == ProvenanceResolutionStatus.UNKNOWN_NO_MATCH
    assert report.test_layer is None


def test_stage5_missing_runtime_class_fail_closed() -> None:
    report = build_testowner_category_provenance_report(
        "tests/ci/example.py",
        categories={
            "static_contract": {
                "mode": "NO_OP",
                "globs": ["tests/ci/**"],
            }
        },
    )
    assert report.matched_category == "static_contract"
    assert report.resolution_status == ProvenanceResolutionStatus.UNKNOWN_MISSING_RUNTIME_CLASS
    assert report.test_layer is None


def test_stage5_unknown_runtime_class_fail_closed() -> None:
    report = build_testowner_category_provenance_report(
        "tests/ci/example.py",
        categories={
            "static_contract": {
                "mode": "NO_OP",
                "globs": ["tests/ci/**"],
                "runtime_class": "hours",
            }
        },
    )
    assert report.resolution_status == ProvenanceResolutionStatus.UNKNOWN_RUNTIME_CLASS
    assert report.test_layer is None
    assert report.test_layer != TestLayer.L1_FAST_CORE


def test_stage5_ambiguous_yaml_runtime_class_fail_closed() -> None:
    report = build_testowner_category_provenance_report(
        "synthetic/ambiguous/path.py",
        categories={
            "alpha": {
                "mode": "FOCUSED",
                "globs": ["synthetic/**"],
                "runtime_class": "seconds",
            },
            "beta": {
                "mode": "FULL",
                "globs": ["synthetic/ambiguous/**"],
                "runtime_class": "full_matrix",
            },
        },
    )
    assert report.resolution_status == ProvenanceResolutionStatus.AMBIGUOUS_MATCH
    assert report.test_layer is None


def test_stage5_budget_report_uses_same_test_layer_not_archived_layer() -> None:
    testowner = (
        "tests/ops/test_bounded_futures_testnet_readiness_review_admission_presentation_"
        "lifecycle_bridge_contract_v0.py"
    )
    report = build_testowner_category_provenance_report(testowner)
    assert report.matched_category == "static_contract"
    assert report.test_layer == TestLayer.L0_STATIC
    assert report.budget_report is not None
    assert report.budget_report["layer"] == TestLayer.L0_STATIC.value
    assert report.budget_report["layer"] != TestLayer.L2_OWNER_TARGETED.value


def test_stage5_path_normalization_is_repo_relative_deterministic() -> None:
    assert normalize_testowner_path("tests/ci/foo.py") == normalize_testowner_path(
        "./tests/ci/foo.py"
    )
    with pytest.raises(ValueError, match="absolute paths"):
        normalize_testowner_path("/Users/local/tests/ci/foo.py")


def test_stage5_provenance_chain_fields_in_dict_report() -> None:
    payload = build_testowner_category_provenance_report_dict(
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )
    assert payload["matched_category"] == "static_contract"
    assert payload["runtime_class"] == "seconds"
    assert payload["test_layer"] == TestLayer.L0_STATIC.value
    assert payload["resolution_status"] == ProvenanceResolutionStatus.RESOLVED.value
    assert payload["reporting_only"] is True


def test_stage5_provenance_does_not_change_diff_aware_selection() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    before = _run_selector(reporting_file)
    _ = build_testowner_category_provenance_report(reporting_file)
    after = _run_selector(reporting_file)
    assert before == after
    assert before["test_selection_mode"] == "NO_OP"


def test_stage5_provenance_does_not_change_run_matrix() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    _ = build_testowner_category_provenance_report(reporting_file)
    sel = _run_selector(reporting_file)
    assert sel["tests_execute_no_op"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"


def test_stage5_provenance_has_no_enforcement_exit_code() -> None:
    payload = build_testowner_category_provenance_report_dict(
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )
    assert payload["resolution_status"] != "PASS"
    assert payload["resolution_status"] in {status.value for status in ProvenanceResolutionStatus}


def test_stage5_stage2_and_stage4_backward_compatible_after_extension() -> None:
    inventory = build_testowner_cost_inventory()
    mapping_report = build_runtime_class_test_layer_mapping_report()
    provenance = build_testowner_category_provenance_report(
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )
    assert len(inventory) == 4
    assert len(mapping_report) >= 3
    assert provenance.resolution_status == ProvenanceResolutionStatus.RESOLVED


# --- Stage 5B: unified provenance-to-budget batch inventory ---


_STAGE5B_RESOLVABLE_TESTOWNERS: tuple[str, ...] = (
    "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py",
    "tests/ci/test_ci_diff_aware_test_selection_v1.py",
    (
        "tests/ops/test_bounded_futures_testnet_readiness_review_admission_presentation_"
        "lifecycle_integration_contract_v0.py"
    ),
)


def test_stage5b_multiple_resolvable_testowners_fully_resolved() -> None:
    inventory = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    assert len(inventory["rows"]) == 3
    assert inventory["summary"]["resolved_rows"] == 3
    for row in inventory["rows"]:
        assert row["resolution_status"] == ProvenanceResolutionStatus.RESOLVED.value
        assert row["test_layer"] is not None
        assert row["matched_category"] is not None
        assert row["runtime_class"] is not None
        assert row["provenance"] is not None


def test_stage5b_inventory_row_contains_full_provenance_chain() -> None:
    inventory = build_testowner_budget_inventory(
        ["tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py"]
    )
    row = inventory["rows"][0]
    assert row["testowner_path"] == (
        "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py"
    )
    assert row["matched_category"] == "static_contract"
    assert row["matched_pattern"] == "tests/ci/**"
    assert row["runtime_class"] == "seconds"
    assert row["test_layer"] == TestLayer.L0_STATIC.value
    assert row["provenance"].endswith(CANONICAL_MAPPING_FILE.as_posix())


def test_stage5b_known_runtime_evidence_joined_correctly() -> None:
    inventory = build_testowner_budget_inventory(
        ["tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py"]
    )
    row = inventory["rows"][0]
    assert row["runtime_seconds"] == 0.18
    assert row["runtime_evidence_source"] is not None
    assert str(row["runtime_evidence_source"]).startswith("archive:")
    assert row["budget_seconds"] == 120
    assert row["budget_status"] == BudgetStatus.WITHIN_BUDGET.value


def test_stage5b_budget_status_uses_stage4_test_layer() -> None:
    testowner = "tests/ci/test_ci_diff_aware_test_selection_v1.py"
    inventory = build_testowner_budget_inventory([testowner])
    row = inventory["rows"][0]
    assert row["test_layer"] == TestLayer.L2_OWNER_TARGETED.value
    assert row["budget_seconds"] == 480
    assert row["budget_status"] == BudgetStatus.NEAR_BUDGET.value


def test_stage5b_missing_runtime_evidence_unknown_no_evidence() -> None:
    inventory = build_testowner_budget_inventory(
        ["tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"]
    )
    row = inventory["rows"][0]
    assert row["resolution_status"] == ProvenanceResolutionStatus.RESOLVED.value
    assert row["runtime_seconds"] is None
    assert row["runtime_evidence_source"] is None
    assert row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value


def test_stage5b_no_category_match_fail_closed() -> None:
    inventory = build_testowner_budget_inventory(["not/a/known/repo/path.xyz"])
    row = inventory["rows"][0]
    assert row["matched_category"] is None
    assert row["resolution_status"] == ProvenanceResolutionStatus.UNKNOWN_NO_MATCH.value
    assert row["test_layer"] is None
    assert row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value


def test_stage5b_missing_runtime_class_fail_closed() -> None:
    inventory = build_testowner_budget_inventory(
        ["tests/ci/example.py"],
        categories={
            "static_contract": {
                "mode": "NO_OP",
                "globs": ["tests/ci/**"],
            }
        },
    )
    row = inventory["rows"][0]
    assert (
        row["resolution_status"] == ProvenanceResolutionStatus.UNKNOWN_MISSING_RUNTIME_CLASS.value
    )
    assert row["test_layer"] is None
    assert row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value


def test_stage5b_unknown_runtime_class_fail_closed() -> None:
    inventory = build_testowner_budget_inventory(
        ["tests/ci/example.py"],
        categories={
            "static_contract": {
                "mode": "NO_OP",
                "globs": ["tests/ci/**"],
                "runtime_class": "hours",
            }
        },
    )
    row = inventory["rows"][0]
    assert row["resolution_status"] == ProvenanceResolutionStatus.UNKNOWN_RUNTIME_CLASS.value
    assert row["test_layer"] is None
    assert row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value


def test_stage5b_ambiguous_match_fail_closed() -> None:
    inventory = build_testowner_budget_inventory(
        ["synthetic/ambiguous/path.py"],
        categories={
            "alpha": {
                "mode": "FOCUSED",
                "globs": ["synthetic/**"],
                "runtime_class": "seconds",
            },
            "beta": {
                "mode": "FULL",
                "globs": ["synthetic/ambiguous/**"],
                "runtime_class": "full_matrix",
            },
        },
    )
    row = inventory["rows"][0]
    assert row["resolution_status"] == ProvenanceResolutionStatus.AMBIGUOUS_MATCH.value
    assert row["test_layer"] is None
    assert row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value


def test_stage5b_unknown_provenance_never_within_budget() -> None:
    inventory = build_testowner_budget_inventory(
        [
            "not/a/known/repo/path.xyz",
            "synthetic/ambiguous/path.py",
        ],
        categories={
            "alpha": {
                "mode": "FOCUSED",
                "globs": ["synthetic/**"],
                "runtime_class": "seconds",
            },
            "beta": {
                "mode": "FULL",
                "globs": ["synthetic/ambiguous/**"],
                "runtime_class": "full_matrix",
            },
        },
    )
    positive = {
        BudgetStatus.WITHIN_BUDGET.value,
        BudgetStatus.NEAR_BUDGET.value,
        BudgetStatus.OVER_BUDGET.value,
    }
    for row in inventory["rows"]:
        if row["resolution_status"] != ProvenanceResolutionStatus.RESOLVED.value:
            assert row["budget_status"] not in positive


def test_stage5b_negative_runtime_fail_closed() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        parse_runtime_seconds(-1.0)


def test_stage5b_non_numeric_runtime_fail_closed() -> None:
    with pytest.raises(ValueError, match="numeric"):
        parse_runtime_seconds("not-a-number")


def test_stage5b_duplicate_testowners_deduplicated_deterministically() -> None:
    testowner = "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py"
    inventory = build_testowner_budget_inventory([testowner, f"./{testowner}", testowner])
    assert len(inventory["rows"]) == 1
    assert inventory["summary"]["duplicate_testowner_skipped_count"] == 2
    assert inventory["summary"]["total_rows"] == 1


def test_stage5b_input_order_does_not_change_semantic_mapping() -> None:
    owners = list(_STAGE5B_RESOLVABLE_TESTOWNERS)
    forward = build_testowner_budget_inventory(owners)
    reverse = build_testowner_budget_inventory(list(reversed(owners)))
    shuffled = build_testowner_budget_inventory([owners[2], owners[0], owners[1]])
    assert forward["rows"] == reverse["rows"] == shuffled["rows"]


def test_stage5b_output_deterministically_sorted() -> None:
    inventory = build_testowner_budget_inventory(list(reversed(_STAGE5B_RESOLVABLE_TESTOWNERS)))
    paths = [row["testowner_path"] for row in inventory["rows"]]
    assert paths == sorted(paths)


def test_stage5b_provenance_preserved_per_row() -> None:
    inventory = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    for row in inventory["rows"]:
        assert row["provenance"] is not None
        assert "categorize+" in row["provenance"]
        assert row["provenance"].endswith(CANONICAL_MAPPING_FILE.as_posix())


def test_stage5b_summary_derived_from_rows_only() -> None:
    inventory = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    summary = inventory["summary"]
    rows = inventory["rows"]
    assert summary["total_rows"] == len(rows)
    assert summary["resolved_rows"] == sum(
        1 for row in rows if row["resolution_status"] == ProvenanceResolutionStatus.RESOLVED.value
    )
    assert summary["unknown_no_evidence_rows"] == sum(
        1 for row in rows if row["budget_status"] == BudgetStatus.UNKNOWN_NO_EVIDENCE.value
    )


def test_stage5b_summary_unknown_not_counted_as_pass() -> None:
    inventory = build_testowner_budget_inventory(
        [
            "tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py",
            "not/a/known/repo/path.xyz",
        ]
    )
    summary = inventory["summary"]
    assert summary["unknown_provenance_rows"] >= 1
    assert summary["unknown_no_evidence_rows"] >= 1
    assert "pass" not in str(summary).lower()


def test_stage5b_does_not_change_diff_aware_selection() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    before = _run_selector(reporting_file)
    _ = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    after = _run_selector(reporting_file)
    assert before == after
    assert before["test_selection_mode"] == "NO_OP"


def test_stage5b_does_not_change_run_matrix() -> None:
    reporting_file = "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    _ = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    sel = _run_selector(reporting_file)
    assert sel["tests_execute_no_op"] == "true"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "false"


def test_stage5b_has_no_enforcement_exit_code() -> None:
    inventory = build_testowner_budget_inventory(list(_STAGE5B_RESOLVABLE_TESTOWNERS))
    assert all(row["budget_status"] != "PASS" for row in inventory["rows"])
    assert all(
        row["budget_status"] in {status.value for status in BudgetStatus}
        for row in inventory["rows"]
    )


def test_stage5b_stage2_stage4_stage5a_backward_compatible() -> None:
    stage2 = build_testowner_cost_inventory()
    stage4 = build_runtime_class_test_layer_mapping_report()
    stage5a = build_testowner_category_provenance_report(
        "tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"
    )
    stage5b = build_testowner_budget_inventory(
        ["tests/ci/test_ci_testowner_runtime_budget_reporting_contract_v0.py"]
    )
    assert len(stage2) == 4
    assert len(stage4) >= 3
    assert stage5a.resolution_status == ProvenanceResolutionStatus.RESOLVED
    assert len(stage5b["rows"]) == 1
