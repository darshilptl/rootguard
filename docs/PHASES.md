# Phases
Each phase follows the protocol in AGENTS.md Section 13: module doc, audit, approval, implement, gate, commit.

## Phase 0: Scaffold and environment
Module doc: docs/modules/00-scaffold.md | Branch: setup/project-init | Commit: chore(scaffold)
Do: uv project (if uv is missing, use venv + pip and record it in BLOCKERS), pyproject, folder skeleton with __init__.py, config.py (HF_HOME=./models/hf), cli/app.py (Typer root, `--version`, empty `dev` sub-app), smoke test.
Gate:
- [ ] `uv run pytest -q` smoke test passes
- [ ] `uv run rootguard --version` works
- [ ] `ollama list` shows qwen3:4b
- [ ] `aa-status` shows AppArmor enabled
- [ ] MiniLM loads from ./models/hf and embeds a sentence
- [ ] `import pyseccomp` works, or the failure is written to docs/BLOCKERS.md (not faked)
- [ ] `git status` clean after commit; .gitignore covers data/external, models/hf, *.db, model.pkl

## Phase 1: DB schema and migrations
Module doc: docs/modules/01-db-schema.md | Branch: feature/db-schema | Commit: feat(db)
Do: db/models.py (records, decisions, outcomes, runs), Alembic initial migration, enum constraints, WAL on connect.
Gate:
- [ ] `alembic upgrade head` succeeds on a fresh DB file
- [ ] insert/read round-trip test passes
- [ ] an invalid enum value is rejected
- [ ] `PRAGMA journal_mode` returns wal

## Phase 2: Command category classifier
Module doc: docs/modules/02-command-categories.md | Branch: feature/command-categories | Commit: feat(categories)
Do: categories.py, `classify(cmd) -> (reversibility, scope, privilege, unknown_flag)`, table-driven by utility and flags.
Gate:
- [ ] >= 40 table tests pass (rm file, rm -rf ~, ls, dd, chmod -R 777 /, export PATH=..., curl | bash, kill -9, pytest, tar)
- [ ] unknown commands are never classified as lowest risk (conservative default plus unknown_flag)

## Phase 3: Seeds and schema validator
Module doc: docs/modules/03-seeds-validator.md | Branch: feature/seeds-validator | Commit: feat(datagen)
Do: datagen/schema.py (Pydantic) and `dev seed`. seed_100.jsonl: 50 incident-derived (8 incident families), 50 benign tasks, >= 10 hard pairs (same command in a safe and a risky record). Start from the 20 reviewed examples supplied by the author; draft the rest from the incident families. Assign family_id. Freeze heldout family ids (~20%, stratified by label, seed 42) in data/heldout/families.json.
Human review of every seed row is mandatory. Freeze only after the user writes "SEEDS APPROVED".
Gate:
- [ ] 100/100 seeds validate
- [ ] counts per label, family, provenance printed
- [ ] families.json exists; its hash and the seed file hash are recorded in STATUS.md after approval

## Phase 4: External dataset importer
Module doc: docs/modules/04-external-importers.md | Branch: feature/external-importers | Commit: feat(importers)
Do: `dev import`. NL2Bash importer (label safe, source user_direct, categories via classifier). Capped mismatch negatives (provenance nl2bash_mismatch, <= 20% of risky). InjecAgent and prodnull importers extract injected_text patterns only, and only after the author has opened the files and the exact schema is recorded.
Gate:
- [ ] row counts per source printed, 0 schema failures
- [ ] data/external/LICENSES.md written
- [ ] split assignment deterministic (hash of id) and no heldout contamination

## Phase 5: Features
Module doc: docs/modules/05-features.md | Branch: feature/features-pipeline | Commit: feat(features)
Do: tagging.py, features.py (six features, embedding cache keyed by text hash, FAISS index over TRAIN only, out-of-fold nn_history).
Gate:
- [ ] same input gives identical features twice
- [ ] matrix shape (n, 6), no NaN
- [ ] nn_history excludes the row itself and heldout (test asserts this)

## Phase 6: Generator pipeline
Module doc: docs/modules/06-variant-generator.md | Branch: feature/variant-generator | Commit: feat(datagen)
Do: `dev generate`. For each seed ask qwen3:4b (thinking off, VERIFY the flag) for N reworded variants with the same meaning and label. Validate schema, dedupe, recompute categories and drop variants whose category differs from the parent. Variants inherit the parent's family_id and split. Export a 10% sample to data/review/spot_check.csv.
Gate:
- [ ] validity rate and drop reasons printed
- [ ] label balance within 40-60%
- [ ] test: no variant of a heldout family is in train
- [ ] spot_check.csv exists (manual review sets reviewed=true)

## Phase 7: Train and evaluate
Module doc: docs/modules/07-train-evaluate.md | Branch: feature/train-evaluate | Commit: feat(model)
Do: `dev train`. LightGBM, seed 42, GroupKFold by family_id on the train split, small grid, save model.pkl plus feature order. Baselines: majority class and similarity-only threshold. Evaluate heldout once and write to runs.
Gate:
- [ ] leakage test: zero family overlap between train and heldout
- [ ] heldout metrics (precision, recall, FPR, F1, confusion matrix) saved
- [ ] results also reported per provenance
- [ ] ablation vs similarity-only baseline reported honestly

## Phase 8: Daemon and staged authz
Module doc: docs/modules/08-daemon-authz.md | Branch: feature/daemon-authz | Commit: feat(daemon)
Do: daemon.py `POST /score`, authz.py (staged pure functions: scope, authorization, impact ceiling, repeat, default deny), reasons from per-feature contributions, every call writes a decisions row.
Gate:
- [ ] API tests pass
- [ ] malformed input returns block
- [ ] missing model.pkl returns block (fail closed)
- [ ] a decisions row exists for every call

## Phase 9: Testbed agent and integration
Module doc: docs/modules/09-testbed-integration.md | Branch: feature/testbed-integration | Commit: feat(testbed)
Do: testbed/agent.py: Ollama qwen3:4b tool-calling loop with a run_command tool routed through /score; modes undefended and defended; executes only inside sandbox/ as an unprivileged user.
Gate:
- [ ] mock-LLM scripted scenarios prove allow, confirm and block paths deterministically
- [ ] one live qwen3:4b run is logged end to end
- [ ] nothing executes outside sandbox/

## Phase 10: Kernel enforcement
Module doc: docs/modules/10-kernel-enforcement.md | Branch: feature/kernel-enforcement | Commit: feat(enforce)
Do: enforce/seccomp.py, enforce/apparmor/ profile; document what it blocks and what it does not.
Gate:
- [ ] a denied syscall fails inside the sandbox
- [ ] AppArmor profile loaded and visible in `aa-status`
- [ ] limitations section updated in docs

## Phase 11: Evaluation harness
Module doc: docs/modules/11-eval-harness.md | Branch: feature/eval-harness | Commit: feat(eval)
Do: `dev eval` and eval/run.py: attack patterns from the 8 incident families as synthetic sandbox cases; held-out variants; adaptive variants (attacker rewording to raise similarity); metrics: block rate, false-positive rate, task completion, RAM/CPU (psutil).
Gate:
- [ ] baseline (defense off) lets each attack through; a case the baseline blocks is flagged invalid
- [ ] defended results stored in runs
- [ ] report generated from the DB only

## Phase 12: CLI and report
Module doc: docs/modules/12-cli-report.md | Branch: feature/cli-report | Commit: feat(cli)
Do: cli/commands init (append marked section, never overwrite), start (detached daemon, pidfile), stop, watch (live Rich view reading decisions), report. ui/ render functions are pure.
Gate:
- [ ] init on a temp project with an existing CLAUDE.md preserves its content (diff test)
- [ ] start/stop lifecycle works
- [ ] watch render functions pass tests with fake rows
- [ ] report numbers equal direct DB queries