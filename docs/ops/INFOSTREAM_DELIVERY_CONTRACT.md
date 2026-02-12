# InfoStream Delivery Contract

**Purpose:** Define the durable repo-commit sink semantics for InfoStream Automation.  
**Workflow:** `.github/workflows/infostream-automation.yml`

## Sink semantics

- **Sink type:** Repo-commit (writes to `reports&#47;infostream&#47;`, `docs/mindmap/INFOSTREAM_LEARNING_LOG.md` and pushes to `main`).
- **Trigger:** Schedule (03:15 UTC daily) or `workflow_dispatch`.
- **Commit scope:** Only staged paths `reports&#47;infostream&#47;` and `docs/mindmap/INFOSTREAM_LEARNING_LOG.md` are committed.

## Failure policy

- **Push:** The job **must fail** if `git push origin main` fails (e.g. no write permission, branch protection). There is no `|| echo` or other swallow; a non-zero exit from push fails the workflow run.
- **Commit:** If there is nothing to commit, the step may complete without error (no change to push). If there are changes and commit succeeds but push fails, the job fails.

## Evidence trail

- **Commit SHA:** After a successful run, the commit created by the workflow appears on `main`; the run logs show the commit message and SHA.
- **Diff scope:** Only the paths above are added and committed; no other files are modified by this workflow.
- **Log lines:** The "📝 Commit changes" step logs `git status --short` and the commit message; the push step has no fallback message so a failure is visible as a failed step.

## Workflow configuration (contract enforcement)

- **Permissions:** Job uses `permissions: contents: write` so the default token can push.
- **Checkout:** `actions&#47;checkout@v4` is used with `persist-credentials: true` so the same token is available for `git push`.
- **No push swallow:** The run script does not use `|| echo "…"` after `git push`; the step fails on push failure.
