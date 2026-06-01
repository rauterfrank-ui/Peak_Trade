"""Static mapping guard contract for Cybersecurity Visibility R-001/R-002/R-007.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests operator artifacts or
touches runtime, hooks, Notion, Market, broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
INPUT_ARTIFACT_TEST = "test_cybersecurity_visibility_r_pending_input_artifact_contract_v0.py"
THIS_MODULE = Path(__file__).name

RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)
FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
REPO_TEST_OWNER_PATH_RX = re.compile(r"`(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")

CHARTER_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_REPO_STATIC_INVENTORY_CHARTER_V0=true"
INPUT_ARTIFACT_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_V0=true"
MAPPING_GUARD_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_V0=true"
EXTERNAL_INPUT_JSONL_MAPPING_GUARD_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_R_PENDING_EXTERNAL_INPUT_JSONL_MAPPING_GUARD_V0=true"
)

INTAKE_PACKET_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_input_jsonl_intake_packet_v0_20260601T020000Z"
)
VALIDATION_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_input_jsonl_validation_v0_20260601T030000Z"
)

EXTERNAL_VALIDATION_EXPECTED: dict[str, str] = {
    "EXTERNAL_INPUT_JSONL_INTAKE_PACKET_CREATED": "true",
    "EXTERNAL_INPUT_JSONL_VALIDATION_PASSED": "true",
    "INPUT_PACKET_VERIFIED": "true",
    "JSONL_PARSE_PASSED": "true",
    "SCHEMA_ALLOWLIST_PASSED": "true",
    "FORBIDDEN_FIELDS_SECRET_SCAN_PASSED": "true",
    "REDACTION_RULES_PASSED": "true",
    "OWNER_REUSE_VERIFIED": "true",
    "SECRETS_INCLUDED": "false",
    "MANIFEST_VERIFY_RC": "0",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "PATH_B_LIFT_DISCUSSION_READY": "false",
    "GLOBAL_PREFLIGHT_LIFTED": "false",
    "RUNTIME_STARTED": "false",
}

GUARD_REGISTRY_EXPECTED: dict[str, str] = {
    "INPUT_JSONL_PROVIDED": "false",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "NO_MAPPING_WITHOUT_INPUT_ARTIFACT": "true",
}

GUARD_REGISTRY_LINE_RX = re.compile(
    r"^(INPUT_JSONL_PROVIDED|LOSSLESS_JSONL_RECOVERY)=(true|false)$"
)

CANONICAL_PENDING_CYBER_TEST_MODULES = frozenset(
    {
        "test_cybersecurity_visibility_r_pending_inventory_charter_v0.py",
        "test_cybersecurity_visibility_r_pending_input_artifact_contract_v0.py",
        "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py",
    }
)


def _ci_audit_text() -> str:
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _fenced_blocks(text: str) -> list[str]:
    return [block.strip() for block in FENCED_BLOCK_RX.findall(text)]


def _block_containing(text: str, anchor: str) -> str:
    for block in _fenced_blocks(text):
        if anchor in block:
            return block
    raise AssertionError(f"missing fenced machine-line block containing {anchor!r}")


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.partition("=")
        if key and value:
            values[key.strip()] = value.strip()
    return values


def _assert_block_keys(
    block: str, *, block_name: str, required_keys: frozenset[str]
) -> dict[str, str]:
    values = _machine_line_values(block)
    missing = required_keys - values.keys()
    assert not missing, f"{block_name} missing keys: {sorted(missing)}"
    for key in required_keys:
        assert values[key] == GUARD_REGISTRY_EXPECTED[key], (
            f"{block_name} {key}={values[key]!r} expected {GUARD_REGISTRY_EXPECTED[key]!r}"
        )
    return values


def _static_visibility_owner_section(text: str) -> str:
    marker = "### Static visibility contract owners (reuse — do not duplicate)"
    start = text.find(marker)
    assert start != -1, "static visibility contract owners section missing"
    return text[start:]


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def test_cybersecurity_visibility_r_pending_mapping_guard_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert "Pending R-001/R-002/R-007 — mapping guard v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_V0=true" in text
    assert "FORBIDS_FLIPPING_INPUT_JSONL_PROVIDED_WITHOUT_AUTHORIZED_MAPPING_SLICE=true" in text
    assert "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT=true" in text
    assert "FORBIDS_REPO_STATIC_SUCCESSOR_AS_DEFINITIVE_MAPPING_INPUT=true" in text
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true" in text
    assert (
        "ACCEPTED_INPUT_ARTIFACTS=FULL_LOSSLESS_RISK_CANDIDATES.jsonl,"
        "APPROVED_OPERATOR_TRIAGE_ARTIFACT" in text
    )
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text

    assert "cannot be documented or tested as **recovered**" in text
    assert "repo-static successor `REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl` alone" in text

    rows = _risk_table_rows(text)
    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in rows
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()

    for mapped_id, expected_owner in (
        ("R-003", "tests/ops/test_run_sample_size_ramp_script_contract_v0.py"),
        ("R-004", "tests/ops/test_run_testnet_evidence_flow_v2_script_contract_v0.py"),
        ("R-005", "tests/ops/test_knowledge_prod_smoke_script.py"),
        ("R-006", "tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py"),
    ):
        owner_cell, status_cell = rows[mapped_id]
        assert expected_owner in owner_cell
        assert status_cell.lower() == "mapped"

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("INPUT_JSONL_PROVIDED="):
            assert stripped == "INPUT_JSONL_PROVIDED=false"
        if stripped.startswith("LOSSLESS_JSONL_RECOVERY="):
            assert stripped == "LOSSLESS_JSONL_RECOVERY=false"

    for marker in (
        "R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
        "R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
        "R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
    ):
        assert marker in text

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_r_pending_mapping_guard_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "Cybersecurity Visibility R pending mapping guard v0" in truth_map
    assert (
        "Cybersecurity Visibility R pending external INPUT_JSONL intake mapping guard v0"
        in truth_map
    )
    assert THIS_MODULE in truth_map
    assert INPUT_ARTIFACT_TEST in truth_map
    assert "non-authorizing" in collapsed
    assert "fastpath" in collapsed or "fast-path" in collapsed or "tests/ci" in truth_map
    assert "INPUT_PACKET_VERIFIED=true" in truth_map
    assert "SECRETS_INCLUDED=false" in truth_map


def test_cybersecurity_visibility_pending_guard_machine_line_consistency_v0() -> None:
    text = _ci_audit_text()
    charter_block = _block_containing(text, CHARTER_BLOCK_ANCHOR)
    input_block = _block_containing(text, INPUT_ARTIFACT_BLOCK_ANCHOR)
    guard_block = _block_containing(text, MAPPING_GUARD_BLOCK_ANCHOR)

    shared_keys = frozenset({"LOSSLESS_JSONL_RECOVERY"})
    _assert_block_keys(charter_block, block_name="charter", required_keys=shared_keys)
    _assert_block_keys(
        input_block,
        block_name="input_artifact",
        required_keys=frozenset(GUARD_REGISTRY_EXPECTED),
    )
    _assert_block_keys(
        guard_block,
        block_name="mapping_guard",
        required_keys=frozenset(GUARD_REGISTRY_EXPECTED),
    )


def test_cybersecurity_visibility_pending_guard_risk_table_registry_v0() -> None:
    text = _ci_audit_text()
    rows = _risk_table_rows(text)

    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in rows
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()
        assert "recovered" not in status_cell.lower()

    for mapped_id, expected_owner in (
        ("R-003", "tests/ops/test_run_sample_size_ramp_script_contract_v0.py"),
        ("R-004", "tests/ops/test_run_testnet_evidence_flow_v2_script_contract_v0.py"),
        ("R-005", "tests/ops/test_knowledge_prod_smoke_script.py"),
        ("R-006", "tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py"),
    ):
        owner_cell, status_cell = rows[mapped_id]
        assert expected_owner in owner_cell
        assert status_cell.lower() == "mapped"


def test_cybersecurity_visibility_static_owner_registry_paths_exist_v0() -> None:
    text = _static_visibility_owner_section(_ci_audit_text())
    paths = sorted(set(REPO_TEST_OWNER_PATH_RX.findall(text)))
    assert paths, "no static visibility contract owner paths found"
    for rel_path in paths:
        assert (REPO_ROOT / rel_path).is_file(), f"missing owner module: {rel_path}"


def test_cybersecurity_visibility_histogram_owner_reuse_modules_exist_v0() -> None:
    text = _ci_audit_text()
    histogram_start = text.find("**Interim classification histogram")
    assert histogram_start != -1
    histogram_section = text[histogram_start : text.find("**Lossless recovery still required")]
    reuse_paths = sorted(set(HISTOGRAM_REUSE_PATH_RX.findall(histogram_section)))
    assert reuse_paths, "histogram must reference existing test modules for reuse"
    for rel_path in reuse_paths:
        assert (REPO_ROOT / rel_path).is_file(), f"missing histogram reuse module: {rel_path}"
    static_paths = set(REPO_TEST_OWNER_PATH_RX.findall(_static_visibility_owner_section(text)))
    assert set(reuse_paths).issubset(static_paths), (
        "histogram reuse modules must be subset of static visibility contract owners"
    )


def _forbidden_guard_registry_assignments(text: str) -> list[str]:
    drift: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = GUARD_REGISTRY_LINE_RX.match(stripped)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if value == "true":
            drift.append(stripped)
        elif key in GUARD_REGISTRY_EXPECTED and value != GUARD_REGISTRY_EXPECTED[key]:
            drift.append(stripped)
    return drift


def test_cybersecurity_visibility_r_pending_external_input_jsonl_mapping_guard_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    external_block = _block_containing(text, EXTERNAL_INPUT_JSONL_MAPPING_GUARD_BLOCK_ANCHOR)
    external_values = _machine_line_values(external_block)

    assert "Pending R-001/R-002/R-007 — external INPUT_JSONL intake mapping guard v0" in text
    assert INTAKE_PACKET_PATH in text
    assert VALIDATION_BUNDLE_PATH in text
    assert THIS_MODULE in text
    assert "does not** ingest operator JSONL into the repo" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text

    for key, expected in EXTERNAL_VALIDATION_EXPECTED.items():
        assert external_values.get(key) == expected, (
            f"external mapping guard {key}={external_values.get(key)!r} expected {expected!r}"
        )

    _assert_block_keys(
        external_block,
        block_name="external_input_jsonl_mapping_guard",
        required_keys=frozenset(
            {
                "INPUT_JSONL_PROVIDED",
                "LOSSLESS_JSONL_RECOVERY",
                "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED",
                "NO_MAPPING_WITHOUT_INPUT_ARTIFACT",
            }
        ),
    )

    assert "non-authorizing" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_pending_guard_negative_drift_forbidden_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()

    drift_lines = _forbidden_guard_registry_assignments(text)
    assert not drift_lines, f"forbidden guard-registry assignments: {drift_lines}"

    rows = _risk_table_rows(text)
    for pending_id in ("R-001", "R-002", "R-007"):
        _, status_cell = rows[pending_id]
        assert status_cell.lower() != "mapped"
        assert "recovered" not in status_cell.lower()

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED="):
            assert stripped.endswith("=false")
        if stripped.startswith("R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED="):
            assert stripped.endswith("=false")
        if stripped.startswith("R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED="):
            assert stripped.endswith("=false")

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text
    for module in CANONICAL_PENDING_CYBER_TEST_MODULES:
        assert (REPO_ROOT / "tests" / "ci" / module).is_file(), (
            f"missing canonical pending cyber test module: {module}"
        )
    assert "Pending R-001/R-002/R-007 — repo-static successor inventory charter v0" in text
    assert "Pending R-001/R-002/R-007 — input artifact contract v0" in text
    assert "Pending R-001/R-002/R-007 — mapping guard v0" in text
    assert "Static inventory schema validation guard v0" in text
    assert "test_static_inventory_schema_guard_contract_v0.py" in text
    static_section = _static_visibility_owner_section(text)
    assert "do not duplicate" in static_section.lower()
