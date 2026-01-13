#!/usr/bin/env python3
"""Unit tests for v2 auto-fixer (conservative strategy)."""

import pytest
from pathlib import Path
import sys

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "ops"))

from autofix_docs_token_policy_inline_code_v2 import (
    looks_like_url,
    looks_like_http_endpoint,
    looks_like_command,
    escape_slashes,
    rewrite_inline_code,
)


class TestHeuristics:
    """Test classification heuristics."""

    def test_looks_like_url(self):
        assert looks_like_url("https://github.com/user/repo")
        assert looks_like_url("http://localhost:8000/api")
        assert not looks_like_url("scripts/example.py")
        assert not looks_like_url("GET /api/health")

    def test_looks_like_http_endpoint(self):
        assert looks_like_http_endpoint("GET /ops/ci-health")
        assert looks_like_http_endpoint("POST /api/v1/foo")
        assert looks_like_http_endpoint("DELETE /resource")
        assert not looks_like_http_endpoint("python scripts/run.py")
        assert not looks_like_http_endpoint("/just/a/path")
        assert not looks_like_http_endpoint("GET")

    def test_looks_like_command(self):
        # Strong: starts with command verb
        assert looks_like_command("pytest tests/ops/test.py")
        assert looks_like_command("python scripts/run.py")
        assert looks_like_command("uv run python main.py")
        assert looks_like_command("git diff origin/main")
        assert looks_like_command("gh pr view 123")

        # Weak: contains command token with spaces
        assert looks_like_command("run pytest tests/unit")
        assert looks_like_command("then git commit -m 'fix'")

        # Should NOT match
        assert not looks_like_command("scripts/example.py")
        assert not looks_like_command("config/example.toml")
        assert not looks_like_command("https://github.com/user/repo")

    def test_escape_slashes(self):
        assert escape_slashes("foo/bar") == "foo&#47;bar"
        assert escape_slashes("foo&#47;bar") == "foo&#47;bar"  # idempotent
        assert escape_slashes("no-slashes") == "no-slashes"


class TestRewriteInlineCode:
    """Test rewrite_inline_code function."""

    def test_commands_rewritten(self):
        md = "`pytest tests/ops/test.py`"
        result, changes = rewrite_inline_code(md)
        assert result == "`pytest tests&#47;ops&#47;test.py`"
        assert changes == 1

    def test_http_endpoints_rewritten(self):
        md = "`GET /ops/ci-health`"
        result, changes = rewrite_inline_code(md)
        assert result == "`GET &#47;ops&#47;ci-health`"
        assert changes == 1

    def test_urls_skipped(self):
        md = "`https://github.com/user/repo`"
        result, changes = rewrite_inline_code(md)
        assert result == md
        assert changes == 0

    def test_already_escaped_skipped(self):
        md = "`scripts&#47;example.py`"
        result, changes = rewrite_inline_code(md)
        assert result == md
        assert changes == 0

    def test_generic_paths_skipped(self):
        md = "`config/example.toml`"
        result, changes = rewrite_inline_code(md)
        assert result == md
        assert changes == 0

    def test_fenced_blocks_protected(self):
        md = """```bash
pytest tests/ops/test.py
```"""
        result, changes = rewrite_inline_code(md)
        assert result == md
        assert changes == 0

    def test_multiple_inline_codes(self):
        md = "Run `pytest tests/unit` and `git commit`"
        result, changes = rewrite_inline_code(md)
        assert "pytest tests&#47;unit" in result
        assert "git commit" in result  # no slash, unchanged
        assert changes == 1

    def test_mixed_commands_and_paths(self):
        md = "Run `pytest tests/ops/test.py` on `config/example.toml`"
        result, changes = rewrite_inline_code(md)
        assert "pytest tests&#47;ops&#47;test.py" in result
        assert "`config/example.toml`" in result  # generic path, not rewritten
        assert changes == 1

    def test_idempotency(self):
        """Running v2 twice should yield 0 rewrites on second pass."""
        md = "`pytest tests/ops/test.py`"
        result1, changes1 = rewrite_inline_code(md)
        assert changes1 == 1
        result2, changes2 = rewrite_inline_code(result1)
        assert changes2 == 0
        assert result1 == result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
