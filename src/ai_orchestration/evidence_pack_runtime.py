"""
Evidence Pack Runtime Helper

Provides runtime helpers for automatic Evidence Pack creation
during Layer Runs (Phase 4A).

Usage:
    from src.ai_orchestration.evidence_pack_runtime import EvidencePackRuntime

    runtime = EvidencePackRuntime(output_dir=".artifacts/evidence_packs")
    runtime.start_run(run_id="run-001", layer_id="L0", autonomy_level=AutonomyLevel.REC)
    # ... perform layer run ...
    runtime.finish_run(run_id="run-001", status="success")
    runtime.save_pack(run_id="run-001")
"""

import hashlib
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .evidence_pack import EvidencePackMetadata, create_evidence_pack, save_evidence_pack
from .models import AutonomyLevel, LayerRunMetadata, RunLogging


class EvidencePackRuntime:
    """
    Runtime helper for automatic Evidence Pack creation.

    Manages Evidence Pack lifecycle during Layer Runs:
    - Automatic pack creation
    - Git SHA tracking
    - Config fingerprinting
    - Artifact tracking
    - Validation
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize runtime helper.

        Args:
            output_dir: Output directory for Evidence Packs
                       (default: .artifacts/evidence_packs)
        """
        if output_dir is None:
            # Default: .artifacts/evidence_packs
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / ".artifacts" / "evidence_packs"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Active runs (in-flight Evidence Packs)
        self.active_runs: Dict[str, EvidencePackMetadata] = {}

        # Run metadata (start/finish times, status)
        self.run_metadata: Dict[str, Dict[str, Any]] = {}

    def _get_git_sha(self) -> str:
        """
        Get current Git SHA.

        Returns:
            Git SHA (40-char hex), or "local-dev" if not in git repo

        Note: Uses GITHUB_SHA env var if available (CI environment),
              otherwise falls back to git command (local).
        """
        # Try GITHUB_SHA first (CI)
        github_sha = os.getenv("GITHUB_SHA")
        if github_sha:
            return github_sha

        # Fallback: git command (local)
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            # Not in git repo or git not available
            return "local-dev"

    def _compute_config_fingerprint(self, config_paths: Optional[List[Path]] = None) -> str:
        """
        Compute fingerprint of config files.

        Args:
            config_paths: List of config file paths to fingerprint
                         (default: config/*.toml)

        Returns:
            SHA256 hex digest of all config files (sorted, concatenated)
        """
        if config_paths is None:
            # Default: all config/*.toml files
            repo_root = Path(__file__).parent.parent.parent
            config_dir = repo_root / "config"
            config_paths = sorted(config_dir.glob("*.toml"))

        # Concatenate all config files (sorted)
        hasher = hashlib.sha256()
        for path in sorted(config_paths):
            if path.exists():
                hasher.update(path.read_bytes())

        return hasher.hexdigest()

    def start_run(
        self,
        run_id: str,
        layer_id: str,
        autonomy_level: AutonomyLevel,
        phase_id: Optional[str] = None,
        description: str = "",
        registry_version: str = "1.0",
        config_paths: Optional[List[Path]] = None,
    ) -> EvidencePackMetadata:
        """
        Start a Layer Run and create Evidence Pack.

        Args:
            run_id: Unique run ID (e.g., UUID)
            layer_id: Layer ID (L0-L6)
            autonomy_level: Autonomy level
            phase_id: Phase identifier (default: "runtime-{layer_id}")
            description: Run description
            registry_version: Model registry version
            config_paths: Config files to fingerprint (optional)

        Returns:
            EvidencePackMetadata instance

        Raises:
            ValueError: If run_id already active
        """
        if run_id in self.active_runs:
            raise ValueError(f"Run {run_id} is already active")

        # Default phase_id
        if phase_id is None:
            phase_id = f"runtime-{layer_id}"

        # Create Evidence Pack
        evidence_pack_id = f"EVP-{layer_id}-{run_id[:8]}"
        pack = create_evidence_pack(
            evidence_pack_id=evidence_pack_id,
            phase_id=phase_id,
            layer_id=layer_id,
            autonomy_level=autonomy_level,
            registry_version=registry_version,
            description=description,
        )

        # Store run metadata
        self.run_metadata[run_id] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": self._get_git_sha(),
            "config_fingerprint": self._compute_config_fingerprint(config_paths),
            "artifacts": [],
            "status": "running",
            "finished_at": None,
        }

        # Store active pack
        self.active_runs[run_id] = pack

        return pack

    def add_layer_run_metadata(
        self,
        run_id: str,
        layer_name: str,
        primary_model_id: str,
        critic_model_id: str,
        capability_scope_id: str,
        matrix_version: str,
        fallback_model_id: Optional[str] = None,
    ) -> None:
        """
        Add Layer Run Metadata to active Evidence Pack.

        Args:
            run_id: Run ID
            layer_name: Layer name
            primary_model_id: Primary model ID
            critic_model_id: Critic model ID
            capability_scope_id: Capability scope ID
            matrix_version: Matrix version
            fallback_model_id: Fallback model ID (optional)

        Raises:
            ValueError: If run_id not active
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Run {run_id} is not active")

        pack = self.active_runs[run_id]
        pack.layer_run_metadata = LayerRunMetadata(
            layer_id=pack.layer_id,
            layer_name=layer_name,
            autonomy_level=pack.autonomy_level,
            primary_model_id=primary_model_id,
            critic_model_id=critic_model_id,
            capability_scope_id=capability_scope_id,
            matrix_version=matrix_version,
            fallback_model_id=fallback_model_id,
        )

    def add_run_log(
        self,
        run_id: str,
        log_run_id: str,
        prompt_hash: str,
        artifact_hash: str,
        inputs_manifest: List[str],
        outputs_manifest: List[str],
        model_id: str,
    ) -> None:
        """
        Add Run Log to active Evidence Pack.

        Args:
            run_id: Evidence Pack run ID
            log_run_id: Run log run ID (can be same as run_id)
            prompt_hash: SHA256 of prompt
            artifact_hash: SHA256 of artifact
            inputs_manifest: List of input files
            outputs_manifest: List of output files
            model_id: Model ID used

        Raises:
            ValueError: If run_id not active
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Run {run_id} is not active")

        pack = self.active_runs[run_id]
        run_log = RunLogging(
            run_id=log_run_id,
            prompt_hash=prompt_hash,
            artifact_hash=artifact_hash,
            inputs_manifest=inputs_manifest,
            outputs_manifest=outputs_manifest,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            model_id=model_id,
        )
        pack.run_logs.append(run_log)

    def track_artifact(self, run_id: str, artifact_path: Path) -> None:
        """
        Track artifact in run metadata.

        Args:
            run_id: Run ID
            artifact_path: Path to artifact

        Raises:
            ValueError: If run_id not active
        """
        if run_id not in self.run_metadata:
            raise ValueError(f"Run {run_id} is not active")

        self.run_metadata[run_id]["artifacts"].append(str(artifact_path))

    def finish_run(
        self,
        run_id: str,
        status: str = "success",
        tests_passed: int = 0,
        tests_total: int = 0,
    ) -> None:
        """
        Finish a Layer Run.

        Args:
            run_id: Run ID
            status: Run status (e.g., "success", "failure", "error")
            tests_passed: Number of tests passed
            tests_total: Total number of tests

        Raises:
            ValueError: If run_id not active
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Run {run_id} is not active")

        # Update run metadata
        self.run_metadata[run_id]["status"] = status
        self.run_metadata[run_id]["finished_at"] = datetime.now(timezone.utc).isoformat()

        # Update Evidence Pack
        pack = self.active_runs[run_id]
        pack.validator_run = True
        pack.tests_passed = tests_passed
        pack.tests_total = tests_total

    def save_pack(self, run_id: str, filepath: Optional[Path] = None) -> Path:
        """
        Save Evidence Pack to disk.

        Args:
            run_id: Run ID
            filepath: Target file path (default: .artifacts/evidence_packs/<run_id>/evidence_pack.json)

        Returns:
            Path to saved Evidence Pack

        Raises:
            ValueError: If run_id not active
        """
        if run_id not in self.active_runs:
            raise ValueError(f"Run {run_id} is not active")

        pack = self.active_runs[run_id]

        # Default filepath
        if filepath is None:
            run_dir = self.output_dir / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            filepath = run_dir / "evidence_pack.json"

        # Save pack
        save_evidence_pack(pack, filepath)

        # Also save run metadata (artifacts sorted for deterministic hashes)
        metadata_path = filepath.parent / "run_metadata.json"
        meta = dict(self.run_metadata[run_id])
        meta["artifacts"] = sorted(meta.get("artifacts", []))
        with open(metadata_path, "w") as f:
            json.dump(meta, f, indent=2)

        return filepath

    def cleanup_run(self, run_id: str) -> None:
        """
        Remove run from active runs (after save).

        Args:
            run_id: Run ID
        """
        if run_id in self.active_runs:
            del self.active_runs[run_id]
        if run_id in self.run_metadata:
            del self.run_metadata[run_id]

    def get_pack(self, run_id: str) -> Optional[EvidencePackMetadata]:
        """
        Get active Evidence Pack.

        Args:
            run_id: Run ID

        Returns:
            EvidencePackMetadata instance, or None if not active
        """
        return self.active_runs.get(run_id)


def create_minimal_evidence_pack_for_run(
    run_id: str,
    layer_id: str,
    autonomy_level: AutonomyLevel,
    output_dir: Optional[Path] = None,
    phase_id: Optional[str] = None,
    description: str = "",
) -> Path:
    """
    Convenience function: Create and save minimal Evidence Pack for a run.

    Args:
        run_id: Unique run ID
        layer_id: Layer ID (L0-L6)
        autonomy_level: Autonomy level
        output_dir: Output directory (default: .artifacts/evidence_packs)
        phase_id: Phase identifier (default: "runtime-{layer_id}")
        description: Run description

    Returns:
        Path to saved Evidence Pack
    """
    runtime = EvidencePackRuntime(output_dir=output_dir)
    runtime.start_run(
        run_id=run_id,
        layer_id=layer_id,
        autonomy_level=autonomy_level,
        phase_id=phase_id,
        description=description,
    )
    runtime.finish_run(run_id=run_id, status="success")
    filepath = runtime.save_pack(run_id=run_id)
    runtime.cleanup_run(run_id=run_id)
    return filepath
