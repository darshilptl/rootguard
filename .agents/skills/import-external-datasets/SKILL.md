---
name: import-external-datasets
description: Normalize cloned external datasets (NL2Bash, injection datasets) into the records schema with provenance
---
Prerequisite: the module doc for this phase is APPROVED.
1. Raw files stay in data/external/<name>/. Never edit them.
2. NL2Bash: read data/bash/all.nl and all.cm line by line (line i pairs with line i). Each pair
   becomes a record: source=user_direct, label=safe, provenance=nl2bash.
3. Derive reversibility/scope/privilege with categories.classify(). Never hand-label.
4. Mismatch negatives (provenance nl2bash_mismatch): pair a request with a command from a
   different row. Cap at 20% of risky records. Report them separately.
5. Injection datasets (InjecAgent, prodnull): open the files first and record the real schema in
   the module doc. Extract injected_text patterns only; they contain no shell commands.
6. Assign split by the families.json rules. Never touch heldout.
7. Print row counts per source, schema failures (must be 0), and write data/external/LICENSES.md.