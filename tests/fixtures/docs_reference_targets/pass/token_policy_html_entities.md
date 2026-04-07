# HTML entity slashes (`&#47;`) — token policy compatibility

Docs token policy encodes illustrative slashes as `&#47;`. The reference-targets normalizer must
decode entities **before** splitting on `#`, or paths are truncated incorrectly.

- Inline code: `scripts&#47;ops&#47;verify_docs_reference_targets.sh`
- Link: [verify script](scripts&#47;ops&#47;verify_docs_reference_targets.sh)
- Hex entity: `scripts&#x2f;ops&#x2f;verify_docs_reference_targets.sh`
- Real anchor (must still strip section only): [ops README](docs/ops/README.md#section)
