---
name: git-workflow
description: Branching, Conventional Commits, and the PR hand-off for each finished phase
---
Branch: from up-to-date main, named in PHASES.md. One phase, one concern.
Before committing (all must be true): gate passed, `uv run pytest -q` green, STATUS.md updated
with real output, module doc Status IMPLEMENTED, `git status` shows no ignored/secret files
(data/external, *.db, models/hf, model.pkl, .env).
Commit format (Conventional Commits, <= 72-char subject, imperative, no period):
  type(scope): subject

  Body: why this change, what it covers, anything notable (wrapped at ~72).

  Refs: docs/modules/NN-<name>.md
Types: feat fix refactor test docs chore build perf.
Example:
  feat(db): add SQLAlchemy schema and initial Alembic migration

  Add records, decisions, outcomes and runs tables with enum constraints
  and WAL mode, per the data contract in AGENTS.md section 6.

  Refs: docs/modules/01-db-schema.md
Never: commit to main, merge, force-push, use --no-verify, or commit a failing state.
Hand-off message to the user after committing:
  - branch name and commit hash
  - suggested PR title (same as the commit subject) and a short description (what, gate results, open items)
  - "Squash merge, delete the branch, then tag: git tag v0.<N>.0"
Then STOP and wait for "NEXT".