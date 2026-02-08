"""
Ingress orchestrator (Runbook A5): wire A2 (events JSONL) → A3 (FeatureView) → A4 (EvidenceCapsule).
Outputs stay pointer-only (no payload/raw/transcript in written files).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.ingress.views.feature_view_builder import build_feature_view_from_jsonl
from src.ingress.io.feature_view_writer import write_feature_view
from src.ingress.capsules.evidence_capsule_builder import build_evidence_capsule
from src.ingress.io.evidence_capsule_writer import write_evidence_capsule


@dataclass
class OrchestratorConfig:
    """Config for run_ingress. base_dir defaults to out/ops/*."""

    base_dir: Path = field(default_factory=lambda: Path("out/ops"))
    run_id: str = "default"
    input_jsonl_path: str = ""

    def views_dir(self) -> Path:
        return self.base_dir / "views"

    def capsules_dir(self) -> Path:
        return self.base_dir / "capsules"


def run_ingress(
    config: OrchestratorConfig,
    labels: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Path]:
    """
    Run A2→A4 pipeline: build FeatureView from JSONL, write it, build EvidenceCapsule, write it.
    Returns (feature_view_json_path, capsule_json_path).
    Stays pointer-only (no payload/raw/transcript in outputs).
    """
    # 1) build_feature_view_from_jsonl(...)
    fv = build_feature_view_from_jsonl(
        config.input_jsonl_path if config.input_jsonl_path else "",
        run_id=config.run_id,
    )
    # 2) write_feature_view(... -> out/ops/views/<run_id>.feature_view.json)
    views_dir = config.views_dir()
    views_dir.mkdir(parents=True, exist_ok=True)
    fv_path = views_dir / f"{config.run_id}.feature_view.json"
    write_feature_view(fv, fv_path)
    # 3) build_evidence_capsule(feature_view=..., labels=...)  (labels optional)
    capsule_id = f"{config.run_id}.capsule"
    ts_ms = fv.ts_ms
    cap = build_evidence_capsule(
        capsule_id=capsule_id,
        run_id=config.run_id,
        ts_ms=ts_ms,
        feature_view=fv,
        labels=labels,
    )
    # 4) write_evidence_capsule(... -> out/ops/capsules/<run_id>.capsule.json)
    capsules_dir = config.capsules_dir()
    capsules_dir.mkdir(parents=True, exist_ok=True)
    cap_path = capsules_dir / f"{config.run_id}.capsule.json"
    write_evidence_capsule(cap, cap_path)
    return (fv_path, cap_path)
