"""Read-only law/policy projection of the frozen source inventory."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
LAW = "config/governance/current_law_impact_map_v1/source_v1.json"
TECHNICAL_ADMISSION = "config/governance/technical_canonical_wiring_authorization_v1.json"
NUMERIC_ADMISSION_PATHS = (
    "src/trading/master_v2/survival_numeric_admission_v1.py",
    "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_explicit_financial_context_v1.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
    "tests/trading/master_v2/test_survival_numeric_admission_v1.py",
)
NUMERIC_ADMISSION_ID = "CURRENT_NUMERIC_INPUT_ADMISSION_AND_EXPLICIT_OFFLINE_FINANCIAL_CONTEXT_V1"

# Frank's 2026-11-22 instruction covers the D01/D02 reference-checker repair.
# Exact source delta only: original frozen map/config and all runtime owners stay.
D01_D02_ADJUDICATION_DELTAS = {
    "src/governance/unified_blueprint_d01_d02_topology_adjudication_v1.py": (
        "cf4c91d2a6c9cd99890c6c14b3a58784c36f60f065c3cf1a4eb8cdb11dd38d9b",
        "7c7a280dfd8b20c16fa138c0c47f495b5d2a1d6672ed804af6c97e0df5ffecef",
    ),
}

# Frank's 2026-11-22 offline causal-hardening instruction: exactly this original
# attribution/learning handoff and original MI measurement reference repair.
# Frozen policy objects and runtime grants stay.
DECISION_ATTRIBUTION_LEARNING_DELTAS = {
    "src/governance/unified_blueprint_decision_attribution_evidence_v1.py": (
        "ba46e7f84113d18b82a1d363b78a6efc816e14fbf4d7728c8921b2a71071a4a2",
        "fcbaeaf33ea162244bcb0045729ee9c093c1b2c45d9a47492ad6008527025ea4",
    ),
}

# Frank's 2026-11-22 offline causal-hardening instruction covers this exact
# P5 artifact-admission/error-translation bundle. Frozen policy objects, source
# tags and runtime grants stay; ordinary development hashes admit no other body.
P5_ARTIFACT_ADMISSION_DELTAS = {
    "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/adapters_v1.py": (
        "30581db340c8588fc4c5e93b7915c393b04eb67629e35ac32e4b89b89bebc4cc",
        "010247d126ecd36ee0ef6516ca6dd4020729ed6dc310d04cc64b158238e66f14",
    ),
    "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/optimization_envelope_evidence_v1.py": (
        "46b1ade28814de75e449d04d486f59a868c49c3cf7798a8449b3f549df2aebee",
        "7b91d4ec326671df7e02713a3216e07915250102c0a2bee6e59e0c2524d40801",
    ),
    "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/meta_learning_routed_evidence_v1.py": (
        "f0c3fde4de45d42b921d696063501afc1a6ed77da165f85cf85ac677a9a42e3b",
        "9066891eb81c326c493ae804599f35b453a2eca7015b1d4f2a2e758bd3b9c089",
    ),
}

# Frank's 2026-11-22 offline causal-hardening instruction: exact original P5
# binding-body/record-ID admission only. Frozen objects and runtime grants stay.
P5_BINDING_CONTEXT_ADMISSION_DELTAS = {
    "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_governed_binding_context_v1.py": (
        "d3257487bffea26ae46340ea8736c2f8780d46a6b14e80479140c7e3b5a555a9",
        "39ad79ae2c45ac393dabc1edb209c731c233740c8fce6c38f1a7ee37935505dd",
    ),
}

# Frank's separate 2026-11-09 approval covers this exact reviewed four-file
# development bundle. Frozen records/tags and all other policy admission stay
# intact. A new binding hash alone cannot authorize another implementation.
ORDERED_FUNDING_EPISODE_DELTAS = {
    "src/ops/exit_policy_producer_binding_v1/position_episode_binding_v1.py": (
        "51c52f3caec87fd051343c1b47053da5f06dfd5812acca878c0f0d2bf5fe5a5d",
        "bf1c90a45a80171b5d3b1ed192a9348fe89271e71be490cff92fa2076e82569d",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_entry_source_v1.py": (
        "300cb76643cb95e05c9abe2d5d53a09fadbead1724b414a4c5c4759ea47817b1",
        "946c35e6c540024679f1a8fb53c9e4b557e5f41ec13972557a1a8f89f52ea769",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py": (
        "853f2fb7fb2eede7b78673944e2118d82b4dadedf4bf0f93327ee9a850a8beed",
        "5b726daeddef92b7697e3a1ac8920bd0b1735b6913def8e41eeeb8f2817db86e",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_close_v1.py": (
        "dd743daba0b43e378cd0c20811d6d6d1f9933a2af91ac58838061fe1c9f0597c",
        "c69cc8a4510de49eee30f241d71759fe54138049ba89731f30ca65ef95c8948f",
    ),
}


# Frank's 2026-11-09 instruction adds one fixed slot/incumbent/replacement
# transaction, 1800 seconds from nomination, its cancellation/restart, and the
# original GGE/Scope/C3/financial path. This is an exact development bundle;
# it neither rewrites frozen inventories/tags nor grants an external effect.
RESERVED_SLOT_ROTATION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "84051cc3949a6736f1252cd425822397b7f80d7924f052746c3823d3c86450cf",
        "bc04c096f9d20fa7dd360523f3d1f5d77f0d62e5e5afd5f32aefee69fc4609d3",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py": (
        "4e174b0048e8de66c5405235512f9da00e7da75b9a7c627b71096b4b888986f8",
        "0e109341649d82a539e6395e784967645a0907b5bc49f41f4e40dff05da96df4",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/bounded_slot_post_close_v1.py": (
        "42fac4a77874917184c0ad436b46d5860924c7c76b73e2dc030cf7cc5129428f",
        "34cbb33104b490f8eb8d2bd536e3e96e9a2f988099ca289c4bcf679517b49a9d",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/constants_v1.py": (
        "536e4827dfea87bcdcfee11234a38d0fb3589f6dd7ae2b073461ed0383c88664",
        "68f9648d45a566ca224575a5dec28c649c36ef93c238daf4883a27dd3d7e8d5a",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "d7c213281a98075f54f1560bd8bd7e7b09f16f3c572f7c916043a691dad48477",
        "8a40e60459b3da835de3cb8d1649c1677043ce53c0825773b83c6fa7ee3aaf01",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/post_close_continuation_v1.py": (
        "adabcae2f9547c0cbf026f971138b31ba8712e8d16c51c0ebe37e2863dd24b1b",
        "fec15a06cc3504c4b37d6029dfa30980ddd3d74b22634712cdb56ef968b8a45c",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/rotation_plan_v1.py": (
        None,
        "9f7322ff1fc357c3b828df4f6c0c73e74db0ee52350d7d90be434ed93255b96c",
    ),
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "5a12b8b0d2f69e74b43ae7e35cf93cdb44b7826f5b86b474d45387ee173d0647",
        "46b4680a588851cd78812be41aa960d73fb4b39130f4c05d7d1cfc7036cb84de",
    ),
    "src/ops/exit_policy_producer_binding_v1/host_binding_v1.py": (
        "70a0fbe3bb90a9ae4bf9cfcda05f57964d0681a5a859e5df6dd36ad8766c22cb",
        "f49f6fd6befc2552f6fdd3e8b74f46558ac1b8675a2656d3c241a74207691ae4",
    ),
    "src/ops/exit_policy_producer_binding_v1/models_v1.py": (
        "d63f2f8ca211c2f613449d95a260f3e261672a6539e6e29152417f3ca6094e24",
        "589dec4be5f00b4909c3aa511a600dfc63a31c92b018b20e9f437faa8334e9bc",
    ),
    "src/ops/exit_policy_producer_binding_v1/persistence_v1.py": (
        "77685dcbd323ebf8e1e35eada804add2cf7d795a05b4b9b8984cd2498f1fb396",
        "adc66058a39f3c84e84fc47ca45fc60f6e99f4605e06dc79d58153fc5de76826",
    ),
    "src/ops/exit_policy_producer_binding_v1/producers_v1.py": (
        "dbeb04582421be8b9891fafd810e5fedf0f4465647fbefa6e34b54b482784f8e",
        "f4b9f591c3e99038c033a0899111d2bcb203eed76b4aec70b0b6396410d78b99",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py": (
        "ceda614f8f65ff18fd9be973968938bb78c41bbea91d9434d844c2626c85c48a",
        "196e7da42a39e625ea4de756df9fc1b3f6533f97a4df7392ae9f94f854bedace",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py": (
        "c04f97c4fe0f405757661a715774ca4debf28d3d00c10c7077e5ed866e1c96d6",
        "ca2c078daeb147d6a2888add896dfc9c6785bfb2a1465a87bfe1aeba6f5869ff",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_close_feedback_v1.py": (
        "a93c61c73ebbbc11402456b2fe4fa36ec3e761b49b3b24309c9f45bf353d944f",
        "12b03e787f3edf42d4171e83e477a98f6b13d0354ce4129e8db3f64c31ef94c4",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_rotation_close_v1.py": (
        None,
        "843de05030c1a4bbb7420762c60fe3e16bfbdbe89b01a184ffe4f857969b69a2",
    ),
    "src/ops/mf_membership_context_artifact_contract_v1.py": (
        "8dda221cd46158140531e0a1cebce689ffe135ee821975fb5d712bf5380ef2be",
        "c813cae3d80dae5338c3bf4a96fe025265dcf0c3b696eb08bce5f8ad6bd6aca8",
    ),
    "src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py": (
        "976131456817f30d0c8c6df37b6a986644ca0ddadfe14aa11918eef9901f808c",
        "370d4a90b668218569faeff5997c1bd759e20af47cbd91ca1116245f9fba4a3d",
    ),
    "src/ops/single_selected_future_policy_v1/producer_v1.py": (
        "fdceed28a977a871f826909320eedc7d72ec268cc8532e9218a83c48d89e06b8",
        "e1adca9f8633cb75cf2f3ff557261839577d852464ee2eed40f54eda00f56c78",
    ),
}


# Cap23 receipt validity is independent of the existing slot rotation timer.
CAP23_SELECTION_VALIDITY_POLICY_DELTAS = {
    "config/ops/single_selected_future_policy_v1.toml": (
        "53e57ca79dc4c49e96e61a29b26eb5fb69d4c151ca4072ec51e145ffd72c1548",
        "7dacf55597c8e82919145577c535eae116109531ac16956b5c93b77e0811b6ca",
    ),
    "src/ops/canonical_r6_phase_8_1_policy_precondition_v1/checklist_v1.py": (
        "39fa1662652f8b0c4dcb7adc1e0957cb1197e863efce9966b87d5ce9d2fcfa3a",
        "451d3693efdaf9857643038fa742bbf2cc2ea84cc19726e68e0bdc2d0ef93d93",
    ),
    "src/ops/canonical_r6_phase_8_1_policy_precondition_v1/verifier_v1.py": (
        "6b31bad30981f6a9364728c0261b52b0765a6b3ede9bf69d0f65c7bb4bec4c8a",
        "0ac98265bc0dec03c9b7bfafb6cf3395a93bf999ea01e1cace5d40d8ac840e0a",
    ),
    "src/ops/single_selected_future_policy_v1/constants_v1.py": (
        "92f9e96ea03392771f990c4f37a500bb5094af155e15ed04088863b88f7930ff",
        "b7add7c90933e448fcc21e6690a979d564c402ee5aadc077df5192d300ae6e5e",
    ),
    "src/ops/single_selected_future_policy_v1/models_v1.py": (
        "bba6eda80367d17eef4ccec35b40eea7d9662394ef6f89c3a818958e44621526",
        "664593c80d8e1d4bfd3327225ba958338d9a518c8dee4fb7bf4c92424c9e0d8f",
    ),
    "src/ops/single_selected_future_policy_v1/policy_v1.py": (
        "e5a30f8b5410401827c1d42c7aaf99f468b13f52cc67ca8e2796d60d46b6d750",
        "a495d1704180844fe99cd6bc9f1cb23b137af61341bf71c6846ad7b4d6eba813",
    ),
}

CAP23_SELECTION_VALIDITY_ROTATION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/constants_v1.py": (
        "68f9648d45a566ca224575a5dec28c649c36ef93c238daf4883a27dd3d7e8d5a",
        "4e72fc1eff15933bdd6c2a303b7d17dc31e884cac8d25ea6aa2aa066a407ae5c",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "91011736f288bd20d5744a883223a34b283f9fa6ff9ed044fe108e76bc53d665",
        "a22c42486628322348ef1e491cc3493fbdc294784116fa2f0d1595f262a23cb0",
    ),
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "46b4680a588851cd78812be41aa960d73fb4b39130f4c05d7d1cfc7036cb84de",
        "195c20b9468bff56df4e15d4c4b55da05a13442f1514be70bcf0b793e27bfc9c",
    ),
    "src/ops/single_selected_future_policy_v1/producer_v1.py": (
        "e1adca9f8633cb75cf2f3ff557261839577d852464ee2eed40f54eda00f56c78",
        "30920e7e4ccae6c7064e4da328cd97f8211fe23f0c596447cce0572f2c2837f3",
    ),
}

# Exact source successor for instrument-bound C1 history and per-lane
# Mark/Index provenance at the unsealed orchestration boundary.
N5_ORIGINAL_MARKET_INPUT_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "a22c42486628322348ef1e491cc3493fbdc294784116fa2f0d1595f262a23cb0",
        "873ea6f58e5c71b3a46d5716fda5ac573998b931d6e77c6c74d41931ed94e067",
    ),
}

# The 19 reviewed rotation files at 2f6091dd0, keyed by path in canonical JSON.
SOPH_SHADOW_SLOT2_ROTATION_PARENT_SHA256 = (
    "898ccf9e4580ed425a2e76b7b7258fa30523402834baf111b5dc69168d4b7238"
)
SOPH_SHADOW_SLOT2_PUBLICATION_DELTAS = {
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "195c20b9468bff56df4e15d4c4b55da05a13442f1514be70bcf0b793e27bfc9c",
        "e472ee7adf42c00173f22f5cce28ef27767e90545582682c680c77116b98c5cb",
    ),
}

# Fixed original ranks extend the exact SOPH publisher revision on the same rotation parent.
FIXED_RANK_PUBLICATION_DELTAS = {
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "e472ee7adf42c00173f22f5cce28ef27767e90545582682c680c77116b98c5cb",
        "3f9259c701a031761be90d9a951660be531134076037d20221c9d00629b63c04",
    ),
}

FIXED_RANK_PERSISTENCE = (
    "src/ops/current_mf_n5_durable_lane_assignment_persistence_v1/persistence_v1.py"
)
FIXED_RANK_PERSISTENCE_SHA256 = "3888a545bd92f39036eecdd66293fd012d6b0d5286e5e66eeb0480df091fc707"

# A slot-4 successor must go through its scoped recovery owner. Pair its
# publisher with the matching persistence implementation for immutable generations.
SHADOW_SLOT4_PUBLICATION_DELTAS = {
    "src/ops/current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1/checked_publication_v1.py": (
        "3f9259c701a031761be90d9a951660be531134076037d20221c9d00629b63c04",
        "c643c3d0b6a75d31586a34c5fc08e77c2ba55e6dd0b67c0409c7d013b631de17",
    ),
}
SHADOW_SLOT4_PERSISTENCE_SHA256 = "bd5b98f6f64ee8403238b65f51caaca4b7827955f3b661ad9a1273e2d4b421e1"

# Frank requested the open test-slot loss close and continuation of BWP1.
# This exact two-adapter successor carries an original-budget proof to the
# existing per-cycle safety input. The reviewed rotation parent, native Core,
# funding episode adapters, startup, recovery and external-effect rights remain.
OPEN_TEST_SLOT_LOSS_PROTECTION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "bc04c096f9d20fa7dd360523f3d1f5d77f0d62e5e5afd5f32aefee69fc4609d3",
        "9a2d6867a1bc4ccc6a9ab53e9d719d69945d5cdf7c435d62228443492ef2dec0",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py": (
        "0e109341649d82a539e6395e784967645a0907b5bc49f41f4e40dff05da96df4",
        "214b7b0ddfe42517b801098d87e60bb6df3adffada3a43cf33d6c73f0aa56c06",
    ),
}


# Current Scope/price-source instruction and the explicit PR/merge request:
# retain source clocks through these three outer adapters. This is a complete
# exact successor of the reviewed loss-protection bundle, not an admission for
# native Core changes, other policy bodies or a development hash by itself.
CURRENT_SCOPE_MARK_ADMISSION_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "9a2d6867a1bc4ccc6a9ab53e9d719d69945d5cdf7c435d62228443492ef2dec0",
        "5d8847e963b1d158621f497ec33b351eb6c49b48e02f3442954bf8221e44e7af",
    ),
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py": (
        "8a40e60459b3da835de3cb8d1649c1677043ce53c0825773b83c6fa7ee3aaf01",
        "91011736f288bd20d5744a883223a34b283f9fa6ff9ed044fe108e76bc53d665",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py": (
        "ca2c078daeb147d6a2888add896dfc9c6785bfb2a1465a87bfe1aeba6f5869ff",
        "c5f842663435ae1240c79b70bb087afc2e5d208949c6c49bfbb46d4bd3c1a425",
    ),
}


# Double Play's bounded close, recovery, POST integrity and 29P assessment sources.
# Each pair pins the reviewed parent and its exact successor.
# The full-scope Layer-C change updates three existing exit-policy sources.
DOUBLE_PLAY_POLICY_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "5d8847e963b1d158621f497ec33b351eb6c49b48e02f3442954bf8221e44e7af",
        "54b3e4304c56871e332cde526d052158ad4bd693f8c401d24a4a45a7350d9d14",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py": (
        "214b7b0ddfe42517b801098d87e60bb6df3adffada3a43cf33d6c73f0aa56c06",
        "1349b51057f4d5e590f304c3bd7677c5d0883e3421d0b5036d896e6a659d5af0",
    ),
    "src/ops/exit_policy_producer_binding_v1/host_binding_v1.py": (
        "f49f6fd6befc2552f6fdd3e8b74f46558ac1b8675a2656d3c241a74207691ae4",
        "112075c1a4160cad51525ff2f9bb4e964bb01da0bd18dc67be8a399fc5f23915",
    ),
    "src/ops/exit_policy_producer_binding_v1/producers_v1.py": (
        "f4b9f591c3e99038c033a0899111d2bcb203eed76b4aec70b0b6396410d78b99",
        "f2b88a9b451230617bf9b16222e8f4ed72316f93d6b6e3d476482ded5b7b8750",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_close_v1.py": (
        "c69cc8a4510de49eee30f241d71759fe54138049ba89731f30ca65ef95c8948f",
        "a56910653c688a597c7fa9cf8ba06f76fee3d0529e45ad8a9d1c0ae47bc9deff",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py": (
        "196e7da42a39e625ea4de756df9fc1b3f6533f97a4df7392ae9f94f854bedace",
        "46064d0180972b2ecbd7f32db5daea76b5201064ff73816a6a905846fa929cb4",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py": (
        "c5f842663435ae1240c79b70bb087afc2e5d208949c6c49bfbb46d4bd3c1a425",
        "082c697efc5953d68c11e4217554bc07a4ca8bc15e94a9365daa7edd4629337f",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_close_feedback_v1.py": (
        "12b03e787f3edf42d4171e83e477a98f6b13d0354ce4129e8db3f64c31ef94c4",
        "75831f7b37a4a6e46e40f0ca6861d0ad3b78b34f98bb39d806e3810b388fb73e",
    ),
}

# Occupied-scope reversal and simulated booking readback, without send authority.
DIRECT_REVERSAL_SOURCE = (
    "src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py"
)
DIRECT_REVERSAL_POLICY_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "54b3e4304c56871e332cde526d052158ad4bd693f8c401d24a4a45a7350d9d14",
        "10b4338fd08e8b2136868f3545160b9c6bfa2d78d2131c34e20c9ead73789363",
    ),
    "src/ops/exit_policy_producer_binding_v1/simulated_accounting_entry_source_v1.py": (
        "946c35e6c540024679f1a8fb53c9e4b557e5f41ec13972557a1a8f89f52ea769",
        "4b6c4da6fa80edf61b020f9ae770216c08c4e2d1582b2f2cbbe1a0b2bcc4c628",
    ),
    DIRECT_REVERSAL_SOURCE: (
        None,
        "2bfaed9ec981285859990bbee35916e762b25f722fc404673b340f4e04379c28",
    ),
}


# Same-slot rotation of a funded simulated position after an occupied mark.
ROTATION_SLOT_CAPITAL_DELTAS = {
    "src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py": (
        "2bfaed9ec981285859990bbee35916e762b25f722fc404673b340f4e04379c28",
        "c5a3c39f8ac4a8a02c73c03c19c79dcbf989c111c90f8975eab03c555245f09b",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py": (
        "24db3e42481dcd98a548afc8c3da1eb40ba575d5af24baaac174e3d1d7315656",
        "12590786da448e581512dd2e33a2faad3e12ac10d75ca915277737cfb82a398e",
    ),
    "src/ops/p5_productive_layered_core_authority_seam_v1/occupied_mark_state_v1.py": (
        "f4f7e4cf6412a01b3862e5654117d87b4ef849def576c022df443f8f57a662a3",
        "2eb4d943a9e7d42c925e058469a673c6be4041782a972ccbaf9cf0da26872bbd",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py": (
        "d6edf567c95875d3748e3a6431f53e9ab275be91d67377d4d307cb820d224c09",
        "42823f0223a7373e6842bbd5a77549a9f01d8e38ccbead8405c346ac83134794",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/slot_economic_source_v1.py": (
        "1acd6f6c58bc6e90ca8e8d5e0ef554056caf51764aba54de3cf74819416341ca",
        "90a9225bf4f18ffd215caaf42f5b056d16f83e7a99b10b72720cf8b256c5e5a4",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/slot_loss_budget_v1.py": (
        "35c1db4f5f28db416d391fe35d6e6c62f0bc82198a79592e9dad813385768ebc",
        "f0c1ea49021eee7288fcf2bc2927ddbeeede0a4bb94a606ca13126b6db16b52e",
    ),
    "src/ops/single_selected_future_policy_v1/persistence_v1.py": (
        "64548daaf97b2423fc063a9a78afe1f29e070a9a878957b48e5fbc8e3bf61d42",
        "f65bb8bfa69298c320b6e13b9627bd10c1b31c028662c5fa1b16f50b9152c10f",
    ),
}


# Authenticated net-order preparation, ending at the existing execution-admission boundary.
AUTHENTICATED_NET_REVERSAL_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "10b4338fd08e8b2136868f3545160b9c6bfa2d78d2131c34e20c9ead73789363",
        "d8a09b2009cb6ddc42e9e51db0db57074b1f84170a90084332a5e7ce4968b655",
    ),
    DIRECT_REVERSAL_SOURCE: (
        "c5a3c39f8ac4a8a02c73c03c19c79dcbf989c111c90f8975eab03c555245f09b",
        "4210e9e91ff534cd5693eab399962fa97ab65411c24b5fda974d4fc0d1c040f9",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py": (
        "f1859aba52e51e5e253d2d82cf00906fb07635397e73b30cf195a3e582c0f64b",
        "7d22a0975b9ca9751ced61e29d13422e9c3100b170c1d3d32d694aa54b338334",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py": (
        "69f835e4f559a94b8562719829f7c0e5b555cac4c57b28a5201c597ebf00d5de",
        "c3b4874fdd149d97bcf7f6c5479017615c82916a4328e38571216fe0e5b0a5ea",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_shared_post_owner_authority_v1.py": (
        "8ca513ed1e5c4bad31e581f244f51e175469c6bb9b6dcfd3d6d87f1d99afe7c6",
        "55c046ea257ef21a5fdeedd163aee24e8c28ccd6df8e28c037c688fba868492c",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py": (
        "42823f0223a7373e6842bbd5a77549a9f01d8e38ccbead8405c346ac83134794",
        "8920456e43c87f2c0c8264aa56d4045aab7171c7da2cf47f1203cef7583fb46d",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/host_v1.py": (
        "45ed0199f0cd5c106fec54a21c2159a96e26e6dd75386acf69d1a148cf418bcc",
        "e3eda2b4deb0a5530483b1da39229552b48df4e6cb88e8bd7df8ecdca32bb9f0",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/slot_loss_budget_v1.py": (
        "f0c1ea49021eee7288fcf2bc2927ddbeeede0a4bb94a606ca13126b6db16b52e",
        "0352383b74293c361fc2f4b99bc0aef80f7d0badc5c779c65058f25ab1d51643",
    ),
}


# Exact successor for the one-shot net order handoff and original hold readback.
AUTHENTICATED_NET_REVERSAL_SEND_DELTAS = {
    DIRECT_REVERSAL_SOURCE: (
        "4210e9e91ff534cd5693eab399962fa97ab65411c24b5fda974d4fc0d1c040f9",
        "411e4ed47500d9d0606ec2e693de90fb62a2c80b560503d602849a3ae25853e5",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/host_v1.py": (
        "e3eda2b4deb0a5530483b1da39229552b48df4e6cb88e8bd7df8ecdca32bb9f0",
        "bc771b98c527a599c3b11d6f1c5283cefa58dac7c92ba3dca8fe6d823dc9c5ba",
    ),
}


# Exact successor for the authenticated readback and the original-store booking.
NET_REVERSAL_GET_RECONCILIATION_SOURCE = "src/ops/full_core_live_path_composition_root_v1/current_productive_net_reversal_reconciliation_v1.py"
AUTHENTICATED_NET_REVERSAL_BOOKING_DELTAS = {
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py": (
        "7d22a0975b9ca9751ced61e29d13422e9c3100b170c1d3d32d694aa54b338334",
        "565dd0427cf333336d7ccd18384320d496bfbba57c61b2d8fd39de8a0eabc8a0",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py": (
        "c3b4874fdd149d97bcf7f6c5479017615c82916a4328e38571216fe0e5b0a5ea",
        "0625a210cd524e293c99f38bb9a4f5c1cf60da9406710249198ff71545bbbb1a",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_position_management_quantity_handoff_v1.py": (
        "23f6064aec921600cb2772c9ad2ffcb8bbd93117c3473098434c78a03975e223",
        "1e811356c1d81f21ccc0b28bdac376b293e8d98c95dd43adb2dd04d6f93c174e",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_position_close_v1.py": (
        "619e7f9a5a964f3a0a9b1424ed735175f6df78fa11a1112468a42cf0de606665",
        "960ddb132ccf69d61b75e4b4f0c45a9f58e11e369de201f4b604b9e4199fb64e",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "d8a09b2009cb6ddc42e9e51db0db57074b1f84170a90084332a5e7ce4968b655",
        "d2bec19b8d496e26885dad5a40b0888572bbba91e8bda80f25880dd8543b34a7",
    ),
    DIRECT_REVERSAL_SOURCE: (
        "411e4ed47500d9d0606ec2e693de90fb62a2c80b560503d602849a3ae25853e5",
        "93edf5489c9ba630d28754901eb7b71b77c753153ffe55b2004565a04fe635f1",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py": (
        "8920456e43c87f2c0c8264aa56d4045aab7171c7da2cf47f1203cef7583fb46d",
        "fd1cf078fc86bbb166d913ddae7341b9ec78a23dc8da4fe47233426a62a3b9e9",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/host_v1.py": (
        "bc771b98c527a599c3b11d6f1c5283cefa58dac7c92ba3dca8fe6d823dc9c5ba",
        "6e7f41ab30d61b58e6a0916a2c032840319db9d5cebfe3b2f1d83dfd47dca8ab",
    ),
    NET_REVERSAL_GET_RECONCILIATION_SOURCE: (
        None,
        "9cb8cce89fe4784ed0ced1965c79ead8f10cd8991d09e80efbbce62ed39959ff",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/live_net_reversal_booking_v1.py": (
        None,
        "973a0d63554b974f5691a187daca700da66e9aeb35cd72309dc74de410c68d90",
    ),
}

LIVE_INITIAL_SLOT_BUDGET_DELTAS = {
    "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py": (
        "fd1cf078fc86bbb166d913ddae7341b9ec78a23dc8da4fe47233426a62a3b9e9",
        "25c76eb8ec00b1e5e0d33d116ad7c19ed32be9014fa667e67697569a34dc13fd",
    ),
}


OCCUPIED_N1_RUNTIME_DELTAS = {
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "d2bec19b8d496e26885dad5a40b0888572bbba91e8bda80f25880dd8543b34a7",
        "2d49dacfe1c5f5f988a0a702a03b6754c65981fec9dfa93ac774ac5e42292cf6",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py": (
        "93edf5489c9ba630d28754901eb7b71b77c753153ffe55b2004565a04fe635f1",
        "2b62cc9e782f113c731d559ab270b685114e94b57cb87a045afef5b2c0647906",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py": (
        "565dd0427cf333336d7ccd18384320d496bfbba57c61b2d8fd39de8a0eabc8a0",
        "7acbca9c53e83fdcb44a574618e7010ee78cd4daebd2716ffeafd371ead864da",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py": (
        "0625a210cd524e293c99f38bb9a4f5c1cf60da9406710249198ff71545bbbb1a",
        "a01e1276e2c5da3856c0d4203253b14dace8186d7d1f0cd2a9b2228d00cc0735",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/host_v1.py": (
        "6e7f41ab30d61b58e6a0916a2c032840319db9d5cebfe3b2f1d83dfd47dca8ab",
        "02d1773c0a39a9f71a83a71ea82623e1a790092931af49d091bc330243633267",
    ),
}


# Paket 3, Slice 1. Only these exact Safety-owner changes are admitted.
# The frozen policy sources, inventory and all other policy checks remain bound.
OPT_GOVERNANCE_HANDOFF_RETIREMENT_DELTAS = {
    "src/governance/ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1.py": (
        "ac896c8001617c2cc8cdcfca5225f1afa81bc03524244cfcc1ec44dda04062a5",
        "0265a99e89dcf920eaf545de9d8f88078799fd14b6a9c8752858b0d11c30d3dd",
    ),
    "src/governance/optimization_proposal_governance_ingress_v1.py": (
        "2ae0bf6eae57ad8a9d3ffe50c05aa1cbd20f1c1a98aa098f41c9a1c7faa77481",
        "eb2c479ed37e5c88ae3a5876f6ccf8577172edca279dc244ed3d22220a9d378e",
    ),
}

MANAGED_FILEGATE_OWNER_DELTAS = {
    "src/risk_layer/kill_switch/core.py": (
        "050e370eba75fa418fc89a7c3860119178bdde6903c92bba2e1ed1089f340210",
        "c171e4288eca2942dc955a377c3ce58147ae767eb32b8c5aa19897cfbcc2a05f",
    ),
    "src/risk_layer/kill_switch/persistence.py": (
        "95700e7929ce355245a4c9f2ca4ddee07337c65bf4884ca65a95e473ca3ae57e",
        "00b467776cdcec3c7fe32b075a03a89989d819d4684d6b6beaed6f83707dadc2",
    ),
}

# Exact offline G2 source and field-mapping changes.
G2_ARCHIVE_PROJECTION_DELTAS = {
    "config/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1_field_mapping_ledger_v1.json": (
        "209034aac331c7fe9ce443a113c49fd605b6841b685320d3661105bcc76dc34a",
        "9c661ffd77d80f9780c0e265e13f4633370cf18467bef4d8f578d2b654b979b5",
    ),
    "src/governance/governed_authority_map_atlas_guided_whole_system_g2_primary_causal_e2e_v1.py": (
        "a2221ea8bd07069c9b8166597f66f7c11d8da272aeb251d5a7effcf3160fcf91",
        "1b0fc364b5c78f2f486494c046c26615f1b57833f5e17ccb52c5c90d06d536b5",
    ),
    "src/governance/governed_m4_m8_evidence_return_to_meta_learning_optimization_feedback_real_mechanical_continuation_v1.py": (
        "8b56a8d02b5cc2ef584e1264a91454b9ee5636091a3f18e56afff91fd4d93a0c",
        "0fa9bb43914ee82426817b7d6e180ab8675d9e95eb3530a3fa617bda35a18666",
    ),
    "src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py": (
        "28f9234a45a3abcbc6948e3fb965f02df884f249d764b1b235511936431d4cec",
        "8aa2d662e3f12d6bcc76f8a7e7364bfb5ae6588b71c2d301a6de66e0bf3183c4",
    ),
    "src/governance/governed_runtime_primary_to_offline_observation_projection_v1.py": (
        "8dd773e29c994f13c63046ed1036d9cb21035c70d19aad196de0a8098398c1f3",
        "1a40ecb31adbbff6201eee838b9021ca9088b59b398b689f613016939ff31c97",
    ),
}
# Reviewed policy-source changes for the execution authority audit.
EXECUTION_AUTHORITY_AUDIT_DELTAS = {
    "src/governance/current_productive_actual_venue_post_admission_policy_v1.py": (
        "9e642bd18b5067dd5ca03513d40fd67a951db194ac72d28f9e75a9b5861148bb",
        "ac0b163ba31e2e1fa73d0bb398c51da4f238551de8e679fed63a2f2f7c18b7e4",
    ),
    "src/governance/current_productive_real_venue_post_admission_v1.py": (
        "583a273355fd0346b4907fb8c64a19ed23788b0f7d68e09bad2a3dfb2fde483d",
        "c3da330b045f6d7fc47c703f1a00c351547f9e586462ee021ea8094becfedfff",
    ),
    "src/governance/f1_m9_owner_apply_authorization_record_v1.py": (
        "afacbec4a05131b514278940a25ecd4276f63f11d30d0ff3798470fe41f4d65c",
        "8d4931570459765549bcd54f4a468dedb518e529af5aa2b0a50a7ab6db950555",
    ),
    "src/governance/f1_m9_productive_apply_execution_boundary_v1.py": (
        "2042a614932c9ea06b2f1c52e9554183464107d88cc02f7c1b4ef39f32dfb12a",
        "a6e87080209373061f9926326f91b075d5ee0a5b21474168a3a736daae94fb1c",
    ),
    "src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py": (
        "109cbc001d92daf042409b052530338cfa3575d057e5c3932fa4f07e3bb49279",
        "b6a6f0f877a05ac0083fa50bbbde4e5b78209aef2c73e14b2403de0fe988547b",
    ),
    "src/governance/f1_m9_scoped_owner_apply_authority_v1.py": (
        "bbd03f7f131201c68e5a0d4e065b2f92428d34ca4d4c2cda486c81570181289b",
        "0512872ea352b2b8d375c826394656a51490b0c23fe2e56273aef91233ac13eb",
    ),
    "src/governance/f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1.py": (
        "130d501e6973da96c866f4705b3b81a79155951799c99afdd718b70e535a5677",
        "dd238805e5c5587a0c6afae8a8f5125aa8aa72a2db7f7f70329d895449fba4bb",
    ),
    "src/governance/governed_f1_m9_scoped_owner_threshold_value_ratification_real_mechanical_continuation_v1.py": (
        "f63e45854c36670664e79048c45cf63cf2be08a45d8ca474be83d92303b222c6",
        "def572409eafb63fb62a6bfb75c29500517abed23aa87f583b8f6a33d1ca5d49",
    ),
    "src/governance/k1_opaque_signing_handle_governed_construction_v1.py": (
        "036b586eeefcd14ca54acfb18059a5aea3f17e374fad3bc41977e4a034ec2929",
        "a51b7a409d69b2fdabfc04f62864b31d61c3912d98681e36d19381704114600c",
    ),
    "src/governance/post_6940_live_readiness_convergence_v1.py": (
        "302251e5dda81aac4acca9e017825654c25ed29a6de033eb2ba8a1640624a490",
        "e0af832064e4c44587b7cf093f95a4170ce072265c157d9c5a72bb2f0f26a22b",
    ),
    "src/governance/post_6941_pre_external_intent_to_execution_seam_adjudication_v1.py": (
        "6544ad9470a29e83881986a3a24e8318238321ca0ed6975841b40b99f3ae5056",
        "7a7104d720db8f9b26a17a42dd89b823f9b9458070eca1e59829aee4d2529afe",
    ),
    "src/governance/post_6942_external_effect_authorization_full_chain_forensic_v1.py": (
        "19f2d5e8f98a16a1cc02ef4a8e2e42f3b4d96e14cdb28872602fe391444792c5",
        "0e5d788025f1556a37705d84c7e48bb2554d185edd5316ed15da8e339bfaa084",
    ),
    "src/governance/real_keychain_access_governed_credential_material_acquisition_v1.py": (
        "f0c07693ccce9cb0649bc26d116b1a5a71125762767408daab23c92dcf31fa11",
        "0ff9dcf45a087da77eba1a45d0374fcba954cc996478207b01d0975c0af7e08a",
    ),
}

OWNER_ADJUDICATION_DELTAS = {
    "config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json": (
        "a68d5a7d3b3eb1f096c41c6ac6e9033f6d8cc5197f0a227f6cffc4f978317e41",
        "efc3a5f485d93573a1aa55332ff6fb782103138acc1601bc6138258b0db2808d",
    ),
    "config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json": (
        "f22a3d378704e9ead4472014afe372b711f0f61fe0767b2916a5d9e7c08ce4fd",
        "a3528a9f935658292498db899187c936c177fe91cf51048f466e71bbc18a185a",
    ),
    "src/governance/economic_diagnostic_optimization_boundary_v0.py": (
        "3d1f997b686ef62573e394da72d777661f0f6af6e2bfcaf84a207185d1ba5755",
        "360d1bd8a0d84127c0624c33110ff5bef6f7d6a38c9ed7456c2e03481872ed1f",
    ),
}


def validate_managed_filegate_owner_bundle(root: Path, policies: list[dict]) -> None:
    frozen = {row["path"]: row["frozen_sha256"] for row in policies}
    pairs = MANAGED_FILEGATE_OWNER_DELTAS
    if any(frozen.get(path) != before for path, (before, _) in pairs.items()):
        raise ValueError("MANAGED_FILEGATE_BASELINE_INVALID")
    actual = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in pairs}
    baseline = {path: pair[0] for path, pair in pairs.items()}
    successor = {path: pair[1] for path, pair in pairs.items()}
    if actual not in (baseline, successor):
        raise ValueError("MANAGED_FILEGATE_REVIEWED_BUNDLE_REQUIRED")


TESTNET_PREPARATION_REVIEW_DELTAS = {
    "scripts/ops/inspect_btc_demo_account_v1.py": (
        "610f6027a1cbde47a4e45024e23db6d012a0420e1ba7b6d6e6c8dce0f74e5c7c",
        "2759cd4fbdd94278887f4d4f4be1f79168916b4ddcc4f1a9507cc1162d322db9",
    ),
    "src/ops/btc_demo_budget_owner_v3.py": (
        "666c1f2dc3126ff5df501a352d734fb9fd3312d1971c019203969f0243b5b8e8",
        "3dbf24c4ef153ea24391f1a22f574183809e4d0b7be66df2633c6645fe06148f",
    ),
    "src/ops/btc_demo_entry_financial_inputs_v1.py": (
        "2657e0d829b0ac1480345c7f928b29fa7bc7857f7d0d56ccd277200448ec896c",
        "f2c9e613309e9085444019dd4866c9a27c2ed108d7273ea4e0ed7febf3293996",
    ),
    "src/ops/btc_demo_lane3_v2.py": (
        "1f123f69c879128faf9d8165ddac551f0733d0a21d95c2c358548a21bed7fce6",
        "27d5d0ed357c9c817392e264eaff6889732da40bad75a12ebb893625aa0051a5",
    ),
    "src/ops/btc_demo_net_reversal_financials_v1.py": (
        None,
        "4bcb0b53328a42e794fec34b230e90f05afab95609d7c68399462d455b866486",
    ),
    "src/ops/btc_demo_net_reversal_pretrade_v1.py": (
        None,
        "8d62a270e43ee9850aed5f159f2b915c79945657c7bcfe55ce3f049325f773a1",
    ),
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py": (
        "2d49dacfe1c5f5f988a0a702a03b6754c65981fec9dfa93ac774ac5e42292cf6",
        "25913575198dc901956f1abb22ef73b2db2f305fc310cffebf3d1ec060b6185f",
    ),
    "src/ops/execution_reconciliation_get_provenance_v1.py": (
        "bdd5d19298e366a052fc12288f080278ea1a0552dbab18fa3d84e0352fd2923d",
        "989c2ab52ab634f120bff840d2d6111dd35df0a37007cf9bb3eb56285363eee0",
    ),
    "src/ops/execution_reconciliation_proof_store_v1.py": (
        "d73867f3e46f069f1b3c64e53b06f58619a3844b61506e780b23c3ef162b5adf",
        "090db83f51bac05461062311ec88a56d84401360afb512d792ecc147ebc25d7f",
    ),
    "src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_okx_venue_auth_headers_v1.py": (
        "4c4376b631dabd5dbaffe7396cdb48ddf467bee9f9e768d4cace74c3fe30976d",
        "87706d5a4e7145bcba071934ae51ac6a119129da370794462ed88a35a8488233",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py": (
        "2b62cc9e782f113c731d559ab270b685114e94b57cb87a045afef5b2c0647906",
        "bd553c70644d8bece02fe36cb6f82d39c9870c17aff6477d33d3ba58727c546a",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py": (
        "12590786da448e581512dd2e33a2faad3e12ac10d75ca915277737cfb82a398e",
        "1c2b5cf741f390ecfca216cb2517ef994e5206d8a1f432b9ea7af7584076602f",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py": (
        "7acbca9c53e83fdcb44a574618e7010ee78cd4daebd2716ffeafd371ead864da",
        "d41c7ae159049b45deca6efac5faf8ac7bdc0175a2447f1a1fe2bfe72ae38899",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py": (
        "98649b127e52d57650eb70bd5f0e1581dedbcfa18eba6c0ef3c5c8fc20a992f8",
        "fa9c0c32a299ae1d7194204cb04697f106028c98beb54c5c5bcd3061b79d50ca",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_n1_venue_quantity_limit_admission_v1.py": (
        "f568c91c37818320bde6142061975bc557cde065c83b0f4fdb55fef196d65b83",
        "537cbdc3ce5be9320579d57fa9d952425177fc146e880a24b6007910a5ffc364",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_net_reversal_reconciliation_v1.py": (
        "9cb8cce89fe4784ed0ced1965c79ead8f10cd8991d09e80efbbce62ed39959ff",
        "6dc77faab538ce75c59aee9ceb1ff2bd8306ce4447750dfdcf8149fad03c6f5c",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py": (
        "7b8fed236443db95ae551f0b9b91ad222883d7a42e1531c175a8789c8df72c1c",
        "26f4b6e83369cf364d8b5b83e33ad1ea0fb337fc401584d58dfa8945284cd014",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_pending_observation_v1.py": (
        "1063d82271629b76df49b3d51d4040fb5d46de2ff16b21b6d31db9a626294e84",
        "ff77d2e67218000b74f56e850ec210c3701ba0333ba4666721e5c039c90582cc",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_shared_post_owner_authority_v1.py": (
        "55c046ea257ef21a5fdeedd163aee24e8c28ccd6df8e28c037c688fba868492c",
        "95d399e03b5f5c6f029b24d05dbb2e9354a2d7fee6898e853a862f85abcbbc27",
    ),
    "src/ops/full_core_live_path_composition_root_v1/fresh_pretrade_runtime_get_v1.py": (
        "004f62a388b4acaf813a31bf6be2224abae3573b24da950fe82893960a79d0a1",
        "d42c18ae8c8a5b5c41f53b663b1bd5bf0341abdf86b0f90e8332ab3496468fce",
    ),
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py": (
        "649d3cda526027fc830e1cbaddcbb4c75988960cfb2ebb69fdc3a339d5885f2e",
        "972571f3bc6d6856c719d218d2a9c2059a2c6dea44bdcc13df8f4d195d37d5f6",
    ),
    "src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py": (
        "2783204b39c31b79588567dce11b947411c7398d02444623180f17c24760a910",
        "80f2bc998febe351e1e8d50462932c4392ccaa5b9f53c3a8e950fab1f9d7763d",
    ),
    "src/ops/okx_eea_private_account_state_runtime_v1/k1_source_v1.py": (
        "7a9c63c21c9c808f87cca4ccbde6eb219428b934e7dd8f39cc0022333c0cae89",
        "d966938308b6b6c8dfab113e3fe171c8e1090ec073efbe3c61cc9d1c19411359",
    ),
    "src/ops/okx_eea_private_account_state_runtime_v1/startup_source_v1.py": (
        "5d97042b35987d8231887c766f2341c03014e58a0e4795bba117e75f1b8c35ec",
        "069298b0194890416ba2390df9c8d773abaffb0f04f0b4a96323dc1a0e2b1227",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py": (
        "25c76eb8ec00b1e5e0d33d116ad7c19ed32be9014fa667e67697569a34dc13fd",
        "4040a0c32f151de2c59b9a52bd044aece2d055f0fc5f01c805dac05112cafc10",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py": (
        "78b413f1dac814623899bd86bf4ec55b4ac782fb27dae8215bb1420c6a122b52",
        "ee234792e4761bc002f4d777887c7894194421006f5f9778d66fa272df69fd87",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/host_v1.py": (
        "02d1773c0a39a9f71a83a71ea82623e1a790092931af49d091bc330243633267",
        "58dab10b38772fff3c2f21170e40a68e814063a8c6fd5346c42dcda73885feec",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/live_l10_close_booking_v1.py": (
        "f7cb389f154118358dea3a279ead47235056c44ff536419de226a5d75714d835",
        "1e5b9f56cbacc1c6314356c9635ab29def8857aee2ffb95d9082bdf510117ef5",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/live_net_reversal_booking_v1.py": (
        "973a0d63554b974f5691a187daca700da66e9aeb35cd72309dc74de410c68d90",
        "a01694bc6e7e9d5672142ea9130260ab2ab51346a167c95b7392077c07b55902",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py": (
        "7b863bab462d1fef9e4e49d9bc49b9227e3f13f0d72e46e28a0844aa5cab81b9",
        "e642694e7c1fab8dc299b724cf1b145b71a7cb76e8e187f34bc0d889a47eee8f",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/test_phase_limits_v1.py": (
        "10e10eb8b1bf2ad862033fc61776e95b57451b7d7b5dacb104f0daaa73373ce5",
        "0ac480b06ac83280dee4418b4c9402fe8858358be24527e46b2a5aad94ad6d53",
    ),
    "src/ops/productive_reconciliation_runtime_binding_v1/startup_gate_v1.py": (
        "b574d572c50d523c7825923c7f196181c29f4343ca1ceb9c2d23f0ee73f0d6af",
        "3d5877bd0b87f491d4695be9b94851581af0ff75d88fabb206509db5378ccd84",
    ),
    "tests/ops/test_btc_demo_entry_reservation_v1.py": (
        "bc4b1293bbdc3ee643f2d8c4e7ce3db0fa8e56fb1065e924fd9a1d05b6d976e0",
        "e003896cfb836e00b68d64fc6af94f8dd6dbf0e3ebe635075a752345b2b4ec12",
    ),
    "tests/ops/test_btc_demo_first_entry_pending_v1.py": (
        None,
        "38c36b93e2bbeb144cd4353afdd568573d85b4212cd5141cf8dc4b6f7484b4f7",
    ),
    "tests/ops/test_btc_testnet_capital_context_v1.py": (
        None,
        "c07d3b28983dd8e4f16d8df8a425c52a5b817a4f5411acbdeac111fba54717ac",
    ),
    "tests/ops/test_btc_testnet_net_reversal_cost_v1.py": (
        None,
        "7fa5a3648d39bd1f6894b28b2ebd41a9ea31780a9ff1232d7b2bfc47e76774f6",
    ),
    "tests/ops/test_btc_testnet_original_budget_host_v1.py": (
        None,
        "a00dc6b154f39889a49e27bfcc9f677352ac7ce757e19c994efa40ab9d0411e8",
    ),
    "tests/ops/test_btc_testnet_original_execution_receipt_v1.py": (
        None,
        "757164ea4251bad9127f85535eb26cea421ddb4043caef5f1e9a0b3a80e24e26",
    ),
    "tests/ops/test_btc_testnet_original_get_environment_v1.py": (
        None,
        "ec264c06e9ce29032922331e2bdbd9ed457577de5c516910b92f2ecdf54ffda5",
    ),
    "tests/ops/test_btc_testnet_original_net_reversal_v1.py": (
        None,
        "df93a7d2477a86cddb0140e1340a085da5e68544db573027866871fe8cfe5f1b",
    ),
    "tests/ops/test_btc_testnet_original_net_submit_v1.py": (
        None,
        "77aba8f7a21152eb6c6c11719c7ec8c2d927e90ef402f104dc8e5a9f32cbf1f1",
    ),
    "tests/ops/test_btc_testnet_original_occupied_core_v1.py": (
        None,
        "945fe1f83272521047b48726fd62854b3cdc01892e50b8eb81e50aaea5698491",
    ),
    "tests/ops/test_current_productive_shared_post_owner_authority_v1.py": (
        "e3aa71b3ece13c559eae30af8f4567b25882c8d987f857f68450b10c409c59a0",
        "abffba5b88e1770b6988e736755917442431b2d9a4eca54b94b9efc34486b0eb",
    ),
    "tests/ops/test_durable_portfolio_budget_recovery_v1.py": (
        "12e0f4d576927d96d761a125ead6b982ee73eb0ade9f941b03df778637167a76",
        "b7636ed30129fef155aa76e6128924c9ed093424795e89bc547a66a682c03803",
    ),
    "tests/ops/test_portfolio_budget_host_v1.py": (
        "dcaba0fafe700831b77443198c62d174ccd55221a1dba4deea1c9653803adc0c",
        "9224ac1c13a983d30e39179a09ce194580817f9711a4f1ff18f9202818acd32c",
    ),
    "tests/ops/test_portfolio_execution_recovery_v1.py": (
        "d9de400892f0b0247b59b131a29cafcb623f86fe0456cda7a8f1d81f27ea4a79",
        "9f71f9b79e83c8a1c33b30dab2c8fe7f5589441d1ff466eca269fc490298dec6",
    ),
    "tests/ops/test_portfolio_sizing_learning_semantic_join_v1.py": (
        "3b4a1194b0b29c59a8e4c15dc3b80c0b9bd0a5c01ac1b0e25a1331f42b5b0517",
        "957281bc9c01a69c419396928584feadb6fc7ef242e3f93ec89aaa291c8a09ab",
    ),
}


# Exact additional source successor for the requested Slot-3 Demo entry dispatch.
# Offline preparation only; no standing credential, order or runtime grant.
TESTNET_ENTRY_SUBMIT_REVIEW_DELTAS = {
    "src/ops/btc_demo_entry_submit_v1.py": (
        None,
        "3857f18ab9974005c2161eefd70de419c5dfee69df0fab59cb91b1fca28a6899",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py": (
        "26f4b6e83369cf364d8b5b83e33ad1ea0fb337fc401584d58dfa8945284cd014",
        "926a67fc072a20f1919de9d22da332236981a420ae2bbd625c0b310b7dde5dd4",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_post_budget_admission_v1.py": (
        "6c97451d8b6e3456af7e108088022e566236a5c8dfd98c70d1c02e6df27341e4",
        "70c8732d0458a4caf085e61ad2a4642579166d6a218c48c0ee01fb856bc81875",
    ),
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py": (
        "c68b956e578251c5861bcdb27d208d422f13b83ee525b3cb4422123927fd8d3c",
        "68a8ae8cd7bb24a9937407ce2a20889b0d9b7ec8df99ef574f180c9414d21956",
    ),
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py": (
        "972571f3bc6d6856c719d218d2a9c2059a2c6dea44bdcc13df8f4d195d37d5f6",
        "23cc26d4b91072dbe11b529c03cbb1ff1b42bee024b9bdc753afb836468f85c1",
    ),
    "tests/ops/test_btc_demo_entry_submit_v1.py": (
        None,
        "660ef17cf27176a716f1d7ffd4604a60b83f10170897ebcd647e2f072ad0975c",
    ),
    "tests/ops/test_btc_demo_first_entry_pending_v1.py": (
        "38c36b93e2bbeb144cd4353afdd568573d85b4212cd5141cf8dc4b6f7484b4f7",
        "1d513804feb575b46ce3d23ead6e48f0c234a238ceb5f719a395c220d516aa5a",
    ),
    "tests/ops/test_btc_testnet_original_execution_receipt_v1.py": (
        "757164ea4251bad9127f85535eb26cea421ddb4043caef5f1e9a0b3a80e24e26",
        "866d5252eee933d865401d3fc3b1606b49fd3a737cf4d54d67a346ba0cf84053",
    ),
    "tests/ops/test_btc_testnet_original_net_reversal_v1.py": (
        "df93a7d2477a86cddb0140e1340a085da5e68544db573027866871fe8cfe5f1b",
        "d13c3db5bc5120344adb2cb31ea1b553b4deabd2c8e7f8d004a73b38080df833",
    ),
    "tests/ops/test_btc_testnet_original_net_submit_v1.py": (
        "77aba8f7a21152eb6c6c11719c7ec8c2d927e90ef402f104dc8e5a9f32cbf1f1",
        "1755ebdc4e08c0a3cc2418bc0af8f4ed3c510c14dca7f51484eff52a7618fdee",
    ),
    "tests/ops/test_btc_testnet_original_occupied_core_v1.py": (
        "945fe1f83272521047b48726fd62854b3cdc01892e50b8eb81e50aaea5698491",
        "54074571d3445f212f2f5a74f4a419ffc5ad6d8e61135c80a21fa85661b2bdc2",
    ),
}


TESTNET_SESSION_CLOSE_REVIEW_DELTAS = {
    "src/ops/btc_demo_budget_owner_v3.py": (
        "3dbf24c4ef153ea24391f1a22f574183809e4d0b7be66df2633c6645fe06148f",
        "adb0479f5a6e10ab5da5f5b20ad5d780e62b92a17ccdfe393727c509f3911375",
    ),
    "src/ops/btc_demo_session_close_reconciliation_v1.py": (
        None,
        "ddd250faed59e74ce9d731f715a296ce2a29c9ef134ca835d48ef710ff7d09ad",
    ),
    "src/ops/btc_demo_session_close_submit_v1.py": (
        None,
        "812cccc1eb848ec40bfd577057fc547d29e8eac7bd4fc82f383283218ff1e8f4",
    ),
    "src/ops/btc_demo_session_close_v1.py": (
        None,
        "b3f15a2cc4870385e6405417fa442573ef7eef3091c7ebed076258fbf3d6ec8f",
    ),
    "src/ops/btc_demo_session_control_v1.py": (
        None,
        "b125b0a64391818a0be2206724d0bd9d94bde49dad782e29eaeaab47217660c8",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_double_play_reversal_v1.py": (
        "bd553c70644d8bece02fe36cb6f82d39c9870c17aff6477d33d3ba58727c546a",
        "43bba39e45dfe8f5ef9744531959c8524ea957488375799cc9c2094bd78db708",
    ),
    "src/ops/full_core_live_path_composition_root_v1/current_productive_shared_post_owner_authority_v1.py": (
        "95d399e03b5f5c6f029b24d05dbb2e9354a2d7fee6898e853a862f85abcbbc27",
        "49e02ef30bc58a8ba4e15d375ef87c59e1f6e8c08b626bfa3abd29940b1aedf5",
    ),
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py": (
        "23cc26d4b91072dbe11b529c03cbb1ff1b42bee024b9bdc753afb836468f85c1",
        "5df84aa61774e52ff8ab88a5898cfb75525dfa5b37a91ecd9edd2bfc0f48e512",
    ),
    "src/ops/portfolio_capital_reservation_budget_v1/position_close_quote_v1.py": (
        None,
        "92a388ca9f4e70702fc55a916c30b12fe4e6dd33af04a909c4a67c6f69e0d773",
    ),
    "tests/ops/test_btc_demo_entry_submit_v1.py": (
        "660ef17cf27176a716f1d7ffd4604a60b83f10170897ebcd647e2f072ad0975c",
        "557409db3b44fc16e42dd3e6ea0d1e7441aacfee09d88be946e08035b19104d0",
    ),
    "tests/ops/test_btc_demo_session_close_v1.py": (
        None,
        "6ad7f2fd172c134abbbbc59b9f9804b0cea701999503bc8946712eea5701e21c",
    ),
    "tests/ops/test_btc_demo_session_control_v1.py": (
        None,
        "f273dc4d860fb78dc3bfae1e14e5ba02af3f76dc1cf995d3de1867604c06bd49",
    ),
}


TESTNET_BOUNDED_HOST_REVIEW_DELTAS = {
    "tests/ops/test_btc_demo_session_close_v1.py": (
        "6ad7f2fd172c134abbbbc59b9f9804b0cea701999503bc8946712eea5701e21c",
        "a6ebeecaad9d1fce6cbeb7bedcb83c1dd621540be13e60ea65fe653271ac9a73",
    ),
    "scripts/ops/run_btc_demo_bounded_host_v1.py": (
        None,
        "a55e3c30a701e184929484567105226c0afe1687f01d92f4dd4a1b66b1a8c362",
    ),
    "src/ops/btc_demo_bounded_host_v1.py": (
        None,
        "df92a4e2d07ba511d5802b7c1f2c5a18e57d967a4f5e74c2933c611058b8f510",
    ),
    "src/ops/btc_demo_bounded_post_owner_v1.py": (
        None,
        "0335b92db8f77d9a4f019c51c82c31d5fcf8e5c2e3c9d5ef1e37eaea7f4e8813",
    ),
    "src/ops/btc_demo_entry_c1_source_v1.py": (
        None,
        "fcf2029753a365370340d373b644b30781b2112e145435fe8cf21e75a781324a",
    ),
    "src/ops/btc_demo_entry_reservation_v1.py": (
        "8b1b535d1a3781e4d696a38b8a7254a70be7ff3e79c811a3b754114296a33818",
        "2dcf4e3d9f89a12bd1ac72f811fdcf18db90eb861100b30ec2806265e415f1ab",
    ),
    "src/ops/btc_demo_net_reversal_pretrade_v1.py": (
        "8d62a270e43ee9850aed5f159f2b915c79945657c7bcfe55ce3f049325f773a1",
        "d924e484ffc8599741aa2f2e3531cecb411d53ae08e7d8c3bc3e2bb94c2c1e49",
    ),
    "src/ops/btc_demo_offline_trading_host_v1.py": (
        "7f6bf2593eb388ebce4f7ef3e4e1b35e266fc815acf2227f69e7424edee36929",
        "c298d7a338b61615a3af47552d0733391499dd6ff986dbaf38c435149b092450",
    ),
    "src/ops/btc_demo_runtime_no_entry_v1.py": (
        None,
        "c9530b9e4ee446260cb9e87ea3cfd21a0cd2be664ea610b45876a9d8fdb18501",
    ),
    "src/ops/btc_demo_runtime_v1.py": (
        None,
        "84060c04c50d875914c698d76e1ff2b42e579c1348a9c017307910f63b6ce207",
    ),
    "src/ops/btc_demo_session_control_v1.py": (
        "b125b0a64391818a0be2206724d0bd9d94bde49dad782e29eaeaab47217660c8",
        "53398c8707509d6a0739507e7d1ba666588e5610c90872513d5927cc40bf9dd0",
    ),
    "tests/ops/test_btc_demo_bounded_host_cli_v1.py": (
        None,
        "2bea9e8c84e3dda43db67e8847d5e47ff0d6797f45cb459fc01172c17b071e93",
    ),
    "tests/ops/test_btc_demo_bounded_host_v1.py": (
        None,
        "bac79fa2edf2da95c15950e747228e495b083d49ebce97ae56edad0dd32a58ad",
    ),
}


def _reviewed_testnet_successor(root, parent):
    expected = _exact_double_play_successor(parent, TESTNET_PREPARATION_REVIEW_DELTAS)
    if (root / "src/ops/btc_demo_entry_submit_v1.py").is_file():
        expected = _exact_double_play_successor(expected, TESTNET_ENTRY_SUBMIT_REVIEW_DELTAS)
    if (root / "src/ops/btc_demo_session_close_v1.py").is_file():
        expected = _exact_double_play_successor(expected, TESTNET_SESSION_CLOSE_REVIEW_DELTAS)
    if (root / "src/ops/btc_demo_bounded_host_v1.py").is_file():
        expected = _exact_double_play_successor(expected, TESTNET_BOUNDED_HOST_REVIEW_DELTAS)
    return expected


def _is_testnet_preparation_candidate(root):
    return any(
        (root / path).is_file() and hashlib.sha256((root / path).read_bytes()).hexdigest() == after
        for path, (_, after) in TESTNET_PREPARATION_REVIEW_DELTAS.items()
    )


def _uses_double_play_policy_bundle(root: Path) -> bool:
    expected = {path: after for path, (_, after) in DOUBLE_PLAY_POLICY_DELTAS.items()}
    direct = (root / DIRECT_REVERSAL_SOURCE).is_file()
    booked = (root / NET_REVERSAL_GET_RECONCILIATION_SOURCE).is_file()
    if direct:
        expected[DIRECT_REVERSAL_SOURCE] = None
        for path, (_, after) in ORDERED_FUNDING_EPISODE_DELTAS.items():
            expected.setdefault(path, after)
        expected = _exact_double_play_successor(expected, DIRECT_REVERSAL_POLICY_DELTAS)
        if any(
            hashlib.sha256((root / path).read_bytes()).hexdigest() == after
            for path, (_, after) in ROTATION_SLOT_CAPITAL_DELTAS.items()
            if (root / path).is_file()
        ):
            for path, (before, _) in ROTATION_SLOT_CAPITAL_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(expected, ROTATION_SLOT_CAPITAL_DELTAS)
        if booked or any(
            hashlib.sha256((root / path).read_bytes()).hexdigest() == after
            for path, (_, after) in AUTHENTICATED_NET_REVERSAL_DELTAS.items()
            if (root / path).is_file()
        ):
            for path, (before, _) in AUTHENTICATED_NET_REVERSAL_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(expected, AUTHENTICATED_NET_REVERSAL_DELTAS)
        if booked or any(
            hashlib.sha256((root / path).read_bytes()).hexdigest() == after
            for path, (_, after) in AUTHENTICATED_NET_REVERSAL_SEND_DELTAS.items()
        ):
            expected = _exact_double_play_successor(
                expected, AUTHENTICATED_NET_REVERSAL_SEND_DELTAS
            )
        if booked:
            for path, (before, _) in AUTHENTICATED_NET_REVERSAL_BOOKING_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(
                expected, AUTHENTICATED_NET_REVERSAL_BOOKING_DELTAS
            )
            expected = _live_initial_slot_budget_successor(root, expected)
            expected = _occupied_n1_runtime_successor(root, expected)
    # Exact successor reviewed for TESTNET preparation only; no runtime authority.
    if _is_testnet_preparation_candidate(root):
        for path, (before, _) in TESTNET_PREPARATION_REVIEW_DELTAS.items():
            expected.setdefault(path, before)
        expected = _exact_double_play_successor(expected, TESTNET_PREPARATION_REVIEW_DELTAS)
        if (root / "src/ops/btc_demo_entry_submit_v1.py").is_file():
            for path, (before, _) in TESTNET_ENTRY_SUBMIT_REVIEW_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(expected, TESTNET_ENTRY_SUBMIT_REVIEW_DELTAS)
        if (root / "src/ops/btc_demo_session_close_v1.py").is_file():
            for path, (before, _) in TESTNET_SESSION_CLOSE_REVIEW_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(expected, TESTNET_SESSION_CLOSE_REVIEW_DELTAS)
        if (root / "src/ops/btc_demo_bounded_host_v1.py").is_file():
            for path, (before, _) in TESTNET_BOUNDED_HOST_REVIEW_DELTAS.items():
                expected.setdefault(path, before)
            expected = _exact_double_play_successor(expected, TESTNET_BOUNDED_HOST_REVIEW_DELTAS)
    actual = {}
    for path in expected:
        source = root / path
        actual[path] = hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
    if not direct and not any(actual[path] == after for path, after in expected.items()):
        return False
    for path, after in expected.items():
        if actual[path] != after:
            raise ValueError("DOUBLE_PLAY_POLICY_REVIEWED_BUNDLE_REQUIRED:" + path)
    return True


def _exact_double_play_successor(parent, deltas):
    successor = dict(parent)
    for path in parent.keys() & deltas.keys():
        before, after = deltas[path]
        if parent[path] != before:
            raise ValueError("DOUBLE_PLAY_POLICY_PARENT_INVALID:" + path)
        successor[path] = after
    return successor


def _live_initial_slot_budget_successor(root, parent):
    if _is_testnet_preparation_candidate(root) or any(
        hashlib.sha256((root / path).read_bytes()).hexdigest() == after
        for path, (_, after) in LIVE_INITIAL_SLOT_BUDGET_DELTAS.items()
        if path in parent
    ):
        return _exact_double_play_successor(parent, LIVE_INITIAL_SLOT_BUDGET_DELTAS)
    return parent


def _occupied_n1_runtime_successor(root, parent):
    if _is_testnet_preparation_candidate(root) or any(
        hashlib.sha256((root / path).read_bytes()).hexdigest() == after
        for path, (_, after) in OCCUPIED_N1_RUNTIME_DELTAS.items()
        if path in parent
    ):
        return _exact_double_play_successor(parent, OCCUPIED_N1_RUNTIME_DELTAS)
    return parent


def _double_play_bundle_successor(root, parent):
    booked = (root / NET_REVERSAL_GET_RECONCILIATION_SOURCE).is_file()
    expected = _exact_double_play_successor(parent, DOUBLE_PLAY_POLICY_DELTAS)
    if (root / DIRECT_REVERSAL_SOURCE).is_file():
        expected = _exact_double_play_successor(expected, DIRECT_REVERSAL_POLICY_DELTAS)
        if booked or any(
            hashlib.sha256((root / path).read_bytes()).hexdigest() == after
            for path, (_, after) in AUTHENTICATED_NET_REVERSAL_DELTAS.items()
            if path in expected
        ):
            expected = _exact_double_play_successor(expected, AUTHENTICATED_NET_REVERSAL_DELTAS)
        if booked or any(
            hashlib.sha256((root / path).read_bytes()).hexdigest() == after
            for path, (_, after) in AUTHENTICATED_NET_REVERSAL_SEND_DELTAS.items()
            if path in expected
        ):
            expected = _exact_double_play_successor(
                expected, AUTHENTICATED_NET_REVERSAL_SEND_DELTAS
            )
        if booked:
            expected = _exact_double_play_successor(
                expected, AUTHENTICATED_NET_REVERSAL_BOOKING_DELTAS
            )
            expected = _live_initial_slot_budget_successor(root, expected)
            expected = _occupied_n1_runtime_successor(root, expected)
    return expected


def validate_reserved_slot_rotation_bundle(
    root: Path, policies: list[dict] | None = None, *, double_play: bool = False
) -> None:
    frozen = {} if policies is None else {row["path"]: row["frozen_sha256"] for row in policies}
    actual = {}
    for path, (before, _after) in RESERVED_SLOT_ROTATION_DELTAS.items():
        if path in frozen and frozen[path] != before:
            raise ValueError("RESERVED_SLOT_ROTATION_BASELINE_INVALID:" + path)
        candidate = root / path
        actual[path] = (
            hashlib.sha256(candidate.read_bytes()).hexdigest() if candidate.is_file() else None
        )
    before = {path: pair[0] for path, pair in RESERVED_SLOT_ROTATION_DELTAS.items()}
    after = {path: pair[1] for path, pair in RESERVED_SLOT_ROTATION_DELTAS.items()}
    protected_after = dict(after)
    for path, (parent, successor) in OPEN_TEST_SLOT_LOSS_PROTECTION_DELTAS.items():
        if path not in after or after[path] != parent:
            raise ValueError("OPEN_TEST_SLOT_LOSS_PROTECTION_PARENT_INVALID:" + path)
        protected_after[path] = successor
    scope_bound_after = dict(protected_after)
    for path, (parent, successor) in CURRENT_SCOPE_MARK_ADMISSION_DELTAS.items():
        if path not in protected_after or protected_after[path] != parent:
            raise ValueError("CURRENT_SCOPE_MARK_ADMISSION_PARENT_INVALID:" + path)
        scope_bound_after[path] = successor
    if double_play:
        expected = _double_play_bundle_successor(root, scope_bound_after)
        if any(
            actual[path] == digest
            for path, (_, digest) in CAP23_SELECTION_VALIDITY_ROTATION_DELTAS.items()
        ):
            expected = _exact_double_play_successor(
                expected, CAP23_SELECTION_VALIDITY_ROTATION_DELTAS
            )
        if any(
            actual[path] == digest for path, (_, digest) in N5_ORIGINAL_MARKET_INPUT_DELTAS.items()
        ):
            expected = _exact_double_play_successor(expected, N5_ORIGINAL_MARKET_INPUT_DELTAS)
        accepted = (expected,)
        parent_bytes = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(parent_bytes).hexdigest() == SOPH_SHADOW_SLOT2_ROTATION_PARENT_SHA256:
            soph = _exact_double_play_successor(expected, SOPH_SHADOW_SLOT2_PUBLICATION_DELTAS)
            accepted += (soph,)
            persistence = root / FIXED_RANK_PERSISTENCE
            if persistence.is_file():
                digest = hashlib.sha256(persistence.read_bytes()).hexdigest()
                fixed = _exact_double_play_successor(soph, FIXED_RANK_PUBLICATION_DELTAS)
                if digest == FIXED_RANK_PERSISTENCE_SHA256:
                    accepted += (fixed,)
                elif digest == SHADOW_SLOT4_PERSISTENCE_SHA256:
                    accepted += (
                        _exact_double_play_successor(fixed, SHADOW_SLOT4_PUBLICATION_DELTAS),
                    )
    else:
        accepted = (before, after, protected_after, scope_bound_after)
    if double_play and _is_testnet_preparation_candidate(root):
        accepted = tuple(
            _reviewed_testnet_successor(root, parent)
            for parent in accepted
            if all(
                parent[path] == TESTNET_PREPARATION_REVIEW_DELTAS[path][0]
                for path in parent.keys() & TESTNET_PREPARATION_REVIEW_DELTAS.keys()
            )
        )
    if actual not in accepted:
        raise ValueError("RESERVED_SLOT_ROTATION_REVIEWED_BUNDLE_REQUIRED")


def validate_ordered_funding_episode_bundle(
    root: Path, policies: list[dict], *, double_play: bool = False
) -> None:
    """Accept the original bundle or the separately reviewed exact successor."""
    frozen = {row["path"]: row["frozen_sha256"] for row in policies}
    actual = {}
    for path, (before, _after) in ORDERED_FUNDING_EPISODE_DELTAS.items():
        if frozen.get(path) != before:
            raise ValueError("ORDERED_FUNDING_EPISODE_BASELINE_INVALID:" + path)
        actual[path] = hashlib.sha256((root / path).read_bytes()).hexdigest()
    if not double_play and all(
        actual[path] == before for path, (before, _) in ORDERED_FUNDING_EPISODE_DELTAS.items()
    ):
        return
    expected = {path: after for path, (_, after) in ORDERED_FUNDING_EPISODE_DELTAS.items()}
    if double_play:
        expected = _double_play_bundle_successor(root, expected)
        if _is_testnet_preparation_candidate(root):
            expected = _reviewed_testnet_successor(root, expected)
    for path, digest in expected.items():
        if actual[path] != digest:
            raise ValueError("ORDERED_FUNDING_EPISODE_REVIEWED_BUNDLE_REQUIRED:" + path)


def validate_numeric_technical_admission_delta(original: bytes, current: bytes) -> None:
    """Admit only the owner-requested six-file extension of the frozen contract.

    Hash rebinding alone cannot change a prior grant, an invariant, an effect,
    or add a seventh file. The original frozen inventory stays authoritative
    for the baseline; this is a separately bound development delta.
    """
    before, after = json.loads(original), json.loads(current)
    mutable = {"allowed_paths", "authorized_surface_notes"}
    if (
        set(before) != set(after)
        or any(after[k] != v for k, v in before.items() if k not in mutable)
        or any(p in before["allowed_paths"] for p in NUMERIC_ADMISSION_PATHS)
        or after["allowed_paths"] != before["allowed_paths"] + list(NUMERIC_ADMISSION_PATHS)
        or not isinstance(after["authorized_surface_notes"], list)
        or len(after["authorized_surface_notes"]) != len(before["authorized_surface_notes"]) + 1
        or after["authorized_surface_notes"][:-1] != before["authorized_surface_notes"]
        or type(after["authorized_surface_notes"][-1]) is not str
        or not after["authorized_surface_notes"][-1].startswith(NUMERIC_ADMISSION_ID + ": ")
    ):
        raise ValueError("POLICY_TECHNICAL_ADMISSION_DELTA_INVALID")


def policy_scope_kind(path: str) -> str | None:
    if path.startswith("config/governance/current_law_impact_map_v1/") or path in {
        "config/ops/docs_truth_map.yaml",
        "config/ops/repo_truth_claims.yaml",
        "config/governance/current_system_census_graph_v1/README.md",
    }:
        return None
    if path.startswith(".cursor/rules/"):
        return "DEVELOPMENT_GUIDANCE"
    if path.startswith("policy_packs/"):
        return "DEVELOPMENT_CHECK_POLICY"
    if path.startswith(("config/", "src/")) and (
        re.search(
            r"policy|policies|governance|(?:^|[_/])law(?:[_/.]|$)|(?:^|[_/])rule(?:[_/.]|$)",
            path,
            re.I,
        )
        or path.startswith(("src/risk/", "src/risk_layer/"))
    ):
        if path.startswith(
            (
                "config/governance/current_system_census_graph_v1/",
                "config/governance/current_system_interaction_authority_map_v1/",
            )
        ):
            return "DOCUMENTARY_INDEX_DATA"
        return "MACHINE_CONFIGURATION" if path.startswith("config/") else "SOURCE_INTERFACE"
    return None


def load_policies(root: Path, doc: dict) -> list[dict]:
    meta = doc["policy_inventory"]
    if (
        set(meta) != {"path", "sha256", "count", "schema"}
        or meta["path"] != "docs/system_atlas/source/current-policies.jsonl.gz"
        or meta["schema"] != "peaktrade.frozen_policy_inventory.v1"
        or type(meta["count"]) is not int
        or not isinstance(meta["sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", meta["sha256"]) is None
    ):
        raise ValueError("POLICY_INVENTORY_CONTRACT_INVALID")
    raw = (root / meta["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != meta["sha256"]:
        raise ValueError("POLICY_INVENTORY_DIGEST_MISMATCH")
    rows = [json.loads(x) for x in gzip.decompress(raw).splitlines()]
    if len(rows) != meta["count"] or len({x["path"] for x in rows}) != len(rows):
        raise ValueError("POLICY_INVENTORY_COUNT_MISMATCH")
    return rows


def link(path: str, label: str | None = None) -> str:
    return f"[{label or path}](../../../../{path})"


def render_law_views(doc: dict, root: Path = ROOT) -> dict[str, str]:
    policies = load_policies(root, doc)
    header = (
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. FROZEN_LAW_POLICY_VIEW AUTHORITY=NONE -->\n\n"
        "```text\nLAW_IMPACT_MAP_AUTHORITY=NONE\nLAW_REFERENCE_IS_NORMATIVE=false\n"
        f"SOURCE_TAG={doc['source_tag']}\nSOURCE_COMMIT={doc['baseline_sha']}\n"
        "RUNTIME_AUTHORIZATION_EFFECT=NONE\n```\n\n"
    )
    intro = (
        "Diese abgeleitete Sicht zeigt Regelquellen, statische Referenzen und Prüfbedarf. "
        "Die Definition und Durchsetzung einer Regel gehören zu ihrem Originalowner. "
        "Ein Pfad, Import oder Stringliteral belegt keine ausgeführte Consumerkette.\n\n"
        "Einstiege: "
        + link("docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md", "Master Runbook")
        + " · "
        + link("docs/system_atlas/generated/SYSTEM_ATLAS.md", "System Atlas")
        + ".\n\n"
    )
    law = ["# Regelquellen\n\n", header, intro]
    for item in sorted(doc["law_references"], key=lambda x: x["law_id"]):
        law += [
            f"## {item['law_id']}\n\n",
            link(item["canonical_source"]) + "\n\n",
            f"Quellanker: `{item['canonical_anchor']}`. SHA256: `{item['source_sha256']}`. "
            f"Index: `{item['index_status']}`.\n\n",
        ]
    objects = ["# Zuordnung zu Fachverträgen\n\n", header, intro]
    objects.append(
        "Die Einträge bezeichnen zu prüfende Fachverträge. Ihre Funktion wird durch "
        "diese Dokumenterzeugung nicht erneut ausgeführt oder als betriebsbereit bestätigt.\n\n"
    )
    for obj in sorted(doc["semantic_objects"], key=lambda x: x["id"]):
        objects += [
            f"## {obj['id']}\n\n",
            f"Rolle: `{obj['semantic_class']}`. Prüfumfang: `{obj['current_status']}`.\n\n",
        ]
        for path in obj.get("code_surfaces", []) + obj.get("config_surfaces", []):
            objects.append("- " + link(path) + "\n")
        objects.append(
            "\nRegelreferenzen: " + ", ".join(f"`{x}`" for x in obj["law_ref_ids"]) + ".\n\n"
        )
    unknown = ["# Offene Beziehungen und Unterschiede\n\n", header, intro]
    unknown.append("## UNKNOWN_RELATION — offene Zuordnungen\n\n")
    for item in doc["unknown_relations"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['unknown_class']}`. {item['statement']}\n\n"]
    for item in doc["semantic_divergence_index"]:
        unknown += [f"## {item['id']}\n\n", f"`{item['adjudication']}`. {item['statement']}\n\n"]
        for path in item.get("evidence_refs", []):
            if (root / path).is_file():
                unknown.append("- " + link(path) + "\n")
        unknown.append("\n")
    census = ["# Policy- und Regeldateien des Freeze\n\n", header, intro]
    census += [
        f"**{len(policies)} Dateien** im ausgewiesenen Suchumfang. "
        "Die vollständigen Referenzstellen und Quelldigests stehen im "
        "[maschinenlesbaren Katalog](../../../system_atlas/source/current-policies.jsonl.gz).\n\n",
        "Suchumfang: versionierte Quell-/Konfigurationspfade mit policy/policies/governance/law/rule, "
        "Risk-Verzeichnisse, Policy Packs und Entwicklungsregeln. Die Quellen der "
        "Dokumentprojektion und die beiden Dokumentgate-Selektoren werden gesondert geprüft. "
        "Der Katalog weist damit diesen Dateiumfang vollständig aus; die semantische "
        "Wirksamkeit jeder Regel bleibt eine Prüfung ihres konkreten Consumers.\n\n",
        "`SOURCE` bezeichnet eine Referenz aus einer Quelldatei, `TOOL` eine aus Werkzeugcode "
        "und `TEST` eine aus Tests. Ein eindeutiger Dateinamenliteral bleibt eine statische "
        "Fundstelle. Keine entdeckte Referenz ist kein Beweis für Nichtverwendung.\n\n",
    ]
    for kind in sorted({p["kind"] for p in policies}):
        census.append(f"## {kind}\n\n")
        for p in policies:
            if p["kind"] != kind:
                continue
            census += [
                "- "
                + link(p["path"])
                + f" · `{p['parse_status']}` · SHA256 `{p['frozen_sha256']}`\n",
                f"  Referenzstellen: SOURCE {p['source_reference_count']}, "
                f"TOOL {p['tool_reference_count']}, TEST {p['test_reference_count']}. "
                f"`{p['reference_status']}`.\n",
            ]
            refs = [r for r in p["static_references"] if r["scope"] == "SOURCE"][:3]
            for ref in refs:
                census.append(
                    "  "
                    + link(ref["path"], ref["path"] + ":" + str(ref["line"]))
                    + f" · `{ref['kind']}`.\n"
                )
        census.append("\n")
    census.append("## Weiterer semantischer Prüfbedarf\n\n")
    for row in doc.get("unclassified_current_surfaces", []):
        census.append("- UNCLASSIFIED: " + link(row["path"]) + "\n")
    for row in doc.get("semantic_divergence_index", []):
        census.append(f"- `{row['id']}`: `{row['adjudication']}`; siehe offene Beziehungen.\n")
    no_refs = sum(not p["static_references"] for p in policies)
    impact = ["# Law Impact Map — Regeln und Änderungsfolgen\n\n", header, intro]
    impact += [
        f"## Bestand\n\n{len(doc['law_references'])} explizite Regelreferenzen, "
        f"{len(doc['semantic_objects'])} Fachverträge und {len(policies)} indexierte Policy-/Regeldateien. "
        f"{no_refs} dieser Dateien haben im erfassten Pythonbestand keine entdeckte statische Referenz.\n\n",
        "- [Regelquellen](law_reference_index_v1.md): Originalowner, Anker und aktueller Digest.\n",
        "- [Fachverträge](semantic_object_index_v1.md): Code-/Configzuordnung ohne neue Freigabe.\n",
        "- [Vollständiger Dateiumfang](surface_census_v1.md): typisierte Policydateien und Referenzstellen.\n",
        "- [Offene Beziehungen](unknown_and_conflict_v1.md): konkrete Unterschiede und Prüfbedarf.\n\n",
        "## Prüfung einer Änderung\n\n",
        "1. Geänderte Originalregel mit dem gebundenen Quellstand vergleichen.\n",
        "2. Direkte Regelreferenzen, statische Import-/Pfadfundstellen und zugeordnete Fachverträge ermitteln.\n",
        "3. Zahlen-, Einheiten-, Zeit-, Identitäts- und Zustandsvertrag am tatsächlichen Consumer prüfen.\n",
        "4. Betroffene Prüfungen mit Originalinputs ausführen; unklassifizierte Folgen als offen belassen.\n",
        "5. Quellenbindung und diese abgeleiteten Ansichten gemeinsam nachführen.\n\n",
        "## Aussagegrenze\n\n",
        "Die jetzige Dokumentprüfung kontrolliert Dateibestand, Syntax strukturierter Quellen, "
        "Digests, Quellanker, Referenzziele und deterministische Ausgabe. Sie erteilt kein "
        "Gesamturteil über die fachliche Richtigkeit sämtlicher Policies und bestätigt keinen "
        "durchgängigen Betrieb. Numerischer Wertverbrauch, Risikoentscheidung, Permit, "
        "Venuewirkung und produktives Apply brauchen jeweils ihre eigenen Nachweise.\n",
    ]
    impact.append("\n## Erhaltene maschinell genutzte Dokumente\n\n")
    impact.append(
        "Diese Dateien sind Originaleingaben oder Schreibziele bestehender Module. Ihre Erhaltung macht sie zu keiner zusätzlichen aktuellen Systemlandkarte. Die jeweiligen Verwendungen sind statische Codebefunde.\n\n"
    )
    for item in doc.get("consumed_documents", []):
        impact.append("- " + link(item["path"]) + f" · `{item['role']}`.\n")
        for ref in [x for x in item["static_references"] if x["scope"] == "SOURCE"]:
            impact.append("  " + link(ref["path"], ref["path"] + ":" + str(ref["line"])) + ".\n")
    return {
        "law_reference_index": "".join(law).rstrip() + "\n",
        "semantic_object_index": "".join(objects).rstrip() + "\n",
        "unknown_and_conflict": "".join(unknown).rstrip() + "\n",
        "surface_census": "".join(census).rstrip() + "\n",
        "law_change_impact": "".join(impact).rstrip() + "\n",
    }


def policy_impact_for_paths(doc: dict, paths: list[str], root: Path = ROOT) -> dict:
    changed = set(paths)
    direct, source_refs, test_refs, tool_refs = set(), set(), set(), set()
    for policy in load_policies(root, doc):
        refs = policy["static_references"]
        if policy["path"] in changed or any(r["path"] in changed for r in refs):
            direct.add(policy["path"])
            for ref in refs:
                target = (
                    source_refs
                    if ref["scope"] == "SOURCE"
                    else test_refs
                    if ref["scope"] == "TEST"
                    else tool_refs
                )
                target.add(ref["path"])
    return {
        "policies": sorted(direct),
        "source_references": sorted(source_refs),
        "test_references": sorted(test_refs),
        "tool_references": sorted(tool_refs),
        "runtime_effect_inferred": False,
    }


def validate_p5_artifact_admission_bundle(root: Path, policies: list[dict]) -> None:
    frozen = {row["path"]: row["frozen_sha256"] for row in policies}
    expected = {path: before for path, (before, _) in P5_ARTIFACT_ADMISSION_DELTAS.items()}
    if any(frozen.get(path) != before for path, before in expected.items()):
        raise ValueError("P5_ARTIFACT_ADMISSION_BASELINE_INVALID")
    actual = {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest()
        if (root / path).is_file()
        else None
        for path in expected
    }
    reviewed = {path: after for path, (_, after) in P5_ARTIFACT_ADMISSION_DELTAS.items()}
    if actual not in (expected, reviewed):
        raise ValueError("P5_ARTIFACT_ADMISSION_REVIEWED_BUNDLE_REQUIRED")


def validate_policy_inventory(root: Path, doc: dict) -> dict:
    model = json.loads((root / "docs/system_atlas/source/current-model.json").read_bytes())
    if doc["baseline_sha"] != model["source_commit"] or doc["source_tag"] != model["source_tag"]:
        raise ValueError("LAW_POLICY_SOURCE_BINDING_MISMATCH")
    resolved = subprocess.check_output(
        ["git", "rev-parse", doc["source_tag"] + "^{commit}"], cwd=root, text=True
    ).strip()
    if resolved != doc["baseline_sha"]:
        raise ValueError("LAW_POLICY_TAG_MISMATCH")
    inventory = [
        json.loads(x)
        for x in gzip.decompress(
            (root / "docs/system_atlas/source/current-files.jsonl.gz").read_bytes()
        ).splitlines()
    ]
    frozen = {p["path"]: p for p in inventory}
    policies = load_policies(root, doc)
    validate_p5_artifact_admission_bundle(root, policies)
    double_play = _uses_double_play_policy_bundle(root)
    validate_ordered_funding_episode_bundle(root, policies, double_play=double_play)
    validate_reserved_slot_rotation_bundle(root, policies, double_play=double_play)
    validate_managed_filegate_owner_bundle(root, policies)
    opt_handoff = OPT_GOVERNANCE_HANDOFF_RETIREMENT_DELTAS
    actual_opt_handoff = {
        path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in opt_handoff
    }
    if actual_opt_handoff not in (
        {path: before for path, (before, _) in opt_handoff.items()},
        {path: after for path, (_, after) in opt_handoff.items()},
    ):
        raise ValueError("OPT_GOVERNANCE_HANDOFF_BUNDLE_DRIFT")
    if {p["path"] for p in policies} != {p for p in frozen if policy_scope_kind(p)}:
        raise ValueError("POLICY_SCOPE_COVERAGE_MISMATCH")
    tree = {}
    for entry in subprocess.check_output(["git", "ls-tree", "-r", "-z", resolved], cwd=root).split(
        b"\0"
    ):
        if entry:
            meta, path = entry.split(b"\t", 1)
            tree[path.decode()] = meta.decode().split()[2]
    development_policy_files = []
    for policy in policies:
        path = policy["path"]
        raw = (root / path).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        original = raw
        if actual != policy["frozen_sha256"]:
            if (
                path
                not in {
                    "config/governance/clean_core_seal_manifest_v1.json",
                    "src/ops/single_selected_future_policy_v1/selection_v1.py",
                    TECHNICAL_ADMISSION,
                }
                and path not in ORDERED_FUNDING_EPISODE_DELTAS
                and path not in RESERVED_SLOT_ROTATION_DELTAS
                and path not in MANAGED_FILEGATE_OWNER_DELTAS
                and path not in opt_handoff
                and G2_ARCHIVE_PROJECTION_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and EXECUTION_AUTHORITY_AUDIT_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and OWNER_ADJUDICATION_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and ROTATION_SLOT_CAPITAL_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and CAP23_SELECTION_VALIDITY_POLICY_DELTAS.get(path)
                != (policy["frozen_sha256"], actual)
                and D01_D02_ADJUDICATION_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and DECISION_ATTRIBUTION_LEARNING_DELTAS.get(path)
                != (policy["frozen_sha256"], actual)
                and P5_ARTIFACT_ADMISSION_DELTAS.get(path) != (policy["frozen_sha256"], actual)
                and P5_BINDING_CONTEXT_ADMISSION_DELTAS.get(path)
                != (policy["frozen_sha256"], actual)
            ):
                raise ValueError("POLICY_SOURCE_DRIFT:" + path)
            binding = json.loads(
                (root / "docs/system_atlas/source/development-binding-v1.json").read_bytes()
            )
            rows = [row for row in binding["files"] if row["path"] == path]
            if (
                binding.get("schema") != "peaktrade.atlas_development_binding.v1"
                or binding.get("authority") != "NONE"
                or binding.get("runtime_authorization_effect") != "NONE"
                or binding.get("frozen_source_commit") != resolved
                or len(rows) != 1
                or rows[0]["before_sha256"] != policy["frozen_sha256"]
                or rows[0]["sha256"] != actual
            ):
                raise ValueError("POLICY_DEVELOPMENT_BINDING_INVALID:" + path)
            original = subprocess.check_output(["git", "show", resolved + ":" + path], cwd=root)
            if path == TECHNICAL_ADMISSION:
                validate_numeric_technical_admission_delta(original, raw)
            development_policy_files.append(path)
        original_digest = hashlib.sha256(original).hexdigest()
        if original_digest != policy["frozen_sha256"] or original_digest != frozen[path]["sha256"]:
            raise ValueError("POLICY_SOURCE_DRIFT:" + path)
        git_digest = hashlib.sha1(
            b"blob " + str(len(original)).encode() + b"\0" + original
        ).hexdigest()
        if git_digest != policy["git_blob_oid"] or git_digest != tree[path]:
            raise ValueError("POLICY_GIT_OBJECT_MISMATCH:" + path)
        if policy["kind"] != policy_scope_kind(path):
            raise ValueError("POLICY_KIND_MISMATCH:" + path)
        for ref in policy["static_references"]:
            if ref["path"] not in frozen or not (root / ref["path"]).is_file() or ref["line"] < 1:
                raise ValueError("POLICY_REFERENCE_MISSING:" + ref["path"])
    for item in doc.get("consumed_documents", []):
        raw = (root / item["path"]).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != item["sha256"] or actual != frozen[item["path"]]["sha256"]:
            raise ValueError("CONSUMED_DOCUMENT_DRIFT:" + item["path"])
        git_digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if git_digest != tree[item["path"]]:
            raise ValueError("CONSUMED_DOCUMENT_GIT_MISMATCH:" + item["path"])
    return {
        "policy_files": len(policies),
        "static_reference_sites": sum(len(p["static_references"]) for p in policies),
        "no_static_reference_discovered": sum(not p["static_references"] for p in policies),
        "by_kind": dict(Counter(p["kind"] for p in policies)),
        "runtime_effect_inferred": False,
        "retained_consumed_documents": len(doc.get("consumed_documents", [])),
        "development_policy_files": development_policy_files,
    }
