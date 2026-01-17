"""
Separation of Duties (SoD) Checker

Validates that Proposer != Critic (different models/instances) for AI Autonomy.

Reference:
- docs/governance/ai_autonomy/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md
- docs/governance/ai_autonomy/SCHEMA_MANDATORY_FIELDS.md
"""

from dataclasses import dataclass
from typing import Optional

from .errors import SoDViolationError
from .models import SoDResult


@dataclass
class SoDCheck:
    """Result of a Separation of Duties check."""

    proposer_model_id: str
    critic_model_id: str
    result: SoDResult
    reason: str
    timestamp: str  # ISO8601


class SoDChecker:
    """
    Validates Separation of Duties (SoD) rules.

    Rules:
    1. Proposer != Critic (different model IDs)
    2. Optional: Critic cannot be fallback model (if policy enforces)
    3. Optional: Provider diversity (e.g., OpenAI vs DeepSeek)
    """

    def __init__(self, enforce_provider_diversity: bool = False):
        """
        Initialize SoD checker.

        Args:
            enforce_provider_diversity: If True, require different providers
        """
        self.enforce_provider_diversity = enforce_provider_diversity

    def check(
        self,
        proposer_model_id: str,
        critic_model_id: str,
        proposer_provider: Optional[str] = None,
        critic_provider: Optional[str] = None,
    ) -> SoDCheck:
        """
        Check Separation of Duties.

        Args:
            proposer_model_id: Proposer model ID
            critic_model_id: Critic model ID
            proposer_provider: Optional provider (e.g., "openai", "deepseek")
            critic_provider: Optional provider

        Returns:
            SoDCheck result

        Raises:
            SoDViolationError: If SoD check fails
        """
        from datetime import datetime, timezone

        timestamp = datetime.now(timezone.utc).isoformat()

        # Rule 1: Proposer != Critic
        if proposer_model_id == critic_model_id:
            return SoDCheck(
                proposer_model_id=proposer_model_id,
                critic_model_id=critic_model_id,
                result=SoDResult.FAIL,
                reason=f"SoD FAIL: Proposer == Critic ({proposer_model_id}). Models must be different.",
                timestamp=timestamp,
            )

        # Rule 2: Provider diversity (optional)
        if self.enforce_provider_diversity:
            if proposer_provider and critic_provider:
                if proposer_provider == critic_provider:
                    return SoDCheck(
                        proposer_model_id=proposer_model_id,
                        critic_model_id=critic_model_id,
                        result=SoDResult.FAIL,
                        reason=f"SoD FAIL: Same provider ({proposer_provider}). Provider diversity required.",
                        timestamp=timestamp,
                    )

        # All checks passed
        return SoDCheck(
            proposer_model_id=proposer_model_id,
            critic_model_id=critic_model_id,
            result=SoDResult.PASS,
            reason=f"SoD PASS: Proposer ({proposer_model_id}) != Critic ({critic_model_id})",
            timestamp=timestamp,
        )

    def validate(
        self,
        proposer_model_id: str,
        critic_model_id: str,
        proposer_provider: Optional[str] = None,
        critic_provider: Optional[str] = None,
    ) -> None:
        """
        Validate SoD (raises exception on failure).

        Args:
            proposer_model_id: Proposer model ID
            critic_model_id: Critic model ID
            proposer_provider: Optional provider
            critic_provider: Optional provider

        Raises:
            SoDViolationError: If SoD check fails
        """
        result = self.check(proposer_model_id, critic_model_id, proposer_provider, critic_provider)
        if result.result == SoDResult.FAIL:
            raise SoDViolationError(result.reason)
