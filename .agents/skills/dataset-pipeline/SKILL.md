---
name: dataset-pipeline
description: Expand seed records into validated training variants using local qwen3:4b
---
Prerequisite: the module doc for this phase is APPROVED and the seeds are frozen.
1. Read data/seeds/seed_100.jsonl.
2. For each seed ask qwen3:4b (thinking off, VERIFY the flag) for N variants: different wording,
   filename and command, same meaning, same label.
3. Validate against datagen/schema.py. Drop invalid ones automatically.
4. Recompute categories from the new action; drop variants whose category differs from the parent.
5. Dedupe on normalized text. Variants inherit the parent's family_id and split.
6. Print validity rate, drop reasons, label balance, per-incident-family counts.
7. Export a 10% random sample to data/review/spot_check.csv for manual review.
8. Insert with provenance=generated, reviewed=false.