"""WP-A4 narrow ConfigPatch -> Manifest -> PromotionCandidate boundary.

Protects the already-adjudicated D4 path. Does not redesign learning or
promotion. Does not claim ConfigPatch is the only learning topology.
Does not treat emitter.py as part of the proven ConfigPatch flow.

Reuse: in-memory ConfigPatch / Manifest / PromotionCandidate contracts plus
AST assignment/call scans of the Owner-listed proven surfaces.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
from datetime import datetime, timezone
from pathlib import Path

from src.governance.promotion_loop.engine import (
    apply_proposals_to_live_overrides,
    build_promotion_candidates_from_patches,
    filter_candidates_for_live,
)
from src.governance.promotion_loop.models import (
    DecisionStatus,
    PromotionCandidate,
    PromotionDecision,
    PromotionProposal,
)
from src.governance.promotion_loop.policy import AutoApplyBounds, AutoApplyPolicy
from src.meta.learning_loop.bridge import normalize_patches
from src.meta.learning_loop.config_patch_manifest_v1 import ConfigPatchManifestV1
from src.meta.learning_loop.manifest_bridge_v1 import (
    build_config_patch_manifest_v1_from_learning_input,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus

REPO_ROOT = Path(__file__).resolve().parents[2]

# Owner-listed currently proven narrow ConfigPatch promotion path only.
PROVEN_CONFIGPATCH_PATH: tuple[str, ...] = (
    "src/meta/learning_loop/models.py",
    "src/meta/learning_loop/config_patch_manifest_v1.py",
    "src/meta/learning_loop/manifest_bridge_v1.py",
    "src/meta/learning_loop/manifest_durable_evidence_binding_v1.py",
    "src/meta/learning_loop/comparison_config_patch_manifest_cross_domain_lineage_binding_v1.py",
    "src/meta/learning_loop/comparison_promotion_candidate_input_v1.py",
    "src/meta/learning_loop/bridge.py",
    "src/meta/learning_loop/__init__.py",
    "src/governance/promotion_loop/engine.py",
    "src/governance/promotion_loop/models.py",
    "src/governance/promotion_loop/proposal_input_refs_v1.py",
    "src/governance/promotion_loop/safety.py",
    "src/governance/promotion_loop/__init__.py",
)

EXCLUDED_EMITTER_REL = "src/meta/learning_loop/emitter.py"

# Required non-claims. Do not invert these in this surface.
SELF_LEARNING_TOPOLOGY = "OPEN_NOT_YET_ADJUDICATED"
SELF_LEARNING_TOPOLOGY_ASSUMED = False
CONFIGPATCH_IS_THE_ONLY_LEARNING_PATH = False
ALL_NORMALIZE_PATCHES_CALLERS_MANIFEST_BOUND = "unproven"

_FORBIDDEN_ACTIVATION_NAMES: frozenset[str] = frozenset(
    {
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
        "enable_live_trading",
        "live_mode_armed",
        "live_authorized",
        "testnet_authorized",
        "canary_authorized",
    }
)
_FORBIDDEN_ORDER_SUBMIT_NAMES: frozenset[str] = frozenset(
    {
        "submit_order",
        "place_order",
        "create_order",
    }
)
_FORBIDDEN_PERMIT_NAMES: frozenset[str] = frozenset(
    {
        "Permit",
        "ExecutionPermit",
    }
)

FIXED_NOW = datetime(2026, 6, 27, 16, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LINEAGE_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _allowed_raw_patch() -> dict:
    return {
        "id": "patch-wp-a4-1",
        "target": "research.offline.window_days",
        "old_value": 30,
        "new_value": 45,
        "status": PatchStatus.APPLIED_OFFLINE.value,
        "reason": "wp-a4 narrow boundary",
        "source_experiment_id": "exp-wp-a4-1",
    }


def _target_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _const_true(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _forbidden_activation_writes(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if not _const_true(node.value):
                continue
            for target in node.targets:
                name = _target_name(target)
                if name in _FORBIDDEN_ACTIVATION_NAMES:
                    hits.append(name)
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    key = target.slice.value
                    if isinstance(key, str) and key in _FORBIDDEN_ACTIVATION_NAMES:
                        hits.append(key)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            if not _const_true(node.value):
                continue
            name = _target_name(node.target)
            if name in _FORBIDDEN_ACTIVATION_NAMES:
                hits.append(name)
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                if keyword.arg in _FORBIDDEN_ACTIVATION_NAMES and _const_true(keyword.value):
                    hits.append(keyword.arg)
    return hits


def _forbidden_calls(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name in _FORBIDDEN_ORDER_SUBMIT_NAMES or name in _FORBIDDEN_PERMIT_NAMES:
            hits.append(name)
    return hits


def _imported_modules(path: Path, tree: ast.AST) -> list[str]:
    current_parts = path.relative_to(REPO_ROOT).with_suffix("").parts
    if current_parts[-1] == "__init__":
        package_parts = current_parts[:-1]
    else:
        package_parts = current_parts[:-1]
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                hits.append(node.module or "")
                continue
            base = list(package_parts)
            for _ in range(node.level - 1):
                if base:
                    base = base[:-1]
            if node.module:
                base.extend(node.module.split("."))
            hits.append(".".join(base))
    return hits


def test_wp_a4_does_not_adjudicate_self_learning_topology() -> None:
    assert SELF_LEARNING_TOPOLOGY == "OPEN_NOT_YET_ADJUDICATED"
    assert SELF_LEARNING_TOPOLOGY_ASSUMED is False
    assert CONFIGPATCH_IS_THE_ONLY_LEARNING_PATH is False
    assert ALL_NORMALIZE_PATCHES_CALLERS_MANIFEST_BOUND == "unproven"


def test_emitter_is_excluded_from_proven_configpatch_path() -> None:
    assert EXCLUDED_EMITTER_REL not in PROVEN_CONFIGPATCH_PATH
    assert (REPO_ROOT / EXCLUDED_EMITTER_REL).is_file()
    for rel in PROVEN_CONFIGPATCH_PATH:
        path = REPO_ROOT / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = _imported_modules(path, tree)
        emitter_hits = [
            name
            for name in imported
            if name == "src.meta.learning_loop.emitter"
            or name.endswith(".emitter")
            or name == "emitter"
        ]
        if rel == "src/meta/learning_loop/__init__.py":
            # Package re-export is existing convenience, not a ConfigPatch step.
            assert emitter_hits == ["src.meta.learning_loop.emitter"]
            continue
        assert emitter_hits == [], f"{rel} must not import emitter.py"


def test_proven_path_builders_do_not_call_emitter() -> None:
    bridge_src = inspect.getsource(build_config_patch_manifest_v1_from_learning_input)
    candidate_src = inspect.getsource(build_promotion_candidates_from_patches)
    apply_src = inspect.getsource(apply_proposals_to_live_overrides)
    normalize_src = inspect.getsource(normalize_patches)
    for source in (bridge_src, candidate_src, apply_src, normalize_src):
        assert "emit_learning_snippet" not in source
        assert "emitter" not in source


def test_configpatch_normalize_and_manifest_path_remains_non_activating() -> None:
    raw = {"patches": [_allowed_raw_patch()]}
    normalized = normalize_patches(raw)
    assert normalized == [
        {
            "target": "research.offline.window_days",
            "new_value": 45,
            "old_value": 30,
            "reason": "wp-a4 narrow boundary",
            "source_experiment_id": "exp-wp-a4-1",
        }
    ]

    manifest = build_config_patch_manifest_v1_from_learning_input(
        raw,
        manifest_id=MANIFEST_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    assert isinstance(manifest, ConfigPatchManifestV1)
    assert len(manifest.patches) == 1
    patch = manifest.patches[0]
    assert isinstance(patch, ConfigPatch)
    assert patch.status is PatchStatus.APPLIED_OFFLINE
    assert patch.target == "research.offline.window_days"

    candidates = build_promotion_candidates_from_patches(manifest.patches)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.eligible_for_live is False
    assert candidate.patch.id == patch.id


def test_eligible_for_live_default_remains_false() -> None:
    field = {item.name: item for item in dataclasses.fields(PromotionCandidate)}[
        "eligible_for_live"
    ]
    assert field.default is False

    patch = ConfigPatch(
        id="patch-wp-a4-default",
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=FIXED_NOW,
    )
    constructed = PromotionCandidate(patch=patch)
    built = build_promotion_candidates_from_patches([patch])[0]
    assert constructed.eligible_for_live is False
    assert built.eligible_for_live is False

    decisions = filter_candidates_for_live([built], safety_config=None, mode="manual_only")
    assert len(decisions) == 1
    assert decisions[0].status is DecisionStatus.REJECTED_BY_POLICY
    assert "eligible_for_live" in decisions[0].reasons[0]


def test_candidate_construction_is_not_live_enablement_or_permit() -> None:
    source = inspect.getsource(build_promotion_candidates_from_patches)
    assert "eligible_for_live=False" in source
    assert "Permit" not in source
    assert "submit_order" not in source
    assert "enable_live_trading" not in source
    assert "LIVE_ENABLED" not in source
    assert "LIVE_ARMED" not in source
    assert "TESTNET_AUTHORIZED" not in source
    assert "CANARY_AUTHORIZED" not in source


def test_apply_proposals_to_live_overrides_remains_non_io_non_activation(
    tmp_path: Path,
) -> None:
    source = inspect.getsource(apply_proposals_to_live_overrides)
    assert "return None" in source
    assert "write_text" not in source
    assert "write_bytes" not in source
    assert "open(" not in source
    assert "mkdir" not in source

    patch = ConfigPatch(
        id="patch-wp-a4-apply",
        target="research.offline.window_days",
        old_value=30,
        new_value=45,
        status=PatchStatus.APPLIED_OFFLINE,
        generated_at=FIXED_NOW,
    )
    candidate = PromotionCandidate(patch=patch, eligible_for_live=True, tags=["research"])
    proposal = PromotionProposal(
        proposal_id="wp_a4_non_activation",
        title="wp-a4 non-activation",
        description="eligible candidate still must not write live overrides",
        decisions=[
            PromotionDecision(
                candidate=candidate,
                status=DecisionStatus.ACCEPTED_FOR_PROPOSAL,
                reasons=["explicit eligibility does not authorize apply"],
            )
        ],
    )
    live_path = tmp_path / "config" / "live_overrides" / "auto.toml"
    result = apply_proposals_to_live_overrides(
        [proposal],
        policy=AutoApplyPolicy(
            mode="bounded_auto",
            leverage_bounds=AutoApplyBounds(min_value=1.0, max_value=2.0, max_step=1.0),
        ),
        live_override_path=live_path,
    )
    assert result is None
    assert not live_path.exists()
    assert not live_path.parent.exists()
    assert list(tmp_path.iterdir()) == []


def test_proven_path_does_not_flip_activation_or_submit_orders() -> None:
    activation_hits: list[tuple[str, str]] = []
    call_hits: list[tuple[str, str]] = []
    for rel in PROVEN_CONFIGPATCH_PATH:
        path = REPO_ROOT / rel
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for name in _forbidden_activation_writes(tree):
            activation_hits.append((rel, name))
        for name in _forbidden_calls(tree):
            call_hits.append((rel, name))
    assert activation_hits == []
    assert call_hits == []
