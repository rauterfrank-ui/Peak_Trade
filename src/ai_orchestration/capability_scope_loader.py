"""
Capability Scope Loader

Loads and parses config/capability_scopes/*.toml into structured Python objects.

Reference:
- config/capability_scopes/*.toml
- docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomli as toml
except ImportError:
    import tomllib as toml

from .errors import CapabilityScopeError


@dataclass
class CapabilityScope:
    """Parsed capability scope configuration for a layer."""

    layer_id: str
    description: str
    autonomy_level: str
    version: str
    effective_date: str

    # Models
    primary: str
    fallback: str
    critic: str

    # Inputs/Outputs/Tooling
    inputs_allowed: List[str]
    inputs_forbidden: List[str]
    outputs_allowed: List[str]
    outputs_forbidden: List[str]
    tooling_allowed: List[str]
    tooling_forbidden: List[str]

    # Constraints
    constraints: Dict[str, Any]

    # Logging
    required_log_fields: List[str]

    # Safety
    safety_checks: List[str]
    alert_on_violation: bool
    alert_channel: str

    # Optional
    web_access: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None


class CapabilityScopeLoader:
    """
    Loads and validates capability scope TOML files.

    Usage:
        loader = CapabilityScopeLoader()
        scope = loader.load("L2")
        assert "files" in scope.tooling_allowed
    """

    def __init__(self, scopes_dir: Optional[Path] = None):
        """
        Initialize loader.

        Args:
            scopes_dir: Path to capability_scopes directory (default: config/capability_scopes)
        """
        if scopes_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            scopes_dir = repo_root / "config" / "capability_scopes"

        self.scopes_dir = scopes_dir

    def load(self, layer_id: str) -> CapabilityScope:
        """
        Load capability scope for a layer.

        Args:
            layer_id: Layer identifier (e.g., "L2")

        Returns:
            CapabilityScope object

        Raises:
            CapabilityScopeError: If file not found or invalid
        """
        # Try common naming patterns
        possible_paths = [
            self.scopes_dir / f"{layer_id}_*.toml",
            self.scopes_dir / f"{layer_id.lower()}_*.toml",
        ]

        scope_path = None
        for pattern in possible_paths:
            matches = list(self.scopes_dir.glob(pattern.name))
            if matches:
                scope_path = matches[0]
                break

        if scope_path is None:
            raise CapabilityScopeError(
                f"Capability scope not found for layer {layer_id} in {self.scopes_dir}"
            )

        try:
            with open(scope_path, "rb") as f:
                data = toml.load(f)
        except Exception as e:
            raise CapabilityScopeError(f"Failed to parse {scope_path}: {e}")

        # Validate required sections
        required_sections = ["scope", "models", "inputs", "outputs", "tooling", "logging", "safety"]
        for section in required_sections:
            if section not in data:
                raise CapabilityScopeError(f"{scope_path} missing required section: {section}")

        # Parse sections
        try:
            scope_meta = data["scope"]
            models = data["models"]
            inputs = data["inputs"]
            outputs = data["outputs"]
            tooling = data["tooling"]
            logging = data["logging"]
            safety = data["safety"]
            constraints = data.get("constraints", {})
            web_access = data.get("web_access")
            validation = data.get("validation")

            return CapabilityScope(
                layer_id=scope_meta["layer_id"],
                description=scope_meta["description"],
                autonomy_level=scope_meta["autonomy_level"],
                version=scope_meta["version"],
                effective_date=scope_meta["effective_date"],
                primary=models["primary"],
                fallback=models["fallback"],
                critic=models["critic"],
                inputs_allowed=inputs["allowed"],
                inputs_forbidden=inputs["forbidden"],
                outputs_allowed=outputs["allowed"],
                outputs_forbidden=outputs["forbidden"],
                tooling_allowed=tooling["allowed"],
                tooling_forbidden=tooling["forbidden"],
                constraints=constraints,
                required_log_fields=logging["required_fields"],
                safety_checks=safety["safety_checks"],
                alert_on_violation=safety["alert_on_violation"],
                alert_channel=safety["alert_channel"],
                web_access=web_access,
                validation=validation,
            )
        except KeyError as e:
            raise CapabilityScopeError(f"{scope_path} missing required field: {e}")

    def validate_input(self, layer_id: str, input_path: str) -> bool:
        """
        Check if input is allowed by capability scope.

        Args:
            layer_id: Layer identifier
            input_path: Input file path to validate

        Returns:
            True if allowed, False if forbidden

        Raises:
            CapabilityScopeError: If scope not found
        """
        scope = self.load(layer_id)

        # Check forbidden first (deny takes precedence)
        for pattern in scope.inputs_forbidden:
            if self._matches_pattern(input_path, pattern):
                return False

        # Check allowed
        for pattern in scope.inputs_allowed:
            if self._matches_pattern(input_path, pattern):
                return True

        return False

    def validate_output(self, layer_id: str, output_type: str) -> bool:
        """
        Check if output type is allowed by capability scope.

        Args:
            layer_id: Layer identifier
            output_type: Output type to validate (e.g., "ScenarioReport")

        Returns:
            True if allowed, False if forbidden

        Raises:
            CapabilityScopeError: If scope not found
        """
        scope = self.load(layer_id)

        # Check forbidden first
        if output_type in scope.outputs_forbidden:
            return False

        # Check allowed
        if output_type in scope.outputs_allowed:
            return True

        return False

    def validate_tooling(self, layer_id: str, tool: str) -> bool:
        """
        Check if tool is allowed by capability scope.

        Args:
            layer_id: Layer identifier
            tool: Tool name to validate (e.g., "web", "files")

        Returns:
            True if allowed, False if forbidden

        Raises:
            CapabilityScopeError: If scope not found
        """
        scope = self.load(layer_id)

        # Check forbidden first
        if tool in scope.tooling_forbidden:
            return False

        # Check allowed
        if tool in scope.tooling_allowed:
            return True

        return False

    def get_envelope_tooling_allowlist(self, layer_id: str) -> List[str]:
        """
        Return the tooling allowlist for the layer envelope (orchestrator boundary).

        Call this when building a LayerEnvelope so tooling selection is always
        derived from capability scope; never hardcode web/shell for files-only layers.

        Args:
            layer_id: Layer identifier (e.g., "L0", "L3", "L4")

        Returns:
            List of allowed tool names (e.g., ["files"] or ["web", "files"])

        Raises:
            CapabilityScopeError: If scope not found
        """
        scope = self.load(layer_id)
        return list(scope.tooling_allowed)

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """
        Simple glob-like pattern matching.

        Args:
            path: Path to check
            pattern: Pattern with wildcards (e.g., "docs/**/*.md")

        Returns:
            True if path matches pattern
        """
        # Simplified pattern matching (no full glob support)
        # Handle wildcards: ** (any dir), * (any file)
        if "**" in pattern:
            # Split on ** and check prefix/suffix
            parts = pattern.split("**")
            if len(parts) == 2:
                prefix, suffix = parts
                return path.startswith(prefix.rstrip("/")) and path.endswith(suffix.lstrip("/"))

        if "*" in pattern:
            # Basic wildcard matching
            import re

            regex = pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(regex, path))

        # Exact match or contains
        return pattern in path or path.startswith(pattern)
