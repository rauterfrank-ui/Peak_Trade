# AI Model Cards (Guardrails)

These YAML files are **required** for any AI model that can be invoked via `create_model_client()`.

They exist to ensure:
- Safety-first defaults (deny-by-default remains enforced by P49/P50)
- Explicit intent, scopes, and constraints per model
- Reproducibility and auditability

Validator: `python -m src.ops.p51.ai_model_cards_validate_v1 --paths docs/ai/model_cards`
