"""
Run Manifest Generator

Generates deterministic Run Manifests and Operator Outputs for AI Layer runs.

Reference:
- docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
- docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import AutonomyLevel, SoDResult


@dataclass
class RunManifest:
    """
    Deterministic Run Manifest for AI Layer runs.

    Every run MUST produce a manifest as evidence artifact.
    """

    # Run Identity (deterministic)
    run_id: str  # Deterministic hash of layer+models+scope+inputs
    run_type: str  # "dry-run" or "live-run"
    timestamp: str  # ISO8601 (injected for determinism)

    # Layer Information
    layer_id: str
    layer_name: str
    autonomy_level: str  # RO/REC/PROP/EXEC

    # Model Assignment
    primary_model_id: str
    fallback_model_ids: List[str]
    critic_model_id: str

    # Capability Scope
    capability_scope_id: str
    capability_scope_version: str

    # SoD Check
    sod_result: str  # PASS/FAIL
    sod_reason: str
    sod_timestamp: str

    # Registry Version
    matrix_version: str  # e.g., "v1.0"
    registry_version: str

    # Artifacts
    artifacts: List[str] = field(default_factory=list)
    operator_output_path: Optional[str] = None

    # Optional
    operator_notes: str = ""
    inputs_manifest: List[str] = field(default_factory=list)
    outputs_manifest: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (stable key order for JSON)."""
        return {
            # Run identity
            "run_id": self.run_id,
            "run_type": self.run_type,
            "timestamp": self.timestamp,
            # Layer
            "layer_id": self.layer_id,
            "layer_name": self.layer_name,
            "autonomy_level": self.autonomy_level,
            # Models
            "primary_model_id": self.primary_model_id,
            "fallback_model_ids": self.fallback_model_ids,
            "critic_model_id": self.critic_model_id,
            # Capability
            "capability_scope_id": self.capability_scope_id,
            "capability_scope_version": self.capability_scope_version,
            # SoD
            "sod_result": self.sod_result,
            "sod_reason": self.sod_reason,
            "sod_timestamp": self.sod_timestamp,
            # Version
            "matrix_version": self.matrix_version,
            "registry_version": self.registry_version,
            # Artifacts
            "artifacts": sorted(self.artifacts),  # Stable sort
            "operator_output_path": self.operator_output_path,
            "operator_notes": self.operator_notes,
            "inputs_manifest": sorted(self.inputs_manifest),
            "outputs_manifest": sorted(self.outputs_manifest),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string (stable key order)."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def save(self, output_path: Path) -> None:
        """Save manifest to JSON file."""
        with open(output_path, "w") as f:
            f.write(self.to_json())


class RunManifestGenerator:
    """
    Generates deterministic Run Manifests for Layer runs.

    Usage:
        generator = RunManifestGenerator()
        manifest = generator.generate(
            layer_id="L2",
            primary_model_id="gpt-5.2-pro",
            critic_model_id="deepseek-r1",
            scope_id="L2_market_outlook",
            sod_result=SoDResult.PASS
        )
        manifest.save(Path("out/run_manifest.json"))
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
        layer_id: str,
        layer_name: str,
        autonomy_level: str,
        primary_model_id: str,
        fallback_model_ids: List[str],
        critic_model_id: str,
        capability_scope_id: str,
        capability_scope_version: str,
        sod_result: SoDResult,
        sod_reason: str,
        matrix_version: str = "v1.0",
        registry_version: str = "1.0",
        run_type: str = "dry-run",
        operator_notes: str = "",
        inputs_manifest: Optional[List[str]] = None,
        outputs_manifest: Optional[List[str]] = None,
    ) -> RunManifest:
        """
        Generate Run Manifest.

        Args:
            layer_id: Layer identifier (e.g., "L2")
            layer_name: Layer name (e.g., "Market Outlook")
            autonomy_level: Autonomy level (RO/REC/PROP/EXEC)
            primary_model_id: Primary model ID
            fallback_model_ids: Fallback model IDs
            critic_model_id: Critic model ID
            capability_scope_id: Capability scope ID
            capability_scope_version: Capability scope version
            sod_result: SoD check result
            sod_reason: SoD check reason
            matrix_version: Matrix version (default: "v1.0")
            registry_version: Registry version (default: "1.0")
            run_type: Run type (default: "dry-run")
            operator_notes: Optional operator notes
            inputs_manifest: Optional inputs list
            outputs_manifest: Optional outputs list

        Returns:
            RunManifest
        """
        # Generate deterministic run_id
        run_id = self._generate_run_id(
            layer_id=layer_id,
            primary_model_id=primary_model_id,
            critic_model_id=critic_model_id,
            capability_scope_id=capability_scope_id,
        )

        # Timestamp (injected or now)
        if self.clock:
            timestamp = self.clock.isoformat()
            sod_timestamp = self.clock.isoformat()
        else:
            now = datetime.now(timezone.utc)
            timestamp = now.isoformat()
            sod_timestamp = now.isoformat()

        return RunManifest(
            run_id=run_id,
            run_type=run_type,
            timestamp=timestamp,
            layer_id=layer_id,
            layer_name=layer_name,
            autonomy_level=autonomy_level,
            primary_model_id=primary_model_id,
            fallback_model_ids=fallback_model_ids,
            critic_model_id=critic_model_id,
            capability_scope_id=capability_scope_id,
            capability_scope_version=capability_scope_version,
            sod_result=sod_result.value,
            sod_reason=sod_reason,
            sod_timestamp=sod_timestamp,
            matrix_version=matrix_version,
            registry_version=registry_version,
            operator_notes=operator_notes,
            inputs_manifest=inputs_manifest or [],
            outputs_manifest=outputs_manifest or [],
        )

    def _generate_run_id(
        self, layer_id: str, primary_model_id: str, critic_model_id: str, capability_scope_id: str
    ) -> str:
        """
        Generate deterministic run_id from inputs.

        Args:
            layer_id: Layer identifier
            primary_model_id: Primary model ID
            critic_model_id: Critic model ID
            capability_scope_id: Capability scope ID

        Returns:
            Deterministic run_id (SHA256 prefix)
        """
        # Stable concatenation
        parts = [layer_id, primary_model_id, critic_model_id, capability_scope_id]
        combined = "|".join(parts)
        hash_digest = hashlib.sha256(combined.encode()).hexdigest()
        # Return short prefix (first 16 chars)
        return f"{layer_id}-{hash_digest[:16]}"


def generate_operator_output(
    manifest: RunManifest,
    findings: Optional[List[str]] = None,
    actions: Optional[List[str]] = None,
) -> str:
    """
    Generate Operator Output (Markdown) from Run Manifest.

    Args:
        manifest: Run Manifest
        findings: Optional list of findings
        actions: Optional list of actions

    Returns:
        Markdown string
    """
    findings = findings or []
    actions = actions or []

    md = f"""# AI Autonomy — Operator Output (Kurzbericht)

**Run ID:** {manifest.run_id}
**Run Type:** {manifest.run_type}
**Timestamp:** {manifest.timestamp}
**Layer:** {manifest.layer_id} ({manifest.layer_name})
**Autonomy:** {manifest.autonomy_level}

---

## Models

- **Primary:** {manifest.primary_model_id}
- **Fallback:** {", ".join(manifest.fallback_model_ids)}
- **Critic:** {manifest.critic_model_id}

---

## Capability Scope

- **ID:** {manifest.capability_scope_id}
- **Version:** {manifest.capability_scope_version}

---

## SoD Check

- **Result:** {manifest.sod_result}
- **Reason:** {manifest.sod_reason}
- **Timestamp:** {manifest.sod_timestamp}

---

## Findings

"""
    if findings:
        for i, finding in enumerate(findings, 1):
            md += f"{i}. {finding}\n"
    else:
        md += "- Keine Findings\n"

    md += "\n---\n\n## Actions\n\n"
    if actions:
        for i, action in enumerate(actions, 1):
            md += f"{i}. {action}\n"
    else:
        md += "- Keine Actions erforderlich\n"

    md += f"\n---\n\n## Operator Notes\n\n{manifest.operator_notes or 'Keine Notizen'}\n\n"
    md += f"---\n\n## Artifacts\n\n"
    if manifest.artifacts:
        for artifact in sorted(manifest.artifacts):
            md += f"- `{artifact}`\n"
    else:
        md += "- Keine Artifacts\n"

    md += "\n---\n\n**END OF OPERATOR OUTPUT**\n"
    return md
