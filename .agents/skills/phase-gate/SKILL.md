---
name: phase-gate
description: Run the current phase's gate checklist after implementation, report pass or fail, stop on failure
---
1. Read docs/STATUS.md for the current phase and its gate in docs/PHASES.md.
2. Run every gate item (tests, commands, counts). Capture real output.
3. Report each item as PASS or FAIL with evidence.
4. Any FAIL: stop, list failures, fix, rerun. Do not commit.
5. All PASS: update docs/STATUS.md (date, one-line result, hashes if applicable) and set the
   module doc Status to IMPLEMENTED, then run git-workflow.
6. Never mark a gate passed without running it.