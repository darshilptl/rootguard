# Status
| Phase | Module doc status | Gate result | Commit | Date |
|---|---|---|---|---|
| 0 | IMPLEMENTED (docs/modules/00-scaffold.md) | 7/7 PASS (see below) | chore(scaffold): add project skeleton, config and CLI entry | 2026-10-13 |
| 1-12 | not started | | | |
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
lightgbm==4.7.0, numpy==2.4.6, pandas==3.0.6, scikit-learn==1.9.1,
torch==2.14.1+cpu (CPU index). OS: Ubuntu 26.04.1 LTS.
