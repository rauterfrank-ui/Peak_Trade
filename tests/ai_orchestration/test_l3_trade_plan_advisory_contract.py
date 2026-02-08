"""
L3 Trade Plan Advisory Layer: deterministic contract tests.

Contract:
- L3 accepts only pointer-only artifacts (FeatureView/EvidenceCapsule style: path+sha256)
  and refuses raw payload keys (payload, raw, transcript, content, diff, etc.).
- L3 tools allowlist == files only (per scope).
- L3 cannot auto-apply learning surfaces when not in policy (deny-by-default).
"""

from pathlib import Path

import pytest

from src.ai_orchestration.capability_scope_loader import CapabilityScopeLoader
from src.governance.learning.learnable_surfaces_policy import get_allowed_surfaces
from src.ingress.capsules.evidence_capsule import ArtifactRef, EvidenceCapsule
from src.ingress.views.feature_view import ArtifactPointer, FeatureView


# Keys that must not appear in L3 input (pointer-only contract: no raw content).
L3_FORBIDDEN_RAW_KEYS = frozenset(
    {
        "payload",
        "raw",
        "transcript",
        "content",
        "diff",
        "body",
        "text",
        "api_key",
        "secret",
        "token",
        "credentials",
    }
)


def _has_forbidden_raw_keys(obj: dict, path: str = "") -> bool:
    """Return True if obj (recursively) contains any L3-forbidden raw key."""
    if not isinstance(obj, dict):
        return False
    for k, v in obj.items():
        key_lower = k.lower()
        if key_lower in L3_FORBIDDEN_RAW_KEYS:
            return True
        if _has_forbidden_raw_keys(v, f"{path}.{k}") if isinstance(v, dict) else False:
            return True
        if isinstance(v, list) and v and isinstance(v[0], dict):
            if _has_forbidden_raw_keys(v[0], f"{path}.{k}[0]"):
                return True
    return False


def _artifacts_are_pointer_only(artifacts: list) -> bool:
    """Check that artifacts list is pointer-only: each item has path and sha256, no raw content."""
    if not isinstance(artifacts, list):
        return False
    for item in artifacts:
        if not isinstance(item, dict):
            return False
        if set(item.keys()) - {"path", "sha256"}:
            return False
        if "path" not in item or "sha256" not in item:
            return False
    return True


def accepts_l3_pointer_only_input(obj: dict) -> bool:
    """
    Contract: L3 accepts only pointer-only inputs (no raw payload keys; artifacts path+sha256 only).

    Returns True if input is acceptable for L3; False if it contains forbidden keys or non-pointer artifacts.
    """
    if _has_forbidden_raw_keys(obj):
        return False
    artifacts = obj.get("artifacts")
    if artifacts is not None and not _artifacts_are_pointer_only(artifacts):
        return False
    return True


class TestL3PointerOnlyInputsContract:
    """L3 accepts only pointer-only artifacts and refuses raw payload keys."""

    def test_feature_view_style_accepted(self):
        """FeatureView-like dict (artifacts = path+sha256 only) is accepted."""
        inp = {
            "run_id": "r1",
            "ts_ms": 0,
            "counts": {},
            "facts": {},
            "artifacts": [{"path": "docs/outlook.md", "sha256": "a" * 64}],
        }
        assert accepts_l3_pointer_only_input(inp) is True

    def test_evidence_capsule_style_accepted(self):
        """EvidenceCapsule-like dict (artifacts = path+sha256 only) is accepted."""
        inp = {
            "capsule_id": "c1",
            "run_id": "r1",
            "ts_ms": 0,
            "artifacts": [{"path": "out/view.json", "sha256": "b" * 64}],
            "labels": {},
        }
        assert accepts_l3_pointer_only_input(inp) is True

    def test_feature_view_dataclass_to_dict_accepted(self):
        """FeatureView.to_dict() is accepted."""
        fv = FeatureView(
            run_id="r1",
            ts_ms=0,
            artifacts=[ArtifactPointer(path="x.json", sha256="c" * 64)],
        )
        assert accepts_l3_pointer_only_input(fv.to_dict()) is True

    def test_evidence_capsule_dataclass_to_dict_accepted(self):
        """EvidenceCapsule.to_dict() is accepted."""
        cap = EvidenceCapsule(
            capsule_id="c1",
            run_id="r1",
            ts_ms=0,
            artifacts=[ArtifactRef(path="y.json", sha256="d" * 64)],
        )
        assert accepts_l3_pointer_only_input(cap.to_dict()) is True

    def test_refuses_payload_key(self):
        """Input with 'payload' key is refused."""
        inp = {"run_id": "r1", "artifacts": [], "payload": "raw content"}
        assert accepts_l3_pointer_only_input(inp) is False

    def test_refuses_raw_key(self):
        """Input with 'raw' key is refused."""
        inp = {"artifacts": [], "raw": "something"}
        assert accepts_l3_pointer_only_input(inp) is False

    def test_refuses_transcript_key(self):
        """Input with 'transcript' key is refused."""
        inp = {"artifacts": [], "transcript": "full convo"}
        assert accepts_l3_pointer_only_input(inp) is False

    def test_refuses_artifact_with_extra_keys(self):
        """Artifacts must be pointer-only; extra keys (e.g. content) refuse."""
        inp = {
            "artifacts": [{"path": "a.json", "sha256": "e" * 64, "content": "forbidden"}],
        }
        assert accepts_l3_pointer_only_input(inp) is False

    def test_artifacts_must_have_path_and_sha256(self):
        """Each artifact must have path and sha256."""
        inp = {"artifacts": [{"path": "a.json"}]}  # missing sha256
        assert accepts_l3_pointer_only_input(inp) is False
        inp2 = {"artifacts": [{"sha256": "f" * 64}]}  # missing path
        assert accepts_l3_pointer_only_input(inp2) is False


class TestL3ToolsAllowlistFilesOnly:
    """L3 scope allows only 'files' tool (no web, code-interpreter, shell, execution)."""

    def test_l3_scope_tooling_allowed_is_files_only(self):
        """CapabilityScopeLoader: L3 tooling_allowed == ['files']."""
        loader = CapabilityScopeLoader()
        scope = loader.load("L3")
        assert scope.tooling_allowed == ["files"]
        assert "web" not in scope.tooling_allowed
        assert "files" in scope.tooling_allowed

    def test_l3_scope_tooling_forbidden_includes_web_shell_execution(self):
        """L3 tooling_forbidden includes web, code-interpreter, shell, execution."""
        loader = CapabilityScopeLoader()
        scope = loader.load("L3")
        forbidden = set(scope.tooling_forbidden)
        assert "web" in forbidden
        assert "shell" in forbidden or "code-interpreter" in forbidden or "execution" in forbidden

    def test_l3_scope_allowed_tools_in_toml_is_files_only(self):
        """L3 TOML [tools] allowed_tools == ['files'] (parse from file)."""
        repo_root = Path(__file__).resolve().parents[2]
        scope_path = repo_root / "config" / "capability_scopes" / "L3_trade_plan_advisory.toml"
        text = scope_path.read_text()
        assert 'allowed_tools = ["files"]' in text or 'allowed_tools = ["files"]' in text
        # Ensure not web
        assert 'allowed_tools = ["web"' not in text and 'allowed_tools = ["web"' not in text


class TestL3LearningSurfacesDenyByDefault:
    """L3 cannot auto-apply learning surfaces when not in policy (deny-by-default)."""

    def test_l3_no_allowed_surfaces_when_policy_empty(self):
        """When policy has no L3 entry, get_allowed_surfaces('L3') returns [] (deny-by-default)."""
        empty_policy: dict = {}
        allowed = get_allowed_surfaces("L3", policy=empty_policy)
        assert allowed == []

    def test_l3_not_in_deny_all_layers(self):
        """L3 is not in DENY_ALL_LAYERS (L0, L4, L5, L6); policy can still give empty list."""
        from src.governance.learning.learnable_surfaces_policy import DENY_ALL_LAYERS

        assert "L3" not in DENY_ALL_LAYERS
