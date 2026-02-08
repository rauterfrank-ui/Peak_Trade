"""
L3 Trade Plan Advisory Runner (scaffold).

Deterministic, pointer-only inputs; files-only tooling; no live execution, no promotion, no learning writes.
Mirrors L1/L2 structure: loads mapping + scope via loaders; returns deterministic output envelope + artifacts list (no raw).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .capability_scope_loader import CapabilityScope, CapabilityScopeLoader
from .errors import OrchestrationError
from .l3_contracts import accepts_l3_pointer_only_input, artifact_paths_from_pointer_only_input
from .model_registry_loader import ModelRegistryLoader
from .models import SoDResult
from .run_manifest import RunManifest, RunManifestGenerator, generate_operator_output
from .sod_checker import SoDChecker


class L3RunnerError(OrchestrationError):
    """L3 Runner error."""

    pass


class L3PointerOnlyViolation(L3RunnerError):
    """Input is not pointer-only (forbidden raw keys or non-pointer artifacts)."""

    pass


class L3ToolingViolation(L3RunnerError):
    """Scope allows more than files (e.g. web) — L3 must be files-only."""

    pass


@dataclass
class L3RunResult:
    """Result of L3 Trade Plan Advisory run (scaffold: deterministic envelope, no raw)."""

    run_id: str
    evidence_pack_id: str
    layer_id: str
    mode: str
    sod_result: str
    artifacts: List[str]  # Paths only (no raw content)
    summary: str


class L3Runner:
    """
    L3 Trade Plan Advisory Runner (scaffold).

    Accepts only pointer-only inputs; enforces tooling == files only; returns deterministic artifact list.
    NO live execution; no promotion; no learning writes.
    """

    def __init__(
        self,
        registry_loader: Optional[ModelRegistryLoader] = None,
        scope_loader: Optional[CapabilityScopeLoader] = None,
        sod_checker: Optional[SoDChecker] = None,
        clock: Optional[datetime] = None,
    ):
        self.registry_loader = registry_loader or ModelRegistryLoader()
        self.scope_loader = scope_loader or CapabilityScopeLoader()
        self.sod_checker = sod_checker or SoDChecker()
        self.clock = clock
        self.manifest_generator = RunManifestGenerator(clock=clock)

    def run(
        self,
        inputs: Dict,
        mode: str = "dry-run",
        out_dir: Optional[Path] = None,
        operator_notes: str = "",
        findings: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
    ) -> L3RunResult:
        """
        Run L3 Trade Plan Advisory (scaffold: validate + manifest + artifact list only).

        Args:
            inputs: Pointer-only input (e.g. FeatureView/EvidenceCapsule style dict); no payload/raw/transcript.
            mode: Run mode (e.g. "dry-run").
            out_dir: Output directory for artifacts.
            operator_notes: Optional operator notes.
            findings: Optional findings list.
            actions: Optional actions list.

        Returns:
            L3RunResult with run_id, evidence_pack_id, artifacts (paths only), summary.

        Raises:
            L3PointerOnlyViolation: If inputs contain forbidden raw keys or non-pointer artifacts.
            L3ToolingViolation: If scope allows tools other than files.
            L3RunnerError: If SoD fails or scope/registry load fails.
        """
        if not accepts_l3_pointer_only_input(inputs):
            raise L3PointerOnlyViolation(
                "L3 accepts only pointer-only inputs (no payload/raw/transcript; artifacts = path+sha256 only)."
            )

        if not out_dir:
            out_dir = Path("evidence_packs") / f"L3_TRADE_PLAN_{self._get_timestamp_str()}"

        # Load layer mapping and scope
        layer_mapping = self.registry_loader.get_layer_mapping("L3")
        primary_model_id = layer_mapping.primary
        critic_model_id = layer_mapping.critic
        scope = self.scope_loader.load("L3")

        # Enforce tooling == files only
        if scope.tooling_allowed != ["files"]:
            raise L3ToolingViolation(
                f"L3 scope must allow only ['files']; got tooling_allowed={scope.tooling_allowed!r}"
            )

        # SoD check
        sod_check = self.sod_checker.check(
            proposer_model_id=primary_model_id,
            critic_model_id=critic_model_id,
        )
        if sod_check.result == SoDResult.FAIL:
            raise L3RunnerError(
                f"SoD check failed: {sod_check.reason}. "
                f"Proposer ({primary_model_id}) != Critic ({critic_model_id}) required."
            )

        # Deterministic run_id and evidence_pack_id
        run_id = self._generate_run_id(
            layer_id="L3",
            primary_model_id=primary_model_id,
            critic_model_id=critic_model_id,
            scope=scope,
        )
        evidence_pack_id = f"EVP-L3-{self._get_timestamp_str()}-{run_id[:8]}"

        # Generate run manifest
        run_manifest = self.manifest_generator.generate(
            layer_id="L3",
            layer_name="Trade Plan Advisory",
            autonomy_level="REC",
            primary_model_id=primary_model_id,
            fallback_model_ids=layer_mapping.fallback,
            critic_model_id=critic_model_id,
            capability_scope_id=scope.layer_id,
            capability_scope_version=scope.version,
            sod_result=sod_check.result,
            sod_reason=sod_check.reason,
            operator_notes=operator_notes,
            inputs_manifest=artifact_paths_from_pointer_only_input(inputs),
        )

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write run_manifest.json
        manifest_path = out_dir / "run_manifest.json"
        run_manifest.save(manifest_path)
        artifact_paths: List[str] = [str(manifest_path)]

        # Write operator_output.md (deterministic, no raw)
        operator_output = generate_operator_output(
            manifest=run_manifest, findings=findings, actions=actions
        )
        output_path = out_dir / "operator_output.md"
        output_path.write_text(operator_output)
        artifact_paths.append(str(output_path))
        run_manifest.operator_output_path = str(output_path)
        run_manifest.artifacts = list(artifact_paths)
        run_manifest.save(manifest_path)

        summary = (
            f"L3 Trade Plan Advisory run completed (scaffold).\n"
            f"  Run ID: {run_id}\n"
            f"  Evidence Pack ID: {evidence_pack_id}\n"
            f"  Mode: {mode}\n"
            f"  SoD: {sod_check.result.value}\n"
            f"  Tooling: files only\n"
            f"  Artifacts: {len(artifact_paths)} files (pointer-only)"
        )

        return L3RunResult(
            run_id=run_id,
            evidence_pack_id=evidence_pack_id,
            layer_id="L3",
            mode=mode,
            sod_result=sod_check.result.value,
            artifacts=artifact_paths,
            summary=summary,
        )

    def _get_timestamp_str(self) -> str:
        if self.clock:
            return self.clock.strftime("%Y%m%d_%H%M%S")
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    def _generate_run_id(
        self,
        layer_id: str,
        primary_model_id: str,
        critic_model_id: str,
        scope: CapabilityScope,
    ) -> str:
        import hashlib

        parts = [layer_id, primary_model_id, critic_model_id, scope.layer_id]
        combined = "|".join(parts)
        h = hashlib.sha256(combined.encode()).hexdigest()
        return f"{layer_id}-{h[:16]}"
