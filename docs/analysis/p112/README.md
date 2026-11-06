# P112 — Execution Router v1 (mocks only)

## Goal
Provide a single safe entrypoint that selects an execution adapter (via registry) and enforces **mode guardrails** (shadow/paper only).

## Non-goals
- No network calls, no real exchange integration.
- No live trading.
