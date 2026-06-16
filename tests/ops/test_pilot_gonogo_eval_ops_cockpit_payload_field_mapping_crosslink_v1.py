"""Static reciprocal crosslink guard for Pilot Go/No-Go Eval ↔ Ops Cockpit Payload field mapping."""

from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PILOT_SLICE_DOC = ROOT / "docs" / "ops" / "specs" / "PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_SCRIPT = ROOT / "scripts" / "ops" / "pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST = ROOT / "tests" / "ops" / "test_pilot_go_no_go_eval_v1.py"
OPS_COCKPIT_MODULE = ROOT / "src" / "webui" / "ops_cockpit.py"
PAYLOAD_CONTRACT_TEST = ROOT / "tests" / "ops" / "test_ops_cockpit_payload_top_level_contract.py"
ROW7_GUARD_TEST = (
    ROOT / "tests" / "ops" / "test_pilot_fee_slippage_conservative_assumptions_crosslink_v1.py"
)
ROWS81011_GUARD_TEST = (
    ROOT / "tests" / "ops" / "test_pilot_gonogo_rows_8_10_11_exclusion_crosslink_v1.py"
)
BOUNDARY_GUARD_TEST = (
    ROOT
    / "tests"
    / "ops"
    / "test_pilot_gonogo_checklist_operational_slice_eval_scope_boundary_crosslink_v1.py"
)
TRUTH_MAP = ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
TEST_REL = "tests/ops/test_pilot_gonogo_eval_ops_cockpit_payload_field_mapping_crosslink_v1.py"
PILOT_SLICE_REL = "docs/ops/specs/PILOT_GO_NO_GO_OPERATIONAL_SLICE.md"
PILOT_EVAL_REL = "scripts/ops/pilot_go_no_go_eval_v1.py"
PILOT_EVAL_TEST_REL = "tests/ops/test_pilot_go_no_go_eval_v1.py"
OPS_COCKPIT_MODULE_REL = "src/webui/ops_cockpit.py"
PAYLOAD_CONTRACT_TEST_REL = "tests/ops/test_ops_cockpit_payload_top_level_contract.py"
ROW7_GUARD_REL = "tests/ops/test_pilot_fee_slippage_conservative_assumptions_crosslink_v1.py"
ROWS81011_GUARD_REL = "tests/ops/test_pilot_gonogo_rows_8_10_11_exclusion_crosslink_v1.py"
BOUNDARY_GUARD_REL = (
    "tests/ops/test_pilot_gonogo_checklist_operational_slice_eval_scope_boundary_crosslink_v1.py"
)
CROSSLINK_PACKAGE_MARKER = "PILOT_GONOGO_EVAL_OPS_COCKPIT_PAYLOAD_FIELD_MAPPING_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
EVALUATED_ROWS = (1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15)
ROW_PAYLOAD_FIELD_HINTS: dict[int, tuple[str, ...]] = {
    1: ("policy_state", "operator_state", "guard_state"),
    2: ("policy_state", "kill_switch_active", "incident_state"),
    3: ("policy_state", "action"),
    4: ("policy_state", "blocked", "incident_state", "requires_operator_attention"),
    5: ("exposure_state", "caps_configured"),
    6: ("guard_state", "treasury_separation"),
    9: ("stale_state",),
    12: ("evidence_state",),
    13: ("dependencies_state",),
    14: ("human_supervision_state",),
    15: ("policy_state", "incident_state"),
}
EVAL_TOP_LEVEL_PAYLOAD_KEYS = frozenset(
    {
        "policy_state",
        "incident_state",
        "exposure_state",
        "guard_state",
        "stale_state",
        "evidence_state",
        "dependencies_state",
        "human_supervision_state",
    }
)
GET_PAYLOAD_RX = re.compile(r'_get\(payload,\s*"([^"]+)"')


def _docs_truth_map_chronicle_row(truth_map: str, needle: str) -> str:
    row_start = truth_map.index(needle)
    row_end = truth_map.index("\n", row_start)
    return truth_map[row_start:row_end]


def _load_pilot_eval_module():
    spec = importlib.util.spec_from_file_location("pilot_go_no_go_eval_v1", PILOT_EVAL_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _slice_row_lines(text: str) -> dict[int, str]:
    rows: dict[int, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\| (\d+) \|", line)
        if match:
            rows[int(match.group(1))] = line
    return rows


def test_crosslink_package_marker_present_v1() -> None:
    assert CROSSLINK_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


def test_operational_slice_documents_row_payload_field_mappings_v1() -> None:
    text = PILOT_SLICE_DOC.read_text(encoding="utf-8")
    assert PILOT_SLICE_DOC.is_file()
    assert "status: DRAFT" in text
    assert "DOCS_TOKEN_PILOT_GO_NO_GO_OPERATIONAL_SLICE" in text
    assert "build_ops_cockpit_payload()" in text
    assert OPS_COCKPIT_MODULE_REL in text

    row_lines = _slice_row_lines(text)
    assert set(row_lines) == set(range(1, 16))
    for row_num in EVALUATED_ROWS:
        line = row_lines[row_num]
        for hint in ROW_PAYLOAD_FIELD_HINTS[row_num]:
            assert hint in line, f"row {row_num} missing payload hint {hint!r}"


def test_pilot_eval_models_11_cockpit_rows_and_payload_paths_v1() -> None:
    mod = _load_pilot_eval_module()
    row_numbers = [num for num, _area, _fn in mod.ROWS]
    assert len(row_numbers) == 11
    assert row_numbers == list(EVALUATED_ROWS)

    pilot_eval_text = PILOT_EVAL_SCRIPT.read_text(encoding="utf-8")
    assert "11 cockpit-based rows" in pilot_eval_text
    assert "build_ops_cockpit_payload" in pilot_eval_text
    assert PILOT_SLICE_REL.split("/")[-1].replace(".md", "") in pilot_eval_text

    referenced_keys = set(GET_PAYLOAD_RX.findall(pilot_eval_text))
    assert referenced_keys == EVAL_TOP_LEVEL_PAYLOAD_KEYS

    pilot_eval_test_text = PILOT_EVAL_TEST.read_text(encoding="utf-8")
    assert 'len(data["rows"]) == 11' in pilot_eval_test_text


def test_ops_cockpit_payload_top_level_contract_covers_eval_paths_v1() -> None:
    contract_text = PAYLOAD_CONTRACT_TEST.read_text(encoding="utf-8")
    assert PAYLOAD_CONTRACT_TEST.is_file()
    assert "SLICE-OC-2" in contract_text
    assert "build_ops_cockpit_payload" in contract_text
    for key in EVAL_TOP_LEVEL_PAYLOAD_KEYS:
        assert key in contract_text

    ops_cockpit_text = OPS_COCKPIT_MODULE.read_text(encoding="utf-8")
    assert OPS_COCKPIT_MODULE.is_file()
    assert "def build_ops_cockpit_payload" in ops_cockpit_text


def test_row_boundary_and_exclusion_guards_referenced_v1() -> None:
    for path in (ROW7_GUARD_TEST, ROWS81011_GUARD_TEST, BOUNDARY_GUARD_TEST):
        assert path.is_file()
    row7_text = ROW7_GUARD_TEST.read_text(encoding="utf-8")
    rows81011_text = ROWS81011_GUARD_TEST.read_text(encoding="utf-8")
    boundary_text = BOUNDARY_GUARD_TEST.read_text(encoding="utf-8")
    assert (
        "PILOT_FEE_SLIPPAGE_CONSERVATIVE_ASSUMPTIONS_CI_AUDIT_PILOT_GONOGO_BACKTEST_SMOKE_RECIPROCAL_CROSSLINK_V1=true"
        in row7_text
    )
    assert (
        "PILOT_GONOGO_ROWS_8_10_11_EXCLUSION_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in rows81011_text
    )
    assert (
        "PILOT_GONOGO_CHECKLIST_OPERATIONAL_SLICE_EVAL_SCOPE_BOUNDARY_CI_AUDIT_DOCS_TRUTH_MAP_RECIPROCAL_CROSSLINK_V1=true"
        in boundary_text
    )


def test_docs_truth_map_field_mapping_chronicle_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    row = _docs_truth_map_chronicle_row(
        truth_map,
        "Pilot Go/No-Go Eval ↔ Ops Cockpit Payload Field Mapping CI_AUDIT reciprocal crosslink guard v1",
    )
    for required in (
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        OPS_COCKPIT_MODULE_REL,
        PAYLOAD_CONTRACT_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
        BOUNDARY_GUARD_REL,
        TEST_REL,
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_11_COCKPIT_ROWS=true",
        "PILOT_OPERATIONAL_SLICE_ROW_PAYLOAD_MAPPINGS_DOCUMENTED=true",
        "PILOT_EVAL_PAYLOAD_PATHS_ALIGNED_WITH_SLICE=true",
        "OPS_COCKPIT_PAYLOAD_TOP_LEVEL_CONTRACT_ALIGNED=true",
        "OPS_COCKPIT_PAYLOAD_SEMANTIC_TOUCHED=false",
        "DRAFT_POSTURE_CHANGED=false",
        "non-authorizing",
        "NEW_COCKPIT_ROW_CREATED=false",
    ):
        assert required.lower() in row.lower()


def test_ci_audit_field_mapping_reciprocal_crosslink_v1() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    section_start = ci_audit.index(
        "## Pilot Go/No-Go Eval ↔ Ops Cockpit Payload Field Mapping CI_AUDIT reciprocal crosslink — docs/tests-only guard v1"
    )
    section_text = ci_audit[section_start : section_start + 5500]
    for required in (
        CROSSLINK_PACKAGE_MARKER,
        "PILOT_EVAL_11_COCKPIT_ROWS=true",
        "PILOT_OPERATIONAL_SLICE_ROW_PAYLOAD_MAPPINGS_DOCUMENTED=true",
        "PILOT_EVAL_PAYLOAD_PATHS_ALIGNED_WITH_SLICE=true",
        "OPS_COCKPIT_PAYLOAD_TOP_LEVEL_CONTRACT_ALIGNED=true",
        "PILOT_ROW7_GUARD_REFERENCED=true",
        "PILOT_ROWS_8_10_11_GUARD_REFERENCED=true",
        "PILOT_EVAL_SCOPE_BOUNDARY_GUARD_REFERENCED=true",
        "OPS_COCKPIT_PAYLOAD_SEMANTIC_TOUCHED=false",
        "DRAFT_POSTURE_CHANGED=false",
        "PILOT_GO_NO_GO_AUTHORITY_CREATED=false",
        "NEW_COCKPIT_ROW_CREATED=false",
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        OPS_COCKPIT_MODULE_REL,
        PAYLOAD_CONTRACT_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
        BOUNDARY_GUARD_REL,
        TEST_REL,
        "build_ops_cockpit_payload()",
        "SLICE-OC-2",
        "11 cockpit rows",
        "non-authorizing",
    ):
        assert required.lower() in section_text.lower()


def test_canonical_owners_referenced_in_docs_v1() -> None:
    truth_map = TRUTH_MAP.read_text(encoding="utf-8")
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    for rel in (
        PILOT_SLICE_REL,
        PILOT_EVAL_REL,
        PILOT_EVAL_TEST_REL,
        OPS_COCKPIT_MODULE_REL,
        PAYLOAD_CONTRACT_TEST_REL,
        ROW7_GUARD_REL,
        ROWS81011_GUARD_REL,
        BOUNDARY_GUARD_REL,
        TEST_REL,
    ):
        assert rel in truth_map
        assert rel in ci_audit


def test_guard_module_is_offline_static_only_v1() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    )
    forbidden = {"subprocess", "socket", "requests", "httpx", "urllib"}
    assert forbidden.isdisjoint(imports)
