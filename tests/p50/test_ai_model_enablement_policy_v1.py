import pytest

from src.ai.policy.ai_model_enablement_policy_v1 import (
    AiModelPolicyError,
    read_policy_v1,
    write_policy_v1,
    mint_confirm_token_v1,
    policy_allows_ai_call_v1,
)


@pytest.fixture(autouse=True)
def _isolate_policy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PEAKTRADE_STAGE", "testnet")
    monkeypatch.setenv("PEAKTRADE_AI_CONFIRM_SECRET", "secret123")
    yield


def test_default_denies():
    with pytest.raises(AiModelPolicyError):
        policy_allows_ai_call_v1(confirm_token=None)


def test_enable_arm_requires_token_in_testnet(monkeypatch):
    p = read_policy_v1()
    p["enabled"] = True
    p["armed"] = True
    write_policy_v1(p)

    with pytest.raises(AiModelPolicyError):
        policy_allows_ai_call_v1(confirm_token=None)

    tok = mint_confirm_token_v1(p, reason="test")
    policy_allows_ai_call_v1(confirm_token=tok)


def test_token_stage_mismatch(monkeypatch):
    p = read_policy_v1()
    p["enabled"] = True
    p["armed"] = True
    write_policy_v1(p)

    tok = mint_confirm_token_v1(p, reason="test")
    # Switch to live (token required); token was minted for testnet -> mismatch
    monkeypatch.setenv("PEAKTRADE_STAGE", "live")
    with pytest.raises(AiModelPolicyError):
        policy_allows_ai_call_v1(confirm_token=tok)


def test_shadow_default_token_not_required(monkeypatch):
    monkeypatch.setenv("PEAKTRADE_STAGE", "shadow")
    p = read_policy_v1()
    p["enabled"] = True
    p["armed"] = True
    write_policy_v1(p)

    # shadow token_required defaults to False
    policy_allows_ai_call_v1(confirm_token=None)
