"""
Truth core — shared loaders and deterministic evaluation for docs drift + repo claims.
"""

from __future__ import annotations

from .evaluator import (
    any_required_present,
    evaluate_docs_drift,
    evaluate_repo_truth_claims,
    path_matches_sensitive,
)
from .git_refs import git_changed_files_three_dot
from .loaders import load_docs_truth_map, load_repo_truth_claims, load_yaml_file
from .models import (
    DocsDriftEvaluationResult,
    DocsDriftViolation,
    RepoTruthEvaluationResult,
    TruthCheckResult,
    TruthStatus,
)

__all__ = [
    "DocsDriftEvaluationResult",
    "DocsDriftViolation",
    "RepoTruthEvaluationResult",
    "TruthCheckResult",
    "TruthStatus",
    "any_required_present",
    "evaluate_docs_drift",
    "evaluate_repo_truth_claims",
    "git_changed_files_three_dot",
    "load_docs_truth_map",
    "load_repo_truth_claims",
    "load_yaml_file",
    "path_matches_sensitive",
]
