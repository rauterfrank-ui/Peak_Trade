# /pt-eval

Run (or propose) promptfoo eval and redteam for this change.

Provide commands:
- bash scripts/aiops/run_promptfoo_eval.sh (recommended)
- OR: npx promptfoo@latest eval -c evals/aiops/promptfooconfig.yaml --fail-on-error
- npx promptfoo@latest redteam run

Output:
- Which suite(s) you ran
- Pass/fail
- Any findings & recommended mitigations
- Logs location (.artifacts/aiops/)
