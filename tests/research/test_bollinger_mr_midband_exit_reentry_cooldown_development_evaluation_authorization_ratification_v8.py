"""Contract tests for V8 development-evaluation authorization ratification."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8 import (
    EvaluationAuthorizationRatificationError,
    GO_TOKEN,
    READY_AUTHORITY_DIGEST,
    build_ratification_payload,
    compute_ratification_digest,
    resolve_effective_evaluation_authorization,
    validate_ratification,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.panel_runner_v8 import (
    assert_v8_authority_and_prereg_gates,
    run_development_evaluation,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v8 import (
    AUTHORIZED_STATUS,
    READY_STATUS,
    assert_transition_allowed,
)

REPO = Path(__file__).resolve().parents[2]
HYPOTHESIS = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"


def test_ready_to_authorized_transition_allowed() -> None:
    assert_transition_allowed(from_state=READY_STATUS, to_state=AUTHORIZED_STATUS)


def test_wrong_source_state_forbidden() -> None:
    with pytest.raises(Exception, match="FORBIDDEN_LIFECYCLE_TRANSITION"):
        assert_transition_allowed(
            from_state="IMPLEMENTATION_WIRED_NOT_AUTHORIZED",
            to_state=AUTHORIZED_STATUS,
        )


def test_missing_ratification_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.RATIFICATION_REL_PATH",
        "config/research/__missing_v7_auth_ratification.json",
    )
    from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8 import (
        load_ratification,
    )

    with pytest.raises(EvaluationAuthorizationRatificationError, match="MISSING_RATIFICATION"):
        load_ratification(REPO)


def test_prereg_digest_drift_fail_closed() -> None:
    payload = build_ratification_payload()
    mutated = copy.deepcopy(payload)
    mutated["preregistration_digest"] = "0" * 64
    mutated["ratification_digest"] = compute_ratification_digest(mutated)
    with pytest.raises(
        EvaluationAuthorizationRatificationError, match="PREREGISTRATION_DIGEST_MISMATCH"
    ):
        validate_ratification(mutated, repo_root=REPO, require_panel_released=False)


def test_dataset_digest_drift_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8._slot_consumed",
        lambda repo: False,
    )
    payload = build_ratification_payload()
    mutated = copy.deepcopy(payload)
    mutated["expected_manifest_sha256"] = "1" * 64
    mutated["ratification_digest"] = compute_ratification_digest(mutated)
    with pytest.raises(
        EvaluationAuthorizationRatificationError, match="MANIFEST_DIGEST_BINDING_MISMATCH"
    ):
        validate_ratification(mutated, repo_root=REPO, require_panel_released=False)


def test_go_token_invalid_fail_closed() -> None:
    payload = build_ratification_payload()
    mutated = copy.deepcopy(payload)
    mutated["go_token"] = "WRONG"
    mutated["ratification_digest"] = compute_ratification_digest(mutated)
    with pytest.raises(EvaluationAuthorizationRatificationError, match="GO_TOKEN_INVALID"):
        validate_ratification(mutated, repo_root=REPO, require_panel_released=False)


def test_slot_consumed_blocks_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claim_dir = tmp_path / "eval"
    claim_dir.mkdir()
    (claim_dir / "run_slot_claim.json").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.EVAL_EVIDENCE_REL",
        str(claim_dir.relative_to(tmp_path)),
    )
    # Point repo_root helper to tmp by patching load path usage via validate with custom repo
    # Simpler: patch _slot_consumed
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8._slot_consumed",
        lambda repo: True,
    )
    payload = build_ratification_payload()
    with pytest.raises(EvaluationAuthorizationRatificationError, match="RUN_SLOT_ALREADY_CONSUMED"):
        validate_ratification(payload, repo_root=REPO, require_panel_released=False)


def test_panel_not_released_blocks_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.is_panel_released",
        lambda archive_root=None: False,
    )
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8._slot_consumed",
        lambda repo: False,
    )
    payload = build_ratification_payload()
    with pytest.raises(EvaluationAuthorizationRatificationError, match="PANEL_NOT_RELEASED"):
        validate_ratification(payload, repo_root=REPO, require_panel_released=True)


def test_runner_blocked_when_effective_auth_mocked_false(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.panel_runner_v8.resolve_effective_evaluation_authorization",
        lambda repo_root=None, archive_root=None: {
            "evaluation_authorized": False,
            "reason": "MOCKED_FALSE",
            "lifecycle_status": "EVALUATION_AUTHORIZED",
        },
    )
    out = tmp_path / "no_auth_run"
    with pytest.raises(RuntimeError, match="V8_EVALUATION_NOT_AUTHORIZED"):
        run_development_evaluation(
            output_dir=out,
            authorize_hypothesis_id=HYPOTHESIS,
            allow_panel_run=True,
            repo_root=REPO,
        )
    assert not (out / "run_slot_claim.json").exists()


def test_gate_blocked_without_ratification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.is_panel_released",
        lambda archive_root=None: True,
    )
    claim = (
        REPO
        / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8"
        / "run_slot_claim.json"
    )
    assert not claim.exists()
    with pytest.raises(RuntimeError, match="V8_EVALUATION_NOT_AUTHORIZED"):
        assert_v8_authority_and_prereg_gates(
            repo=REPO, require_evaluation_authorized=True, require_ready_status=True
        )


def test_effective_auth_false_while_ready_not_ratified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.is_panel_released",
        lambda archive_root=None: True,
    )
    effective = resolve_effective_evaluation_authorization(REPO)
    assert effective["evaluation_authorized"] is False
    assert str(effective.get("reason") or "").startswith("LIFECYCLE_NOT_AUTHORIZED")
    assert effective["lifecycle_status"] == READY_STATUS


@pytest.mark.skipif(
    not Path(
        "/Users/frnkhrz/Peak_Trade_data_archive/dev_pre_holdout_panel_v1_20260720T2052Z"
    ).is_dir(),
    reason="released development panel not present on this host",
)
def test_effective_auth_with_real_released_panel_still_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PEAK_TRADE_DATA_ARCHIVE_ROOT", "/Users/frnkhrz/Peak_Trade_data_archive")
    effective = resolve_effective_evaluation_authorization(REPO)
    assert effective["evaluation_authorized"] is False
    assert str(effective.get("reason") or "").startswith("LIFECYCLE_NOT_AUTHORIZED")


def test_go_token_constant() -> None:
    assert GO_TOKEN.startswith("GO_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_V8_")


def test_preauth_parity_required_for_ratification(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = build_ratification_payload()
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_authorization_ratification_v8.validate_pre_authorization_frozen_parameter_parity",
        lambda contract: (_ for _ in ()).throw(Exception("FORCED_PREAUTH_FAIL")),
    )
    with pytest.raises(EvaluationAuthorizationRatificationError, match="PRE_AUTHORIZATION_PARITY"):
        validate_ratification(payload, repo_root=REPO, require_panel_released=False)


def test_preauth_blocks_before_slot_on_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.panel_runner_v8.validate_pre_authorization_frozen_parameter_parity",
        lambda contract: (_ for _ in ()).throw(
            __import__(
                "src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v8",
                fromlist=["PreAuthorizationParityError"],
            ).PreAuthorizationParityError("FORCED")
        ),
    )
    with pytest.raises(RuntimeError, match="PRE_AUTHORIZATION_PARITY"):
        assert_v8_authority_and_prereg_gates(
            repo=REPO, require_evaluation_authorized=False, require_ready_status=True
        )
