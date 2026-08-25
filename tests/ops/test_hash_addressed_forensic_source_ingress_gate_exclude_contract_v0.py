"""Exact-hash-path ingress gate exclude contract.

Proves future source bytes under:

    forensic/evidence/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/

are skipped by product-docs changed-mode gates and by mutating / large-file
pre-commit hooks, without creating a generic forensic/** or
forensic/evidence/** blind zone.

This is not source import. Tests match path strings / synthetic fixtures only.
AUTHORITY=NONE. CANONICAL=false.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

from scripts.ops.validate_docs_token_policy import (
    DocsTokenPolicyValidator,
    is_forensic_changed_md_excluded_path,
    is_hash_addressed_forensic_source_changed_md_path,
)

SOURCE_SHA256 = "a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"
HASH_DIR = f"forensic/evidence/sha256-{SOURCE_SHA256}"
SOURCE_MD = f"{HASH_DIR}/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
LEAF_README = f"{HASH_DIR}/00_READ_ME_FIRST.md"
SIBLING_HASH_MD = (
    "forensic/evidence/sha256-08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092/"
    "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
)
OTHER_HASH_MD = (
    "forensic/evidence/sha256-10d9293134426805f38996be848e1de853636d8e6f60745a2330bdfd94e3719f/"
    "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
)
BOUNDARY_MD = f"{HASH_DIR}_other/x.md"
EVIDENCE_ROOT_MD = "forensic/evidence/example.md"
SIBLING_PACK_MD = "forensic/other_pack/example.md"
DOCS_MD = "docs/ops/example.md"
EXISTING_V2_SOURCE_MD = (
    "forensic/lossless_structural_projection_v2_v2_1_pack_v1/evidence/"
    "raw_verbatim_identity_copies_authority_none/"
    "PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md"
)
ILLUSTRATIVE_TOKEN = "`src/trading/does_not_exist_for_gate_contract.py`"
MISSING_REF_LINE = "See src/trading/does_not_exist_for_gate_contract.py for details.\n"
MUTATOR_HOOK_IDS = ("end-of-file-fixer", "trailing-whitespace", "mixed-line-ending")
LARGE_FILE_HOOK_ID = "check-added-large-files"
GENERIC_FORENSIC_PATTERNS = (
    r"^forensic/\*\*",
    r"^forensic/\.\*",
    r"forensic/\*\*",
    r"^forensic/",
)


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


def _precommit_config() -> dict:
    path = _repo_root() / ".pre-commit-config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _hook(config: dict, hook_id: str) -> dict:
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if hook.get("id") == hook_id:
                return hook
    raise AssertionError(f"missing pre-commit hook {hook_id}")


def _compile_exclude(hook: dict) -> re.Pattern[str]:
    exclude = hook.get("exclude")
    assert exclude, f"hook {hook.get('id')} has no exclude"
    return re.compile(exclude)


def test_predicate_is_not_a_global_forensic_or_evidence_exclude() -> None:
    assert is_hash_addressed_forensic_source_changed_md_path(SOURCE_MD)
    assert is_hash_addressed_forensic_source_changed_md_path(LEAF_README)
    assert is_forensic_changed_md_excluded_path(SOURCE_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(SIBLING_PACK_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(EVIDENCE_ROOT_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(BOUNDARY_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(SIBLING_HASH_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(OTHER_HASH_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path(DOCS_MD)
    assert not is_hash_addressed_forensic_source_changed_md_path("forensic/README.md")
    assert not is_forensic_changed_md_excluded_path(EVIDENCE_ROOT_MD)
    assert not is_forensic_changed_md_excluded_path(SIBLING_HASH_MD)


def test_token_policy_changed_mode_skips_hash_leaf_and_keeps_product_and_siblings(
    tmp_path: Path,
) -> None:
    repo, base = _init_repo_with_base(tmp_path)
    _commit_paths(
        repo,
        {
            SOURCE_MD: f"Hash source identity copy {ILLUSTRATIVE_TOKEN}\n",
            LEAF_README: f"Hash leaf readme {ILLUSTRATIVE_TOKEN}\n",
            DOCS_MD: f"Product docs {ILLUSTRATIVE_TOKEN}\n",
            SIBLING_PACK_MD: f"Sibling forensic {ILLUSTRATIVE_TOKEN}\n",
            EVIDENCE_ROOT_MD: f"Evidence root {ILLUSTRATIVE_TOKEN}\n",
            BOUNDARY_MD: f"Boundary sibling {ILLUSTRATIVE_TOKEN}\n",
            SIBLING_HASH_MD: f"Other hash identity {ILLUSTRATIVE_TOKEN}\n",
        },
        "add markdown",
    )

    validator = DocsTokenPolicyValidator(repo)
    changed = {str(p.relative_to(repo)) for p in validator.get_changed_markdown_files(base)}
    assert SOURCE_MD not in changed
    assert LEAF_README not in changed
    assert DOCS_MD in changed
    assert SIBLING_PACK_MD in changed
    assert EVIDENCE_ROOT_MD in changed
    assert BOUNDARY_MD in changed
    assert SIBLING_HASH_MD in changed

    hash_only, hash_only_base = _init_repo_with_base(tmp_path / "hash_only")
    _commit_paths(
        hash_only,
        {SOURCE_MD: f"Hash source identity copy {ILLUSTRATIVE_TOKEN}\n"},
        "hash source only",
    )
    hash_only_cli = _run_token_policy_cli(hash_only, hash_only_base)
    assert hash_only_cli.returncode == 0, hash_only_cli.stdout + hash_only_cli.stderr

    docs_cli = _run_token_policy_cli(repo, base)
    assert docs_cli.returncode == 1, docs_cli.stdout + docs_cli.stderr
    combined = docs_cli.stdout + docs_cli.stderr
    assert DOCS_MD in combined
    assert SOURCE_MD not in combined
    assert LEAF_README not in combined


def test_reference_targets_changed_mode_skips_hash_leaf_and_keeps_product_and_siblings(
    tmp_path: Path,
) -> None:
    repo, base = _init_repo_with_base(tmp_path)
    _commit_paths(
        repo,
        {
            SOURCE_MD: MISSING_REF_LINE,
            LEAF_README: MISSING_REF_LINE,
            DOCS_MD: MISSING_REF_LINE,
            SIBLING_PACK_MD: MISSING_REF_LINE,
            EVIDENCE_ROOT_MD: MISSING_REF_LINE,
            BOUNDARY_MD: MISSING_REF_LINE,
            SIBLING_HASH_MD: MISSING_REF_LINE,
        },
        "add markdown refs",
    )

    result = _run_reference_targets_changed(repo, base)
    assert result.returncode == 1, result.stdout + result.stderr
    output = result.stdout + result.stderr
    assert DOCS_MD in output
    assert SIBLING_PACK_MD in output
    assert EVIDENCE_ROOT_MD in output
    assert BOUNDARY_MD in output
    assert SIBLING_HASH_MD in output
    assert SOURCE_MD not in output
    assert LEAF_README not in output

    hash_only, hash_only_base = _init_repo_with_base(tmp_path / "hash_only")
    _commit_paths(hash_only, {SOURCE_MD: MISSING_REF_LINE}, "hash source only")
    hash_only_result = _run_reference_targets_changed(hash_only, hash_only_base)
    assert hash_only_result.returncode == 0, hash_only_result.stdout + hash_only_result.stderr


def test_precommit_mutators_exclude_exact_source_file_not_generic_forensic() -> None:
    config = _precommit_config()
    for hook_id in MUTATOR_HOOK_IDS:
        compiled = _compile_exclude(_hook(config, hook_id))
        assert compiled.search(SOURCE_MD), f"{hook_id} must skip exact hash source file"
        assert not compiled.search(LEAF_README), f"{hook_id} must still hygiene leaf readme"
        assert not compiled.search(EVIDENCE_ROOT_MD)
        assert not compiled.search(SIBLING_PACK_MD)
        assert not compiled.search(SIBLING_HASH_MD)
        assert not compiled.search(OTHER_HASH_MD)
        assert not compiled.search(BOUNDARY_MD)
        assert not compiled.search("forensic/README.md")
        assert not compiled.search("docs/ops/example.md")


def test_precommit_large_file_exclude_is_exact_source_file_and_keeps_maxkb() -> None:
    hook = _hook(_precommit_config(), LARGE_FILE_HOOK_ID)
    compiled = _compile_exclude(hook)
    args = hook.get("args") or []
    assert "--maxkb=1024" in args
    assert compiled.search(SOURCE_MD)
    assert compiled.search(EXISTING_V2_SOURCE_MD)
    assert not compiled.search(LEAF_README)
    assert not compiled.search(EVIDENCE_ROOT_MD)
    assert not compiled.search(SIBLING_PACK_MD)
    assert not compiled.search(SIBLING_HASH_MD)
    assert not compiled.search(OTHER_HASH_MD)
    assert not compiled.search(BOUNDARY_MD)
    assert not compiled.search("forensic/README.md")


def test_precommit_excludes_are_not_generic_forensic_wide() -> None:
    config = _precommit_config()
    hook_ids = (*MUTATOR_HOOK_IDS, LARGE_FILE_HOOK_ID)
    for hook_id in hook_ids:
        exclude = _hook(config, hook_id).get("exclude") or ""
        compact = re.sub(r"\s+", "", exclude)
        for pattern in GENERIC_FORENSIC_PATTERNS:
            assert re.search(pattern, compact) is None, (
                f"{hook_id} exclude must not contain generic forensic pattern {pattern!r}: {exclude}"
            )
        assert "forensic/**" not in exclude
        assert "forensic/evidence/**" not in exclude
        assert "*.md" not in exclude


def test_precommit_does_not_enable_lfs() -> None:
    text = (_repo_root() / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    assert "git-lfs" not in text.lower()
    assert "filter=lfs" not in text.lower()
    gitattributes = _repo_root() / ".gitattributes"
    assert not gitattributes.exists()
