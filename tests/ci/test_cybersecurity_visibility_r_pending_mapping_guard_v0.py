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
DERIVED_MAPPING_PLAN_PROGRESS_TEST = (
    "test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0.py"
)
RELEASE_RC_INDEX_HEADING = "## Cybersecurity Visibility Release RC v0 — index v0"

RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)
FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
REPO_TEST_OWNER_PATH_RX = re.compile(r"`(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")

ADOPTION_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_OPERATOR_ACCEPTED_ARCHIVE_FULL_LOSSLESS_ADOPTION_V0=true"
)
ADOPTION_HEADING = (
    "Pending R-001/R-002/R-007 — operator-accepted archive FULL_LOSSLESS governance adoption v0"
)
ARCHIVE_FULL_LOSSLESS_SHA256 = (
    "eff5698370a8cd38cacf02325d81223ca667d4995bda8cfcb6435b5de5327f26"
)
CHARTER_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_REPO_STATIC_INVENTORY_CHARTER_V0=true"
INPUT_ARTIFACT_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_V0=true"
MAPPING_GUARD_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_V0=true"
EXTERNAL_INPUT_JSONL_MAPPING_GUARD_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_R_PENDING_EXTERNAL_INPUT_JSONL_MAPPING_GUARD_V0=true"
)
WAVE1_BATCH_CLOSURE_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0=true"
)

DERIVED_EVIDENCE_MAPPED_RISKS: dict[str, tuple[str, str]] = {
    "R-001": (
        "tests/ci/test_workflow_write_permissions_visibility_contract_v0.py",
        "DERIVED-CYBER-R-001-001",
    ),
    "R-002": (
        "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py",
        "DERIVED-CYBER-R-002-001",
    ),
    "R-007": (
        "tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py",
        "DERIVED-CYBER-R-007-001",
    ),
}

WAVE1_BATCH_CLOSURE_PLAN_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_wave1_batch_closure_plan_readonly_v0_20260601T182957Z"
)
PR3894_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_wave1_execution_guard_prep_pr_merge_closeout_readonly_v0_20260601T182216Z"
)
DERIVED_JSONL_BUILD_VALIDATE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_jsonl_build_validate_v0_20260601T165743Z"
)
WAVE1_EXECUTION_READINESS_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_wave1_execution_readiness_precheck_readonly_v0_20260601T182100Z"
)

WAVE1_BATCH_CLOSURE_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0": "true",
    "MAPPED_BY_DERIVED_EVIDENCE_ONLY": "true",
    "DERIVED_EVIDENCE_MAPPED_STATUS_ALLOWED": "true",
    "FORBIDS_DEFINITIVE_MAPPED_WITHOUT_INPUT": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
}

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


def _assert_derived_evidence_mapped(status_cell: str) -> None:
    assert "mapped-by-derived-evidence" in status_cell.lower()
    assert status_cell.strip().lower() != "mapped"


def _assert_derived_evidence_mapped_row(
    owner_cell: str,
    status_cell: str,
    *,
    expected_owner: str,
    derived_id: str,
) -> None:
    assert expected_owner in owner_cell
    _assert_derived_evidence_mapped(status_cell)
    assert derived_id in status_cell


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
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        assert risk_id in rows
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )

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

    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        assert risk_id in rows
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )
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
    for risk_id in DERIVED_EVIDENCE_MAPPED_RISKS:
        _, status_cell = rows[risk_id]
        assert status_cell.strip().lower() != "mapped"
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
    assert "CSC-LOSSLESS-v1 dataset reflection guard v0" in text
    assert "test_csc_lossless_v1_dataset_reflection_contract_v0.py" in text
    assert "CSC-RCHAIN-v1 accepted groups reflection guard v0" in text
    assert "test_csc_rchain_v1_grouping_reflection_contract_v0.py" in text
    static_section = _static_visibility_owner_section(text)
    assert "do not duplicate" in static_section.lower()


def test_cybersecurity_visibility_wave1_batch_closure_mapping_guard_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    batch_block = _block_containing(text, WAVE1_BATCH_CLOSURE_BLOCK_ANCHOR)
    batch_values = _machine_line_values(batch_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping wave-1 batch closure v0" in text
    assert WAVE1_BATCH_CLOSURE_PLAN_PATH in text
    assert PR3894_CLOSEOUT_PATH in text
    assert WAVE1_EXECUTION_READINESS_PRECHECK_PATH in text
    assert DERIVED_JSONL_BUILD_VALIDATE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_WAVE1_BATCH_CLOSURE_PR=true" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text
    assert "does not** assign definitive **`mapped`** status" in text

    for key, expected in WAVE1_BATCH_CLOSURE_EXPECTED.items():
        assert batch_values.get(key) == expected, (
            f"wave-1 batch closure {key}={batch_values.get(key)!r} expected {expected!r}"
        )

    rows = _risk_table_rows(text)
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_release_rc_v0_slice_cv1_mapping_guard_crosslink_v0() -> None:
    text = _ci_audit_text()
    start = text.find(RELEASE_RC_INDEX_HEADING)
    assert start != -1, "missing Cybersecurity Visibility Release RC v0 index section"
    section = text[start : start + 8000]

    assert "CYBERSECURITY_VISIBILITY_RELEASE_RC_V0" in section
    assert THIS_MODULE in section
    assert DERIVED_MAPPING_PLAN_PROGRESS_TEST in section
    assert "docs/tests-only" in section
    assert "no parallel" in section.lower()
    assert "CYBER_REAL_DATA_PII_BLOCKED=true" in text
    assert "NO_RUNTIME=true" in text
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


CV3B_READOUT_HEADING = "### Defensive visibility readout / owner-triage guard v0 (SLICE-CV-3b)"
CV3B_BLOCK_ANCHOR = "CV3B_DEFENSIVE_VISIBILITY_READOUT_OWNER_TRIAGE_GUARD_V0=true"
DERIVED_MAPPING_PLAN_PROGRESS_MODULE = (
    "tests/ci/test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0.py"
)
INVENTORY_CHARTER_MODULE = (
    "tests/ci/test_cybersecurity_visibility_r_pending_inventory_charter_v0.py"
)


def _cv3b_readout_block(text: str) -> str:
    start = text.index(CV3B_READOUT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def test_cybersecurity_visibility_cv3b_mapping_guard_readout_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _cv3b_readout_block(text)
    collapsed = block.lower()

    assert CV3B_BLOCK_ANCHOR in block
    assert THIS_MODULE in block
    assert DERIVED_MAPPING_PLAN_PROGRESS_MODULE in block
    assert INVENTORY_CHARTER_MODULE in block
    assert "Retained risk table" in block
    assert "mapped-by-derived-evidence" in collapsed
    assert "definitive" in collapsed
    assert "INPUT_JSONL_PROVIDED=false" in block
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in block
    assert "non-authorizing" in collapsed

    rows = _risk_table_rows(text)
    for risk_id in ("R-001", "R-002", "R-007"):
        _, status_cell = rows[risk_id]
        assert "mapped-by-derived-evidence" in status_cell
        assert status_cell.strip() != "mapped"

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


CV3C_REPORT_HEADING = "### Static defensive visibility report contract v0 (SLICE-CV-3c)"
CV3C_BLOCK_ANCHOR = "CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_V0=true"
INPUT_ARTIFACT_MODULE = (
    "tests/ci/test_cybersecurity_visibility_r_pending_input_artifact_contract_v0.py"
)


def _cv3c_report_block(text: str) -> str:
    start = text.index(CV3C_REPORT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def test_cybersecurity_visibility_cv3c_mapping_guard_report_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _cv3c_report_block(text)
    collapsed = block.lower()

    assert CV3C_BLOCK_ANCHOR in block
    assert THIS_MODULE in block
    assert INPUT_ARTIFACT_MODULE in block
    assert DERIVED_MAPPING_PLAN_PROGRESS_MODULE in block
    assert "definitive" in collapsed
    assert "blocked" in collapsed
    assert "INPUT_JSONL_PROVIDED=false" in block
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in block
    assert "static/derived/read-only only" in collapsed
    assert "non-authorizing" in collapsed

    artifact_text = (REPO_ROOT / INPUT_ARTIFACT_MODULE).read_text(encoding="utf-8")
    assert CV3C_BLOCK_ANCHOR in artifact_text or CV3C_REPORT_HEADING in artifact_text
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_archive_adoption_mapping_guard_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    adoption_block = _block_containing(text, ADOPTION_BLOCK_ANCHOR)
    adoption_values = _machine_line_values(adoption_block)

    assert ADOPTION_HEADING in text
    assert ARCHIVE_FULL_LOSSLESS_SHA256 in text
    assert adoption_values["NOT_ORIGINAL_TMP_FULL_LOSSLESS"] == "true"
    assert adoption_values["DERIVED_ONLY_USED_AS_AUTHORITY"] == "false"
    assert adoption_values["INPUT_JSONL_PROVIDED"] == "false"
    assert adoption_values["LOSSLESS_JSONL_RECOVERY"] == "false"
    assert adoption_values["DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED"] == "true"
    assert adoption_values["FORBIDS_ORIGINAL_TMP_RECOVERY_CLAIM"] == "true"

    assert "Pending R-001/R-002/R-007 — mapping guard v0" in text
    assert "cannot be documented or tested as **recovered**" in text

    rows = _risk_table_rows(text)
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )

    assert "original recovered" not in collapsed.replace("not be claimed recovered", "")
    assert "does not** use `DERIVED_LOSSLESS_RISK_CANDIDATES_FROM_CSC_RCHAIN_EVIDENCE.jsonl` as authority" in text
