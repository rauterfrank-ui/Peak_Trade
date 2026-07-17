# Authority classification (PR-C)

- Dashboard adapters are read-only consumers.
- Diagnostics projections preserve non_authoritative=True / diagnostic_only=True.
- Economic gate PASS is authoritative for promotion-eligibility semantics only when status is ECONOMICALLY_VIABLE_OFFLINE; RESEARCH_ONLY/PROMISING map to DIAGNOSTIC_ONLY with authoritative_gate=false.
- Safety/authority without a consolidated producer remains NOT_BOUND / UNKNOWN — never false/inactive defaults.
- UI read-only capability is not projected as domain authority.
- LIVE_AUTHORIZED=false from this prompt is an operator constraint, not a runtime-produced SafetyAuthoritySnapshotV1.
