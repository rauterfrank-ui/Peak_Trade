"""
Unit tests for docs token policy validator.
"""

import tempfile
from pathlib import Path
import pytest

from scripts.ops.validate_docs_token_policy import (
    DocsTokenPolicyValidator,
    TokenType,
    ScanResult,
)


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repo structure for testing."""
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()

    # Create some real files
    (repo_root / "scripts").mkdir()
    (repo_root / "scripts" / "real_script.py").write_text("# real file")

    (repo_root / "config").mkdir()
    (repo_root / "config" / "real_config.toml").write_text("# real config")

    (repo_root / "docs").mkdir()

    return repo_root


@pytest.fixture
def validator(temp_repo):
    """Create a validator instance."""
    return DocsTokenPolicyValidator(temp_repo)


class TestTokenClassification:
    """Test token classification logic."""

    def test_classify_url(self, validator):
        """URLs should be classified as URL."""
        assert validator._classify_token("https://example.com/path") == TokenType.URL
        assert validator._classify_token("http://github.com/repo/file") == TokenType.URL

    def test_classify_encoded(self, validator):
        """Tokens with &#47; should be classified as ENCODED."""
        assert validator._classify_token("config&#47;my_file.toml") == TokenType.ENCODED
        assert validator._classify_token("scripts&#47;run.py") == TokenType.ENCODED

    def test_classify_command(self, validator):
        """Commands should be classified as COMMAND."""
        assert validator._classify_token("python scripts/run.py") == TokenType.COMMAND
        assert validator._classify_token("git diff --stat") == TokenType.COMMAND
        assert validator._classify_token("make test/unit") == TokenType.COMMAND

    def test_classify_real_repo_target(self, validator):
        """Existing files should be classified as REAL_REPO_TARGET."""
        assert validator._classify_token("scripts/real_script.py") == TokenType.REAL_REPO_TARGET
        assert validator._classify_token("config/real_config.toml") == TokenType.REAL_REPO_TARGET

    def test_classify_illustrative(self, validator):
        """Non-existent paths should be classified as ILLUSTRATIVE."""
        assert validator._classify_token("scripts/fake_script.py") == TokenType.ILLUSTRATIVE
        assert validator._classify_token("config/missing.toml") == TokenType.ILLUSTRATIVE
        assert validator._classify_token("src/data/loader.py") == TokenType.ILLUSTRATIVE

    def test_classify_branch_name(self, validator):
        """Branch names should be classified as BRANCH_NAME."""
        assert validator._classify_token("feature/my-feature") == TokenType.BRANCH_NAME
        assert validator._classify_token("docs/update-readme") == TokenType.BRANCH_NAME
        assert validator._classify_token("fix/bug-123") == TokenType.BRANCH_NAME

    def test_classify_local_path(self, validator):
        """Local paths should be classified as LOCAL_PATH."""
        assert validator._classify_token("./scripts/run.py") == TokenType.LOCAL_PATH
        assert validator._classify_token("../config/file.toml") == TokenType.LOCAL_PATH
        assert validator._classify_token("~/Documents/file.txt") == TokenType.LOCAL_PATH
        assert validator._classify_token("/usr/local/bin") == TokenType.LOCAL_PATH


class TestEncodingRequirement:
    """Test when encoding is required."""

    def test_illustrative_requires_encoding(self, validator):
        """Illustrative paths should require encoding."""
        assert validator._should_require_encoding(
            "scripts/fake.py",
            TokenType.ILLUSTRATIVE
        )

    def test_branch_name_requires_encoding(self, validator):
        """Branch names should require encoding."""
        assert validator._should_require_encoding(
            "feature/my-feature",
            TokenType.BRANCH_NAME
        )

    def test_real_target_no_encoding(self, validator):
        """Real repo targets should NOT require encoding."""
        assert not validator._should_require_encoding(
            "scripts/real_script.py",
            TokenType.REAL_REPO_TARGET
        )

    def test_url_no_encoding(self, validator):
        """URLs should NOT require encoding."""
        assert not validator._should_require_encoding(
            "https://example.com/path",
            TokenType.URL
        )

    def test_command_no_encoding(self, validator):
        """Commands should NOT require encoding."""
        assert not validator._should_require_encoding(
            "python scripts/run.py",
            TokenType.COMMAND
        )

    def test_allowlist_no_encoding(self, temp_repo):
        """Allowlisted tokens should NOT require encoding."""
        # Create allowlist
        allowlist_path = temp_repo / "allowlist.txt"
        allowlist_path.write_text("some/path\npath/to/file\n")

        validator = DocsTokenPolicyValidator(temp_repo, allowlist_path)

        assert not validator._should_require_encoding(
            "some/path",
            TokenType.ILLUSTRATIVE
        )


class TestFileScan:
    """Test scanning Markdown files."""

    def test_scan_file_with_violations(self, temp_repo, validator):
        """Scan file with illustrative paths (should find violations)."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Here's an example: `scripts/fake_script.py` is illustrative.

And another: `config/missing.toml`.
""")

        result = validator.scan_file(md_file)

        assert not result.passed
        assert len(result.violations) == 2
        assert result.violations[0].token == "scripts/fake_script.py"
        assert result.violations[1].token == "config/missing.toml"
        assert "&#47;" in result.violations[0].fix_suggestion

    def test_scan_file_with_encoded_tokens(self, temp_repo, validator):
        """Scan file with properly encoded tokens (should pass)."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Here's a properly encoded example: `scripts&#47;fake_script.py`.

And another: `config&#47;missing.toml`.
""")

        result = validator.scan_file(md_file)

        assert result.passed
        assert len(result.violations) == 0

    def test_scan_file_with_real_paths(self, temp_repo, validator):
        """Scan file with real repo paths (should pass)."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Here's a real file: `scripts/real_script.py`.

And another: `config/real_config.toml`.
""")

        result = validator.scan_file(md_file)

        assert result.passed
        assert len(result.violations) == 0

    def test_scan_file_ignores_code_blocks(self, temp_repo, validator):
        """Fenced code blocks should be ignored."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

```bash
python scripts/fake_script.py
cd config/missing/
```

This inline token `scripts/fake_script.py` should still be caught.
""")

        result = validator.scan_file(md_file)

        # Should only catch the inline token, not the code block
        assert not result.passed
        assert len(result.violations) == 1
        assert result.violations[0].line == 9  # The inline token line

    def test_scan_file_with_urls(self, temp_repo, validator):
        """URLs should not trigger violations."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Here's a URL: `https://github.com/user/repo/blob/main/file.py`.

And another: `http://example.com/path/to/resource`.
""")

        result = validator.scan_file(md_file)

        assert result.passed
        assert len(result.violations) == 0

    def test_scan_file_with_commands(self, temp_repo, validator):
        """Commands should not trigger violations."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Run this: `python scripts/fake_script.py`.

Or this: `git diff origin/main`.
""")

        result = validator.scan_file(md_file)

        assert result.passed
        assert len(result.violations) == 0

    def test_scan_file_with_branch_names(self, temp_repo, validator):
        """Branch names should require encoding."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Check out branch: `feature/my-feature`.

Or this one: `docs/update-readme`.
""")

        result = validator.scan_file(md_file)

        assert not result.passed
        assert len(result.violations) == 2
        assert "feature/my-feature" in result.violations[0].token
        assert "docs/update-readme" in result.violations[1].token

    def test_scan_file_mixed_content(self, temp_repo, validator):
        """Test file with mixed content types."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Real file: `scripts/real_script.py` ✅

Illustrative (encoded): `scripts&#47;fake.py` ✅

Illustrative (not encoded): `config/missing.toml` ❌

URL: `https://example.com/path` ✅

Command: `python scripts/run.py` ✅

Branch (not encoded): `feature/test` ❌
""")

        result = validator.scan_file(md_file)

        assert not result.passed
        assert len(result.violations) == 2
        violations_tokens = [v.token for v in result.violations]
        assert "config/missing.toml" in violations_tokens
        assert "feature/test" in violations_tokens


class TestAllowlist:
    """Test allowlist functionality."""

    def test_allowlist_skips_violations(self, temp_repo):
        """Allowlisted tokens should not trigger violations."""
        # Create allowlist
        allowlist_path = temp_repo / "allowlist.txt"
        allowlist_path.write_text("scripts/special_case.py\nconfig/allowed.toml\n")

        validator = DocsTokenPolicyValidator(temp_repo, allowlist_path)

        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

This is allowed: `scripts/special_case.py`.

This too: `config/allowed.toml`.

But not this: `config/not_allowed.toml`.
""")

        result = validator.scan_file(md_file)

        assert not result.passed
        assert len(result.violations) == 1
        assert result.violations[0].token == "config/not_allowed.toml"


class TestEdgeCases:
    """Test edge cases."""

    def test_no_tokens_with_slash(self, temp_repo, validator):
        """File with no tokens containing '/' should pass."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

Some code: `print("hello")`.

A variable: `my_var = 42`.
""")

        result = validator.scan_file(md_file)

        assert result.passed
        assert result.total_tokens == 0  # No tokens with '/'

    def test_empty_file(self, temp_repo, validator):
        """Empty file should pass."""
        md_file = temp_repo / "docs" / "empty.md"
        md_file.write_text("")

        result = validator.scan_file(md_file)

        assert result.passed
        assert result.total_tokens == 0

    def test_multiline_code_blocks(self, temp_repo, validator):
        """Multiple code blocks should be handled correctly."""
        md_file = temp_repo / "docs" / "test.md"
        md_file.write_text("""
# Test Document

```python
def example():
    path = "scripts/fake.py"
    return path
```

Some text here.

```bash
cd config/missing/
ls -la
```

This should be caught: `scripts/fake.py`.
""")

        result = validator.scan_file(md_file)

        assert not result.passed
        assert len(result.violations) == 1
        assert result.violations[0].token == "scripts/fake.py"


def test_integration_scenario(temp_repo):
    """Full integration test with realistic documentation."""
    # Create allowlist
    allowlist_path = temp_repo / "allowlist.txt"
    allowlist_path.write_text("some/generic/path\n")

    validator = DocsTokenPolicyValidator(temp_repo, allowlist_path)

    # Create a realistic documentation file
    md_file = temp_repo / "docs" / "guide.md"
    md_file.write_text("""
# Developer Guide

## Quick Start

1. Configure your settings in `config&#47;my_custom.toml` (illustrative, encoded) ✅
2. Run the script: `python scripts/real_script.py` (command, real file) ✅
3. View logs at `scripts&#47;output&#47;logs.txt` (illustrative, encoded) ✅

## Real Files

- Source code: `scripts/real_script.py` (real file) ✅
- Configuration: `config/real_config.toml` (real file) ✅

## Examples (Should Fail - Not Encoded)

- Bad example 1: `scripts/fake_file.py` ❌
- Bad example 2: `config/missing.toml` ❌

## External Resources

- Documentation: `https://docs.example.com/guide/intro` (URL) ✅
- Repository: `https://github.com/user/repo` (URL) ✅

## Git Workflow

1. Create branch: `feature&#47;my-feature` (branch, encoded) ✅
2. Checkout: `git checkout feature/test` (command) ✅

## Generic Placeholders

- Use `some/generic/path` for testing (allowlisted) ✅

## Code Examples

```bash
# This should be ignored (fenced code block)
cd scripts/fake/
python missing.py
```

Done!
""")

    result = validator.scan_file(md_file)

    # Should find exactly 2 violations (the "Bad example" cases)
    assert not result.passed
    assert len(result.violations) == 2

    violations_tokens = {v.token for v in result.violations}
    assert "scripts/fake_file.py" in violations_tokens
    assert "config/missing.toml" in violations_tokens

    # Verify fix suggestions
    for v in result.violations:
        assert "&#47;" in v.fix_suggestion
        assert v.token.replace("/", "&#47;") in v.fix_suggestion
