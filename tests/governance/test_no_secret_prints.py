"""
Governance: no secret-printing or debug-tracing patterns in src/scripts/workflows.

Allow explicit exceptions via inline marker: # SECRET_PRINT_ALLOWED: <reason>
"""
import re
from pathlib import Path

ALLOW_PREFIXES = (
    "out/ops/",
    "scripts/ops/",   # setup/diag scripts may reference token env for documentation
    "scripts/utils/",
)

# High-signal: shell debug, CI debug env, echo/printf of secret env vars in workflows/code.
DENY_PATTERNS = [
    re.compile(r"set\s+-x"),
    re.compile(r"ACTIONS_STEP_DEBUG"),
    re.compile(r"ACTIONS_RUNNER_DEBUG"),
    re.compile(r"GIT_TRACE"),
    re.compile(r"GIT_CURL_VERBOSE"),
    re.compile(
        r"echo\s+.*\$\{?(OPENAI|ANTHROPIC|COHERE|API|TOKEN|SECRET|PASSWORD|GITHUB_TOKEN)",
        re.I,
    ),
    re.compile(
        r"printf\s+.*\$\{?(OPENAI|ANTHROPIC|COHERE|API|TOKEN|SECRET|PASSWORD|GITHUB_TOKEN)",
        re.I,
    ),
]


def iter_text_files():
    roots = ("src", "scripts", ".github/workflows")
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if f.is_dir():
                continue
            s = f.as_posix()
            if s.startswith(ALLOW_PREFIXES):
                continue
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tgz"}:
                continue
            yield f


def test_no_secret_printing_or_debug_tracing():
    hits = []
    for f in iter_text_files():
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "SECRET_PRINT_ALLOWED:" in txt:
            continue
        for pat in DENY_PATTERNS:
            if pat.search(txt):
                hits.append(f"{f.as_posix()}: pattern={pat.pattern}")
                break
    assert not hits, (
        "Potential secret-print/debug-trace detected:\n" + "\n".join(hits)
    )
