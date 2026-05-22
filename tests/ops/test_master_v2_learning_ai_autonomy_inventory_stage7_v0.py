"""Static contract tests for Stage-7 model/policy approval state machine (Learning Inventory §10)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
)
TAXONOMY_SPEC = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
ROADMAP_SPEC = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
PROMOTION_SM = REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md"
DECISION_AUTHORITY_MAP = (
    REPO_ROOT / "docs" / "ops" / "specs" / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
)

FORBIDDEN_DUPLICATE_SPEC_PATHS = (
    "STAGE_7_MODEL_APPROVAL",
    "MODEL_APPROVAL_STATE_MACHINE",
    "STAGE_7_MODEL_POLICY_APPROVAL",
)

REQUIRED_STATE_IDS = (
    "S0_IDLE",
    "S1_MODEL_RECOMMENDATION",
    "S2_POLICY_CANDIDATE_DRAFT",
    "S3_OFFLINE_RETRAIN_COMPLETE",
    "S4_SHADOW_EVIDENCE",
    "S5_PAPER_EVIDENCE",
    "S6_TESTNET_EVIDENCE",
    "S7_APPROVAL_PACKET_ASSEMBLED",
    "S8_GOVERNANCE_REVIEW",
    "S9_OPERATOR_DECISION_PENDING",
    "S10_OPERATOR_ACCEPTED_BOUNDED",
    "S11_CANARY_PILOT_ELIGIBLE",
    "S12_LIVE_DEPLOY_PENDING_EXTERNAL",
    "S13_MONITORED_AUTONOMY_LOCKED",
    "S14_ROLLBACK_OR_VETO",
    "S15_RETIRED",
)

STAGE_7_MACHINE_MARKERS = (
    "STAGE_7_MODEL_APPROVAL_STATE_MACHINE_V0=true",
    "STAGE_7_APPROVAL_STATE_COUNT=16",
    "MODEL_RECOMMENDATION_NON_AUTHORIZING=true",
    "POLICY_CANDIDATE_NON_EXECUTING=true",
    "APPROVAL_PACKET_REVIEW_INPUT_ONLY=true",
    "ONLINE_LEARNING_TO_LIVE_FORBIDDEN=true",
    "MODEL_CHANGE_REQUIRES_REAPPROVAL=true",
    "FORBIDDEN_AUTO_PROMOTION_RECOMMENDATION_TO_LIVE=true",
    "FORBIDDEN_AUTO_PROMOTION_EVIDENCE_PASS_TO_LIVE=true",
    "FORBIDDEN_AUTO_PROMOTION_PACKET_TO_GO_DECISION=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true",
    "GO_DECISION_REQUIRES_EXTERNAL_RECORD=true",
    "AI_L6_EXEC_FORBIDDEN=true",
    "KILLSWITCH_SAFETY_VETO_DOMINATES=true",
)


def _spec_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_stage_7_section_present() -> None:
    text = _spec_text()
    assert "## 10) Stage-7 model/policy approval state machine" in text
    assert "Reuse-before-new" in text


def test_all_stage_7_machine_markers_present() -> None:
    text = _spec_text()
    for marker in STAGE_7_MACHINE_MARKERS:
        assert marker in text


def test_all_s0_through_s15_state_ids_present() -> None:
    text = _spec_text()
    assert "STAGE_7_APPROVAL_STATE_COUNT=16" in text
    for state_id in REQUIRED_STATE_IDS:
        assert f"`{state_id}`" in text, f"missing state_id {state_id!r}"


def test_forbidden_auto_promotion_literals_present() -> None:
    text = _spec_text()
    for literal in (
        "FORBIDDEN_AUTO_PROMOTION_RECOMMENDATION_TO_LIVE",
        "FORBIDDEN_AUTO_PROMOTION_EVIDENCE_PASS_TO_LIVE",
        "FORBIDDEN_AUTO_PROMOTION_PACKET_TO_GO_DECISION",
        "FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL",
    ):
        assert literal in text


def test_semantic_distinctions_and_critical_inequality_present() -> None:
    text = _spec_text()
    assert "approval_packet_complete ≠ operator_decision_granted ≠ go_decision_granted" in text
    assert "Model recommendation" in text
    assert "Policy candidate" in text
    assert "Monitored autonomy" in text or "Monitored autonomy (Stage 7)" in text


def test_vetoes_and_non_goals_present() -> None:
    text = _spec_text()
    assert "S14_ROLLBACK_OR_VETO" in text
    assert "KillSwitch" in text
    assert "No parallel Stage-7 approval spec" in text
    assert "non-authorizing" in text.lower()


def test_no_duplicate_stage_7_approval_spec_introduced() -> None:
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_PATHS:
        matches = list(specs_dir.glob(f"*{fragment}*"))
        assert matches == [], f"duplicate spec surface: {matches}"


def test_taxonomy_crosslinks_learning_inventory_section_10() -> None:
    taxonomy = TAXONOMY_SPEC.read_text(encoding="utf-8")
    inventory = _spec_text()
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in taxonomy
    assert "§10" in taxonomy
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in inventory
    assert "§12" in inventory


def test_taxonomy_crosslinks_learning_inventory_section_11_v0() -> None:
    """Taxonomy §12 stage-7 indexes Inventory §11 evidence pointer; §10 approval owner preserved."""
    taxonomy = TAXONOMY_SPEC.read_text(encoding="utf-8")
    inventory = _spec_text()
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in taxonomy
    assert "§10" in taxonomy
    assert "§11" in taxonomy
    assert "learning-change evidence pointer index" in taxonomy.lower()
    assert "approval SM" in taxonomy or "approval state machine" in taxonomy.lower()
    assert "non-authorizing" in taxonomy.lower()
    assert "§11" in inventory
    assert "§10" in inventory
    assert "stage 7" in inventory.lower() or "§12" in inventory
    assert "LEARNING_CHANGE_EVIDENCE_INDEX_POINTER_ONLY=true" in inventory
    assert "## 10) Stage-7 model/policy approval state machine" in inventory


def test_taxonomy_crosslinks_learning_inventory_section_12_v0() -> None:
    """Taxonomy §12 stage-7 indexes Inventory §12 trigger pointer; §10/§11 separation preserved."""
    taxonomy = TAXONOMY_SPEC.read_text(encoding="utf-8")
    inventory = _spec_text()
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in taxonomy
    assert "§10" in taxonomy
    assert "§11" in taxonomy
    assert "learning-trigger pointer index" in taxonomy.lower()
    assert (
        "Inventory §12" in taxonomy or "distinct from this spec §12 autonomy crosswalk" in taxonomy
    )
    assert "learning-change evidence pointer index" in taxonomy.lower()
    assert "approval SM" in taxonomy or "approval state machine" in taxonomy.lower()
    assert "non-authorizing" in taxonomy.lower()
    assert "LEARNING_TRIGGERS_COMPACT_INDEX_V0=true" in inventory
    assert "LEARNING_TRIGGERS_POINTER_ONLY=true" in inventory
    assert "## 12) Learning triggers compact pointer index" in inventory
    assert "§11" in inventory
    assert "§10" in inventory
    assert "src/trigger_training/" in inventory


def test_roadmap_crosslinks_learning_inventory_section_10() -> None:
    roadmap = ROADMAP_SPEC.read_text(encoding="utf-8")
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in roadmap
    assert "§10" in roadmap or "Stage-7" in roadmap


def test_promotion_sm_crosslinks_learning_inventory_section_10() -> None:
    promotion = PROMOTION_SM.read_text(encoding="utf-8")
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in promotion
    assert "§10" in promotion


def test_decision_authority_map_crosslinks_learning_inventory_section_10() -> None:
    """DAM stage-10 row indexes Inventory §10; stale 'missing approval chain' wording removed."""
    dam = DECISION_AUTHORITY_MAP.read_text(encoding="utf-8")
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in dam
    assert "§10" in dam
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in dam
    assert "§12" in dam
    assert "S0" in dam or "Stage-7" in dam
    assert "non-authorizing" in dam.lower()
    assert "runtime enforcement" in dam.lower()
    assert "consolidated authoritative approver map is not yet canonicalized" not in dam
    assert "authoritative approval chain is not yet canonically unified" not in dam
    assert "canonical authoritative approval chain is missing" not in dam


def test_inventory_decision_authority_row_dam_bidirectional_crossref_v0() -> None:
    """Inventory §4 row and §5 no longer mark DAM missing/partial after #3623 cross-ref sync."""
    inventory = _spec_text()
    dam = DECISION_AUTHORITY_MAP.read_text(encoding="utf-8")
    assert (
        "decision-authority map marks learning/model/policy chain as missing or partial"
        not in inventory
    )
    assert "one consolidated canonical chain remains incomplete" not in inventory
    assert "**§10** is canonical Stage-7 approval index" in inventory
    assert "Decision Authority Map stage-10 row cross-references **§10**" in inventory
    assert "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md" in inventory
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in dam
    assert "§10" in dam
    assert "runtime enforcement" in inventory.lower()


LEARNING_CHANGE_EVIDENCE_INDEX_MARKERS = (
    "LEARNING_CHANGE_EVIDENCE_INDEX_V0=true",
    "LEARNING_CHANGE_EVIDENCE_INDEX_POINTER_ONLY=true",
    "LEARNING_CHANGE_EVIDENCE_INDEX_NON_AUTHORIZING=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "GLB015_EVIDENCE_NOT_APPROVAL=true",
)

LEARNING_CHANGE_EVIDENCE_INDEX_STATE_IDS = (
    "S1_MODEL_RECOMMENDATION",
    "S3_OFFLINE_RETRAIN_COMPLETE",
    "S4_SHADOW_EVIDENCE",
    "S5_PAPER_EVIDENCE",
    "S6_TESTNET_EVIDENCE",
    "S7_APPROVAL_PACKET_ASSEMBLED",
    "S9_OPERATOR_DECISION_PENDING",
    "S12_LIVE_DEPLOY_PENDING_EXTERNAL",
    "S13_MONITORED_AUTONOMY_LOCKED",
    "S14_ROLLBACK_OR_VETO",
)


def test_learning_change_evidence_index_section_present_v0() -> None:
    """Inventory §11 learning-change evidence index exists (§8 follow-up slice)."""
    text = _spec_text()
    assert "## 11) Learning-change evidence index" in text
    for marker in LEARNING_CHANGE_EVIDENCE_INDEX_MARKERS:
        assert marker in text
    assert "Reuse-before-new" in text
    assert "No parallel Stage-7 approval" in text


def test_learning_change_evidence_index_maps_to_section10_states_v0() -> None:
    """§11 pointer table maps learning-change evidence types to §10 state ids."""
    text = _spec_text()
    assert "### 11.1 Pointer index" in text
    for state_id in LEARNING_CHANGE_EVIDENCE_INDEX_STATE_IDS:
        assert state_id in text
    assert "build_generic_evidence_run_registry_v1.py" in text
    assert "AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2" in text


def test_learning_change_evidence_index_non_authorizing_v0() -> None:
    """§11 is pointer-only; does not authorize runtime, live deploy, or model release."""
    text = _spec_text()
    assert "pointer index" in text.lower()
    assert "non-authorizing" in text.lower()
    assert "TESTNET_PASS_DOES_NOT_AUTHORIZE_LIVE=true" in text
    assert "GO_DECISION_REQUIRES_EXTERNAL_RECORD=true" in text
    assert "No approval grant" in text
    assert "No runtime transition enforcement" in text
    assert "evidence_complete ≠ approval_packet_complete" in text
    assert "consolidated learning-change evidence index" in text.lower()
    assert "Addressed in §11" in text


LEARNING_TRIGGERS_COMPACT_INDEX_MARKERS = (
    "LEARNING_TRIGGERS_COMPACT_INDEX_V0=true",
    "LEARNING_TRIGGERS_POINTER_ONLY=true",
    "LEARNING_TRIGGERS_NON_AUTHORIZING=true",
    "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "TRIGGER_DOES_NOT_AUTHORIZE_RETRAIN=true",
    "TRIGGER_DOES_NOT_AUTHORIZE_RUNTIME=true",
    "FORBIDDEN_AUTO_RETRAINING_FROM_TRIGGER=true",
    "MODEL_DEPLOY_NOT_AUTHORIZED=true",
)

LEARNING_TRIGGERS_SECTION10_STATE_IDS = (
    "S1_MODEL_RECOMMENDATION",
    "S2_POLICY_CANDIDATE_DRAFT",
    "S3_OFFLINE_RETRAIN_COMPLETE",
    "S4_SHADOW_EVIDENCE",
    "S5_PAPER_EVIDENCE",
    "S6_TESTNET_EVIDENCE",
    "S7_APPROVAL_PACKET_ASSEMBLED",
    "S8_GOVERNANCE_REVIEW",
    "S9_OPERATOR_DECISION_PENDING",
    "S14_ROLLBACK_OR_VETO",
)


def test_learning_triggers_compact_index_section_present_v0() -> None:
    """Inventory §12 learning triggers compact pointer index exists."""
    text = _spec_text()
    assert "## 12) Learning triggers compact pointer index" in text
    for marker in LEARNING_TRIGGERS_COMPACT_INDEX_MARKERS:
        assert marker in text
    assert "Reuse-before-new" in text
    assert "No parallel Stage-7 approval" in text
    assert "Addressed in §12" in text


def test_learning_triggers_map_to_section10_and_section11_v0() -> None:
    """§12 pointer table maps trigger events to §10 states and §11 evidence refs."""
    text = _spec_text()
    assert "### 12.1 Pointer index" in text
    for state_id in LEARNING_TRIGGERS_SECTION10_STATE_IDS:
        assert state_id in text
    assert "§11 S1 row" in text
    assert "§11 S14 row" in text
    assert "MODEL_CHANGE_REQUIRES_REAPPROVAL=true" in text
    assert "BAYESIAN re-entry rule" in text


def test_learning_triggers_non_authorizing_v0() -> None:
    """§12 is pointer-only; does not authorize runtime, retrain, or model deploy."""
    text = _spec_text()
    assert "pointer index" in text.lower()
    assert "non-authorizing" in text.lower()
    assert "TRIGGER_DOES_NOT_AUTHORIZE_RUNTIME=true" in text
    assert "No approval grant" in text
    assert "No runtime trigger dispatcher" in text
    assert "trigger_event ≠ approval_packet_complete" in text
    assert "consolidated learning triggers compact pointer index" in text.lower()


def test_learning_triggers_excludes_trigger_training_module_v0() -> None:
    """§12 excludes trigger_training drills and parallel Stage-7 specs."""
    text = _spec_text()
    assert "src/trigger_training/" in text
    assert "trigger_training_sessions" in text
    assert "offline trigger-training drill scripts" in text
    specs_dir = REPO_ROOT / "docs" / "ops" / "specs"
    for fragment in FORBIDDEN_DUPLICATE_SPEC_PATHS:
        matches = list(specs_dir.glob(f"*{fragment}*"))
        assert matches == [], f"duplicate spec surface: {matches}"
