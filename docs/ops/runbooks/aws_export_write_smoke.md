# AWS Export Write Smoke (PR-CD)

**Retired.** The AWS GitHub export path was removed. The original instructions below record its former configuration.

Workflow:
- [Workflow definition at retirement](https://github.com/rauterfrank-ui/Peak_Trade/blob/72aa9b1d1219080b1344b668ab7dfebba5c15f75/.github/workflows/prcd-aws-export-write-smoke.yml)

Purpose:
- Optional write+delete smoke test to prove GitHub Actions can write to the export target.

Hard gates:
1) Repo variable must be enabled:
- `PT_EXPORT_SMOKE_WRITE_ENABLED=true`
2) Manual trigger must include:
- `confirm_token=YES_WRITE_SMOKE`

Writes:
- A tiny marker file into:
  - ``<export_remote>&#47;<export_prefix>&#47;_smoke&#47;aws_export_write_smoke&#47;<timestamp>.txt``
- Then deletes it.

Outputs (Artifact):
- ``reports&#47;status&#47;aws_export_write_smoke.json``
- ``reports&#47;status&#47;aws_export_write_smoke.md``
