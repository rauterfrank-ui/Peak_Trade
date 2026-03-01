# AWS Export Smoke (PR-CC)

Workflow:
- `.github/workflows/prcc-aws-export-smoke.yml`

Purpose:
- Read-only verification that the configured export target is reachable from GitHub Actions.

Inputs (Repo Secrets):
- `PT_EXPORT_REMOTE` (e.g. s3://bucket or rclone remote)
- `PT_EXPORT_PREFIX` (optional)
- `PT_RCLONE_CONF_B64` (base64 rclone.conf)

Outputs (Artifact):
- `reports/status/aws_export_smoke.json`
- `reports/status/aws_export_smoke.md`

Interpretation:
- `ok=true` + `listed_ok=true` means Actions can list the export prefix.
- If `ok=false`, check reason codes in the JSON and verify the secrets are set correctly.
