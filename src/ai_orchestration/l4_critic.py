"""
L4 Governance Critic Runner

Reviews Evidence Packs from other layers (L1/L2) and produces governance decisions.

Reference:
- docs/governance/ai_autonomy/PHASE4_L1_L4_INTEGRATION.md
- config/capability_scopes/L4_governance_critic.toml
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .capability_scope_loader import CapabilityScopeLoader
from .errors import OrchestrationError
from .model_client import ModelClient, ModelRequest, create_model_client
from .model_registry_loader import ModelRegistryLoader
from .models import SoDResult
from .sod_checker import SoDChecker
from .transcript_store import TranscriptStore


class L4CriticError(OrchestrationError):
    """L4 Critic error."""

    pass


class SoDViolation(L4CriticError):
    """Separation of Duties violation."""

    pass


class CapabilityScopeViolation(L4CriticError):
    """Capability scope violation."""

    pass


@dataclass
class CriticDecision:
    """Critic decision result."""

    decision: str  # ALLOW, REVIEW_REQUIRED, AUTO_APPLY_DENY, REJECT
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    rationale: str
    policy_references: List[str]
    evidence_ids: List[str]
    risk_notes: List[str]
    timestamp: str


@dataclass
class L4CriticResult:
    """Result of L4 Governance Critic run."""

    run_id: str
    evidence_pack_id: str
    layer_id: str
    mode: str
    sod_result: str
    capability_scope_result: str
    decision: CriticDecision
    artifacts: Dict[str, Path]
    proposer_model_id: str
    critic_model_id: str
    summary: str


class L4Critic:
    """
    L4 Governance Critic Runner.

    Reviews Evidence Packs and produces governance decisions with policy enforcement.
    """

    def __init__(
        self,
        registry_loader: Optional[ModelRegistryLoader] = None,
        scope_loader: Optional[CapabilityScopeLoader] = None,
        sod_checker: Optional[SoDChecker] = None,
        clock: Optional[datetime] = None,
    ):
        """
        Initialize L4 Critic.

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

    def run(
        self,
        evidence_pack_path: Path,
        mode: str,
        transcript_path: Optional[Path] = None,
        out_dir: Optional[Path] = None,
        operator_notes: str = "",
    ) -> L4CriticResult:
        """
        Run L4 Governance Critic on an Evidence Pack.

        Args:
            evidence_pack_path: Path to Evidence Pack directory
            mode: Run mode ("replay", "dry", "live", "record")
            transcript_path: Path to transcript (required for replay/dry)
            out_dir: Output directory for artifacts
            operator_notes: Optional operator notes

        Returns:
            L4CriticResult

        Raises:
            L4CriticError: If run fails
            SoDViolation: If SoD check fails
            CapabilityScopeViolation: If capability scope check fails
        """
        # Validate inputs
        if not evidence_pack_path.exists():
            raise L4CriticError(f"Evidence pack not found: {evidence_pack_path}")

        if mode in ["replay", "dry"] and not transcript_path:
            raise L4CriticError(f"Transcript path required for mode={mode}")

        # Load Evidence Pack metadata
        evidence_pack_json = evidence_pack_path / "evidence_pack.json"
        if not evidence_pack_json.exists():
            raise L4CriticError(f"Evidence pack metadata not found: {evidence_pack_json}")

        with open(evidence_pack_json) as f:
            evidence_pack_data = json.load(f)

        evidence_pack_id = evidence_pack_data.get("evidence_pack_id", "UNKNOWN")
        proposer_model_id = evidence_pack_data.get("models", {}).get("proposer", {}).get("model_id", "UNKNOWN")

        # Load layer mapping for L4
        layer_mapping = self.registry_loader.get_layer_mapping("L4")
        critic_model_id = layer_mapping.primary  # L4 uses primary as the critic

        # Load capability scope
        scope = self.scope_loader.load("L4")

        # SoD Check (pre-flight): proposer from evidence pack != L4 critic
        sod_check = self.sod_checker.check(
            proposer_model_id=proposer_model_id,
            critic_model_id=critic_model_id,
        )

        if sod_check.result != SoDResult.PASS:
            raise SoDViolation(
                f"SoD violation: proposer={proposer_model_id}, critic={critic_model_id}. "
                f"Reason: {sod_check.reason}"
            )

        # Output directory
        if not out_dir:
            out_dir = Path("evidence_packs") / f"L4_CRITIC_{self._get_timestamp_str()}"

        out_dir.mkdir(parents=True, exist_ok=True)

        # Load transcript for replay/dry modes
        transcript = None
        if mode in ["replay", "dry"]:
            store = TranscriptStore(transcript_path)
            transcript = store.get_transcript()

        # Run L4 Critic
        critic_output = self._run_critic(
            evidence_pack_data=evidence_pack_data,
            critic_model_id=critic_model_id,
            mode=mode,
            transcript=transcript,
        )

        # Extract decision from critic output
        decision = self._extract_decision(critic_output)

        # Capability Scope Check
        capability_check_result = self._check_capability_scope(
            critic_output=critic_output,
            scope=scope,
        )

        if capability_check_result != "PASS":
            raise CapabilityScopeViolation(
                f"Capability scope violation: {capability_check_result}"
            )

        # Generate run ID (deterministic)
        run_id = self._generate_run_id(
            evidence_pack_id=evidence_pack_id,
            critic_model_id=critic_model_id,
            critic_hash=hashlib.sha256(critic_output.encode()).hexdigest()[:8],
        )

        # Generate artifacts
        artifacts = self._generate_artifacts(
            run_id=run_id,
            evidence_pack_id=evidence_pack_id,
            evidence_pack_data=evidence_pack_data,
            critic_model_id=critic_model_id,
            critic_output=critic_output,
            decision=decision,
            sod_check=sod_check,
            capability_check_result=capability_check_result,
            mode=mode,
            out_dir=out_dir,
            operator_notes=operator_notes,
        )

        # Create summary
        summary = (
            f"L4 Critic Run Complete\n"
            f"Run ID: {run_id}\n"
            f"Evidence Pack: {evidence_pack_id}\n"
            f"Decision: {decision.decision} ({decision.severity})\n"
            f"SoD: {sod_check.result.value}\n"
            f"Capability Scope: {capability_check_result}\n"
            f"Artifacts: {len(artifacts)} files"
        )

        return L4CriticResult(
            run_id=run_id,
            evidence_pack_id=evidence_pack_id,
            layer_id="L4",
            mode=mode,
            sod_result=sod_check.result.value,
            capability_scope_result=capability_check_result,
            decision=decision,
            artifacts=artifacts,
            proposer_model_id=proposer_model_id,
            critic_model_id=critic_model_id,
            summary=summary,
        )

    def _run_critic(
        self,
        evidence_pack_data: Dict,
        critic_model_id: str,
        mode: str,
        transcript: Optional[Dict],
    ) -> str:
        """Run L4 critic model on evidence pack."""
        # Extract evidence pack summary for prompt
        evidence_pack_id = evidence_pack_data.get("evidence_pack_id", "UNKNOWN")
        layer_id = evidence_pack_data.get("layer_id", "UNKNOWN")
        proposer_model = evidence_pack_data.get("models", {}).get("proposer", {}).get("model_id", "UNKNOWN")

        # Build critic prompt
        prompt = self._build_critic_prompt(evidence_pack_data)

        # Create model client
        client = create_model_client(
            mode=mode,
            transcript=transcript,
        )

        # Create request
        request = ModelRequest(
            model_id=critic_model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are an L4 Governance Critic. Review evidence packs and provide policy-based recommendations.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.0,  # Deterministic
            max_tokens=4000,
        )

        # Execute
        response = client.complete(request)

        # Extract content
        return response.content

    def _build_critic_prompt(self, evidence_pack_data: Dict) -> str:
        """Build prompt for L4 critic."""
        evidence_pack_id = evidence_pack_data.get("evidence_pack_id", "UNKNOWN")
        layer_id = evidence_pack_data.get("layer_id", "UNKNOWN")
        proposer_model = evidence_pack_data.get("models", {}).get("proposer", {}).get("model_id", "UNKNOWN")
        critic_model = evidence_pack_data.get("models", {}).get("critic", {}).get("model_id", "UNKNOWN")
        sod_result = evidence_pack_data.get("sod_check", {}).get("result", "UNKNOWN")
        capability_result = evidence_pack_data.get("capability_scope_check", {}).get("result", "UNKNOWN")

        prompt = f"""# Governance Critic Review Request

## Evidence Pack Summary
- **Evidence Pack ID**: {evidence_pack_id}
- **Layer**: {layer_id}
- **Proposer Model**: {proposer_model}
- **Critic Model**: {critic_model}
- **SoD Check**: {sod_result}
- **Capability Scope Check**: {capability_result}

## Your Task
As an L4 Governance Critic, review this evidence pack and provide:

1. **Decision**: ALLOW | REVIEW_REQUIRED | AUTO_APPLY_DENY | REJECT
2. **Severity**: LOW | MEDIUM | HIGH | CRITICAL
3. **Rationale**: Why this decision?
4. **Policy References**: Which policies apply?
5. **Evidence IDs**: Which evidence items support your decision?
6. **Risk Notes**: What risks are present?

## Output Format
Please provide your review in the following format:

```
DECISION: <ALLOW|REVIEW_REQUIRED|AUTO_APPLY_DENY|REJECT>
SEVERITY: <LOW|MEDIUM|HIGH|CRITICAL>
RATIONALE: <1-2 sentences explaining decision>
POLICY_REFS: <comma-separated policy IDs>
EVIDENCE_IDS: <comma-separated evidence IDs>
RISK_NOTES: <comma-separated risk notes>

## Detailed Analysis
<Your detailed analysis here>
```

Ensure your decision:
- References specific evidence IDs
- Cites relevant policies
- Fails closed if uncertain (default to REVIEW_REQUIRED or REJECT)
- Does NOT include forbidden outputs (UnlockCommand, ExecutionCommand, etc.)
"""
        return prompt

    def _extract_decision(self, critic_output: str) -> CriticDecision:
        """Extract structured decision from critic output."""
        # Parse structured fields
        decision_match = re.search(r"DECISION:\s*(\w+)", critic_output)
        severity_match = re.search(r"SEVERITY:\s*(\w+)", critic_output)
        rationale_match = re.search(r"RATIONALE:\s*(.+?)(?=\n(?:POLICY_REFS|EVIDENCE_IDS|RISK_NOTES|##))", critic_output, re.DOTALL)
        policy_refs_match = re.search(r"POLICY_REFS:\s*(.+?)(?=\n(?:EVIDENCE_IDS|RISK_NOTES|##))", critic_output, re.DOTALL)
        evidence_ids_match = re.search(r"EVIDENCE_IDS:\s*(.+?)(?=\n(?:RISK_NOTES|##))", critic_output, re.DOTALL)
        risk_notes_match = re.search(r"RISK_NOTES:\s*(.+?)(?=\n##)", critic_output, re.DOTALL)

        decision = decision_match.group(1) if decision_match else "REVIEW_REQUIRED"
        severity = severity_match.group(1) if severity_match else "MEDIUM"
        rationale = rationale_match.group(1).strip() if rationale_match else "No rationale provided"

        policy_refs = []
        if policy_refs_match:
            policy_refs = [p.strip() for p in policy_refs_match.group(1).split(",") if p.strip()]

        evidence_ids = []
        if evidence_ids_match:
            evidence_ids = [e.strip() for e in evidence_ids_match.group(1).split(",") if e.strip()]

        risk_notes = []
        if risk_notes_match:
            risk_notes = [r.strip() for r in risk_notes_match.group(1).split(",") if r.strip()]

        timestamp = self._get_timestamp_str()

        return CriticDecision(
            decision=decision,
            severity=severity,
            rationale=rationale,
            policy_references=policy_refs,
            evidence_ids=evidence_ids,
            risk_notes=risk_notes,
            timestamp=timestamp,
        )

    def _check_capability_scope(self, critic_output: str, scope) -> str:
        """Check capability scope compliance."""
        # Check for forbidden outputs
        violations = []
        for forbidden in scope.outputs_forbidden:
            if forbidden.lower() in critic_output.lower():
                violations.append(f"Forbidden output detected: {forbidden}")

        # Check required constraints from TOML (must_reference_evidence)
        # For L4, we expect evidence IDs to be present in output
        if "EVIDENCE_IDS:" not in critic_output or not re.search(r"EVIDENCE_IDS:\s*\S+", critic_output):
            violations.append("Must reference evidence IDs")

        if violations:
            return f"FAIL: {'; '.join(violations)}"

        return "PASS"

    def _generate_artifacts(
        self,
        run_id: str,
        evidence_pack_id: str,
        evidence_pack_data: Dict,
        critic_model_id: str,
        critic_output: str,
        decision: CriticDecision,
        sod_check,
        capability_check_result: str,
        mode: str,
        out_dir: Path,
        operator_notes: str,
    ) -> Dict[str, Path]:
        """Generate L4 critic artifacts."""
        artifacts = {}

        # 1. Critic Report (Markdown)
        report_path = out_dir / "critic_report.md"
        report_content = f"""# L4 Governance Critic Report

## Run Metadata
- **Run ID**: {run_id}
- **Evidence Pack ID**: {evidence_pack_id}
- **Critic Model**: {critic_model_id}
- **Timestamp**: {self._get_timestamp_str()}
- **Mode**: {mode}

## Decision
- **Decision**: {decision.decision}
- **Severity**: {decision.severity}
- **Rationale**: {decision.rationale}

## Policy References
{chr(10).join(f"- {ref}" for ref in decision.policy_references) if decision.policy_references else "- None"}

## Evidence IDs Referenced
{chr(10).join(f"- {eid}" for eid in decision.evidence_ids) if decision.evidence_ids else "- None"}

## Risk Notes
{chr(10).join(f"- {note}" for note in decision.risk_notes) if decision.risk_notes else "- None"}

## Detailed Analysis
{critic_output}

## Operator Notes
{operator_notes if operator_notes else "None"}
"""
        with open(report_path, "w") as f:
            f.write(report_content)
        artifacts["critic_report"] = report_path

        # 2. Critic Decision (JSON)
        decision_path = out_dir / "critic_decision.json"
        decision_data = {
            "run_id": run_id,
            "evidence_pack_id": evidence_pack_id,
            "decision": decision.decision,
            "severity": decision.severity,
            "rationale": decision.rationale,
            "policy_references": decision.policy_references,
            "evidence_ids": decision.evidence_ids,
            "risk_notes": decision.risk_notes,
            "timestamp": decision.timestamp,
            "sod_check": {
                "result": sod_check.result.value,
                "reason": sod_check.reason,
            },
            "capability_scope_check": {
                "result": capability_check_result,
            },
        }
        with open(decision_path, "w") as f:
            json.dump(decision_data, f, indent=2, sort_keys=True)
        artifacts["critic_decision"] = decision_path

        # 3. Critic Manifest (JSON)
        manifest_path = out_dir / "critic_manifest.json"
        manifest_data = {
            "run_id": run_id,
            "layer_id": "L4",
            "critic_model_id": critic_model_id,
            "mode": mode,
            "timestamp": self._get_timestamp_str(),
            "inputs": {
                "evidence_pack_id": evidence_pack_id,
                "evidence_pack_layer": evidence_pack_data.get("layer_id", "UNKNOWN"),
            },
            "outputs": {
                "decision": decision.decision,
                "severity": decision.severity,
            },
        }
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2, sort_keys=True)
        artifacts["critic_manifest"] = manifest_path

        # 4. Operator Summary
        summary_path = out_dir / "operator_summary.txt"
        summary_content = f"""L4 GOVERNANCE CRITIC SUMMARY
{'=' * 60}

Run ID:           {run_id}
Evidence Pack:    {evidence_pack_id}
Critic Model:     {critic_model_id}
Mode:             {mode}

DECISION:         {decision.decision}
SEVERITY:         {decision.severity}

Rationale:        {decision.rationale}

SoD Check:        {sod_check.result.value}
Scope Check:      {capability_check_result}

Artifacts:        {len(artifacts)} files
Output Directory: {out_dir}
"""
        with open(summary_path, "w") as f:
            f.write(summary_content)
        artifacts["operator_summary"] = summary_path

        return artifacts

    def _generate_run_id(self, evidence_pack_id: str, critic_model_id: str, critic_hash: str) -> str:
        """Generate deterministic run ID."""
        components = f"L4-{evidence_pack_id}-{critic_model_id}-{critic_hash}"
        run_hash = hashlib.sha256(components.encode()).hexdigest()[:16]
        return f"L4-{run_hash}"

    def _get_timestamp(self) -> datetime:
        """Get current or fixed timestamp."""
        return self.clock if self.clock else datetime.now(timezone.utc)

    def _get_timestamp_str(self) -> str:
        """Get timestamp as ISO8601 string."""
        return self._get_timestamp().isoformat()
