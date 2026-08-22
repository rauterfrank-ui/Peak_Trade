# Raw verbatim identity copies

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_RAW_EVIDENCE_AREA
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
NOT_CANONICAL=true
NOT_THE_TARGET_REPLACEMENT=true
NORMALIZATION=NONE
```

These files are **byte-identical copies** of bound sources, written with
`Path.read_bytes()` / `Path.write_bytes()`. SHA256 of destination was
re-read and matched to the source and to the previously bound expected
digest.

Do not:

- Unicode-normalize
- change line endings
- pretty-print JSON
- deduplicate
- re-render Markdown
- treat these copies as SSOT or as a rewritten TARGET

Desktop originals and transcripts remain the external sources. These
copies exist so the worktree remains inspectable if chat history is
gone. They are not a license to mutate the Desktop originals.

Machine map: `../../manifests/raw_evidence_preservation_map.json`.
