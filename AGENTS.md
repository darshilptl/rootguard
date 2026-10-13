# RootGuard: Agent Instructions

## 1. What this is
A research project (M.Tech dissertation), not a product.
Title: Beyond the Chatbox: A Boundary Study of Provenance-Based Defense Against
Irreversible Prompt Injection in OS-Level Autonomous Agents.
Question: do known defense patterns (source tagging, isolation, capability checks)
hold when applied to agents that run real OS commands, where mistakes are
irreversible, and where do they fail?
What we build: a scoring algorithm plus enforcement layer that sits beside an agent.
For every proposed command it receives (user_request, proposed_action, source) and
returns allow / confirm / block with a reason.
Writing rule: in docs and comments say "defense layer" or "scoring algorithm", never "tool" or "product".
Honesty rule: this measures a defense, it does not claim to solve prompt injection.
Report failures as found. Never invent or estimate results; metrics come only from
eval/ runs stored in the DB.

## 2. Scope
- Linux only (Ubuntu 26.04), AppArmor active.
- Agent under test and variant generator: Ollama `qwen3:4b` only.
- Root (the author's other project) is NOT an integration target. Do not reference it.
- Out of scope: chat agents, GUI agents, payment/API agents, Windows/macOS.

## 3. Hard rules
1. Default deny. Any inconclusive stage, missing model file, malformed input or
   exception returns BLOCK (fail closed).
2. Never use an LLM to judge another LLM's action. Scoring is LightGBM only.
   Qwen is used only for (a) the testbed agent and (b) rewording seed records.
3. Never train, tune, or compute nn_history on data with split='heldout'.
   Heldout is evaluated once per run id.
4. Split by family_id (GroupKFold), never by row. All variants of a seed share its
   family_id and its split.
5. Never run real destructive commands outside `sandbox/`. Sandbox holds synthetic
   files only and runs as an unprivileged user.
6. Never overwrite a user's CLAUDE.md or AGENTS.md. Append a marked section only.
7. Python owns the DB schema (SQLAlchemy + Alembic). Nothing else edits it.
8. No network calls from core scoring code.
9. Do not add features, tables, files outside the folder map, or dependencies not
   listed here. Ask first.
10. A phase is done only when its gate in docs/PHASES.md passes. Never skip a gate.
11. Never write code for a phase before its module doc is APPROVED by the user (Section 13).
12. Never guess facts (versions, flags, URLs, package names). Mark VERIFY, check, record evidence.
13. If a requirement is ambiguous, write it under "Open questions" in the module doc and
    stop. Do not pick an answer silently.
14. Skills are plain markdown in .claude/skills/<name>/SKILL.md. If your harness does not
    auto-load them, open and follow the named file at the step that names it.
15. Never merge, push to main, force-push, or skip hooks (--no-verify). Never commit
    data/external, *.db, models/hf, model.pkl, secrets.
16. data/seeds/seed_100.jsonl is human-reviewed ground truth. Never edit it after the
    freeze (hash recorded in docs/STATUS.md).

## 4. Pipeline (do not reorder)
tag source -> six features -> LightGBM score -> staged authz -> seccomp/AppArmor -> log

## 5. The six features (exactly these, in this order)
1. similarity: cosine(MiniLM(request), MiniLM(action)), clipped to [0,1]
2. source_trusted: 1 if source == user_direct else 0
3. reversibility: reversible=0, irreversible=1
4. scope: single_file/single_process=0, single_folder/multi_file=1, system_wide=2
5. privilege: user=0, root=1
6. nn_history: mean label (risky=1) of k nearest TRAIN records in FAISS.
   In training it is computed out-of-fold and never includes the row itself.
Decision rule (initial values, tune only by CV on train, not yet validated):
score < 0.3 allow, 0.3-0.7 confirm, > 0.7 block, inconclusive block.

## 6. Data contract (records table)
id, family_id, user_request, source, injected_text (nullable), proposed_action,
reversibility, scope, privilege, label, reasoning, provenance, split, reviewed, created_at
- source: user_direct | file_content | web_content | tool_output | pr_content | agent_internal
- scope: single_file | single_folder | multi_file | single_process | system_wide
- label: safe | risky
- provenance: seed | nl2bash | nl2bash_mismatch | injection_dataset | generated | live_log
- split: train | heldout
Other tables: decisions, outcomes, runs.
Every record validates against src/rootguard/datagen/schema.py (Pydantic).
Reports always break results down by provenance (real-derived vs generated).

## 7. Data flow
alembic upgrade head          -> empty rootguard.db (4 tables)
seed_100.jsonl                -> records (provenance=seed)            [dev seed]
data/external/nl2bash         -> records (nl2bash, nl2bash_mismatch)  [dev import]
injection datasets            -> injected_text patterns only          [dev import]
Qwen variants of seeds        -> records (generated, parent's family_id/split) [dev generate]
records WHERE split='train'   -> model.pkl                            [dev train]
runtime / eval                -> decisions, outcomes, runs
Cloned datasets are raw input only. Training reads only from `records`.

## 8. External sources (clone into data/external/, never edit the raw files)
git clone https://github.com/TellinaTool/nl2bash.git data/external/nl2bash
  -> uses data/bash/all.nl and data/bash/all.cm (line i pairs with line i). Data: MIT.
git clone https://github.com/uiuc-kang-lab/InjecAgent.git data/external/InjecAgent
  -> uses data/user_cases.jsonl, attacker_cases_dh.jsonl, attacker_cases_ds.jsonl.
     Injected-text patterns only (no shell commands in it).
https://huggingface.co/datasets/prodnull/prompt-injection-repo-dataset
  -> GATED (HF login + accept terms, done manually by the author). apache-2.0.
     Injected-text patterns only. Save under data/external/prodnull/.
Optional, not yet inspected: https://huggingface.co/datasets/rogue-security/coding-agent-security-benchmark
  -> cc-by-nc-4.0. Inspect contents before importing anything.
Rules: write a license note per source into data/external/LICENSES.md. Do not import a
source whose files you have not opened and verified. External sources supply no risky
shell commands; risky shell rows come from seeds and generated variants only.

## 9. Code style
- Small pure functions, type hints, one responsibility per module, no global state,
  no clever abstractions, no deep inheritance.
- Config in one dataclass (config.py). Fixed random seed = 42.
- Every module ships with tests in tests/. Prefer table-driven tests.
- Errors are explicit; never swallow exceptions inside the decision path.

## 10. CLI rules
- Rich only in v1. No Textual unless the user approves.
- Commands contain no business logic: they call library functions. ui/ only renders.
- The daemon writes SQLite with WAL on. `watch` and `report` only read.
- `rootguard dev ...` holds pipeline commands; each phase adds its own dev subcommand.

## 11. Folder structure
```
rootguard/
├── AGENTS.md  pyproject.toml  .gitignore
├── docs/
│   ├── PHASES.md  STATUS.md  BLOCKERS.md
│   └── modules/  NN-<name>.md        # one implementation doc per phase
├── .agents/skills/ module-spec/ module-audit/ git-workflow/ phase-gate/
│                   import-external-datasets/ dataset-pipeline/ train-model/ sandbox-eval/
├── data/ external/  seeds/seed_100.jsonl  heldout/families.json  review/  rootguard.db
├── models/hf/
├── src/rootguard/
│   ├── config.py daemon.py tagging.py features.py categories.py authz.py
│   ├── cli/
│   │   ├── app.py  runtime.py
│   │   ├── commands/ init.py start.py stop.py watch.py report.py dev.py
│   │   └── ui/ console.py tables.py live.py prompts.py
│   ├── db/ (models.py, migrations/)
│   ├── importers/  datagen/ (schema.py, pipeline.py)  model/ (train.py, infer.py)
│   ├── enforce/ (seccomp.py, apparmor/)  integrations/ (claude_code_hook.py)
├── testbed/agent.py
├── sandbox/
├── eval/
└── tests/
```

## 12. Commands
uv sync | uv run pytest -q | uv run alembic upgrade head
uv run rootguard init|start|stop|watch|report
uv run rootguard dev seed|import|generate|train|eval
uv run python -m eval.run

## 13. Phase protocol (every phase, no exceptions)
1. Branch from up-to-date main (name in docs/PHASES.md).
2. module-spec skill: write docs/modules/NN-<name>.md, Status DRAFT. No code.
3. module-audit skill: audit the doc, append the audit report, Status AUDITED
   (or fix and re-audit until READY).
4. STOP. Print "AWAITING APPROVAL: NN-<name>". Do nothing until the user writes "APPROVED NN".
5. Implement exactly what the doc says. If you must deviate: edit the doc, Status
   returns to DRAFT, re-audit, re-approval.
6. phase-gate skill: run every gate item. Any FAIL: fix and rerun. No commit on a failing gate.
7. git-workflow skill: commit. Update docs/STATUS.md with real output. Module doc Status IMPLEMENTED.
8. STOP. Tell the user to open the PR (squash merge) and tag. Wait for "NEXT".

Stop and ask when: a gate fails twice, a VERIFY item cannot be resolved, a requirement is
ambiguous, a new dependency is needed, or anything touches heldout or frozen seeds.

## 14. Git workflow (trunk-based, solo)
- Default branch `main`. No `dev` branch. One short-lived branch per phase, one concern each.
- Branch prefixes: feature/ setup/ fix/ refactor/ hotfix/
- Commits: Conventional Commits. `type(scope): imperative subject`, <= 72 chars, no period.
  Types: feat fix refactor test docs chore build perf. Body explains why. Footer: `Refs: docs/modules/NN-name.md`.
- Commit only after the gate passes. Small, logical commits. Never commit a broken state.
- PRs into main, squash merge. The user merges and tags (`v0.N.0` after phase N). Agents never merge.
- Delete the branch after merge.