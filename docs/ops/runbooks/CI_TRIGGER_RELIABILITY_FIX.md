# CI Trigger Reliability Fix

## Goal
Normalize pull request trigger behavior so PR checks start reliably on normal PR lifecycle events.

## Trigger contract
For PR-relevant workflows, use:
- `opened`
- `synchronize`
- `reopened`
- `ready_for_review`

## Why
GitHub default pull request types do not include `ready_for_review`. Draft-to-ready transitions can therefore miss expected PR runs unless this type is explicit.

## Scope
This fix is limited to workflow trigger reliability.
It does not change trading/runtime behavior and does not touch paper/shadow/evidence data.
