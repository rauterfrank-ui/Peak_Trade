# P60 — AI Guardrails Paper/Shadow Runbook v1

## Übersicht
P60 dokumentiert die AI-Layer Guardrails und den sicheren Paper/Shadow-Execution-Pfad. Live und Record bleiben **hard-blocked**.

## Abhängigkeiten
- **P49**: AI Model Hard Gate v1 (deny-by-default)
- **P50**: AI Model Enablement Policy v1 (enable + arm + token; audit trail)
- **P57**: Switch-Layer Paper/Shadow Runner (live/record deny-by-default)

## Runbooks
| Runbook | Pfad | Zweck |
|---------|------|-------|
| AI Guardrails | `docs/ops/ai/ai_guardrails_runbook_v1.md` | Prinzipien, Gates, Quick Verify |
| AI Model Enablement | `docs/ops/ai/ai_model_enablement_runbook_v1.md` | Enable/arm/token flow |
| Switch-Layer Paper/Shadow | `docs/ops/ai/switch_layer_paper_shadow_runbook_v1.md` | P57 orchestration |

## Modi
- **paper**, **shadow**: erlaubt, wenn Policy es gestattet
- **live**, **record**: **blockiert** (hard gate) bis dedizierter Release
