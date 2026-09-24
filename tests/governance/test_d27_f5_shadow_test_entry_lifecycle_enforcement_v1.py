"""D27 F5 shadow test-entry lifecycle enforcement tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1 import (
    F5ShadowBaselineBindingScopeV1,
    prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1,
)
from src.governance.d27_f5_shadow_test_entry_authority_subfamily_adjudication_v1 import (
    prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1,
)
from src.governance.d27_f5_shadow_test_entry_lifecycle_enforcement_v1 import (
    DECISION_CONFIG,
    D27F5ShadowTestEntryLifecycleError,
    F5_FRESH_TEST_ENTRY_GATE,
    enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1,
    enforce_d27_f5_shadow_test_entry_lifecycle_admission_v1,
    prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.campaign_runner_v1 import (
    run_shadow_campaign_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    CALIBRATION_PROTOCOL_REL,
    PRODUCTIVE_NUMERIC_VALUES_SET,
    STAGE1_MANIFEST_REL,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.evidence_emitter_v1 import (
    ShadowCampaignEmitError,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.reproducibility_v1 import (
    sha256_file,
)
from tests.ops.test_productive_pure_stack_numeric_policy_shadow_campaign_v1 import (
    _hermetic_repo,
    _request,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_decision_closure_and_regression_6768_6769() -> None:
    assert prove_d27_f5_shadow_test_entry_lifecycle_enforcement_v1(repo_root=REPO_ROOT)
    assert prove_d27_f5_shadow_test_entry_subfamily_adjudication_v1(repo_root=REPO_ROOT)
    assert prove_d26_f5_shadow_d26_baseline_binding_owner_policy_adjudication_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["f5_shadow_lifecycle_enforcement_implemented"] is True
    assert decision["d26_native_baseline_required_on_f5"] is False
    assert decision["productive_numeric_values_set_current"] == 0
    assert decision["new_authority_created"] is False


def test_authorized_digest_conjunction_admits() -> None:
    stage1 = sha256_file(REPO_ROOT / STAGE1_MANIFEST_REL)
    protocol = sha256_file(REPO_ROOT / CALIBRATION_PROTOCOL_REL)
    admission = enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1(
        repo_root=REPO_ROOT,
        declared_stage1_manifest_digest=stage1,
        declared_calibration_protocol_digest=protocol,
    )
    assert admission.test_entry_gate == F5_FRESH_TEST_ENTRY_GATE
    assert (
        admission.d26_native_baseline_scope
        == F5ShadowBaselineBindingScopeV1.OUT_OF_SCOPE_FOR_D26_NATIVE_SCHEMA.value
    )
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0


@pytest.mark.parametrize(
    ("stage1", "protocol", "match"),
    [
        ("", "a" * 64, "STAGE1_MANIFEST_DIGEST_INVALID"),
        ("a" * 64, "", "CALIBRATION_PROTOCOL_DIGEST_INVALID"),
        ("0" * 64, None, "STAGE1_MANIFEST_DIGEST_MISMATCH"),
        (None, "0" * 64, "CALIBRATION_PROTOCOL_DIGEST_MISMATCH"),
    ],
)
def test_digest_denials_fail_closed(stage1: str | None, protocol: str | None, match: str) -> None:
    good_stage1 = sha256_file(REPO_ROOT / STAGE1_MANIFEST_REL)
    good_protocol = sha256_file(REPO_ROOT / CALIBRATION_PROTOCOL_REL)
    declared_stage1 = stage1 if stage1 is not None else good_stage1
    declared_protocol = protocol if protocol is not None else good_protocol
    with pytest.raises(D27F5ShadowTestEntryLifecycleError, match=match):
        enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1(
            repo_root=REPO_ROOT,
            declared_stage1_manifest_digest=declared_stage1,
            declared_calibration_protocol_digest=declared_protocol,
        )


def test_gate_mismatch_denied() -> None:
    stage1 = sha256_file(REPO_ROOT / STAGE1_MANIFEST_REL)
    protocol = sha256_file(REPO_ROOT / CALIBRATION_PROTOCOL_REL)
    with pytest.raises(D27F5ShadowTestEntryLifecycleError, match="TEST_ENTRY_GATE_MISMATCH"):
        enforce_d27_f5_shadow_test_entry_lifecycle_admission_v1(
            family_gate_id="F5-FRESH",
            declared_test_entry_gate="WRONG_GATE",
            repo_root=REPO_ROOT,
            declared_stage1_manifest_digest=stage1,
            declared_calibration_protocol_digest=protocol,
        )


def test_missing_manifest_source_denied(tmp_path: Path) -> None:
    repo = tmp_path / "empty_repo"
    repo.mkdir()
    with pytest.raises(D27F5ShadowTestEntryLifecycleError, match="STAGE1_MANIFEST_SOURCE_MISSING"):
        enforce_d27_f5_fresh_shadow_campaign_test_entry_lifecycle_v1(
            repo_root=repo,
            declared_stage1_manifest_digest="a" * 64,
            declared_calibration_protocol_digest="b" * 64,
        )


def test_shadow_campaign_runner_denies_before_entry(tmp_path: Path) -> None:
    _hermetic_repo(tmp_path)
    req = _request(tmp_path, campaign_id="camp_lifecycle_deny")
    bad = req.__class__(
        **{
            **req.__dict__,
            "reproducibility": req.reproducibility.__class__(
                **{
                    **req.reproducibility.__dict__,
                    "stage1_manifest_digest": "0" * 64,
                }
            ),
        }
    )
    with pytest.raises(ShadowCampaignEmitError, match="STAGE1_MANIFEST_DIGEST_MISMATCH"):
        run_shadow_campaign_v1(bad)


def test_shadow_campaign_runner_happy_path_uses_lifecycle(tmp_path: Path) -> None:
    result = run_shadow_campaign_v1(_request(tmp_path, campaign_id="camp_lifecycle_ok"))
    assert result.productive_numeric_values_set == 0
    assert result.rejection_reasons == () or "stage1_manifest_digest_mismatch" not in (
        result.rejection_reasons
    )
