---
name: module-audit
description: Audit a module doc against AGENTS.md and PHASES.md before approval; list required changes
---
Inputs: the module doc, AGENTS.md, the phase entry in PHASES.md, earlier module docs.
Check each item and cite evidence (file and section):
A. Traceability: every Do item in PHASES.md appears in the doc; every Gate item is present verbatim.
B. Rules: no conflict with AGENTS.md hard rules 1-16 (list the rule numbers checked).
C. Contract: fields, enums, feature order and table names match AGENTS.md Sections 5-6 exactly.
D. Scope: no new dependency, table, feature, or file outside the folder map. Anything extra must be
   listed under Open questions for the user to decide.
E. Testability: each gate item maps to a named test or a command with expected output.
F. Failure behavior: fail-closed paths are stated for anything on the decision path.
G. Unknowns: each VERIFY item is resolved with evidence or marked open. No guessed facts.
H. Dependencies: interfaces consumed from earlier modules exist as defined in their docs.
Output, appended under "Audit report" in the module doc:
| ID | Check | PASS/FAIL | Evidence | Required change |
Verdict: READY FOR APPROVAL or NEEDS CHANGES. If NEEDS CHANGES: fix the doc, re-audit.
Any edit to the doc after an audit resets Status to DRAFT.
Then STOP and print "AWAITING APPROVAL: NN-<name>".
Limit: an audit by the same agent that wrote the doc is weak. If your harness supports a
fresh-context subagent, run the audit there. The user's approval is the real gate.