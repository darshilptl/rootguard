---
name: module-spec
description: Write the implementation document for a phase before any code, in docs/modules/
---
1. Read AGENTS.md, the phase entry in docs/PHASES.md, and earlier module docs it depends on.
2. Create docs/modules/NN-<name>.md (name from the phase entry), Status: DRAFT.
3. Write no code, tests, or migrations in this step.
4. Every unknown fact (version, flag, URL, package behavior) goes under VERIFY with the exact
   check you will run. Never fill in guessed values.
5. Copy the phase's Gate items verbatim into the Gate section.
6. Next step: run module-audit.

Template:
# Module NN: <name>
Status: DRAFT | AUDITED | APPROVED | IMPLEMENTED
Branch: <from PHASES.md>   Commit plan: <type(scope): subject>
## Purpose (2-3 sentences)
## Requirements covered (AGENTS.md rule numbers and PHASES.md Do items)
## Depends on (earlier modules and the interfaces consumed)
## Files to create or modify (paths only, all inside the folder map)
## Interfaces (function signatures with types, inputs, outputs)
## Data and DB changes (tables, columns, enums, exactly per AGENTS.md Section 6)
## Logic (numbered steps, including edge cases)
## Failure behavior (what blocks, what raises; fail-closed paths)
## Tests (test names and what each asserts; one or more per gate item)
## Gate (verbatim from PHASES.md)
## VERIFY (item | check to run | result, filled in later)
## Open questions
## Out of scope
## Audit report (filled by module-audit)