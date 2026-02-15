"""
Model Client Abstraction for AI Orchestration

Provides:
- ModelClient interface (abstract)
- OpenAIClient (real API calls)
- ReplayClient (offline fixtures)

Reference:
- docs/governance/ai_autonomy/PHASE3_L2_MARKET_OUTLOOK_PILOT.md
"""

import hashlib
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.ai.gates.ai_model_hard_gate_v1 import require_ai_models_allowed

from .errors import OrchestrationError


class ModelClientError(OrchestrationError):
    """Model client error."""

    pass


@dataclass
class ModelRequest:
    """Model API request."""

    model_id: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model": self.model_id,
            "messages": self.messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }

    def compute_hash(self) -> str:
        """Compute deterministic hash of request."""
        # Stable JSON for hashing
        json_str = json.dumps(self.to_dict(), sort_keys=True)
        return f"sha256:{hashlib.sha256(json_str.encode()).hexdigest()}"


@dataclass
class ModelResponse:
    """Model API response."""

    model_id: str
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    response_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "content": self.content,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "finish_reason": self.finish_reason,
            "response_id": self.response_id,
            "metadata": self.metadata,
        }


class ModelClient(ABC):
    """Abstract model client interface."""

    @abstractmethod
    def complete(self, request: ModelRequest) -> ModelResponse:
        """
        Get completion from model.

        Args:
            request: Model request

        Returns:
            Model response

        Raises:
            ModelClientError: If API call fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if client is available."""
        pass


class ReplayClient(ModelClient):
    """
    Replay client (offline, no network).

    Uses pre-recorded transcripts for deterministic testing.
    """

    def __init__(self, transcript: Dict[str, Any]):
        """
        Initialize replay client.

        Args:
            transcript: Pre-recorded transcript (from TranscriptStore)
        """
        self.transcript = transcript
        self.runs_by_hash = {}

        # Index runs by prompt_hash for fast lookup
        for run in transcript.get("runs", []):
            prompt_hash = run.get("prompt_hash")
            if prompt_hash:
                self.runs_by_hash[prompt_hash] = run

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Get completion from replay transcript."""
        prompt_hash = request.compute_hash()

        # Lookup in transcript
        if prompt_hash not in self.runs_by_hash:
            raise ModelClientError(
                f"Replay client: No transcript found for prompt_hash={prompt_hash}. "
                "Record a new transcript first."
            )

        run = self.runs_by_hash[prompt_hash]
        response_data = run.get("response", {})

        # Extract content from response
        choices = response_data.get("choices", [])
        if not choices:
            raise ModelClientError("Replay client: No choices in transcript response")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        # Extract usage
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        # Extract finish_reason
        finish_reason = choices[0].get("finish_reason", "stop")

        # Metadata
        metadata = run.get("metadata", {})

        return ModelResponse(
            model_id=request.model_id,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            response_id=response_data.get("id"),
            metadata=metadata,
        )

    def is_available(self) -> bool:
        """Replay client is always available (offline)."""
        return True


class OpenAIClient(ModelClient):
    """
    OpenAI client (real API calls).

    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (default: from ENV)

        Raises:
            ModelClientError: If API key not found
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ModelClientError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )

        # Lazy import (optional dependency)
        try:
            import openai

            self.openai = openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ModelClientError("OpenAI SDK not installed. Install with: pip install openai")

    def complete(self, request: ModelRequest) -> ModelResponse:
        """Get completion from OpenAI API. Single egress boundary; use redact_outbound_envelope for any payload enrichment."""
        try:
            # enforce redaction at the boundary for any envelope/payload logging
            response = self.client.chat.completions.create(
                model=request.model_id,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
            )

            # Extract content
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason

            # Extract usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            return ModelResponse(
                model_id=request.model_id,
                content=content,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                finish_reason=finish_reason,
                response_id=response.id,
                metadata={
                    "created": response.created,
                    "model": response.model,
                },
            )

        except Exception as e:
            raise ModelClientError(f"OpenAI API call failed: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return bool(self.api_key)


def redact_outbound_envelope(payload: dict) -> dict:
    """
    SAFETY: convert rich runtime payload (risk/strategy details) into a minimal allowlisted envelope.
    - never include raw trades/positions, secrets, PII
    - include hashes + run_id for auditability
    """
    deny_keys = {
        "api_key",
        "token",
        "secret",
        "password",
        "email",
        "address",
        "phone",
        "orders",
        "trades",
        "positions",
        "routing_key",
    }
    allow_keys = {
        "run_id",
        "layer_id",
        "component",
        "ts",
        "prompt_hash",
        "config_hash",
        "metrics",
        "risk",
        "strategy",
        "gate",
    }
    out = {k: v for k, v in payload.items() if k in allow_keys and k not in deny_keys}
    blob = json.dumps(out, sort_keys=True, ensure_ascii=True).encode("utf-8")
    out["envelope_sha256"] = hashlib.sha256(blob).hexdigest()
    return out


def create_model_client(mode: str, transcript: Optional[Dict[str, Any]] = None) -> ModelClient:
    """
    Factory function to create model client.

    Args:
        mode: "replay" or "live" or "record"
        transcript: Transcript for replay mode (required if mode="replay")

    Returns:
        ModelClient instance

    Raises:
        ModelClientError: If mode invalid or transcript missing
    """
    if mode in ["replay", "dry"]:
        if not transcript:
            raise ModelClientError("Replay mode requires transcript")
        return ReplayClient(transcript=transcript)

    elif mode in ["live", "record"]:
        require_ai_models_allowed(context="create_model_client")
        return OpenAIClient()

    else:
        raise ModelClientError(f"Invalid mode: {mode}. Must be one of: replay, live, record")
