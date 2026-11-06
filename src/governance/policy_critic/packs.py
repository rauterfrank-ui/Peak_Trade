"""
Policy Pack Loader and Pack-aware PolicyCritic.

Policy Packs allow environment-specific rule configurations:
- CI: balanced (block critical, warn on risky)
- Research: permissive (except secrets/live-unlock)
- Live-Adjacent: strict (fail-closed on everything)
"""

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .models import Severity
from .rules import PolicyRule


@dataclass
class PolicyPack:
    """A policy pack configuration."""

    pack_id: str
    version: str
    description: str
    enabled_rules: List[str]
    severity_overrides: Dict[str, str] = field(default_factory=dict)
    critical_paths: List[str] = field(default_factory=list)
    required_context_keys: List[str] = field(default_factory=list)
    default_action_on_error: str = "REVIEW_REQUIRED"
    settings: Dict = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Compute stable hash of pack configuration for audit trail."""
        # Include all fields that affect policy behavior
        hash_input = (
            f"{self.pack_id}:{self.version}:"
            f"{sorted(self.enabled_rules)}:"
            f"{sorted(self.severity_overrides.items())}:"
            f"{sorted(self.critical_paths)}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]


class PackLoader:
    """Loads and manages policy packs."""

    def __init__(self, pack_dir: Optional[Path] = None):
        """
        Initialize pack loader.

        Args:
            pack_dir: Directory containing .yml pack files (defaults to repo root/policy_packs)
        """
        if pack_dir is None:
            # Default to policy_packs/ at repo root
            pack_dir = Path(__file__).parent.parent.parent.parent / "policy_packs"
        self.pack_dir = Path(pack_dir)
        self._cache: Dict[str, PolicyPack] = {}

    def load_pack(self, pack_id: str) -> PolicyPack:
        """
        Load a policy pack by ID.

        Args:
            pack_id: Pack identifier (e.g., 'ci', 'research', 'live_adjacent')

        Returns:
            PolicyPack instance

        Raises:
            FileNotFoundError: If pack file doesn't exist
            ValueError: If pack YAML is invalid
        """
        # Check cache first
        if pack_id in self._cache:
            return self._cache[pack_id]

        # Load from file
        pack_file = self.pack_dir / f"{pack_id}.yml"
        if not pack_file.exists():
            raise FileNotFoundError(f"Policy pack not found: {pack_file}")

        with open(pack_file, "r") as f:
            data = yaml.safe_load(f)

        # Validate required fields
        required = ["pack_id", "version", "description", "enabled_rules"]
        for field in required:
            if field not in data:
                raise ValueError(f"Policy pack missing required field: {field}")

        pack = PolicyPack(
            pack_id=data["pack_id"],
            version=data["version"],
            description=data["description"],
            enabled_rules=data["enabled_rules"],
            severity_overrides=data.get("severity_overrides", {}),
            critical_paths=data.get("critical_paths", []),
            required_context_keys=data.get("required_context_keys", []),
            default_action_on_error=data.get("default_action_on_error", "REVIEW_REQUIRED"),
            settings=data.get("settings", {}),
        )

        # Validate pack_id matches filename
        if pack.pack_id != pack_id:
            raise ValueError(f"Pack ID mismatch: {pack.pack_id} != {pack_id}")

        self._cache[pack_id] = pack
        return pack

    def list_available_packs(self) -> List[str]:
        """List all available pack IDs."""
        if not self.pack_dir.exists():
            return []
        return [p.stem for p in self.pack_dir.glob("*.yml")]


class PackAwareRule:
    """Wrapper that applies pack overrides to rules."""

    def __init__(self, rule: PolicyRule, pack: PolicyPack):
        self.rule = rule
        self.pack = pack

        # Apply severity override if present
        if rule.rule_id in pack.severity_overrides:
            override = pack.severity_overrides[rule.rule_id]
            self.effective_severity = Severity[override]
        else:
            self.effective_severity = rule.severity

    def check(self, diff: str, changed_files: List[str], context: Optional[dict] = None):
        """Check with pack-aware severity."""
        violations = self.rule.check(diff, changed_files, context)

        # Apply severity override
        for violation in violations:
            violation.severity = self.effective_severity

        return violations


def create_pack_aware_critic(pack: PolicyPack, rules: List[PolicyRule]):
    """
    Create a PolicyCritic with pack-aware rules.

    Args:
        pack: The policy pack to apply
        rules: Base rules to wrap

    Returns:
        PolicyCritic instance with pack-aware rules
    """
    from .critic import PolicyCritic

    # Filter rules based on pack's enabled_rules
    enabled_rules = [r for r in rules if r.rule_id in pack.enabled_rules]

    # Wrap rules with pack awareness
    pack_aware_rules = [PackAwareRule(rule, pack) for rule in enabled_rules]

    # Create critic with pack-aware rules
    critic = PolicyCritic(rules=pack_aware_rules)

    # Store pack metadata on critic for reporting
    critic._policy_pack = pack  # type: ignore

    return critic
