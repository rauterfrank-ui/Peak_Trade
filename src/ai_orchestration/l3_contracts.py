"""
L3 Trade Plan Advisory: input/output contracts.

- Pointer-only inputs: no raw payload/transcript/content; artifacts = path+sha256 only.
- Used by L3Runner and contract tests.
"""

from typing import Dict, List, Any

# Keys that must not appear in L3 input (pointer-only contract: no raw content).
L3_FORBIDDEN_RAW_KEYS = frozenset(
    {
        "payload",
        "raw",
        "transcript",
        "content",
        "diff",
        "body",
        "text",
        "api_key",
        "secret",
        "token",
        "credentials",
    }
)


def _has_forbidden_raw_keys(obj: Any, path: str = "") -> bool:
    """Return True if obj (recursively) contains any L3-forbidden raw key."""
    if not isinstance(obj, dict):
        return False
    for k, v in obj.items():
        key_lower = k.lower()
        if key_lower in L3_FORBIDDEN_RAW_KEYS:
            return True
        if isinstance(v, dict) and _has_forbidden_raw_keys(v, f"{path}.{k}"):
            return True
        if isinstance(v, list) and v and isinstance(v[0], dict):
            if _has_forbidden_raw_keys(v[0], f"{path}.{k}[0]"):
                return True
    return False


def _artifacts_are_pointer_only(artifacts: Any) -> bool:
    """Check that artifacts list is pointer-only: each item has path and sha256, no raw content."""
    if not isinstance(artifacts, list):
        return False
    for item in artifacts:
        if not isinstance(item, dict):
            return False
        if set(item.keys()) - {"path", "sha256"}:
            return False
        if "path" not in item or "sha256" not in item:
            return False
    return True


def accepts_l3_pointer_only_input(obj: Dict[str, Any]) -> bool:
    """
    Contract: L3 accepts only pointer-only inputs (no raw payload keys; artifacts path+sha256 only).

    Returns True if input is acceptable for L3; False if it contains forbidden keys or non-pointer artifacts.
    """
    if _has_forbidden_raw_keys(obj):
        return False
    artifacts = obj.get("artifacts")
    if artifacts is not None and not _artifacts_are_pointer_only(artifacts):
        return False
    return True


def artifact_paths_from_pointer_only_input(obj: Dict[str, Any]) -> List[str]:
    """
    Extract artifact paths from a pointer-only L3 input (for deterministic output envelope).

    Returns list of path strings; empty if no artifacts key or empty list.
    """
    artifacts = obj.get("artifacts")
    if not artifacts or not _artifacts_are_pointer_only(artifacts):
        return []
    return [str(a.get("path", "")) for a in artifacts if a.get("path")]
