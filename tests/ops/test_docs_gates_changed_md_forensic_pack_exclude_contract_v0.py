"""Changed-mode exclude contract for the V2/V2.1 preservation pack leaf.

Proves both product-docs gates skip Markdown under exactly:

    forensic/lossless_structural_projection_v2_v2_1_pack_v1/

and keep gating docs/**, sibling forensic/**, and similar-named prefixes.
This is not a generic forensic/** exclude.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.ops.validate_docs_token_policy import (
    DocsTokenPolicyValidator,
    is_v2_v21_preservation_pack_changed_md_path,
)

PACK_PREFIX = "forensic/lossless_structural_projection_v2_v2_1_pack_v1"
PACK_MD = f"{PACK_PREFIX}/00_READ_ME_FIRST.md"
SIBLING_MD = "forensic/other_pack/example.md"
BOUNDARY_MD = "forensic/lossless_structural_projection_v2_v2_1_pack_v1_other/x.md"
DOCS_MD = "docs/ops/example.md"
FIXTURE_MD = "tests/fixtures/changed_skip.md"
ILLUSTRATIVE_TOKEN = "`src/trading/does_not_exist_for_gate_contract.py`"
MISSING_REF_LINE = "See src/trading/does_not_exist_for_gate_contract.py for details.\n"


def _repo_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )


def _write(repo: Path, rel: str, content: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _init_repo_with_base(tmp_path: Path) -> tuple[Path, str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "PeakTradeTest")
    _write(repo, "README.md", "# base\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return repo, base


def _commit_paths(repo: Path, rel_paths: dict[str, str], message: str) -> None:
    for rel, content in rel_paths.items():
        _write(repo, rel, content)
    _git(repo, "add", *rel_paths.keys())
    _git(repo, "commit", "-m", message)


def _run_token_policy_cli(repo: Path, base: str) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "scripts" / "ops" / "validate_docs_token_policy.py"
    return subprocess.run(
        [sys.executable, str(script), "--base", base],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_reference_targets_changed(repo: Path, base: str) -> subprocess.CompletedProcess[str]:
    script = _repo_root() / "scripts" / "ops" / "verify_docs_reference_targets.sh"
    return subprocess.run(
        ["bash", str(script), "--changed", "--base", base, "--repo-root", str(repo)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )


def test_predicate_is_not_a_global_forensic_exclude() -> None:
    assert is_v2_v21_preservation_pack_changed_md_path(PACK_MD)
    assert not is_v2_v21_preservation_pack_changed_md_path(SIBLING_MD)
    assert not is_v2_v21_preservation_pack_changed_md_path(BOUNDARY_MD)
    assert not is_v2_v21_preservation_pack_changed_md_path(DOCS_MD)
    assert not is_v2_v21_preservation_pack_changed_md_path("forensic/README.md")


def test_token_policy_changed_mode_skips_pack_leaf_and_keeps_product_and_sibling(
    tmp_path: Path,
) -> None:
    repo, base = _init_repo_with_base(tmp_path)
    _commit_paths(
        repo,
        {
            PACK_MD: f"Pack identity copy {ILLUSTRATIVE_TOKEN}\n",
            DOCS_MD: f"Product docs {ILLUSTRATIVE_TOKEN}\n",
            SIBLING_MD: f"Sibling forensic {ILLUSTRATIVE_TOKEN}\n",
            BOUNDARY_MD: f"Boundary sibling {ILLUSTRATIVE_TOKEN}\n",
        },
        "add markdown",
    )

    validator = DocsTokenPolicyValidator(repo)
    changed = {str(p.relative_to(repo)) for p in validator.get_changed_markdown_files(base)}
    assert PACK_MD not in changed
    assert DOCS_MD in changed
    assert SIBLING_MD in changed
    assert BOUNDARY_MD in changed

    pack_only, pack_only_base = _init_repo_with_base(tmp_path / "pack_only")
    _commit_paths(
        pack_only,
        {PACK_MD: f"Pack identity copy {ILLUSTRATIVE_TOKEN}\n"},
        "pack only",
    )
    pack_only_cli = _run_token_policy_cli(pack_only, pack_only_base)
    assert pack_only_cli.returncode == 0, pack_only_cli.stdout + pack_only_cli.stderr

    docs_cli = _run_token_policy_cli(repo, base)
    assert docs_cli.returncode == 1, docs_cli.stdout + docs_cli.stderr
    combined = docs_cli.stdout + docs_cli.stderr
    assert DOCS_MD in combined
    assert PACK_MD not in combined


def test_reference_targets_changed_mode_skips_pack_leaf_and_keeps_product_and_sibling(
    tmp_path: Path,
) -> None:
    repo, base = _init_repo_with_base(tmp_path)
    _commit_paths(
        repo,
        {
            PACK_MD: MISSING_REF_LINE,
            DOCS_MD: MISSING_REF_LINE,
            SIBLING_MD: MISSING_REF_LINE,
            BOUNDARY_MD: MISSING_REF_LINE,
        },
        "add markdown refs",
    )

    result = _run_reference_targets_changed(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert DOCS_MD in output
    assert SIBLING_MD in output
    assert BOUNDARY_MD in output
    assert PACK_MD not in output

    pack_only, pack_only_base = _init_repo_with_base(tmp_path / "pack_only")
    _commit_paths(pack_only, {PACK_MD: MISSING_REF_LINE}, "pack only")
    pack_only_result = _run_reference_targets_changed(pack_only, pack_only_base)
    assert pack_only_result.returncode == 0, pack_only_result.stdout + pack_only_result.stderr


def test_reference_targets_changed_mode_still_skips_tests_fixtures(tmp_path: Path) -> None:
    repo, base = _init_repo_with_base(tmp_path)
    _commit_paths(
        repo,
        {
            PACK_MD: MISSING_REF_LINE,
            FIXTURE_MD: MISSING_REF_LINE,
        },
        "pack plus fixture",
    )
    result = _run_reference_targets_changed(repo, base)
    assert result.returncode == 0, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert "not applicable" in output or "Docs Reference Targets" in output
    assert FIXTURE_MD not in output
    assert PACK_MD not in output
