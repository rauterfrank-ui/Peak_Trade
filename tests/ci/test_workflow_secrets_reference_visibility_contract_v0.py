"""Static visibility contract for GitHub workflow secrets, vars, and braced contexts.

Parses workflow YAML files as UTF-8 text only. Never reads credential payloads
or repository variable values, never calls GitHub APIs, never dispatches
workflows, never executes scripts, and never touches runtime, scheduler, daemon,
paper/shadow/testnet/live, broker/exchange, or order-submission paths.

This contract freezes the current workflow `secrets.*` reference inventory as
an owner-review surface. It does not require workflow YAML changes and does
not treat the current set as a new hard failure without owner decision.

Follow-up (github_actions_vars_context_visibility_v1): collects repo-local
`vars.<NAME>` identifier references (expression or `${{ }}` forms) as a sorted
inventory only; new vars references do not fail CI because no frozen vars allowlist
is enforced here.

Follow-up (github_actions_braced_env_matrix_expression_visibility_v1): braced
`${{ env.NAME }}` names are normalized uppercase (like secrets/vars); braced
`${{ matrix.NAME }}` axis keys preserve YAML spelling (may include hyphens).

Follow-up (github_actions_braced_needs_github_event_inputs_visibility_v1): braced
`${{ needs.<segment> ... }}` inventories only the first path segment after `needs.`
(job id / needs-key spelling preserved); braced `${{ github.event.inputs.NAME }}`
lists dispatch input names only (no values).
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

SECRET_REF_RX = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}", re.I)
LOOSE_SECRETS_RX = re.compile(r"secrets\.", re.I)

# Matches `vars.NAME` in `${{ vars.NAME }}`, `if: vars.NAME == ...`, etc.
VAR_NAME_RX = re.compile(r"(?<![A-Za-z0-9_])vars\.([A-Za-z0-9_]+)", re.I)

ENV_BRACED_RX = re.compile(r"\$\{\{\s*env\.([A-Za-z0-9_]+)\s*\}\}", re.I)
MATRIX_BRACED_RX = re.compile(r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}")

# First segment after `needs.` inside a braced expression (job id / needs key).
NEEDS_BRACED_SEGMENT_RX = re.compile(r"\$\{\{\s*needs\.([A-Za-z0-9_-]+)")
GITHUB_EVENT_INPUTS_BRACED_RX = re.compile(
    r"\$\{\{\s*github\.event\.inputs\.([A-Za-z0-9_-]+)\s*\}\}"
)

KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES = frozenset(
    {
        "add-to-project.yml",
        "aiops-promptfoo-evals.yml",
        "ci-export-pack-download-verify.yml",
        "ci-operator-verify-registry.yml",
        "ci-scheduled-paper-and-export-smoke.yml",
        "ci.yml",
        "cursor_auto_automerge.yml",
        "cursor_auto_pr.yml",
        "infostream-automation.yml",
        "market_outlook_automation.yml",
        "paper_session_audit_evidence.yml",
        "paper_tests_audit_evidence.yml",
        "pr-head-sha-required-checks-liveness-guard.yml",
        "prcc-aws-export-smoke.yml",
        "prcd-aws-export-write-smoke.yml",
    }
)

KNOWN_SECRET_REFERENCE_NAMES = frozenset(
    {
        "ADD_TO_PROJECT_PAT",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "PT_EXPORT_ID",
        "PT_EXPORT_PREFIX",
        "PT_EXPORT_REMOTE",
        "PT_RCLONE_CONF_B64",
    }
)


def _workflow_files() -> list[Path]:
    return sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in WORKFLOW_ROOT.glob(pattern)
        if path.is_file()
    )


def _workflow_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _secret_reference_names(text: str) -> set[str]:
    return set(m.upper() for m in SECRET_REF_RX.findall(text))


def _workflows_with_secrets_references() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _secret_reference_names(text)
        if names or LOOSE_SECRETS_RX.search(text):
            result[workflow.name] = names

    return result


def _var_reference_names(text: str) -> set[str]:
    return {m.upper() for m in VAR_NAME_RX.findall(text)}


def _workflows_with_vars_references() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _var_reference_names(text)
        if names:
            result[workflow.name] = names

    return result


def _sorted_vars_reference_inventory() -> dict[str, list[str]]:
    raw = _workflows_with_vars_references()
    return {wf: sorted(names) for wf, names in sorted(raw.items())}


def _braced_env_reference_names(text: str) -> set[str]:
    return {m.upper() for m in ENV_BRACED_RX.findall(text)}


def _workflows_with_braced_env_references() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _braced_env_reference_names(text)
        if names:
            result[workflow.name] = names

    return result


def _sorted_braced_env_reference_inventory() -> dict[str, list[str]]:
    raw = _workflows_with_braced_env_references()
    return {wf: sorted(names) for wf, names in sorted(raw.items())}


def _braced_matrix_reference_names(text: str) -> set[str]:
    return set(MATRIX_BRACED_RX.findall(text))


def _workflows_with_braced_matrix_references() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _braced_matrix_reference_names(text)
        if names:
            result[workflow.name] = names

    return result


def _sorted_braced_matrix_reference_inventory() -> dict[str, list[str]]:
    raw = _workflows_with_braced_matrix_references()
    return {wf: sorted(names) for wf, names in sorted(raw.items())}


def _braced_needs_segment_names(text: str) -> set[str]:
    return set(NEEDS_BRACED_SEGMENT_RX.findall(text))


def _workflows_with_braced_needs_segments() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _braced_needs_segment_names(text)
        if names:
            result[workflow.name] = names

    return result


def _sorted_braced_needs_segment_inventory() -> dict[str, list[str]]:
    raw = _workflows_with_braced_needs_segments()
    return {wf: sorted(names) for wf, names in sorted(raw.items())}


def _braced_github_event_inputs_names(text: str) -> set[str]:
    return set(GITHUB_EVENT_INPUTS_BRACED_RX.findall(text))


def _workflows_with_braced_github_event_inputs() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}

    for workflow in _workflow_files():
        text = _workflow_text(workflow)
        names = _braced_github_event_inputs_names(text)
        if names:
            result[workflow.name] = names

    return result


def _sorted_braced_github_event_inputs_inventory() -> dict[str, list[str]]:
    raw = _workflows_with_braced_github_event_inputs()
    return {wf: sorted(names) for wf, names in sorted(raw.items())}


def test_workflow_secrets_reference_visibility_contract_has_workflows_to_check() -> None:
    workflows = _workflow_files()

    assert WORKFLOW_ROOT.exists()
    assert workflows


def test_workflow_secrets_reference_visibility_contract_module_avoids_execution_hooks() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")
    import_lines = [
        line.strip()
        for line in test_text.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    forbidden_import_prefixes = [
        "import os",
        "from os",
        "import subprocess",
        "from subprocess",
        "import runpy",
        "from runpy",
        "import importlib",
        "from importlib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "import urllib",
        "from urllib",
        "import socket",
        "from socket",
    ]

    found = [
        prefix
        for prefix in forbidden_import_prefixes
        if any(line.startswith(prefix) for line in import_lines)
    ]
    assert not found, f"static workflow contract must not import execution/network hooks: {found}"


def test_workflow_secrets_reference_visibility_contract_classifies_current_workflow_set() -> None:
    current = frozenset(_workflows_with_secrets_references())

    assert current == KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES


def test_workflow_secrets_reference_visibility_contract_classifies_current_secret_names() -> None:
    current_names: set[str] = set()
    for names in _workflows_with_secrets_references().values():
        current_names.update(names)

    assert current_names == KNOWN_SECRET_REFERENCE_NAMES


def test_workflow_secrets_reference_visibility_contract_known_sets_stay_documentary() -> None:
    """Known sets are owner-review surfaces, not workflow-change mandates."""
    assert len(KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES) == 15
    assert len(KNOWN_SECRET_REFERENCE_NAMES) == 7


def test_workflow_secrets_reference_visibility_contract_requires_names_for_known_set() -> None:
    current = _workflows_with_secrets_references()

    missing = [
        workflow for workflow in KNOWN_WORKFLOWS_WITH_SECRETS_REFERENCES if workflow not in current
    ]

    assert not missing, f"known workflows lost secrets-reference visibility: {missing}"


def test_workflow_secrets_reference_visibility_contract_never_checks_secret_values() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8").lower()

    forbidden_value_access_markers = [
        " ".join(("gh", "secret", "list")),
        " ".join(("gh", "secret", "view")),
        " ".join(("gh", "api")),
        " ".join(("secrets", "get")),
        "".join(("get_secret", "_value")),
    ]

    found = [marker for marker in forbidden_value_access_markers if marker in test_text]
    assert not found, f"contract must never access secret values: {found}"


def test_workflow_secrets_reference_visibility_contract_retains_static_local_scope() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8")

    forbidden_fragments = [
        "".join(("subprocess", ".")),
        "".join(("os", ".system")),
        "".join(("runpy", ".")),
        "".join(("importlib", ".import_module")),
        "".join(("requests", ".")),
        "".join(("httpx", ".")),
        "".join(("urllib", ".")),
        "".join(("socket", ".")),
        " ".join(("gh", "workflow", "run")),
        " ".join(("gh", "api")),
    ]

    found = [fragment for fragment in forbidden_fragments if fragment in test_text]
    assert not found, f"contract must remain static/local-only: {found}"


_SYNTHETIC_VARS_SNIPPET = (
    "jobs:\n"
    "  x:\n"
    "    if: vars.FEATURE_TOGGLE == 'true'\n"
    "    env:\n"
    "      A: ${{ vars.MY_REPO_VAR }}\n"
)


def test_github_actions_vars_context_visibility_v1_parser_detects_expression_and_braced_forms() -> (
    None
):
    names = _var_reference_names(_SYNTHETIC_VARS_SNIPPET)
    assert names == {"FEATURE_TOGGLE", "MY_REPO_VAR"}


def test_github_actions_vars_context_visibility_v1_inventory_sorted_deterministic() -> None:
    first = _sorted_vars_reference_inventory()
    second = _sorted_vars_reference_inventory()
    assert first == second
    assert list(first.keys()) == sorted(first.keys())
    for names in first.values():
        assert names == sorted(names)


def test_github_actions_vars_context_visibility_v1_inventory_shape() -> None:
    inventory = _sorted_vars_reference_inventory()

    assert inventory
    for filename, names in inventory.items():
        assert filename.endswith((".yml", ".yaml"))
        assert names
        assert len(names) == len(set(names))
        for name in names:
            assert name == name.upper()
            assert name.isascii()
            assert name.replace("_", "").isalnum()


def test_github_actions_vars_context_visibility_v1_ci_scheduled_smoke_lists_scheduling_vars() -> (
    None
):
    inventory = _sorted_vars_reference_inventory()
    row = inventory.get("ci-scheduled-paper-and-export-smoke.yml")
    assert row is not None
    assert "PT_SCHEDULED_PAPER_TESTS_ENABLED" in row
    assert "PT_SCHEDULED_EXPORT_VERIFY_ENABLED" in row


def test_github_actions_vars_context_visibility_v1_never_checks_variable_values() -> None:
    test_text = Path(__file__).read_text(encoding="utf-8").lower()

    forbidden_value_access_markers = [
        " ".join(("gh", "variable", "get")),
        " ".join(("gh", "api")),
    ]

    found = [marker for marker in forbidden_value_access_markers if marker in test_text]
    assert not found, f"contract must not resolve GitHub variable values: {found}"


_SYNTHETIC_BRACED_ENV_MATRIX_SNIPPET = (
    "jobs:\n"
    "  j:\n"
    "    env:\n"
    "      X: ${{ env.MY_ENV_VAR }}\n"
    "    steps:\n"
    "      - run: echo '${{ matrix.shard }}' '${{ matrix.python-version }}'\n"
)


def test_github_actions_braced_env_matrix_expression_visibility_v1_parser_synthetic_snippet() -> (
    None
):
    assert _braced_env_reference_names(_SYNTHETIC_BRACED_ENV_MATRIX_SNIPPET) == {"MY_ENV_VAR"}
    assert _braced_matrix_reference_names(_SYNTHETIC_BRACED_ENV_MATRIX_SNIPPET) == {
        "shard",
        "python-version",
    }


def test_github_actions_braced_env_matrix_expression_visibility_v1_inventory_deterministic() -> (
    None
):
    env_first = _sorted_braced_env_reference_inventory()
    env_second = _sorted_braced_env_reference_inventory()
    assert env_first == env_second
    assert list(env_first.keys()) == sorted(env_first.keys())
    for names in env_first.values():
        assert names == sorted(names)

    matrix_first = _sorted_braced_matrix_reference_inventory()
    matrix_second = _sorted_braced_matrix_reference_inventory()
    assert matrix_first == matrix_second
    assert list(matrix_first.keys()) == sorted(matrix_first.keys())
    for names in matrix_first.values():
        assert names == sorted(names)


def test_github_actions_braced_env_matrix_expression_visibility_v1_inventory_shape() -> None:
    env_inv = _sorted_braced_env_reference_inventory()
    matrix_inv = _sorted_braced_matrix_reference_inventory()

    assert env_inv
    assert matrix_inv

    for filename, names in env_inv.items():
        assert filename.endswith((".yml", ".yaml"))
        assert names
        assert len(names) == len(set(names))
        for name in names:
            assert name == name.upper()
            assert name.isascii()
            assert name.replace("_", "").isalnum()

    for filename, names in matrix_inv.items():
        assert filename.endswith((".yml", ".yaml"))
        assert names
        assert len(names) == len(set(names))
        for name in names:
            assert name.isascii()
            assert re.fullmatch(r"[A-Za-z0-9_-]+", name)


def test_github_actions_braced_env_matrix_expression_visibility_v1_aiops_trend_ledger_env_smoke() -> (
    None
):
    inventory = _sorted_braced_env_reference_inventory()
    row = inventory.get("aiops-trend-ledger-from-seed.yml")
    assert row is not None
    assert "ARTIFACT_NAME" in row


def test_github_actions_braced_env_matrix_expression_visibility_v1_ci_matrix_smoke() -> None:
    inventory = _sorted_braced_matrix_reference_inventory()
    row = inventory.get("ci.yml")
    assert row is not None
    assert "python-version" in row


_SYNTHETIC_BRACED_NEEDS_GITHUB_EVENT_INPUTS_SNIPPET = (
    "jobs:\n"
    "  x:\n"
    "    steps:\n"
    "      - run: |\n"
    "          echo '${{ needs.fast-lane.result }}'\n"
    "          echo '${{ needs.my-job.outputs.shard }}'\n"
    "          echo '${{ github.event.inputs.confirm_token }}'\n"
)


def test_github_actions_braced_needs_github_event_inputs_visibility_v1_parser_synthetic_snippet() -> (
    None
):
    text = _SYNTHETIC_BRACED_NEEDS_GITHUB_EVENT_INPUTS_SNIPPET
    assert _braced_needs_segment_names(text) == {"fast-lane", "my-job"}
    assert _braced_github_event_inputs_names(text) == {"confirm_token"}


def test_github_actions_braced_needs_github_event_inputs_visibility_v1_inventory_deterministic() -> (
    None
):
    needs_first = _sorted_braced_needs_segment_inventory()
    needs_second = _sorted_braced_needs_segment_inventory()
    assert needs_first == needs_second
    assert list(needs_first.keys()) == sorted(needs_first.keys())
    for names in needs_first.values():
        assert names == sorted(names)

    gin_first = _sorted_braced_github_event_inputs_inventory()
    gin_second = _sorted_braced_github_event_inputs_inventory()
    assert gin_first == gin_second
    assert list(gin_first.keys()) == sorted(gin_first.keys())
    for names in gin_first.values():
        assert names == sorted(names)


def test_github_actions_braced_needs_github_event_inputs_visibility_v1_inventory_shape() -> None:
    needs_inv = _sorted_braced_needs_segment_inventory()
    gin_inv = _sorted_braced_github_event_inputs_inventory()

    assert needs_inv
    assert gin_inv

    for filename, names in needs_inv.items():
        assert filename.endswith((".yml", ".yaml"))
        assert names
        assert len(names) == len(set(names))
        for name in names:
            assert name.isascii()
            assert re.fullmatch(r"[A-Za-z0-9_-]+", name)

    for filename, names in gin_inv.items():
        assert filename.endswith((".yml", ".yaml"))
        assert names
        assert len(names) == len(set(names))
        for name in names:
            assert name.isascii()
            assert re.fullmatch(r"[A-Za-z0-9_-]+", name)


def test_github_actions_braced_needs_github_event_inputs_visibility_v1_ci_needs_segments_smoke() -> (
    None
):
    inventory = _sorted_braced_needs_segment_inventory()
    row = inventory.get("ci.yml")
    assert row is not None
    assert "changes" in row
    assert "fast-lane" in row


def test_github_actions_braced_needs_github_event_inputs_visibility_v1_prcd_github_event_inputs_smoke() -> (
    None
):
    inventory = _sorted_braced_github_event_inputs_inventory()
    row = inventory.get("prcd-aws-export-write-smoke.yml")
    assert row is not None
    assert "confirm_token" in row


def test_cybersecurity_visibility_chain_owner_registry_crosslink_v0() -> None:
    """CI audit anchor + DOCS_TRUTH_MAP registry pointers for Cybersecurity Visibility Chain."""
    ci_audit_text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    ci_collapsed = ci_audit_text.lower()
    truth_map_text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    truth_collapsed = truth_map_text.lower()

    assert "Cybersecurity Visibility Chain" in ci_audit_text
    assert "CI_AUDIT_KNOWN_ISSUES.md" in ci_audit_text
    assert "non-authorizing" in ci_collapsed
    assert "broker/exchange" in ci_collapsed or "broker" in ci_collapsed

    for owner in (
        "test_workflow_secrets_reference_visibility_contract_v0.py",
        "test_workflow_write_permissions_visibility_contract_v0.py",
        "test_workflow_network_gh_marker_visibility_contract_v0.py",
        "test_workflow_manual_dispatch_sensitive_surface_contract_v0.py",
        "test_workflow_artifact_retention_visibility_contract_v0.py",
        "test_workflow_permission_boundary_visibility_v1.py",
        "test_webui_api_security_headers_visibility_contract_v0.py",
        "test_workflows_no_pull_request_target_contract_v0.py",
    ):
        assert owner in ci_audit_text

    for risk_id, owner_module in (
        ("R-003", "test_run_sample_size_ramp_script_contract_v0.py"),
        ("R-004", "test_run_testnet_evidence_flow_v2_script_contract_v0.py"),
        ("R-005", "test_knowledge_prod_smoke_script.py"),
        ("R-006", "test_prcd_aws_export_write_smoke_workflow_contract_v0.py"),
    ):
        assert risk_id in ci_audit_text
        assert owner_module in ci_audit_text

    for derived_id, owner_module in (
        ("R-001", "test_workflow_write_permissions_visibility_contract_v0.py"),
        ("R-002", "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"),
        ("R-007", Path(__file__).name),
    ):
        assert derived_id in ci_audit_text
        assert owner_module in ci_audit_text
        assert "mapped" in ci_collapsed
        assert "DERIVED-CYBER-" in ci_audit_text

    assert "INPUT_JSONL_PROVIDED=true" in ci_audit_text

    assert "2026-05-23" in truth_map_text
    assert "Cybersecurity Visibility Chain" in truth_map_text
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map_text
    assert Path(__file__).name in truth_map_text
    assert "non-authorizing" in truth_collapsed
    assert "r-003" in truth_collapsed or "R-003" in truth_map_text


WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_TESTS = (
    REPO_ROOT
    / "tests/ci/test_cybersecurity_visibility_repo_static_histogram_workflow_secrets_visibility_crosslink_v0.py"
)
WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_MARKER = (
    "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_WORKFLOW_SECRETS_VISIBILITY_CROSSLINK_V0=true"
)


def test_workflow_secrets_owner_crosslinks_cybersecurity_histogram_v0() -> None:
    """Reciprocal static crosslink to workflow_secrets_visibility histogram owner."""
    ci_audit_text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    ci_collapsed = ci_audit_text.lower()

    assert WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_MARKER in ci_audit_text
    assert "workflow_secrets_visibility" in ci_audit_text
    assert "INPUT_JSONL_PROVIDED=true" in ci_audit_text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=false" in ci_audit_text
    assert WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_TESTS.is_file()

    crosslink_text = WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_TESTS.read_text(encoding="utf-8")
    assert Path(__file__).name in crosslink_text
    assert WORKFLOW_SECRETS_HISTOGRAM_CROSSLINK_MARKER in crosslink_text
    assert "tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py" in crosslink_text

    assert "secret access approved" not in ci_collapsed
    assert "workflow_dispatch executed" not in ci_collapsed
    assert "mapping completed" not in ci_collapsed
