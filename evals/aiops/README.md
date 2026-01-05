# Peak_Trade AI Evals Runbook (promptfoo)

## Local
Prereq: Node.js available.

Run eval:
```bash
npx promptfoo@latest eval -c evals/aiops/promptfooconfig.yaml --fail-on-error -o evals/aiops/results.json -o evals/aiops/report.html
```

Run red-team:
```bash
npx promptfoo@latest redteam run
```

Notes:
- Keep provider keys in env vars, never in repo.
- Use evals as a quality gate before PR creation.
