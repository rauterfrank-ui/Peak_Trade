# AI Model Cards (Guardrails)

These YAML files are **required** for any AI model that can be invoked via `create_model_client()`.

They exist to ensure:
- Safety-first defaults (deny-by-default remains enforced by P49/P50)
- Explicit intent, scopes, and constraints per model
- Reproducibility and auditability

The [AI model card workflow](../../../.github/workflows/ai-model-cards-validate.yml)
checks the YAML format, required sections and unique card IDs.
