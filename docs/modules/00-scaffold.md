# Module 00: Scaffold and environment

Status: IMPLEMENTED
Branch: setup/project-init   Commit plan: `chore(scaffold): add project skeleton, config and CLI entry`

## Purpose

Create the minimal runnable skeleton of the RootGuard defense layer so every
later phase has a known-good baseline: packaging metadata, folder skeleton,
central config, a Typer CLI root with `--version` and an empty `dev` sub-app,
and one smoke test. No scoring, data, or enforcement logic belongs here.

## Requirements covered

- AGENTS.md rule 9: only files inside the Section 11 folder map; no new
  dependency beyond what this doc lists under VERIFY/Open questions.
- AGENTS.md rule 10/11: this doc precedes any code; gate in docs/PHASES.md
  decides when the phase is done.
- AGENTS.md rule 12: every unverified fact is a VERIFY row; nothing guessed.
- AGENTS.md rule 14: skills followed are module-spec (this doc) and
  module-audit (next step).
- AGENTS.md rule 15: never merge / push to main / force-push / `--no-verify`;
  never commit `data/external`, `*.db`, `models/hf`, `model.pkl`, secrets.
- AGENTS.md Section 9: config in one dataclass, fixed seed 42; small pure
  functions with type hints; every module ships with tests.
- AGENTS.md Section 10: Rich only, no Textual; CLI commands contain no
  business logic; `dev` sub-app holds pipeline commands (empty for now).
- AGENTS.md Section 11: folder map compliance (paths listed below).
- AGENTS.md Section 12 and PHASES.md Phase 0 "Do" items (see Logic).
- Writing rule: this doc says "defense layer" / "scoring algorithm" only.

## Depends on

None. This is the first phase; there are no earlier module docs and no
interfaces to consume.

## Files to create or modify (paths only, all inside the folder map)

Create:

- `pyproject.toml` (packaging metadata, `requires-python`, dependencies,
  `rootguard` script entry)
- `src/rootguard/__init__.py` (empty; marks the package)
- `src/rootguard/config.py` (central dataclass: HF home, seed)
- `src/rootguard/cli/__init__.py` (empty; marks the subpackage)
- `src/rootguard/cli/app.py` (Typer root with `--version`, empty `dev`
  sub-app)
- `tests/__init__.py` (empty; marks the test package)
- `tests/test_smoke.py` (smoke test: `--version` exits 0; config defaults)
- `docs/modules/00-scaffold.md` (this file)

Create on disk but NOT committed (covered by `.gitignore`):

- `.venv/` (local virtualenv; `uv` is missing, see VERIFY V1)
- `models/hf/` (MiniLM snapshot for gate item 5; ignored by git)
- `data/` working dirs as needed (ignored where applicable)

Modify:

- `docs/BLOCKERS.md` (append Phase 0 findings: venv+pip fallback, pyseccomp
  result; never faked)
- `docs/STATUS.md` (Phase 0 row only, after the gate passes, per phase-gate)

Already correct, no change needed (verified 2026-10-13):

- `.gitignore` covers `data/external/`, `models/hf/`, `*.db` (+`-wal`/`-shm`),
  `model.pkl`, `.venv/` (gate item 7 will re-check this).

## Interfaces

```python
# src/rootguard/config.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class RootGuardConfig:
    hf_home: Path = Path("./models/hf")
    seed: int = 42

def load_config() -> RootGuardConfig: ...
# Returns defaults; no env overrides in Phase 0 (out of scope).
```

```python
# src/rootguard/cli/app.py
import typer

app: typer.Typer        # root; exposes --version via callback
dev_app: typer.Typer    # empty sub-app for future `dev` pipeline commands
def version_callback(value: bool) -> None: ...
# Prints the package version and raises typer.Exit when --version is passed.
# Exact version source (importlib.metadata vs single-sourced constant) is
# VERIFY V5; the smoke test pins the observable behavior, not the mechanism.
```

CLI surface after this phase:

- `rootguard --version` (exit 0, prints version)
- `rootguard dev --help` (exit 0, lists no subcommands yet)

## Data and DB changes

None. No tables, columns, or enums in Phase 0. The `records` / `decisions` /
`outcomes` / `runs` contract (AGENTS.md Section 6) is owned by Phase 1.

## Logic

1. Branch `setup/project-init` from up-to-date `main` (done 2026-10-13;
   repo has no remote, `main` at `0fa3ad7`, tree was clean).
2. `uv` 0.13.0 is installed (`/home/darshil/.local/bin/uv`, confirmed
   2026-10-13 after user install; supersedes VERIFY V1 fallback). Use `uv`
   for env and runs: `uv sync` (creates `.venv/`), `uv run ...`. Record the
   `uv` version in `docs/BLOCKERS.md` only if `uv` misbehaves; otherwise the
   gate outputs are the evidence.
3. Write `pyproject.toml`: project name `rootguard`, minimal dependencies
   `typer`, `rich`, `pytest` (pins are VERIFY V3; resolved at implementation
   and recorded), `[project.scripts] rootguard = "rootguard.cli.app:app"`
   (exact entry form is VERIFY V5).
4. Write `src/rootguard/__init__.py`, `config.py`, `cli/__init__.py`,
   `cli/app.py` exactly per Interfaces. No business logic in CLI commands.
5. Write `tests/test_smoke.py`: (a) `Typer` runner invokes `--version`,
   asserts exit 0 and non-empty output; (b) `load_config()` returns
   `hf_home == Path("./models/hf")` and `seed == 42`.
6. Run `uv run pytest -q` (gate item 1, verbatim).
7. Run `uv run rootguard --version` (gate item 2, verbatim).
8. Gate items 3-6 are environment checks, run and recorded, not coded around:
   `ollama list` (qwen3:4b already observed present 2026-10-13),
   AppArmor-enabled check via `aa-enabled` / sysfs (privileged `aa-status`
   unavailable without root; gate wording changed per user decision, see
   Deviations approved by user),
   MiniLM load-from-`./models/hf` check (checkpoint all-MiniLM-L6-v2
   confirmed; installed into a throwaway env for gate evidence only,
   committed deps stay minimal), `import pyseccomp` (absent 2026-10-13;
   package lookup recorded in BLOCKERS.md; failure path per gate).
9. Re-check `git status` clean and `.gitignore` coverage (gate item 7).

## Failure behavior

- Anything on the future decision path does not exist yet; there is nothing
  to fail closed on in this phase.
- If the venv build, smoke test, or `--version` fails, the phase is not done;
  fix and rerun. No commit on a failing gate.
- Missing `model.pkl`, malformed input, and absent dependencies are Phase 8+
  concerns; this doc states no behavior for them and adds none.

## Tests

- `tests/test_smoke.py::test_version_flag` — covers gate item 2: runner
  invokes `--version`, asserts exit code 0 and version text present.
- `tests/test_smoke.py::test_config_defaults` — covers config contract:
  asserts `hf_home == Path("./models/hf")` and `seed == 42`.
- Gate item 1 is `python -m pytest -q` green (substituted for `uv run`).
- Gate items 3-6 map to shell commands with expected output, recorded in
  STATUS.md at gate time (no committed test fakes an environment check):
  `ollama list` shows `qwen3:4b`; privileged AppArmor check shows enabled;
  MiniLM embeds one sentence from `./models/hf`; `import pyseccomp` result
  recorded honestly.
- Gate item 7 maps to `git status --porcelain` empty plus `.gitignore`
  inspection.

## Gate (verbatim from PHASES.md)

- [ ] `uv run pytest -q` smoke test passes
- [ ] `uv run rootguard --version` works
- [ ] `ollama list` shows qwen3:4b
- [ ] AppArmor enabled (aa-enabled, or /sys/module/apparmor/parameters/enabled = Y)
- [ ] MiniLM loads from ./models/hf and embeds a sentence
- [ ] `import pyseccomp` works, or the failure is written to docs/BLOCKERS.md (not faked)
- [ ] `git status` clean after commit; .gitignore covers data/external, models/hf, *.db, model.pkl

Note: `uv` 0.13.0 confirmed installed 2026-10-13, so gate items 1-2 run
verbatim via `uv run`. No substitution.

Deviations approved by user (2026-10-13, approval message for Phase 0):
D1. Gate item 4 reworded in docs/PHASES.md and in this doc to "AppArmor
    enabled (aa-enabled, or /sys/module/apparmor/parameters/enabled = Y)"
    because privileged `aa-status` needs root, which is unavailable. No sudo
    attempts, no sudoers changes, no workarounds.
D2. Torch for the MiniLM gate check may come from the PyTorch CPU wheel index
    (https://download.pytorch.org/whl/cpu), torch only. (In the event, the
    default-index run was already downloading CUDA wheels when this was
    approved and was left to finish; CPU index recorded for Phase 5+.
    Verified 2026-10-13: the CPU index carries cp314 torch wheels and
    `uv pip install --dry-run` resolves torch==2.14.1+cpu.)

## VERIFY (item | check to run | result)

- V1 `uv` availability | `uv --version` | RESOLVED 2026-10-13: user
  installed `uv`; `uv 0.13.0 (x86_64-unknown-linux-gnu)` at
  `/home/darshil/.local/bin/uv`. No venv+pip fallback needed.
- V2 Python version | `python3 --version` | RAN 2026-10-13: `Python 3.14.4`.
  `requires-python` floor to set at implementation from installer evidence.
- V3 dependency pins (typer, rich, pytest) | resolve latest compatible with
  Python 3.14 at implementation via `uv sync`, record versions with
  `uv pip freeze` in STATUS.md | STRATEGY CONFIRMED by user 2026-10-13
  (accept latest, record). Observed earlier: system python has `rich`
  (importable) but no `typer`, no `pytest`.
- V4 `pyproject.toml` shape (build backend, extras table, script entry) |
  `pip install -e .` must succeed and provide `rootguard` on PATH | PENDING.
- V5 version-source mechanism for `--version` | smoke test asserts behavior
  (exit 0, text), not mechanism | PENDING; decided at implementation, must
  stay trivially simple.
- V6 AppArmor enabled check | `aa-enabled` RAN 2026-10-13: `Yes`;
  `/sys/module/apparmor/parameters/enabled` RAN: `Y`; `dpkg -l` shows
  `apparmor 5.0.2-0ubuntu1~26.04.1` installed | PASS on equivalent evidence
  per user decision D1. Privileged `aa-status` not runnable here
  (`sudo -n aa-status` needs interactive auth; unprivileged read denied).
  No sudo attempts per user instruction.
- V7 pyseccomp package | `uv run python -c "import pyseccomp"` RAN
  2026-10-13: `ModuleNotFoundError`. Read-only lookups RAN 2026-10-13:
  `apt-cache search seccomp` advertises `python3-seccomp` (universe, Python 3
  bindings; import name unverified — direct .deb fetch returned 403 from the
  local mirror, no install attempted); `uv pip install --dry-run pyseccomp`
  resolves PyPI `pyseccomp==0.1.2` for Python 3.14 | Gate failure path
  applies: recorded in BLOCKERS.md, binding choice deferred to Phase 10.
- V8 MiniLM checkpoint id and loader package | checkpoint CONFIRMED by user
  2026-10-13: `sentence-transformers/all-MiniLM-L6-v2`; loader run via
  throwaway `uv run --with sentence-transformers` env (committed deps stay
  minimal) | PASS 2026-10-13: snapshot downloaded to
  `./models/hf/all-MiniLM-L6-v2`, loaded from local path, one sentence
  encoded to shape (1, 384), `MINILM_GATE_OK`, exit 0. Observed earlier:
  `ollama list` shows `qwen3:4b` (2.5 GB) present.
- V9 OS matches scope | `lsb_release -a` RAN 2026-10-13: Ubuntu 26.04.1 LTS
  | CONFIRMED within AGENTS.md scope (Ubuntu 26.04, AppArmor active).

## Open questions

Resolved by the user 2026-10-13 (approval of this doc as amended):

- Q1: RESOLVED — user installed `uv` 0.13.0; proceed with `uv`, no fallback.
- Q2: RESOLVED — vendor `sentence-transformers/all-MiniLM-L6-v2` into
  `./models/hf` for the gate check.
- Q3: RESOLVED — accept latest compatible with Python 3.14 at implementation;
  record resolved versions in STATUS.md.
- Q4: RESOLVED — user accepted the Typer entry form
  (`rootguard = "rootguard.cli.app:app"`); still verified mechanically at
  implementation (`uv run rootguard --version` must exit 0).
- Q5: PARTIALLY OPEN — user intended to fix `docs/BLOCKERS.md`, but the file
  is unchanged as of 2026-10-13 (still the STATUS-table placeholder).
  Phase 0 will APPEND a dated Phase 0 section and preserve existing content;
  it will not rewrite the file. Discrepancy recorded honestly here.

## Out of scope

- Any scoring, feature, DB, daemon, enforcement, testbed, eval, or report
  logic (Phases 1-12).
- Committing `sentence-transformers`/`torch` as project dependencies; the
  MiniLM gate check uses a venv-local install for evidence only.
- Env-var config overrides, `dev` subcommands, Textual UI, network calls.
- Heldout data, frozen seeds (neither exists yet; nothing to touch).

## Audit report (filled by module-audit)

Audited 2026-10-13 in a fresh-context subagent
(`ses_ecbdf4057ffev4NvmYuikf4m7Y`) against AGENTS.md, docs/PHASES.md Phase 0,
and the module-audit skill. The subagent returned the table below and made no
file changes.

| ID | Check | PASS/FAIL | Evidence | Required change |
| A | Traceability: Do + Gate verbatim | PASS | PHASES.md Phase 0 Do items all in Logic steps 2-5, Files, Interfaces; Gate matches PHASES.md verbatim; venv substitution recorded, not hidden | None |
| B | Rules 1-16 no conflict | PASS | Rules 1-16 checked: no decision path yet; no LLM judging; no data/split; no commands; BLOCKERS/STATUS append-only; no DB; no network; map-only files; DRAFT with no code; VERIFY with RAN evidence; Q1-Q5 open; skills followed; ignore/commit rules respected; no seeds touched | None |
| C | Contract Sections 5-6 exact | PASS | Data and DB changes states none; contract owned by Phase 1; table names listed correctly; no features/enums redefined | None |
| D | Scope/folder-map/dependencies | PASS | All created/modified files inside Section 11 map; .venv/models-hf/data not committed; deps only as pending VERIFY; torch/sentence-transformers out of scope; checkpoint deferred to Q2 | None |
| E | Testability per gate item | PASS | Each gate item maps to a test or command: smoke tests, ollama/aa-status/MiniLM/pyseccomp commands, git status check; env checks recorded, not faked | None |
| F | Fail-closed stated | PASS | No decision path exists; failing build/test blocks phase; no commit on failing gate; Phase 8+ behavior deferred without invention | None |
| G | VERIFY no guessed facts | PASS | V1-V9 with RAN evidence where probed, PENDING where not; Q2 proposal marked unconfirmed; no guessed versions, flags, or package names | None |
| H | Dependencies on earlier modules | PASS | Depends on: none; correct for the first phase | None |

Verdict: READY FOR APPROVAL

Addendum 2026-10-13 (post-audit amendments, user-directed, approved as
"APPROVED 00" with the five decisions): Q1-Q4 resolved as recorded above
(uv 0.13.0 installed; checkpoint all-MiniLM-L6-v2; latest-compatible deps
recorded; Typer entry form accepted); Q5 partially open (BLOCKERS.md
unchanged on disk — Phase 0 appends, never rewrites). Re-check against A-H:
no Do/Gate text altered (A); no new rule conflicts — uv use matches PHASES.md
primary path (B); no contract change (C); no new files/deps beyond pending
VERIFY, torch/sentence-transformers stay gate-evidence-only and uncommitted
(D); test mapping unchanged (E); failure behavior unchanged (F); VERIFY rows
now resolve V1/V8 and narrow V3 with user decisions, nothing guessed (G); no
new dependencies (H). Status set to APPROVED on the user's explicit approval;
the user's approval remains the real gate.
