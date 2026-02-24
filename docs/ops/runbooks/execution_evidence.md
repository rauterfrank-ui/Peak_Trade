# Execution Evidence Producer

Purpose:
- Produce execution evidence artifacts for the Shadow/Testnet scorecard.
- No trading actions; evidence only.

Workflow:
- .github/workflows/prbg-execution-evidence.yml

Artifacts:
- reports/status/execution_evidence.json
- reports/status/execution_evidence.md

Manual dispatch (validation):
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=ok
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=anomalies
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=errors
