# Test Fixture — FAIL

This fixture contains a missing target reference that should be detected.

## Valid reference

This one exists: docs/ops/README.md

## Invalid reference (should cause failure)

This target does not exist: docs/ops/__fixture_missing_target__347__nope.md

The script should detect this missing target and fail.
