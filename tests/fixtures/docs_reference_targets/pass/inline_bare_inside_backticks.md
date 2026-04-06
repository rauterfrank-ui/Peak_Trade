# Inline code: bare-path scan must not match inside backticks

Missing fixture path only appears inside a shell command; it must not be picked up as a separate bare-path reference.

- `bash scripts/obs/__fixture_missing_for_inline_bare_test__.sh`

Sanity: real bare path still checked:

- docs/ops/README.md
