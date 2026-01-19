"""
Execution Live (C2): governance-safe, snapshot-only dryrun orchestrator.

This package is intentionally IO-agnostic and deterministic:
- no network calls
- no broker dependencies
- no background loops / sleeps unless injected
"""

from __future__ import annotations
