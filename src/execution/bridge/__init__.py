"""
Slice 3: Deterministic BetaEvent -> LedgerEngine Bridge.

This package is designed for CI regression artifacts:
- Same inputs => byte-identical artifacts.
- No wall-clock timestamps or randomness.
"""

from .beta_event_bridge import BetaEventBridge, BetaEventBridgeConfig, BridgeResult
from .artifact_sink import ArtifactSink, FileSystemArtifactSink
from .run_fingerprint import run_fingerprint

__all__ = [
    "BetaEventBridge",
    "BetaEventBridgeConfig",
    "BridgeResult",
    "ArtifactSink",
    "FileSystemArtifactSink",
    "run_fingerprint",
]
