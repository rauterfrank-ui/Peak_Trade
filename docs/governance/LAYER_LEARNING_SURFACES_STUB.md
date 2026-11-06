# Layer Learning Surfaces (STUB)

## Rule
- Learning ist nur erlaubt, wenn ein Layer eine explizite allowlist an learnable surfaces hat.
- Promotion nur via governance gates (research→shadow→testnet→live).

## Layers
### L0_ops_docs
- learnable: []
- rationale: ops/docs, deterministisch, keine Selbständerung

### L1_deep_research
- learnable: [retrieval_query_templates, source_ranking_weights]
- gates: [policy_critic_pass, determinism_contract, evidence_pack_present]

### L2_market_outlook
- learnable: [scenario_priors, no_trade_trigger_thresholds]
- gates: [policy_critic_pass, regression_suite_green, evidence_pack_present]

### L3_trade_plan_advisory
- learnable: [prompt_template_variants] (nur Vorschläge; write->registry verboten ohne Gate)
- gates: [policy_critic_pass]

### L4_governance_critic
- learnable: [] (kritisch; nur Ruleset-Versionen via PR, keine Runtime-Selbständerung)

### L5_risk_gate
- learnable: [] (deterministischer Code)

### L6_execution
- learnable: [] (verboten / stark gegated)
