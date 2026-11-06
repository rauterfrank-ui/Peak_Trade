# CI documentation (index)

This folder provides a **small entry point** for CI-oriented documentation links. It does **not** describe branch protection, merge requirements, or required GitHub checks, and it does **not** change how workflows run.

- Navigation for operators and contributors lives in the workflow frontdoor linked below.
- Typical **local Markdown checks** before a docs change are documented under development tooling (documentation gates).
- **Workflow definitions** themselves live as YAML under `.github/workflows/` at the repository root; treat those files as authoritative for what Actions executes.

**Links**

- [Workflow documentation frontdoor](../WORKFLOW_FRONTDOOR.md)
- [Development tooling (includes Documentation gates for Markdown)](../dev/tooling.md)
- [GitHub Actions workflows directory](../../.github/workflows/)
