# KILL SWITCH ADAPTER MIGRATION REVIEW

## Purpose
Review the current kill-switch adapter migration surface before any runtime mutation.

## Scope
- docs-only review
- exactly one PR
- no paper/shadow/testnet mutation

## Review Questions
1. what should be the canonical kill-switch source for runtime consumers?
2. which consumers depend on kill-switch state today?
3. where is adapter behavior still missing or future work?
4. what should remain unchanged until a later explicit runtime slice?

## Current Surfaces
- operator tooling
- risk gate
- risk hook
- operator visibility / cockpit
- incident / stop documentation

## Expected Findings
- current source-of-truth candidates
- consumer mapping
- future-work gaps
- migration guardrails

## Recommended Outcome
- one concrete migration review with explicit guardrails
- no runtime implementation in this slice
