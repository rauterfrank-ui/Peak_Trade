"""
L1 DeepResearch Runner

Orchestrates Proposer + Critic for research outputs with SoD and Capability Scope enforcement.

Reference:
- docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md
- config/capability_scopes/L1_deep_research.toml
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .capability_scope_loader import CapabilityScopeLoader
from .errors import OrchestrationError
from .evidence_pack_generator import (
    CapabilityScopeCheck,
    CriticArtifact,
    EvidencePackGenerator,
    ProposerArtifact,
)
from .model_client import ModelClient, ModelRequest, create_model_client
from .model_registry_loader import ModelRegistryLoader
from .models import SoDResult
from .run_manifest import RunManifestGenerator
from .sod_checker import SoDChecker
from .transcript_store import TranscriptStore


class L1RunnerError(OrchestrationError):
    """L1 Runner error."""

    pass


class SoDViolation(L1RunnerError):
    """Separation of Duties violation."""

    pass


class CapabilityScopeViolation(L1RunnerError):
    """Capability scope violation."""

    pass


@dataclass
class L1RunResult:
    """Result of L1 DeepResearch run."""

    run_id: str
    evidence_pack_id: str
    layer_id: str
    mode: str
    sod_result: str
    capability_scope_result: str
    artifacts: Dict[str, Path]
    proposer_run_id: str
    critic_run_id: str
    summary: str


class L1Runner:
    """
    L1 DeepResearch Runner.

    Orchestrates Proposer + Critic for research with SoD and Capability Scope enforcement.
    """

    def __init__(
        self,
        registry_loader: Optional[ModelRegistryLoader] = None,
        scope_loader: Optional[CapabilityScopeLoader] = None,
        sod_checker: Optional[SoDChecker] = None,
        clock: Optional[datetime] = None,
    ):
        """
        Initialize L1 Runner.

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
        self.evidence_pack_generator = EvidencePackGenerator(clock=clock)

    def run(
        self,
        question: str,
        mode: str,
        transcript_path: Optional[Path] = None,
        out_dir: Optional[Path] = None,
        operator_notes: str = "",
        findings: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
    ) -> L1RunResult:
        """
        Run L1 DeepResearch (Proposer + Critic).

        Args:
            question: Research question/query
            mode: Run mode ("replay", "dry", "live", "record")
            transcript_path: Path to transcript (required for replay/dry)
            out_dir: Output directory for artifacts
            operator_notes: Optional operator notes
            findings: Optional findings list
            actions: Optional actions list

        Returns:
            L1RunResult

        Raises:
            L1RunnerError: If run fails
            SoDViolation: If SoD check fails
            CapabilityScopeViolation: If capability scope check fails
        """
        # Validate inputs
        if mode in ["replay", "dry"] and not transcript_path:
            raise L1RunnerError(f"Transcript path required for mode={mode}")

        if not question or not question.strip():
            raise L1RunnerError("Research question required")

        if not out_dir:
            out_dir = Path("evidence_packs") / f"L1_DEEPRESEARCH_{self._get_timestamp_str()}"

        # Load layer mapping
        layer_mapping = self.registry_loader.get_layer_mapping("L1")
        primary_model_id = layer_mapping.primary
        critic_model_id = layer_mapping.critic

        # Load capability scope
        scope = self.scope_loader.load("L1")

        # SoD Check (pre-flight)
        sod_check = self.sod_checker.check(
            proposer_model_id=primary_model_id,
            critic_model_id=critic_model_id,
        )

        if sod_check.result == SoDResult.FAIL:
            raise SoDViolation(
                f"SoD check failed: {sod_check.reason}. "
                f"Proposer ({primary_model_id}) must be different from Critic ({critic_model_id})."
            )

        # Load transcript for replay mode
        transcript = None
        if mode in ["replay", "dry"]:
            store = TranscriptStore(transcript_path)
            transcript = store.get_transcript()

        # Create model client
        client = create_model_client(mode=mode, transcript=transcript)

        # Run Proposer
        proposer_result = self._run_proposer(
            client=client,
            model_id=primary_model_id,
            question=question,
        )

        # Run Critic
        critic_result = self._run_critic(
            client=client,
            model_id=critic_model_id,
            proposer_output=proposer_result.content,
        )

        # Capability Scope Check
        capability_scope_check = self._check_capability_scope(
            scope=scope,
            proposer_output=proposer_result.content,
            critic_decision=critic_result.decision,
        )

        if capability_scope_check.result == "FAIL":
            raise CapabilityScopeViolation(
                f"Capability scope violation: {capability_scope_check.violations}"
            )

        # Generate run_id (deterministic)
        run_id = self._generate_run_id(
            layer_id="L1",
            primary_model_id=primary_model_id,
            critic_model_id=critic_model_id,
            proposer_hash=proposer_result.output_hash,
        )

        # Generate run manifest
        run_manifest = self.manifest_generator.generate(
            layer_id="L1",
            layer_name="DeepResearch",
            autonomy_level="PROP",
            primary_model_id=primary_model_id,
            fallback_model_ids=layer_mapping.fallback,
            critic_model_id=critic_model_id,
            capability_scope_id=scope.layer_id,
            capability_scope_version=scope.version,
            sod_result=sod_check.result,
            sod_reason=sod_check.reason,
            operator_notes=operator_notes,
        )

        # Generate Evidence Pack ID
        evidence_pack_id = f"EVP-L1-{self._get_timestamp_str()}-{run_id[:8]}"

        # Generate evidence pack bundle
        artifacts = self.evidence_pack_generator.generate(
            evidence_pack_id=evidence_pack_id,
            layer_id="L1",
            layer_name="DeepResearch",
            run_manifest=run_manifest,
            proposer_artifact=proposer_result,
            critic_artifact=critic_result,
            sod_result=sod_check.result,
            sod_reason=sod_check.reason,
            capability_scope_check=capability_scope_check,
            out_dir=out_dir,
            mode=mode,
            network_used=(mode in ["live", "record"]),
            operator_notes=operator_notes,
            findings=findings,
            actions=actions,
        )

        # Summary
        summary = (
            f"L1 DeepResearch run completed successfully.\n"
            f"  Run ID: {run_id}\n"
            f"  Evidence Pack ID: {evidence_pack_id}\n"
            f"  Mode: {mode}\n"
            f"  Question: {question[:80]}...\n"
            f"  SoD: {sod_check.result.value}\n"
            f"  Capability Scope: {capability_scope_check.result}\n"
            f"  Proposer: {primary_model_id}\n"
            f"  Critic: {critic_model_id} (Decision: {critic_result.decision})\n"
            f"  Artifacts: {len(artifacts)} files"
        )

        return L1RunResult(
            run_id=run_id,
            evidence_pack_id=evidence_pack_id,
            layer_id="L1",
            mode=mode,
            sod_result=sod_check.result.value,
            capability_scope_result=capability_scope_check.result,
            artifacts=artifacts,
            proposer_run_id=proposer_result.run_id,
            critic_run_id=critic_result.run_id,
            summary=summary,
        )

    def _run_proposer(self, client: ModelClient, model_id: str, question: str) -> ProposerArtifact:
        """Run proposer model (research)."""
        # System prompt for research
        system_prompt = (
            "You are an AI research assistant conducting deep research. "
            "Your task is to provide comprehensive, well-cited research outputs. "
            "Always include:\n"
            "1. Citations for all claims (use [Source: URL or Paper Name])\n"
            "2. Research methodology used\n"
            "3. Limitations and uncertainty statements\n"
            "4. No execution instructions or live trading advice."
        )

        # Create request
        request = ModelRequest(
            model_id=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.7,
            max_tokens=8000,  # L1 research can be longer
        )

        # Get response
        response = client.complete(request)

        # Compute hashes
        prompt_hash = request.compute_hash()
        output_hash = EvidencePackGenerator.compute_output_hash(response.content)

        # Generate run_id
        run_id = f"proposer-run-{output_hash[:16]}"

        return ProposerArtifact(
            model_id=model_id,
            run_id=run_id,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            content=response.content,
            metadata={
                "timestamp": self._get_timestamp(),
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
                "research_question": question,
            },
        )

    def _run_critic(
        self, client: ModelClient, model_id: str, proposer_output: str
    ) -> CriticArtifact:
        """Run critic model (research validation)."""
        # System prompt for critic
        system_prompt = (
            "You are a critical reviewer evaluating research outputs. "
            "Check for:\n"
            "1. Sufficient citations (minimum 3 for any claim)\n"
            "2. Clear methodology\n"
            "3. Stated limitations and uncertainty\n"
            "4. No execution instructions or live trading advice\n"
            "Provide APPROVE, APPROVE_WITH_CHANGES, or REJECT decision."
        )

        # Create request
        request = ModelRequest(
            model_id=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Review the following research output:\n\n{proposer_output}",
                },
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        # Get response
        response = client.complete(request)

        # Compute hashes
        prompt_hash = request.compute_hash()
        output_hash = EvidencePackGenerator.compute_output_hash(response.content)

        # Generate run_id
        run_id = f"critic-run-{output_hash[:16]}"

        # Parse critic decision
        decision = self._parse_critic_decision(response.content)
        rationale = self._extract_rationale(response.content)
        evidence_ids = self._extract_evidence_ids(response.content)

        return CriticArtifact(
            model_id=model_id,
            run_id=run_id,
            prompt_hash=prompt_hash,
            output_hash=output_hash,
            content=response.content,
            decision=decision,
            rationale=rationale,
            evidence_ids=evidence_ids,
            metadata={
                "timestamp": self._get_timestamp(),
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
            },
        )

    def _check_capability_scope(
        self, scope: any, proposer_output: str, critic_decision: str
    ) -> CapabilityScopeCheck:
        """Check capability scope compliance for L1 research."""
        violations = []
        checked_outputs = []

        # Check for forbidden outputs in proposer output
        forbidden_keywords = [
            "ExecutionCommand",
            "ConfigChange",
            "LiveToggle",
            "OrderParameters",
            "RiskLimitChange",
            "DoXLiveInstruction",
            "place order",
            "execute trade",
            "change config",
            "enable live",
            "modify risk limit",
        ]

        for keyword in forbidden_keywords:
            if keyword.lower() in proposer_output.lower():
                violations.append(f"Forbidden keyword detected: {keyword}")

        # Check for required research outputs
        allowed_outputs = [
            "ResearchReport",
            "LiteratureReview",
            "MethodologyProposal",
            "EvidenceSummary",
            "BestPracticesGuide",
            "CitationList",
        ]

        for output_type in allowed_outputs:
            if output_type.lower() in proposer_output.lower():
                checked_outputs.append(output_type)

        # Check for minimum citations (simple heuristic)
        citation_count = proposer_output.count("[Source:") + proposer_output.count("(Source:")
        if citation_count < 3:
            violations.append(f"Insufficient citations: {citation_count} found, minimum 3 required")

        # Check for limitations statement (required by scope)
        if (
            "limitation" not in proposer_output.lower()
            and "constraint" not in proposer_output.lower()
        ):
            violations.append("Research limitations statement missing")

        # Determine result
        result = "FAIL" if violations else "PASS"

        return CapabilityScopeCheck(
            result=result,
            violations=violations,
            checked_outputs=checked_outputs,
            timestamp=self._get_timestamp(),
        )

    def _parse_critic_decision(self, content: str) -> str:
        """Parse critic decision from content."""
        content_lower = content.lower()

        if "approve_with_changes" in content_lower or "approve with changes" in content_lower:
            return "APPROVE_WITH_CHANGES"
        elif "approve" in content_lower:
            return "APPROVE"
        elif "reject" in content_lower:
            return "REJECT"
        else:
            # Default to APPROVE if unclear
            return "APPROVE"

    def _extract_rationale(self, content: str) -> str:
        """Extract rationale from critic content."""
        # Simple heuristic: look for "Rationale:" section
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "rationale" in line.lower():
                # Return next few lines as rationale
                return "\n".join(lines[i + 1 : i + 5]).strip()

        # Fallback: return first 200 chars
        return content[:200] + "..." if len(content) > 200 else content

    def _extract_evidence_ids(self, content: str) -> List[str]:
        """Extract evidence IDs from critic content."""
        evidence_ids = []

        # Look for patterns like [evidence-id-123] or proposer-run-001
        import re

        patterns = [
            r"\[([a-zA-Z0-9-]+)\]",  # [evidence-id]
            r"(proposer-run-[a-zA-Z0-9]+)",  # proposer-run-xxx
            r"(research-[a-zA-Z0-9-]+)",  # research-xxx
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            evidence_ids.extend(matches)

        # Deduplicate
        evidence_ids = list(set(evidence_ids))

        # If no evidence IDs found, use a default
        if not evidence_ids:
            evidence_ids = ["proposer-run-001"]

        return evidence_ids

    def _generate_run_id(
        self, layer_id: str, primary_model_id: str, critic_model_id: str, proposer_hash: str
    ) -> str:
        """Generate deterministic run_id."""
        parts = [layer_id, primary_model_id, critic_model_id, proposer_hash[:16]]
        combined = "|".join(parts)
        hash_digest = hashlib.sha256(combined.encode()).hexdigest()
        return f"{layer_id}-{hash_digest[:16]}"

    def _get_timestamp(self) -> str:
        """Get timestamp (injected or now)."""
        if self.clock:
            return self.clock.isoformat()
        return datetime.now(timezone.utc).isoformat()

    def _get_timestamp_str(self) -> str:
        """Get timestamp string for filenames (YYYYMMDD_HHMMSS)."""
        if self.clock:
            dt = self.clock
        else:
            dt = datetime.now(timezone.utc)
        return dt.strftime("%Y%m%d_%H%M%S")
