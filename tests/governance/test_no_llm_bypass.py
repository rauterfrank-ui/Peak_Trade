"""
Governance: no direct LLM calls outside src/ai_orchestration.

Allow explicit exceptions via inline marker: # ORCH_BYPASS_ALLOWED: <reason>
"""
import re
from pathlib import Path

ALLOW_PREFIXES = (
    "src/ai_orchestration/",
    "out/ops/",
    "docs/",
)

DENY_PATTERNS = [
    re.compile(r"\bfrom\s+openai\s+import\b"),
    re.compile(r"\bimport\s+openai\b"),
    re.compile(r"\bOpenAI\s*\("),
    re.compile(r"\bchat\.completions\.create\b"),
    re.compile(r"\bresponses\.create\b"),
    re.compile(r"\banthropic\b"),
    re.compile(r"\bcohere\b"),
]


def iter_py_files():
    for root in ("src", "scripts"):
        p = Path(root)
        if not p.exists():
            continue
        for f in p.rglob("*.py"):
            s = f.as_posix()
            if s.startswith(ALLOW_PREFIXES):
                continue
            yield f


def test_no_direct_llm_calls_outside_orchestrator():
    hits = []
    for f in iter_py_files():
        txt = f.read_text(encoding="utf-8", errors="replace")
        for pat in DENY_PATTERNS:
            if pat.search(txt):
                hits.append(f"{f.as_posix()}: pattern={pat.pattern}")
                break
    # Allow explicit exceptions by inline marker:
    #   # ORCH_BYPASS_ALLOWED: <reason>
    filtered = []
    for h in hits:
        f = Path(h.split(": pattern=", 1)[0])
        txt = f.read_text(encoding="utf-8", errors="replace")
        if "ORCH_BYPASS_ALLOWED:" in txt:
            continue
        filtered.append(h)

    assert not filtered, (
        "Direct LLM usage outside orchestrator detected:\n" + "\n".join(filtered)
    )
