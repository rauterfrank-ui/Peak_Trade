"""
Transcript Store for Record/Replay

Manages JSON fixtures for deterministic model call replay.

Reference:
- docs/governance/ai_autonomy/PHASE3_L2_MARKET_OUTLOOK_PILOT.md
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import OrchestrationError
from .model_client import ModelRequest, ModelResponse


class TranscriptStoreError(OrchestrationError):
    """Transcript store error."""

    pass


class TranscriptStore:
    """
    Transcript store for record/replay.

    Stores model API calls and responses in stable JSON format.
    """

    def __init__(self, transcript_path: Optional[Path] = None):
        """
        Initialize transcript store.

        Args:
            transcript_path: Path to transcript JSON file
        """
        self.transcript_path = transcript_path
        self.transcript: Dict[str, Any] = {
            "transcript_id": "",
            "recorded_at": "",
            "scenario": "",
            "runs": [],
        }

        # Load if exists
        if transcript_path and transcript_path.exists():
            self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load transcript from file.

        Returns:
            Transcript dict

        Raises:
            TranscriptStoreError: If file not found or invalid
        """
        if not self.transcript_path or not self.transcript_path.exists():
            raise TranscriptStoreError(
                f"Transcript not found: {self.transcript_path}"
            )

        try:
            with open(self.transcript_path, "r") as f:
                self.transcript = json.load(f)
            return self.transcript
        except Exception as e:
            raise TranscriptStoreError(f"Failed to load transcript: {e}")

    def save(self) -> None:
        """
        Save transcript to file.

        Raises:
            TranscriptStoreError: If save fails
        """
        if not self.transcript_path:
            raise TranscriptStoreError("No transcript path set")

        try:
            # Ensure directory exists
            self.transcript_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with stable ordering
            with open(self.transcript_path, "w") as f:
                json.dump(self.transcript, f, indent=2, sort_keys=True)
        except Exception as e:
            raise TranscriptStoreError(f"Failed to save transcript: {e}")

    def record_run(
        self,
        run_id: str,
        role: str,
        model_id: str,
        request: ModelRequest,
        response: ModelResponse,
    ) -> None:
        """
        Record a model run to transcript.

        Args:
            run_id: Unique run ID
            role: "proposer" or "critic"
            model_id: Model ID
            request: Model request
            response: Model response
        """
        prompt_hash = request.compute_hash()

        run_record = {
            "run_id": run_id,
            "role": role,
            "model_id": model_id,
            "prompt_hash": prompt_hash,
            "request": {
                "model": request.model_id,
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
            "response": {
                "id": response.response_id,
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response.content,
                        },
                        "finish_reason": response.finish_reason,
                    }
                ],
                "usage": {
                    "prompt_tokens": response.prompt_tokens,
                    "completion_tokens": response.completion_tokens,
                    "total_tokens": response.total_tokens,
                },
            },
            "metadata": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **response.metadata,
            },
        }

        self.transcript["runs"].append(run_record)

    def get_transcript(self) -> Dict[str, Any]:
        """Get transcript dictionary."""
        return self.transcript

    def initialize_transcript(
        self, transcript_id: str, scenario: str
    ) -> None:
        """
        Initialize new transcript.

        Args:
            transcript_id: Transcript identifier
            scenario: Scenario name
        """
        self.transcript = {
            "transcript_id": transcript_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "scenario": scenario,
            "runs": [],
        }

    @staticmethod
    def create_sample_transcript(output_path: Path) -> None:
        """
        Create sample transcript for testing.

        Args:
            output_path: Path to save transcript
        """
        sample = {
            "transcript_id": "l2-market-outlook-sample-2026-01-10",
            "recorded_at": "2026-01-10T12:00:00+00:00",
            "scenario": "market-outlook-baseline",
            "runs": [
                {
                    "run_id": "proposer-run-001",
                    "role": "proposer",
                    "model_id": "gpt-5.2-pro",
                    "prompt_hash": "sha256:abc123def456",
                    "request": {
                        "model": "gpt-5.2-pro",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a market analyst providing outlook reports.",
                            },
                            {
                                "role": "user",
                                "content": "Provide a market outlook for Q1 2026.",
                            },
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000,
                    },
                    "response": {
                        "id": "chatcmpl-sample-001",
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": "# Market Outlook Q1 2026\n\n"
                                    "## Scenario Analysis\n\n"
                                    "**Base Case:** Moderate growth with elevated uncertainty.\n\n"
                                    "**Key Drivers:**\n"
                                    "- Central bank policy normalization\n"
                                    "- Geopolitical tensions remain elevated\n"
                                    "- Tech sector consolidation\n\n"
                                    "**No-Trade Triggers:**\n"
                                    "- VIX > 30\n"
                                    "- Credit spreads > 200bps\n\n"
                                    "**Uncertainty Level:** HIGH (geopolitical risks)",
                                },
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 45,
                            "completion_tokens": 123,
                            "total_tokens": 168,
                        },
                    },
                    "metadata": {
                        "timestamp": "2026-01-10T12:00:01+00:00",
                        "latency_ms": 2345,
                    },
                },
                {
                    "run_id": "critic-run-001",
                    "role": "critic",
                    "model_id": "deepseek-r1",
                    "prompt_hash": "sha256:xyz789uvw012",
                    "request": {
                        "model": "deepseek-r1",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a critical reviewer evaluating market outlook reports.",
                            },
                            {
                                "role": "user",
                                "content": "Review the following market outlook:\n\n"
                                "[Proposer output included here]",
                            },
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000,
                    },
                    "response": {
                        "id": "chatcmpl-sample-002",
                        "choices": [
                            {
                                "message": {
                                    "role": "assistant",
                                    "content": "# Critic Review\n\n"
                                    "**Decision:** APPROVE_WITH_CHANGES\n\n"
                                    "**Rationale:**\n"
                                    "- Scenario analysis is comprehensive\n"
                                    "- No-trade triggers are appropriate\n"
                                    "- Uncertainty assessment is explicit\n\n"
                                    "**Suggested Changes:**\n"
                                    "- Add quantitative risk metrics\n"
                                    "- Clarify geopolitical risk scenarios\n\n"
                                    "**Evidence IDs:** [proposer-run-001, baseline-scenario-2026-01]",
                                },
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 234,
                            "completion_tokens": 89,
                            "total_tokens": 323,
                        },
                    },
                    "metadata": {
                        "timestamp": "2026-01-10T12:00:05+00:00",
                        "latency_ms": 1567,
                    },
                },
            ],
        }

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write sample
        with open(output_path, "w") as f:
            json.dump(sample, f, indent=2, sort_keys=True)
