"""
Contract tests for scripts/ops/docs_token_hygiene_inline_code_paths.py (v0).

Drive CLI via subprocess for dry-run / skip paths; exercise helpers with synthetic Markdown only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "docs_token_hygiene_inline_code_paths.py"

sys.path.insert(0, str(_REPO_ROOT / "scripts" / "ops"))
from docs_token_hygiene_inline_code_paths import (  # noqa: E402
    encode_slashes,
    process_markdown,
    should_encode_inline_code_token,
)


def _run_cli(path_arg: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--path", path_arg],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def test_process_markdown_inline_paths_only_outside_fences_idempotent() -> None:
    md = """See `docs/guide.md`, `plain`, and a fenced slash token:

```
scripts/ops/example.py still/has/slashes
```

Tilde fence:

~~~
src/other/file.rs
~~~
"""
    assert should_encode_inline_code_token("docs/guide.md")
    assert not should_encode_inline_code_token("plain")
    assert encode_slashes("docs/guide.md") == "docs&#47;guide.md"

    once = process_markdown(md)
    assert "`docs&#47;guide.md`" in once
    assert "`plain`" in once
    assert "scripts/ops/example.py still/has/slashes" in once
    assert "src/other/file.rs" in once

    twice = process_markdown(once)
    assert twice == once


def test_cli_dry_run_shows_diff_and_leaves_file_unchanged(tmp_path: Path) -> None:
    before = "Use `reports/summary.md` for details.\n"
    f = tmp_path / "synthetic.md"
    f.write_text(before, encoding="utf-8")

    proc = _run_cli(str(f.resolve()))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    out = proc.stdout + proc.stderr
    assert "DRY-RUN" in out
    assert "== docs token hygiene (inline code paths) ==" in out
    assert "---" in out  # unified_diff marker
    assert f.read_text(encoding="utf-8") == before


def test_cli_skip_when_already_encoded(tmp_path: Path) -> None:
    before = "Already `docs&#47;guide.md`.\n"
    f = tmp_path / "encoded.md"
    f.write_text(before, encoding="utf-8")

    proc = _run_cli(str(f.resolve()))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "SKIP: no changes" in proc.stdout
    assert f.read_text(encoding="utf-8") == before
