# Status
| Phase | Module doc status | Gate result | Commit | Date |
|---|---|---|---|---|
| 0 | IMPLEMENTED (docs/modules/00-scaffold.md) | 7/7 PASS (see below) | chore(scaffold): add project skeleton, config and CLI entry | 2026-10-13 |
| 1 | IMPLEMENTED (docs/modules/01-db-schema.md) | 4/4 PASS (see below) | feat(db): add four-table schema and initial migration | 2026-10-13 |
| 2-12 | not started | | | |
Rules: update only after running the gate. Record real output summaries, never claims.
Hashes: seed_100.jsonl = (pending), families.json = (pending)

## Phase 0 gate evidence (2026-10-13, branch setup/project-init)

- `uv run pytest -q`: 2 passed in 0.09s.
- `uv run rootguard --version`: `rootguard 0.0.0`, exit 0.
- `ollama list` shows `qwen3:4b` (359d7dd4bcda, 2.5 GB).
- AppArmor enabled on equivalent evidence (author-approved rewording):
  `aa-enabled` = `Yes`, `/sys/module/apparmor/parameters/enabled` = `Y`,
  `apparmor 5.0.2-0ubuntu1~26.04.1` installed. Privileged `aa-status`
  unavailable without root; no sudo attempted.
- MiniLM `sentence-transformers/all-MiniLM-L6-v2` snapshot in
  `./models/hf/all-MiniLM-L6-v2`, loaded from local path, one sentence
  embedded to shape (1, 384). Loader ran in a throwaway
  `uv run --with sentence-transformers` env; not a project dependency.
- `import pyseccomp` fails (`ModuleNotFoundError`); failure recorded in
  docs/BLOCKERS.md with read-only lookup outputs, per the gate failure path.
- `git status` clean after commit (checked before commit); `.gitignore`
  covers `data/external/`, `models/hf/`, `*.db` (+`-wal`/`-shm`),
  `model.pkl`, `.venv/`.

Resolved versions: uv 0.13.0, Python 3.14.4, typer==0.27.3, rich==15.0.0,
pytest==9.1.1 (via `uv sync`, recorded in uv.lock).
Python 3.14 dry-run resolution (nothing installed): faiss-cpu==1.15.1,
lightgbm==4.7.0, numpy==2.5.4, pandas==3.0.6, scikit-learn==1.9.1,
torch==2.14.1+cpu (CPU index). OS: Ubuntu 26.04.1 LTS.
Correction 2026-10-13 (found in Phase 1): the numpy version first recorded
(2.4.6) came from a venv uv had created on Python 3.11; re-checked under
3.14.4 (2.5.4). See BLOCKERS.md correction row.

## Phase 1 gate evidence (2026-10-13, branch feature/db-schema)

- `uv run alembic upgrade head` on a fresh `data/rootguard.db`: success, no
  output; tables records/decisions/outcomes/runs + alembic_version 0001
  present. File removed afterwards; tests own tmp databases.
- `uv run pytest -q`: 19 passed (2 smoke + 17 db).
- Invalid enum rejected by the DB itself: raw-SQL inserts with bogus values
  raise `IntegrityError` for all 7 records enums, decisions source/decision/
  mode, score=1.5 (range CHECK), runs kind, and outcomes outcome (with a real
  parent decision id, proving the CHECK not the FK fires).
- `PRAGMA journal_mode` via `get_engine()` on a fresh file returns `wal`.
- Migration review: autogenerate duplicated every enum CHECK; deduped by hand
  to 13 CheckConstraints. `records` DDL in SQLite contains 14 CHECK
  occurrences (7 inline Enum + 7 table-level).

Resolved versions: sqlalchemy==2.1.4, alembic==1.20.0 (plus mako==1.4.3) on
Python 3.14.4 (`.python-version` pins 3.14; venv was found on 3.11 and
re-synced — see BLOCKERS.md).

## Retrospective approvals (author, 2026-10-13, after gate)

1. `.python-version` pinning Python 3.14 APPROVED; interpreter stays 3.14.4;
   correction documented here and in BLOCKERS.md.
2. AGENTS.md §15 appendix ACCEPTED as append-only (existing content preserved
   byte-for-byte; diff of the commit shows addition only); documents the
   root-level `alembic.ini` folder-map exception.
3. Phase 1 gate results ACCEPTED as reported (4/4 PASS). Commit `df80ccd`
   verified to contain only the approved scope (16 files; no seeds/heldout,
   no scope expansion). No merge, squash, branch deletion, or tag performed —
   awaiting author.
