# Phase W — GitHub Consumer: Download + Verify Export Packs (S3-compatible)

## Goal
GitHub Actions downloads an export pack from S3-compatible object storage and verifies:
- `manifest.json` present
- `SHA256SUMS.stable.txt` present
- `sha256sum -c` passes

No inbound access to the Data Node is required.

## Required GitHub Secrets
- `PT_RCLONE_CONF_B64` — base64-encoded `rclone.conf` (read-only credentials)
- **Repository variable** `PT_EXPORT_CI_ENABLED` — set to `true` to run this job on pull_request (otherwise skipped)
- `PT_EXPORT_REMOTE` — rclone remote + bucket, e.g. `ptos:peaktrade-exports`
- `PT_EXPORT_PREFIX` — prefix under bucket, e.g. `exports&#47;policy_telemetry_real`
Optional:
- `PT_EXPORT_ID` — pin export_id (else workflow selects latest)
Workflow dispatch input `export_id` can also pin a run.

## Notes
- The workflow selects the lexicographically last `export_<id>&#47;` directory under the prefix.
- Use timestamped export_ids for stable ordering.

- export_id normalization: The workflow accepts either an ID with or without the `export_` prefix. It will download `${PT_EXPORT_PREFIX}/export_<id>`; if you pass `export_<id>` it will not double-prefix.
