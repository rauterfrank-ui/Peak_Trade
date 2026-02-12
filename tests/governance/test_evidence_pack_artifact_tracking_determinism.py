"""
Governance: Evidence Pack Artifact Tracking Determinism

Deterministic tests for:
- Artifact list stable ordering (same set of paths → same serialized order)
- Stable hashes for same inputs (run_manifest / run_metadata JSON hash)
"""

import hashlib
import json
from pathlib import Path

import pytest

from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime
from src.ai_orchestration.models import AutonomyLevel
from src.ai_orchestration.run_manifest import RunManifest


def _json_hash(obj: dict) -> str:
    """Canonical JSON hash (sort_keys=True, no trailing whitespace)."""
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class TestRunManifestArtifactOrderingDeterminism:
    """RunManifest artifact list has stable ordering in output."""

    def test_artifacts_sorted_in_to_dict(self):
        manifest = RunManifest(
            run_id="L2-abc123",
            run_type="dry-run",
            timestamp="2026-01-10T12:00:00+00:00",
            layer_id="L2",
            layer_name="Market Outlook",
            autonomy_level="REC",
            primary_model_id="gpt-5",
            fallback_model_ids=[],
            critic_model_id="deepseek",
            capability_scope_id="L2_scope",
            capability_scope_version="1.0",
            sod_result="PASS",
            sod_reason="SoD OK",
            sod_timestamp="2026-01-10T12:00:00+00:00",
            matrix_version="v1.0",
            registry_version="1.0",
            artifacts=["out/z.json", "out/a.json", "out/m.json"],
        )
        d = manifest.to_dict()
        assert d["artifacts"] == ["out/a.json", "out/m.json", "out/z.json"]

    def test_same_artifact_set_different_input_order_same_hash(self):
        """Same artifact set in different order yields same to_dict and JSON hash (stable sort)."""
        ts = "2026-01-10T12:00:00+00:00"
        base = dict(
            run_id="L2-abc123def456",
            run_type="dry-run",
            timestamp=ts,
            layer_id="L2",
            layer_name="Market Outlook",
            autonomy_level="REC",
            primary_model_id="gpt-5",
            fallback_model_ids=[],
            critic_model_id="deepseek",
            capability_scope_id="L2_scope",
            capability_scope_version="1.0",
            sod_result="PASS",
            sod_reason="SoD OK",
            sod_timestamp=ts,
            matrix_version="v1.0",
            registry_version="1.0",
        )
        m1 = RunManifest(artifacts=["out/c.json", "out/a.json", "out/b.json"], **base)
        m2 = RunManifest(artifacts=["out/b.json", "out/c.json", "out/a.json"], **base)
        d1 = m1.to_dict()
        d2 = m2.to_dict()
        assert d1["artifacts"] == sorted(d1["artifacts"])
        assert d2["artifacts"] == sorted(d2["artifacts"])
        assert d1["artifacts"] == d2["artifacts"]
        assert _json_hash(d1) == _json_hash(d2)


class TestEvidencePackRuntimeArtifactTrackingDeterminism:
    """EvidencePackRuntime track_artifact produces stable ordering when persisted."""

    def test_track_artifact_order_persisted_sorted(self, tmp_path):
        """Persisted run_metadata artifacts list is sorted for same set."""
        out = tmp_path / "out"
        out.mkdir()
        runtime = EvidencePackRuntime(output_dir=out)
        runtime.start_run(
            run_id="run-1",
            layer_id="L0",
            autonomy_level=AutonomyLevel.RO,
        )
        # Track in non-alphabetical order
        runtime.track_artifact("run-1", Path("out/z.json"))
        runtime.track_artifact("run-1", Path("out/a.json"))
        runtime.track_artifact("run-1", Path("out/m.json"))
        runtime.finish_run("run-1", status="success")
        runtime.save_pack("run-1")

        run_dir = out / "run-1"
        meta_path = run_dir / "run_metadata.json"
        assert meta_path.exists()
        with open(meta_path) as f:
            meta = json.load(f)
        artifacts = meta.get("artifacts", [])
        assert artifacts == ["out/a.json", "out/m.json", "out/z.json"]

        runtime.cleanup_run("run-1")

    def test_same_artifacts_different_track_order_same_persisted_artifacts_list(self, tmp_path):
        """Same set of artifacts tracked in different order yields same sorted persisted list."""
        out = tmp_path / "out"
        out.mkdir()
        paths = ["out/a.json", "out/b.json", "out/c.json"]

        def run_and_get_artifacts(order, run_id: str):
            runtime = EvidencePackRuntime(output_dir=out)
            runtime.start_run(
                run_id=run_id,
                layer_id="L0",
                autonomy_level=AutonomyLevel.RO,
            )
            for p in order:
                runtime.track_artifact(run_id, Path(p))
            runtime.finish_run(run_id, status="success")
            runtime.save_pack(run_id)
            meta_path = out / run_id / "run_metadata.json"
            with open(meta_path) as f:
                meta = json.load(f)
            runtime.cleanup_run(run_id)
            return meta.get("artifacts", [])

        list1 = run_and_get_artifacts([paths[0], paths[1], paths[2]], "run-1")
        list2 = run_and_get_artifacts([paths[2], paths[0], paths[1]], "run-2")
        assert list1 == list2 == ["out/a.json", "out/b.json", "out/c.json"]
        assert _json_hash({"artifacts": list1}) == _json_hash({"artifacts": list2})
