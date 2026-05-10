"""Static contract tests for .github/workflows/prcd-aws-export-write-smoke.yml.

Parses workflow text only. Never dispatches workflows, never runs aws_export_write_smoke.py,
never accesses secret values, and never performs network I/O from this module.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "prcd-aws-export-write-smoke.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_prcd_aws_export_write_smoke_workflow_contract_target_present() -> None:
    assert WORKFLOW.exists()
    assert WORKFLOW.is_file()


def test_prcd_aws_export_write_smoke_workflow_contract_module_avoids_execution_hooks() -> None:
    """Keep this module read-only (no subprocess/HTTP client imports spelled in source)."""
    lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    stripped = [ln.strip() for ln in lines]
    banned_starts = (
        "import subprocess",
        "from subprocess ",
        "from subprocess\t",
        "import runpy",
        "from runpy ",
        "from runpy\t",
        "import importlib",
        "from importlib ",
        "from importlib\t",
        "import urllib",
        "from urllib",
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
    )
    hits = [ln for ln in stripped if ln.startswith(banned_starts)]
    assert not hits, f"unexpected execution/network-oriented imports: {hits}"


def test_prcd_aws_export_write_smoke_workflow_contract_preserves_manual_dispatch_surface() -> None:
    text = _workflow_text()

    assert "workflow_dispatch:" in text
    assert "inputs:" in text


def test_prcd_aws_export_write_smoke_workflow_contract_has_explicit_permissions_block() -> None:
    text = _workflow_text()

    assert "permissions:" in text
    assert "contents:" in text

    forbidden_broad_permissions = (
        "contents: write",
        "actions: write",
        "packages: write",
        "pull-requests: write",
        "id-token: write",
    )

    found = [fragment for fragment in forbidden_broad_permissions if fragment in text]
    assert not found, f"workflow should not request broad write permissions: {found}"


def test_prcd_aws_export_write_smoke_workflow_contract_keeps_secret_references_explicit() -> None:
    text = _workflow_text()

    assert "secrets." in text
    assert "AWS" in text


def test_prcd_aws_export_write_smoke_workflow_contract_does_not_hardcode_secret_values() -> None:
    text = _workflow_text().lower()

    forbidden_secret_value_markers = (
        "aws_access_key_id=",
        "aws_secret_access_key=",
        "aws_session_token=",
        "-----begin private key-----",
        "bearer ",
    )

    found = [marker for marker in forbidden_secret_value_markers if marker in text]
    assert not found, f"workflow must not hardcode secret-like values: {found}"


def test_prcd_aws_export_write_smoke_workflow_contract_preserves_artifact_surface() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact" in text
    assert "retention-days" in text


def test_prcd_aws_export_write_smoke_workflow_contract_preserves_frozen_observability_tolerances() -> (
    None
):
    """R-006 observability: softened failure handling stays visible in YAML."""
    text = _workflow_text()
    assert "|| true" in text


def test_prcd_aws_export_write_smoke_workflow_contract_does_not_dispatch_other_workflows() -> None:
    text = _workflow_text().lower()

    forbidden_fragments = (
        "gh workflow run",
        "gh run rerun",
        "workflow_dispatch -f",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"workflow must not dispatch other workflows: {found}"


def test_prcd_aws_export_write_smoke_workflow_contract_does_not_directly_submit_trading_orders() -> (
    None
):
    text = _workflow_text().lower()

    forbidden_fragments = (
        "create_order(",
        ".create_order",
        "submit_order(",
        ".submit_order",
        "place_order(",
        ".place_order",
        "market_buy(",
        "market_sell(",
        "private_post_order",
        "futures_create_order",
        "binance.create_order",
        "exchange.create_order",
        "ccxt.",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"workflow must not directly submit trading orders: {found}"


def test_prcd_aws_export_write_smoke_workflow_contract_does_not_use_unscoped_destructive_cleanup() -> (
    None
):
    text = _workflow_text().lower()

    forbidden_fragments = (
        "rm -rf /",
        "rm -rf $github_workspace",
        "rm -rf ${github_workspace}",
        "rm -rf .git",
        "git clean -fdx",
        "git reset --hard",
    )

    found = [fragment for fragment in forbidden_fragments if fragment in text]
    assert not found, f"workflow contains unscoped destructive cleanup: {found}"


def test_prcd_aws_export_write_smoke_workflow_contract_keeps_no_runtime_authority_boundary_visible() -> (
    None
):
    text = _workflow_text().lower()

    authority_markers = (
        "live",
        "testnet",
        "broker",
        "exchange",
        "order",
    )

    if not any(marker in text for marker in authority_markers):
        return

    guard_markers = (
        "dry",
        "smoke",
        "audit",
        "export",
        "evidence",
        "artifact",
        "verify",
    )

    present_guards = [marker for marker in guard_markers if marker in text]
    assert present_guards, (
        "sensitive authority terms require visible non-runtime/smoke/export guard vocabulary"
    )
