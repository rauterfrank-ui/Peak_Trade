"""
Layer envelope tooling allowlist (cross-layer).

- Envelope tooling selection equals scope.tooling_allowed (single boundary).
- L3 / L0 / L4: never web/shell/etc.; only files.
"""

import pytest

from src.ai_orchestration.capability_scope_loader import CapabilityScopeLoader

# Layers that have capability scopes in config
LAYER_IDS_WITH_SCOPE = ["L0", "L1", "L2", "L3", "L4"]

# Layers that must be files-only (no web, shell, code-interpreter, execution)
FILES_ONLY_LAYERS = ["L0", "L3", "L4"]


class TestEnvelopeToolingEqualsScope:
    """Given a layer_id, envelope tooling selection equals scope.tooling_allowed."""

    @pytest.mark.parametrize("layer_id", LAYER_IDS_WITH_SCOPE)
    def test_envelope_tooling_equals_scope_tooling_allowed(self, layer_id):
        """get_envelope_tooling_allowlist(layer_id) == scope.tooling_allowed."""
        loader = CapabilityScopeLoader()
        scope = loader.load(layer_id)
        envelope_tooling = loader.get_envelope_tooling_allowlist(layer_id)
        assert envelope_tooling == scope.tooling_allowed


class TestFilesOnlyLayersNoWebShell:
    """L3 / L0 / L4: never include web, shell, etc.; only files."""

    @pytest.mark.parametrize("layer_id", FILES_ONLY_LAYERS)
    def test_files_only_layer_envelope_is_files_only(self, layer_id):
        """Envelope tooling for L0/L3/L4 is exactly ['files']."""
        loader = CapabilityScopeLoader()
        envelope_tooling = loader.get_envelope_tooling_allowlist(layer_id)
        assert envelope_tooling == ["files"]

    @pytest.mark.parametrize("layer_id", FILES_ONLY_LAYERS)
    def test_files_only_layer_never_includes_web_shell(self, layer_id):
        """L0/L3/L4 envelope must not include web, shell, code-interpreter, execution."""
        loader = CapabilityScopeLoader()
        envelope_tooling = loader.get_envelope_tooling_allowlist(layer_id)
        forbidden = {"web", "shell", "code-interpreter", "execution"}
        for tool in forbidden:
            assert tool not in envelope_tooling, f"{layer_id} must not allow {tool}"
