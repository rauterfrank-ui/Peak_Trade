# Edge Cases — Markdown Links

This fixture tests edge cases for markdown link syntax.

## Markdown Links []()

Standard markdown links to existing files:

- [Ops Hub](docs/ops/README.md)
- [](docs/ops/README.md)
- [Ops Center](scripts/ops/ops_center.sh)

## Links with Anchor / Query

These should NOT fail - script must strip # and ? fragments:

- [Risk Roadmap](RISK_LAYER_ROADMAP.md#overview)
- [Ops Hub Query](docs/ops/README.md?plain=1)

## Wildcards in Link Targets

These should NOT be checked as targets:

- [Wildcard](docs/*.md)
- [Glob](docs/**/README.md)

## URL Autolink with docs/... in String

This should NOT count as a repo-target:

- <https://example.com/docs/ops/README.md>
