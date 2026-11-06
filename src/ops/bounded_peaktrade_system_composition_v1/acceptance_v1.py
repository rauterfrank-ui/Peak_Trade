"""Static local acceptance inventory, separate from economic/operational authority.

This verifies bound receipts and coverage, not the truth of prose claims. Actual
consumer assertions belong to the referenced executed episode tests and review.
"""

from hashlib import sha256
from pathlib import Path
import xml.etree.ElementTree as ET

from .manifest_v1 import repository_source_digest_v1


def project_bounded_offline_acceptance_v1(
    *,
    expected_source_digest,
    junit_path,
    expected_junit_sha256,
    required_case_ids,
    case_evidence,
    selected_optional_case_ids=(),
):
    """Validate a *current* explicit offline inventory; never issue permission."""
    if expected_source_digest != repository_source_digest_v1():
        raise ValueError("ACCEPTANCE_SOURCE_GENERATION_CHANGED")
    raw = Path(junit_path).read_bytes()
    if sha256(raw).hexdigest() != expected_junit_sha256:
        raise ValueError("ACCEPTANCE_TEST_RECEIPT_CHANGED")
    root = ET.fromstring(raw)
    tests = root.findall(".//testcase")
    population = {(t.attrib["classname"], t.attrib["name"]) for t in tests}
    if len(population) != len(tests) or not population:
        raise ValueError("ACCEPTANCE_TEST_POPULATION_AMBIGUOUS")
    if any(root.findall(".//" + tag) for tag in ("failure", "error", "skipped")):
        raise ValueError("ACCEPTANCE_TEST_POPULATION_NOT_PASS")
    required = set(required_case_ids)
    optional = set(selected_optional_case_ids)
    if (
        not required
        or len(required) != len(required_case_ids)
        or required & optional
        or len(optional) != len(selected_optional_case_ids)
    ):
        raise ValueError("ACCEPTANCE_REQUIREMENTS_AMBIGUOUS")
    observed = {}
    for case in case_evidence:
        key = case["case_id"]
        if key in observed or key not in required | optional:
            raise ValueError("ACCEPTANCE_UNKNOWN_OR_DUPLICATE_CASE")
        if case["data_class"] != "EXPLICIT_SYNTHETIC_OFFLINE":
            raise ValueError("ACCEPTANCE_DATA_CLASS_UNSUPPORTED")
        if not case["actual_owners"] or not case["scope_limit"]:
            raise ValueError("ACCEPTANCE_OWNER_AND_SCOPE_REQUIRED")
        refs = {(r["class"], r["name"]) for r in case["tests"]}
        if not refs or not refs <= population:
            raise ValueError("ACCEPTANCE_CASE_TEST_NOT_EXECUTED")
        if case["status"] not in {"PASS_SELECTED_OFFLINE_PROFILE", "BLOCKED", "INCOMPLETE"}:
            raise ValueError("ACCEPTANCE_CASE_STATUS_INVALID")
        observed[key] = case
    missing = sorted((required | optional) - observed.keys())
    blocked = sorted(
        k for k, v in observed.items() if v["status"] != "PASS_SELECTED_OFFLINE_PROFILE"
    )
    return {
        "schema": "bounded_offline_acceptance_inventory.v1",
        "source_tree_digest": expected_source_digest,
        "junit_sha256": expected_junit_sha256,
        "distinct_passing_test_count": len(population),
        "required_case_ids": sorted(required),
        "selected_optional_case_ids": sorted(optional),
        "missing_cases": missing,
        "blocked_or_incomplete_cases": blocked,
        "inventory_status": "INCOMPLETE" if missing else "BLOCKED" if blocked else "COMPLETE",
        "semantic_review_required": True,
        "economic_quality": "BLOCKED_POSITIVE_CONTRACT_NOT_RATIFIED",
        "natural_source_accepted": False,
        "full_system_accepted": False,
        "operational_authority": "NONE",
    }
