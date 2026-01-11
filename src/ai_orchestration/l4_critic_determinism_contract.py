"""
L4 Critic Determinism Contract (Phase 4D)

Explicit, versioned contract for deterministic L4 Critic replay behavior.

Design Principles:
- Evidence-first: canonicalized artifacts + stable hashing + explicit rules
- Backwards compatible: works with existing CriticReport schema
- No-live: pure analysis/validation code, no trading/execution
- Stable outputs: JSON with sorted keys, LF line endings, reproducible hashes

Reference:
- docs/governance/ai_autonomy/PHASE4D_L4_CRITIC_DETERMINISM_CONTRACT.md

Usage:
    from src.ai_orchestration.l4_critic_determinism_contract import (
        DeterminismContract,
        canonicalize,
        hash_canonical,
        compare_reports,
    )

    contract = DeterminismContract.default_v1_0_0()
    canonical = canonicalize(report_dict, contract=contract)
    report_hash = hash_canonical(report_dict, contract=contract)
    result = compare_reports(baseline, candidate, contract=contract)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# =============================================================================
# Constants
# =============================================================================

CONTRACT_SCHEMA_VERSION = "1.0.0"

# Volatile field patterns (simple substring matching)
DEFAULT_VOLATILE_KEY_PATTERNS = [
    "timestamp",
    "created_at",
    "duration",
    "elapsed",
    "run_id",
    "pid",
    "hostname",
    "absolute_path",
    "_temp",
    "_tmp",
]

# Top-level keys required in a valid L4 Critic report
REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "pack_id",
    "mode",
    "critic",
    "inputs",
    "summary",
    "findings",
    "meta",
}


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class DeterminismContract:
    """
    Contract defining determinism rules for L4 Critic reports.

    Attributes:
        schema_version: Contract schema version (semver)
        ignore_rules: List of key patterns to remove during canonicalization
        numeric_tolerance: Dict mapping JSON paths to float tolerances
        required_top_level_keys: Set of required top-level keys
        normalize_paths: Whether to normalize file paths (backslash->slash, strip repo root)
    """

    schema_version: str
    ignore_rules: List[str]
    numeric_tolerance: Dict[str, float] = field(default_factory=dict)
    required_top_level_keys: Set[str] = field(default_factory=set)
    normalize_paths: bool = True

    @classmethod
    def default_v1_0_0(cls) -> DeterminismContract:
        """Create default v1.0.0 contract."""
        return cls(
            schema_version="1.0.0",
            ignore_rules=DEFAULT_VOLATILE_KEY_PATTERNS.copy(),
            numeric_tolerance={},
            required_top_level_keys=REQUIRED_TOP_LEVEL_KEYS.copy(),
            normalize_paths=True,
        )


@dataclass
class ComparisonResult:
    """
    Result of comparing two reports.

    Attributes:
        equal: Whether reports are considered equal under the contract
        baseline_hash: SHA256 hash of canonicalized baseline
        candidate_hash: SHA256 hash of canonicalized candidate
        diff_summary: Short, deterministic summary of differences
        first_mismatch_path: JSON path to first difference (if any)
    """

    equal: bool
    baseline_hash: str
    candidate_hash: str
    diff_summary: str
    first_mismatch_path: Optional[str]


# =============================================================================
# Canonicalization
# =============================================================================


def _should_ignore_key(key: str, ignore_rules: List[str]) -> bool:
    """Check if a key should be ignored (simple substring match)."""
    key_lower = key.lower()
    return any(pattern.lower() in key_lower for pattern in ignore_rules)


def _normalize_path(path_str: str) -> str:
    """
    Normalize file path for deterministic comparison.

    Rules:
    - Convert backslashes to forward slashes
    - Strip absolute path prefixes (assume repo-relative is preferred)
    """
    # Convert backslashes to forward slashes
    normalized = path_str.replace("\\", "/")

    # Strip common absolute path prefixes (heuristic)
    # Examples: /Users/xxx/Peak_Trade/ -> Peak_Trade/
    #           C:\Users\xxx\Peak_Trade\ -> Peak_Trade/
    for prefix_pattern in [
        r"^[A-Za-z]:/(?:Users|home)/[^/]+/",  # Windows absolute
        r"^/(?:Users|home)/[^/]+/",  # Unix absolute
    ]:
        normalized = re.sub(prefix_pattern, "", normalized)

    return normalized


def _normalize_value(value: Any, contract: DeterminismContract) -> Any:
    """
    Normalize a single value according to contract rules.

    - Strings: normalize paths if normalize_paths=True
    - Floats: keep as-is (tolerance applied during comparison)
    - Other: return unchanged
    """
    if isinstance(value, str) and contract.normalize_paths:
        # Heuristic: if string looks like a path (contains / or \), normalize
        if "/" in value or "\\" in value:
            return _normalize_path(value)
    return value


def canonicalize(obj: Any, *, contract: DeterminismContract) -> Any:
    """
    Canonicalize an object according to the determinism contract.

    Rules:
    - Remove keys matching ignore_rules (recursive)
    - Sort dict keys
    - Normalize paths (if enabled)
    - Preserve list order (deterministic ordering should be in source data)

    Args:
        obj: Object to canonicalize (dict, list, or primitive)
        contract: Determinism contract defining rules

    Returns:
        Canonicalized object
    """
    if isinstance(obj, dict):
        canonical = {}
        for key, value in obj.items():
            # Skip volatile keys
            if _should_ignore_key(key, contract.ignore_rules):
                continue
            # Recursively canonicalize value
            canonical[key] = canonicalize(value, contract=contract)
        return canonical

    elif isinstance(obj, list):
        # Preserve list order; canonicalize each element
        return [canonicalize(item, contract=contract) for item in obj]

    else:
        # Normalize primitives (strings, numbers, etc.)
        return _normalize_value(obj, contract)


# =============================================================================
# Stable JSON
# =============================================================================


def dumps_canonical_json(obj: Any) -> str:
    """
    Serialize object to canonical JSON string.

    Rules:
    - Sorted keys
    - Compact separators (no trailing whitespace)
    - 2-space indentation
    - UTF-8 (ensure_ascii=False)
    - Trailing newline

    Args:
        obj: Object to serialize (should be canonicalized first)

    Returns:
        Canonical JSON string
    """
    json_str = json.dumps(
        obj,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ": "),
        indent=2,
    )
    # Ensure trailing newline (standard for text files)
    if not json_str.endswith("\n"):
        json_str += "\n"
    return json_str


# =============================================================================
# Hashing
# =============================================================================


def sha256_text(text: str) -> str:
    """
    Compute SHA256 hash of text string.

    Args:
        text: Text to hash (typically canonical JSON)

    Returns:
        Hex-encoded SHA256 hash (64 chars)
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_canonical(obj: Any, contract: DeterminismContract) -> str:
    """
    Compute stable SHA256 hash of canonicalized object.

    Args:
        obj: Object to hash (dict, list, or primitive)
        contract: Determinism contract

    Returns:
        Hex-encoded SHA256 hash
    """
    canonical = canonicalize(obj, contract=contract)
    canonical_json = dumps_canonical_json(canonical)
    return sha256_text(canonical_json)


# =============================================================================
# Comparison
# =============================================================================


def _find_first_mismatch(
    baseline: Any,
    candidate: Any,
    path: str = "$",
    tolerance: Dict[str, float] = None,
) -> Optional[str]:
    """
    Find first mismatch path between two objects (DFS).

    Args:
        baseline: Baseline object
        candidate: Candidate object
        path: Current JSON path (for error reporting)
        tolerance: Dict mapping JSON paths to float tolerances

    Returns:
        JSON path to first mismatch, or None if equal
    """
    tolerance = tolerance or {}

    # Type mismatch
    if type(baseline) is not type(candidate):
        return path

    if isinstance(baseline, dict):
        # Key set mismatch
        baseline_keys = set(baseline.keys())
        candidate_keys = set(candidate.keys())
        if baseline_keys != candidate_keys:
            return path

        # Recurse into dict values (sorted keys for determinism)
        for key in sorted(baseline_keys):
            child_path = f"{path}.{key}"
            mismatch = _find_first_mismatch(
                baseline[key], candidate[key], child_path, tolerance
            )
            if mismatch:
                return mismatch

    elif isinstance(baseline, list):
        # Length mismatch
        if len(baseline) != len(candidate):
            return path

        # Recurse into list elements
        for i, (b_item, c_item) in enumerate(zip(baseline, candidate)):
            child_path = f"{path}[{i}]"
            mismatch = _find_first_mismatch(b_item, c_item, child_path, tolerance)
            if mismatch:
                return mismatch

    elif isinstance(baseline, float) and isinstance(candidate, float):
        # Apply tolerance if configured for this path
        tol = tolerance.get(path, 0.0)
        if abs(baseline - candidate) > tol:
            return path

    else:
        # Direct comparison for primitives
        if baseline != candidate:
            return path

    return None


def compare_reports(
    baseline: Any,
    candidate: Any,
    contract: DeterminismContract,
) -> ComparisonResult:
    """
    Compare two L4 Critic reports under the determinism contract.

    Args:
        baseline: Baseline report (dict)
        candidate: Candidate report (dict)
        contract: Determinism contract

    Returns:
        ComparisonResult with equality status and diagnostics
    """
    # Canonicalize both reports
    baseline_canonical = canonicalize(baseline, contract=contract)
    candidate_canonical = canonicalize(candidate, contract=contract)

    # Compute hashes
    baseline_hash = hash_canonical(baseline, contract)
    candidate_hash = hash_canonical(candidate, contract)

    # Quick equality check via hash
    if baseline_hash == candidate_hash:
        return ComparisonResult(
            equal=True,
            baseline_hash=baseline_hash,
            candidate_hash=candidate_hash,
            diff_summary="Reports are identical (hash match)",
            first_mismatch_path=None,
        )

    # Find first mismatch for diagnostics
    first_mismatch_path = _find_first_mismatch(
        baseline_canonical,
        candidate_canonical,
        tolerance=contract.numeric_tolerance,
    )

    diff_summary = (
        f"Reports differ (first mismatch at {first_mismatch_path})"
        if first_mismatch_path
        else "Reports differ (hash mismatch, no specific path identified)"
    )

    return ComparisonResult(
        equal=False,
        baseline_hash=baseline_hash,
        candidate_hash=candidate_hash,
        diff_summary=diff_summary,
        first_mismatch_path=first_mismatch_path,
    )


# =============================================================================
# I/O Helpers
# =============================================================================


def load_json(path: Path) -> Any:
    """
    Load JSON from file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON object

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    """
    Write object to JSON file with canonical formatting.

    Args:
        path: Output path
        obj: Object to serialize (should be canonicalized first)
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    canonical_json = dumps_canonical_json(obj)
    path.write_text(canonical_json, encoding="utf-8")
