# WebUI Ops Cockpit v2.1 Truth-First

## Purpose
Refines the existing read-only Ops Cockpit UX with:
- clearer truth coverage
- stronger scanability
- explicit unavailable-source rendering
- unchanged truth-first boundaries

## Scope
- read-only only
- no execution logic changes
- no config changes
- no gate changes

## Routes
- `&#47;ops`
- `&#47;api&#47;ops-cockpit`

## Implementation Targets
- `src&#47;webui&#47;ops_cockpit.py`
- `src&#47;webui&#47;app.py`
- `tests&#47;webui&#47;test_ops_cockpit.py`

## Canonical Truth Sources
- `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;AI_UNKNOWN_REDUCTION_V1.md`
- `docs&#47;governance&#47;ai&#47;CRITIC_PROPOSER_BOUNDARY_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;PROVIDER_MODEL_BINDING_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;EXECUTION_ADJACENT_AI_BOUNDARY_SPEC_V1.md`
- `docs&#47;governance&#47;ai&#47;RUNTIME_UNKNOWN_RESOLUTION_V1.md`
- `docs&#47;governance&#47;ai&#47;CRITIC_RUNTIME_RESOLUTION_V2.md`
- `docs&#47;governance&#47;ai&#47;PROPOSER_RUNTIME_RESOLUTION_V1.md`
