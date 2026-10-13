---
name: sandbox-eval
description: Run attack patterns against the undefended and defended testbed agent and compute metrics
---
Prerequisite: the module doc for this phase is APPROVED.
1. Build each attack pattern as synthetic files and commands inside sandbox/ only.
2. For every case run two modes: undefended (must let the attack through) and defended
   (must block or confirm). If undefended blocks, mark the case invalid and fix it.
3. Include held-out variants and adaptive variants (attacker rewording to raise similarity).
4. Record block rate, false-positive rate, task completion, RAM and CPU to the runs table.
5. Generate reports from the DB only. Never write numbers by hand.