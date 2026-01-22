"""
Slice 3: Deterministic BetaEventBridge -> LedgerEngine
=====================================================

Contract (high level):
- Same inputs (events + prices refs + config) => byte-identical artifacts.
- No wall-clock / randomness in bridge or artifacts.
- Canonical JSON/JSONL (sorted keys, stable separators, utf-8, '\n' newlines).
"""

from .bridge import BetaEventBridge, BetaBridgeArtifacts, BetaBridgeConfig
from .canonical import canonical_json_bytes, canonical_jsonl_bytes, canonical_json_line
from .sink import DeterministicArtifactSink, run_fingerprint

__all__ = [
    "BetaEventBridge",
    "BetaBridgeArtifacts",
    "BetaBridgeConfig",
    "DeterministicArtifactSink",
    "run_fingerprint",
    "canonical_json_bytes",
    "canonical_jsonl_bytes",
    "canonical_json_line",
]
