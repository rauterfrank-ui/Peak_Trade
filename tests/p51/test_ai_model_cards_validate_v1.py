from __future__ import annotations

from pathlib import Path

from src.ops.p51.ai_model_cards_validate_v1 import validate_one


def test_example_card_passes() -> None:
    p = Path("docs/ai/model_cards/example_openai_chat.yml")
    viols = validate_one(p)
    assert viols == []


def test_forbidden_purpose_fails(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yml"
    bad.write_text(
        "\n".join(
            [
                "id: x",
                "provider: openai",
                "model: y",
                "purpose: 'Execute trades automatically'",
                "data_handling: {pii: forbidden, secrets: forbidden, storage: no}",
                "guardrails: {allowed_tasks: [x], forbidden_tasks: [place_orders, withdraw_funds, bypass_gates], must_include: ['deny-by-default']}",
                "risk: {level: low, rationale: x}",
                "ops: {owner: x, last_reviewed_utc: '2026-02-15T00:00:00Z'}",
            ]
        ),
        encoding="utf-8",
    )
    viols = validate_one(bad)
    assert any("forbidden substring" in v.msg.lower() for v in viols)
