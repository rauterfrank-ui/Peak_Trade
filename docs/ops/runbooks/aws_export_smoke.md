# AWS Export Smoke (PR-CC)

**Retired.** The AWS GitHub export path was removed. The original instructions below record its former configuration.

Workflow:
- [Workflow definition at retirement](https://github.com/rauterfrank-ui/Peak_Trade/blob/72aa9b1d1219080b1344b668ab7dfebba5c15f75/.github/workflows/prcc-aws-export-smoke.yml)

Purpose:
- Read-only verification that the configured export target is reachable from GitHub Actions.

Inputs (Repo Secrets):
- `PT_EXPORT_REMOTE` (e.g. s3://bucket or rclone remote)
- `PT_EXPORT_PREFIX` (optional)
- `PT_RCLONE_CONF_B64` (base64 rclone.conf)

Outputs (Artifact):
- ``reports&#47;status&#47;aws_export_smoke.json``
- ``reports&#47;status&#47;aws_export_smoke.md``

Interpretation:
- `ok=true` + `listed_ok=true` means Actions can list the export prefix.
- If `ok=false`, check reason codes in the JSON and verify the secrets are set correctly.
