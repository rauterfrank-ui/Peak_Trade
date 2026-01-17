"""
Multi-Model Runner with Dry-Run Mode

NO real model API calls. Orchestration validation + artifact generation only.

Reference:
- docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .capability_scope_loader import CapabilityScopeLoader
from .errors import DryRunError, ForbiddenAutonomyError, InvalidLayerError
from .model_registry_loader import ModelRegistryLoader
from .models import AutonomyLevel, SoDResult
from .run_manifest import RunManifest, RunManifestGenerator, generate_operator_output
from .sod_checker import SoDChecker


class MultiModelRunner:
    """
    Multi-Model Runner with Dry-Run Mode.

    NO real model API calls. Orchestration validation + artifact generation only.

    Usage:
        runner = MultiModelRunner()
        manifest = runner.dry_run(
            layer_id="L2",
            primary_model_id="gpt-5.2-pro",
            critic_model_id="deepseek-r1",
            out_dir=Path("out")
        )
    """

    def __init__(
        self,
        registry_loader: Optional[ModelRegistryLoader] = None,
        scope_loader: Optional[CapabilityScopeLoader] = None,
        sod_checker: Optional[SoDChecker] = None,
        clock: Optional[datetime] = None,
    ):
        """
        Initialize runner.

        Args:
            registry_loader: Model registry loader (default: auto)
            scope_loader: Capability scope loader (default: auto)
            sod_checker: SoD checker (default: auto)
            clock: Fixed clock for determinism (default: now)
        """
        self.registry_loader = registry_loader or ModelRegistryLoader()
        self.scope_loader = scope_loader or CapabilityScopeLoader()
        self.sod_checker = sod_checker or SoDChecker()
        self.clock = clock
        self.manifest_generator = RunManifestGenerator(clock=clock)

    def dry_run(
        self,
        layer_id: str,
        primary_model_id: str,
        critic_model_id: str,
        out_dir: Path,
        run_id: Optional[str] = None,
        operator_notes: str = "",
        findings: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
    ) -> RunManifest:
        """
        Perform dry-run: validate orchestration + generate artifacts.

        NO real model API calls.

        Args:
            layer_id: Layer identifier (e.g., "L2")
            primary_model_id: Primary model ID
            critic_model_id: Critic model ID
            out_dir: Output directory for artifacts
            run_id: Optional run_id override (default: auto-generated)
            operator_notes: Optional operator notes
            findings: Optional findings list
            actions: Optional actions list

        Returns:
            RunManifest

        Raises:
            InvalidLayerError: If layer not found
            ForbiddenAutonomyError: If EXEC layer
            DryRunError: If validation fails
        """
        # Validate layer
        try:
            layer_mapping = self.registry_loader.get_layer_mapping(layer_id)
        except Exception as e:
            raise InvalidLayerError(f"Layer {layer_id} not found: {e}")

        # Check for EXEC (forbidden)
        autonomy = layer_mapping.autonomy.upper()
        if "EXEC" in autonomy and "forbidden" not in autonomy.lower():
            raise ForbiddenAutonomyError(
                f"Layer {layer_id} has EXEC autonomy. Execution is forbidden without approval."
            )

        # Validate models exist in registry
        try:
            primary_model = self.registry_loader.get_model(primary_model_id)
            critic_model = self.registry_loader.get_model(critic_model_id)
        except Exception as e:
            raise DryRunError(f"Model validation failed: {e}")

        # Load capability scope
        try:
            scope = self.scope_loader.load(layer_id)
        except Exception as e:
            raise DryRunError(f"Capability scope validation failed: {e}")

        # SoD check
        sod_check = self.sod_checker.check(
            proposer_model_id=primary_model_id,
            critic_model_id=critic_model_id,
            proposer_provider=primary_model.provider,
            critic_provider=critic_model.provider,
        )

        if sod_check.result == SoDResult.FAIL:
            raise DryRunError(f"SoD check failed: {sod_check.reason}")

        # Generate manifest
        manifest = self.manifest_generator.generate(
            layer_id=layer_id,
            layer_name=layer_mapping.description,
            autonomy_level=layer_mapping.autonomy,
            primary_model_id=primary_model_id,
            fallback_model_ids=layer_mapping.fallback,
            critic_model_id=critic_model_id,
            capability_scope_id=scope.layer_id,
            capability_scope_version=scope.version,
            sod_result=sod_check.result,
            sod_reason=sod_check.reason,
            matrix_version="v1.0",
            registry_version="1.0",
            run_type="dry-run",
            operator_notes=operator_notes,
        )

        # Override run_id if provided
        if run_id:
            manifest.run_id = run_id

        # Create output directory
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write run_manifest.json
        manifest_path = out_dir / "run_manifest.json"
        manifest.save(manifest_path)
        manifest.artifacts.append(str(manifest_path))

        # Write operator_output.md
        operator_output = generate_operator_output(
            manifest=manifest, findings=findings, actions=actions
        )
        output_path = out_dir / "operator_output.md"
        output_path.write_text(operator_output)
        manifest.artifacts.append(str(output_path))
        manifest.operator_output_path = str(output_path)

        # Update manifest with artifact paths (re-save)
        manifest.save(manifest_path)

        return manifest
