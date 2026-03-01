# AWS Export Write Smoke (PR-CD)

Workflow:
- ``.github&#47;workflows&#47;prcd-aws-export-write-smoke.yml``

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

## Delete permissions

If the IAM principal can write but cannot delete (missing s3:DeleteObject), the write smoke reports:
- reason: DELETE_DENIED_WARNING
- ok: true, wrote: true, deleted: false

Recommendation:
- Configure an S3 lifecycle rule to expire
  ``<export_prefix>/_smoke/aws_export_write_smoke/*`` quickly (e.g. 1 day).

