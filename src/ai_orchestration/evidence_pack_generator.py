"""
Evidence Pack Generator

Generates Evidence Pack bundles for AI Layer runs with deterministic artifacts.

Reference:
- docs/governance/ai_autonomy/PHASE3_L2_MARKET_OUTLOOK_PILOT.md
- docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import OrchestrationError
from .model_client import ModelResponse
from .models import SoDResult
from .run_manifest import RunManifest, generate_operator_output


class EvidencePackError(OrchestrationError):
    """Evidence pack generation error."""

    pass


@dataclass
class ProposerArtifact:
    """Proposer model artifact."""

    model_id: str
    run_id: str
    prompt_hash: str
    output_hash: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CriticArtifact:
    """Critic model artifact."""

    model_id: str
    run_id: str
    prompt_hash: str
    output_hash: str
    content: str
    decision: str  # APPROVE, APPROVE_WITH_CHANGES, REJECT
    rationale: str
    evidence_ids: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityScopeCheck:
    """Capability scope validation result."""

    result: str  # PASS, FAIL
    violations: List[str]
    checked_outputs: List[str]
    timestamp: str


class EvidencePackGenerator:
    """
    Generates Evidence Pack bundles for AI Layer runs.

    Evidence Pack Bundle contains:
    - evidence_pack.json (metadata + index)
    - run_manifest.json (from Phase 2)
    - operator_output.md (from Phase 2)
    - proposer_output.json (proposer model output)
    - critic_output.json (critic model output)
    - sod_check.json (SoD validation result)
    - capability_scope_check.json (capability scope validation)
    """

    def __init__(self, clock: Optional[datetime] = None):
        """
        Initialize generator.

        Args:
            clock: Optional fixed datetime for determinism (default: now)
        """
        self.clock = clock

    def generate(
        self,
        evidence_pack_id: str,
        layer_id: str,
        layer_name: str,
        run_manifest: RunManifest,
        proposer_artifact: ProposerArtifact,
        critic_artifact: CriticArtifact,
        sod_result: SoDResult,
        sod_reason: str,
        capability_scope_check: CapabilityScopeCheck,
        out_dir: Path,
        mode: str = "replay",
        network_used: bool = False,
        operator_notes: str = "",
        findings: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """
        Generate Evidence Pack bundle.

        Args:
            evidence_pack_id: Evidence Pack ID (e.g., "EVP-L2-2026-01-10-001")
            layer_id: Layer ID
            layer_name: Layer name
            run_manifest: Run Manifest (from Phase 2)
            proposer_artifact: Proposer model artifact
            critic_artifact: Critic model artifact
            sod_result: SoD check result
            sod_reason: SoD check reason
            capability_scope_check: Capability scope validation
            out_dir: Output directory for artifacts
            mode: Run mode (replay, live, record)
            network_used: Whether network was used
            operator_notes: Optional operator notes
            findings: Optional findings list
            actions: Optional actions list

        Returns:
            Dict of artifact paths

        Raises:
            EvidencePackError: If generation fails
        """
        # Ensure output directory exists
        out_dir.mkdir(parents=True, exist_ok=True)

        artifacts = {}

        # 1. Generate run_manifest.json
        manifest_path = out_dir / "run_manifest.json"
        run_manifest.save(manifest_path)
        artifacts["run_manifest"] = manifest_path

        # 2. Generate operator_output.md
        operator_output = generate_operator_output(
            manifest=run_manifest,
            findings=findings,
            actions=actions,
        )
        output_path = out_dir / "operator_output.md"
        output_path.write_text(operator_output)
        artifacts["operator_output"] = output_path

        # 3. Generate proposer_output.json
        proposer_path = out_dir / "proposer_output.json"
        proposer_data = {
            "model_id": proposer_artifact.model_id,
            "run_id": proposer_artifact.run_id,
            "prompt_hash": proposer_artifact.prompt_hash,
            "output_hash": proposer_artifact.output_hash,
            "content": self._redact_content(proposer_artifact.content),
            "metadata": proposer_artifact.metadata,
        }
        self._write_json(proposer_path, proposer_data)
        artifacts["proposer_output"] = proposer_path

        # 4. Generate critic_output.json
        critic_path = out_dir / "critic_output.json"
        critic_data = {
            "model_id": critic_artifact.model_id,
            "run_id": critic_artifact.run_id,
            "prompt_hash": critic_artifact.prompt_hash,
            "output_hash": critic_artifact.output_hash,
            "content": self._redact_content(critic_artifact.content),
            "decision": critic_artifact.decision,
            "rationale": critic_artifact.rationale,
            "evidence_ids": sorted(critic_artifact.evidence_ids),
            "metadata": critic_artifact.metadata,
        }
        self._write_json(critic_path, critic_data)
        artifacts["critic_output"] = critic_path

        # 5. Generate sod_check.json
        sod_path = out_dir / "sod_check.json"
        sod_data = {
            "proposer_model_id": proposer_artifact.model_id,
            "critic_model_id": critic_artifact.model_id,
            "result": sod_result.value,
            "reason": sod_reason,
            "timestamp": self._get_timestamp(),
        }
        self._write_json(sod_path, sod_data)
        artifacts["sod_check"] = sod_path

        # 6. Generate capability_scope_check.json
        scope_path = out_dir / "capability_scope_check.json"
        scope_data = {
            "result": capability_scope_check.result,
            "violations": sorted(capability_scope_check.violations),
            "checked_outputs": sorted(capability_scope_check.checked_outputs),
            "timestamp": capability_scope_check.timestamp,
        }
        self._write_json(scope_path, scope_data)
        artifacts["capability_scope_check"] = scope_path

        # 7. Generate evidence_pack.json (metadata + index)
        evidence_pack_data = {
            "evidence_pack_id": evidence_pack_id,
            "evidence_pack_version": "2.0",
            "creation_timestamp": self._get_timestamp(),
            "layer_id": layer_id,
            "layer_name": layer_name,
            "run_id": run_manifest.run_id,
            "mode": mode,
            "network_used": network_used,
            "proposer": {
                "model_id": proposer_artifact.model_id,
                "run_id": proposer_artifact.run_id,
                "prompt_hash": proposer_artifact.prompt_hash,
                "output_hash": proposer_artifact.output_hash,
                "artifact_path": "proposer_output.json",
            },
            "critic": {
                "model_id": critic_artifact.model_id,
                "run_id": critic_artifact.run_id,
                "prompt_hash": critic_artifact.prompt_hash,
                "output_hash": critic_artifact.output_hash,
                "artifact_path": "critic_output.json",
            },
            "sod_check": {
                "result": sod_result.value,
                "reason": sod_reason,
                "artifact_path": "sod_check.json",
            },
            "capability_scope_check": {
                "result": capability_scope_check.result,
                "violations": sorted(capability_scope_check.violations),
                "artifact_path": "capability_scope_check.json",
            },
            "artifacts": sorted(
                [
                    "run_manifest.json",
                    "operator_output.md",
                    "proposer_output.json",
                    "critic_output.json",
                    "sod_check.json",
                    "capability_scope_check.json",
                    "evidence_pack.json",
                ]
            ),
            "operator_notes": operator_notes,
            "matrix_version": run_manifest.matrix_version,
            "registry_version": run_manifest.registry_version,
        }

        evidence_pack_path = out_dir / "evidence_pack.json"
        self._write_json(evidence_pack_path, evidence_pack_data)
        artifacts["evidence_pack"] = evidence_pack_path

        return artifacts

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON with stable ordering."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _get_timestamp(self) -> str:
        """Get timestamp (injected or now)."""
        if self.clock:
            return self.clock.isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _redact_content(self, content: str) -> str:
        """
        Redact sensitive content from artifacts.

        Currently a pass-through, but can be extended to:
        - Remove PII
        - Redact secrets/API keys
        - Truncate long outputs
        """
        # TODO: Add redaction rules if needed
        return content

    @staticmethod
    def compute_output_hash(content: str) -> str:
        """Compute SHA256 hash of output content."""
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
