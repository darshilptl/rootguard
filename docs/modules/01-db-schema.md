# Module 01: DB schema and migrations

Status: IMPLEMENTED
Branch: feature/db-schema   Commit plan: `feat(db): add four-table schema and initial migration`

## Purpose

Give the RootGuard defense layer its SQLite foundation: SQLAlchemy 2.0
declarative models for the four tables, an Alembic initial migration that
creates them with database-level enum CHECK constraints, and WAL mode enabled
on every connection. Later phases (seeds, imports, training, daemon, eval)
only read and write through this layer.

## Requirements covered

- AGENTS.md rule 7: Python owns the DB schema (SQLAlchemy + Alembic); nothing
  else edits it.
- AGENTS.md rule 9: files only inside the Section 11 folder map
  (`src/rootguard/db/`, `tests/`); new dependencies (SQLAlchemy, Alembic)
  listed here under VERIFY/Open questions, versions resolved at
  implementation and recorded.
- AGENTS.md rules 10/11: this doc precedes any code; the PHASES.md gate
  decides when the phase is done.
- AGENTS.md rule 12: unverified facts are VERIFY rows (V1-V5); nothing guessed.
- AGENTS.md rule 13: anything not specified is an Open question (Q1-Q6).
- AGENTS.md rule 15: no merges, no `--no-verify`; never commit `*.db`.
- AGENTS.md Section 6: `records` columns and enum sets exactly as specified.
- AGENTS.md Section 9: small pure functions, type hints, tests per module.
- PHASES.md Phase 1 "Do" items (see Logic) and Gate (copied verbatim below).
- Writing rule: "defense layer" / "scoring algorithm" only.

## Depends on

- docs/modules/00-scaffold.md (IMPLEMENTED): package layout
  (`src/rootguard/`), `RootGuardConfig` / `load_config()` from
  `src/rootguard/config.py`. Phase 1 proposes adding `db_path` to that
  config (Open question Q3); 00-scaffold is IMPLEMENTED, so this amends it
  and needs explicit approval.

## Files to create or modify (paths only, all inside the folder map)

Create:

- `src/rootguard/db/__init__.py` (empty; marks the subpackage)
- `src/rootguard/db/models.py` (SQLAlchemy 2.0 declarative `Base` + the four
  model classes)
- `src/rootguard/db/engine.py` (single engine factory with WAL listener;
  reason: "WAL on every connection" needs exactly one place that sets it)
- `src/rootguard/db/migrations/env.py` (Alembic env; imports `Base.metadata`;
  also ensures the sqlite parent directory exists so `alembic upgrade head`
  works on a fresh checkout — mirrors `get_engine`)
- `src/rootguard/db/migrations/script.py.mako` (Alembic template, unmodified
  default)
- `src/rootguard/db/migrations/versions/0001_initial.py` (hand-reviewed
  initial migration; see Logic step 4 for autogenerate-then-review)
- `alembic.ini` (repo root; folder-map exception APPROVED per Q4 — a marked
  section appended to AGENTS.md documents it, existing content preserved)
- `.python-version` (repo root; pins interpreter 3.14 after finding uv had
  created the venv on 3.11 — NOT pre-approved, needs retro-approval; see V4)
- `tests/test_db.py` (gate tests, named in Tests below)

Modify:

- `src/rootguard/config.py` (add `db_path: Path = Path("data/rootguard.db")`;
  PROPOSED, needs approval — Q3)
- `pyproject.toml` (add `sqlalchemy`, `alembic` dependencies; versions
  resolved at implementation, recorded in STATUS.md — V4)
- `docs/STATUS.md` (Phase 1 row, after the gate passes, per phase-gate)

Placement of the Alembic config file is resolved per Q4: root-level
`alembic.ini` (approved folder-map exception, documented by a marked appended
section in AGENTS.md) so the documented command `alembic upgrade head` works.

## Interfaces

```python
# src/rootguard/db/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): ...

class Record(Base):
    __tablename__ = "records"
    # columns exactly per "Data and DB changes" below

class Decision(Base): ...   # __tablename__ = "decisions"
class Outcome(Base): ...    # __tablename__ = "outcomes"
class Run(Base): ...        # __tablename__ = "runs"
```

```python
# src/rootguard/db/engine.py
from pathlib import Path
from sqlalchemy import Engine, create_engine, event

def get_engine(db_path: Path) -> Engine: ...
# Creates / opens the SQLite file at db_path and registers a "connect"
# listener that executes PRAGMA journal_mode=WAL on every new connection.
# Raises the original exception on any failure; no silent fallback.
```

Enum columns use `sqlalchemy.Enum` with `create_constraint=True` and
`validate_strings=True` so that (a) the DDL carries a CHECK constraint and
(b) the ORM rejects bad values early. The database-level CHECK is what gate
item 3 tests (VERIFY V1/V2 confirm the CHECKs exist in the migration and in
SQLite). `features_json`, `config_json`, `metrics_json` use `sqlalchemy.JSON`.

## Data and DB changes

### records (exact AGENTS.md Section 6 contract)

| column | type | nullable | constraint / default |
|---|---|---|---|
| id | Integer PK autoincrement | no | primary key |
| family_id | String | no | none (groups variants; Phase 3 assigns) |
| user_request | Text | no | none |
| source | Enum | no | CHECK in (user_direct, file_content, web_content, tool_output, pr_content, agent_internal) |
| injected_text | Text | yes | none |
| proposed_action | Text | no | none |
| reversibility | Enum | no | CHECK in (reversible, irreversible) (value set from AGENTS.md Section 5) |
| scope | Enum | no | CHECK in (single_file, single_folder, multi_file, single_process, system_wide) |
| privilege | Enum | no | CHECK in (user, root) (value set from AGENTS.md Section 5) |
| label | Enum | no | CHECK in (safe, risky) |
| reasoning | Text | no | none (Q5: allow empty string vs nullable — proposed NOT NULL, see Open questions) |
| provenance | Enum | no | CHECK in (seed, nl2bash, nl2bash_mismatch, injection_dataset, generated, live_log) |
| split | Enum | no | CHECK in (train, heldout) |
| reviewed | Boolean | no | default False (proposed — Q5) |
| created_at | DateTime(timezone=True) | no | server_default func.now() (proposed — Q5) |

### Proposed, needs user approval (the other three tables are NOT in AGENTS.md)

APPROVED 2026-10-13 (APPROVED 01): tables approved as proposed below, S1-S6
accepted, S7 amended to ON DELETE RESTRICT (see Open questions Q1/Q2).

Advisor proposal, reproduced verbatim, then suggestions with reasons:

- decisions: id, ts, run_id (nullable), request, proposed_action, source,
  features_json, score, decision (allow/confirm/block), reason,
  mode (undefended/defended/live), model_version
- outcomes: id, decision_id (FK), outcome
  (correct/false_positive/miss/unknown), note, ts
- runs: id, kind (train/eval), started_at, finished_at, seed, config_json,
  metrics_json, notes

Suggestions with reasons (accept / amend / reject in approval):

- S1: `decisions.source` gets the same 6-value CHECK as `records.source`.
  Reason: it mirrors the record source; prevents drift between tables.
- S2: `decisions.decision` and `decisions.mode` get CHECK constraints with
  exactly the advisor's value sets. Reason: same consistency argument; the
  gate-3 style test can cover them.
- S3: `decisions.score` is Float, NULLABLE, with CHECK (score BETWEEN 0 AND 1).
  Reason: fail-closed BLOCKs (missing model file, malformed input — Phase 8)
  have no score; NULL records that honestly instead of a fake 0.0.
- S4: `decisions.run_id` is a NULLABLE FOREIGN KEY to `runs.id`.
  Reason: nullable covers live mode (no run); the FK keeps eval reports
  joinable. Without the FK, orphaned run_ids are possible.
- S5: `outcomes.outcome` gets the advisor's 4-value CHECK; `runs.kind` gets a
  (train, eval) CHECK. Reason: as S2.
- S6: all tables use Integer PK autoincrement ids; timestamp columns default
  to func.now() and are NOT NULL; free-text note/reason columns are NOT NULL
  (empty string allowed). Reason: uniform, simple, matches `records` defaults.
- S7: `outcomes.decision_id` is FK to `decisions.id`, NOT NULL, with
  ON DELETE RESTRICT (AMENDED per approval — see Q1/Q2). Reason: preserve
  outcome and evaluation evidence; rows are never deleted from shared
  databases. Test teardown uses separate temporary database files, so no
  deletes are needed.

## Logic

1. Resolve and install `sqlalchemy`, `alembic` via `uv sync` (latest
   compatible with Python 3.14, recorded in STATUS.md — V4). No other new
   dependency.
2. Write `src/rootguard/db/models.py` per Interfaces and Data and DB changes.
3. Write `src/rootguard/db/engine.py`: `get_engine()` creates the parent
   directory if needed, then registers an event listener that runs
   `PRAGMA journal_mode=WAL` on every new DBAPI connection. Errors propagate.
4. Write the initial migration: generate with `alembic revision
   --autogenerate` against an empty database, then HAND-REVIEW the script
   and fix it until every enum CHECK from the Data section is present
   literally in the migration file (VERIFY V2). Reason: autogenerate is a
   draft aid, not the source of truth; the reviewed script is.
5. Gate item 1: point the app at a fresh temp DB file and run
   `alembic upgrade head`; assert all four tables exist.
6. Gate item 2: insert one valid row per table through the ORM, read it back,
   assert every column round-trips.
7. Gate item 3: insert via RAW SQL (bypassing ORM validation) with an invalid
   enum value and assert the database raises `IntegrityError`. Table-driven
   over all constrained columns (the 7 `records` enums plus S1/S2/S5 if
   approved), so the CHECKs themselves — not Python validation — are proven.
8. Gate item 4: open a fresh DB file through `get_engine()` and assert
   `PRAGMA journal_mode` returns `wal` (case-insensitive).
9. Edge cases: `get_engine()` on a path whose parent is missing creates the
   parent (data/); `upgrade head` on an already-migrated DB is a no-op
   success; NULL into a NOT NULL column raises (no silent coercion). Test
   teardown uses separate temporary database files (never deletes from a
   shared database), consistent with ON DELETE RESTRICT.

## Failure behavior

- No decision path exists yet, so nothing fail-closed to state for scoring.
- Constraint violations raise `sqlalchemy.exc.IntegrityError` to the caller;
  this layer catches nothing and coerces nothing.
- Migration or engine errors propagate with the original exception. No
  fallbacks (e.g. no silent downgrade to in-memory or to DELETE journal mode).
- Phase 8 will define BLOCK-on-error for the scoring path; this doc adds no
  behavior for it.

## Tests (`tests/test_db.py`)

- `test_alembic_upgrade_head_on_fresh_db` — covers gate item 1: fresh tmp
  DB file, `upgrade head`, assert the four tables exist.
- `test_records_round_trip` — covers gate item 2: insert/read one valid row
  per table, assert all columns round-trip.
- `test_invalid_enum_values_rejected_by_db` — covers gate item 3:
  table-driven over every CHECK-constrained column; raw-SQL insert of an
  invalid value asserts `IntegrityError` from SQLite itself.
- `test_journal_mode_is_wal` — covers gate item 4: fresh DB via
  `get_engine()`, `PRAGMA journal_mode` returns `wal` (case-insensitive).
- `test_migration_contains_enum_checks` — supports VERIFY V2: asserts each
  expected CHECK value set appears in the reviewed migration script.

## Gate (verbatim from PHASES.md)

- [ ] `alembic upgrade head` succeeds on a fresh DB file
- [ ] insert/read round-trip test passes
- [ ] an invalid enum value is rejected
- [ ] `PRAGMA journal_mode` returns wal

## VERIFY (item | check to run | result)

- V1 installed SQLAlchemy Enum-on-SQLite behavior | `uv pip freeze` for the
  resolved version + inspect generated DDL for `CHECK` on each enum column |
  RESOLVED 2026-10-13: sqlalchemy==2.1.4 (Python 3.14.4).
  `Enum(create_constraint=True, validate_strings=True)` renders CHECKs:
  the `records` DDL in a migrated SQLite file contains 14 CHECK occurrences
  (7 inline from the Enum type + 7 table-level), and the raw-SQL gate-3 test
  raises `IntegrityError` for every constrained column. Mechanism confirmed,
  not assumed.
- V2 migration contains the CHECKs | `grep -i "check"` on
  `versions/0001_initial.py` + `test_migration_contains_enum_checks` |
  RESOLVED 2026-10-13: autogenerate rendered every enum CHECK but DUPLICATED
  each one (two identical lines); hand-review removed the duplicates, keeping
  one table-level CHECK per constrained column plus the single
  `decision_score_range` CHECK (13 CheckConstraint occurrences total: 7
  records + 1 runs + 3 decisions enum + 1 score range + 1 outcomes). All 36
  enum values asserted present by `test_migration_contains_enum_checks`,
  which passes.
- V3 WAL on fresh DB | `PRAGMA journal_mode` via `get_engine()` on a tmp
  file, asserted by `test_journal_mode_is_wal` | RESOLVED 2026-10-13:
  returns `wal` (test passes).
- V4 dependency versions (sqlalchemy, alembic) | resolve latest compatible
  with Python 3.14 via `uv sync`, record `uv pip freeze` in STATUS.md |
  RESOLVED 2026-10-13: sqlalchemy==2.1.4, alembic==1.20.0 (plus mako==1.4.3)
  on Python 3.14.4. CORRECTION: the project venv was silently created on
  Python 3.11.16 by uv discovery; found 2026-10-13, pinned to 3.14 with
  `.python-version` (`uv python pin 3.14`) and re-synced. The Phase 0
  dry-run wheel evidence was re-run under 3.14 (numpy corrected 2.4.6 to
  2.5.4); see BLOCKERS.md correction row. `.python-version` needs
  retro-approval as a root file (flagged in the Phase 1 report).
- V5 `alembic` CLI availability | `uv run alembic --version` at
  implementation | RESOLVED 2026-10-13: `alembic 1.20.0`. The literal gate
  command `uv run alembic upgrade head` succeeded on a fresh
  `data/rootguard.db` (4 tables + alembic_version=0001); the file was
  removed afterwards so tests alone own tmp databases.

## Open questions

Resolved 2026-10-13 in APPROVED 01 (all approved scope for implementation):

- Q1: RESOLVED — decisions, outcomes, runs tables approved as proposed.
  S1-S6 accepted as proposed. S7 amended to ON DELETE RESTRICT.
- Q2: RESOLVED — RESTRICT explicitly confirmed. Outcome and evaluation
  evidence is preserved; test teardown uses temporary databases.
- Q3: RESOLVED — add `db_path: Path = Path("data/rootguard.db")` to
  `RootGuardConfig`; caller-supplied paths supported for tests
  (via `get_engine(db_path)`).
- Q4: RESOLVED — root-level `alembic.ini` so `alembic upgrade head` works.
  Folder-map exception documented by appending a marked section to AGENTS.md
  (existing content preserved, per AGENTS.md rule 6); `alembic.ini` added to
  the module file list.
- Q5: RESOLVED — nullability/defaults accepted: `reasoning` NOT NULL (empty
  strings allowed), `reviewed` NOT NULL DEFAULT False, timestamps NOT NULL
  with database-side defaults; specified nullable fields stay nullable
  (`injected_text`, `decisions.score`, `decisions.run_id`,
  `runs.finished_at`, note fields per S6).
- Q6: RESOLVED — latest compatible SQLAlchemy + Alembic for Python 3.14 via
  `uv sync`; actual installed versions recorded in docs/STATUS.md.

## Out of scope

- Any seed, import, feature, training, daemon, enforcement, testbed, eval, or
  CLI logic (Phases 2-12). No rows are inserted except by tests into tmp files.
- `data/rootguard.db` itself: tests use tmp files only; no real DB file is
  committed (and `*.db` is gitignored).
- Query helpers, repositories, or session wrappers beyond `get_engine`.
- Touching heldout data or seeds (neither exists yet).

## Audit report (filled by module-audit)

Audited 2026-10-13 in a fresh-context subagent
(`ses_ecbaac4a5ffehckh73R4W556IQ`) against AGENTS.md, docs/PHASES.md Phase 1,
docs/modules/00-scaffold.md, and the module-audit skill. The subagent returned
the table below and made no file changes.

| ID | Check | PASS/FAIL | Evidence | Required change |
| A | Traceability: Do + Gate verbatim | PASS | Phase 1 Do items covered in Files, Interfaces, Logic steps 2-4; Gate matches PHASES.md verbatim (4 items) | None |
| B | Rules 1-16 no conflict | PASS | All 16 rules checked: no decision path/LLM/split logic/commands; SQLAlchemy+Alembic only; map-only files; DRAFT with no code; VERIFY pending; Q1-Q6 open; no merges; tmp-only DBs; no seeds touched | None |
| C | Contract Sections 5-6 exact | PASS | 15 records columns in Section 6 order; all 7 CHECK sets match Sections 5-6; table names match; other tables marked Proposed, not claimed | None |
| D | Scope/folder-map/dependencies | PASS | All files inside Section 11 map; only sqlalchemy/alembic as new deps (V4/Q6); table details via Q1/Q2; ini placement via Q4; config amendment via Q3 | None |
| E | Testability per gate item | PASS | One named test per gate item plus a migration-content test for V2; gate-3 test uses raw SQL so the DB CHECKs themselves are proven | None |
| F | Fail-closed stated | PASS | No decision path yet; IntegrityError propagates uncaught; no silent fallbacks; Phase 8 behavior deferred without invention | None |
| G | VERIFY no guessed facts | PASS | V1-V5 all PENDING with concrete checks; assumed mechanism marked as not fact; no versions/flags/URLs asserted | None |
| H | Dependencies on earlier modules | PASS | Depends on 00-scaffold interfaces verified to exist; db_path addition flagged as amendment in Q3 | None |

Verdict: READY FOR APPROVAL

## Re-audit report (amendments under APPROVED 01)

Re-audited 2026-10-13 in a fresh-context subagent
(`ses_ecba0fc5fffe0HDp5vudKQr5SX`) after incorporating the six APPROVED 01
decisions. The subagent returned the table below and made no file changes.

| ID | Check | PASS/FAIL | Evidence | Required change |
| A | Traceability: Do + Gate verbatim | PASS | Do items covered in Files/Interfaces/Logic; Gate matches PHASES.md verbatim (4 items) | None |
| B | Rules 1-16 no conflict | PASS | No scoring/LLM/split logic; tmp-file DBs only; AGENTS.md append-only; Python owns schema; map-only files + approved alembic.ini exception; DRAFT with no code; VERIFY pending; Q1-Q6 explicitly approved | None |
| C | Contract Sections 5-6 exact | PASS | 15 records columns in order; all 7 CHECK sets match Sections 5-6; Q5 defaults do not contradict the contract | None |
| D | Scope/folder-map/dependencies | PASS | Only sqlalchemy/alembic as new deps; root alembic.ini listed as approved exception; config/pyproject/STATUS modifications inside map | None |
| E | Testability per gate item | PASS | One named test per gate item (raw-SQL CHECK proof for gate 3) plus migration-content test | None |
| F | Fail-closed stated | PASS | IntegrityError propagates uncaught; no silent fallbacks; Phase 8 deferred without invention | None |
| G | VERIFY no guessed facts | PASS | V1-V5 pending with concrete checks; assumed mechanism marked as not fact | None |
| H | Dependencies on earlier modules | PASS | 00-scaffold interfaces verified; db_path flagged as amendment | None |

Verdict: READY FOR APPROVAL (amended scope; Status set to APPROVED on the
user's explicit APPROVED 01 decisions)
