---
name: train-model
description: Compute the six features, train and evaluate the LightGBM risk model without leakage
---
Prerequisite: the module doc for this phase is APPROVED.
1. Load train-split records only. Compute the six features (nn_history out-of-fold).
2. Tune with GroupKFold by family_id on train only. Seed 42.
3. Train the LightGBM binary classifier. Save model.pkl and the feature order file.
4. Train the baselines: majority class and similarity-only threshold.
5. Evaluate on heldout exactly once. Write precision, recall, FPR, F1 and the confusion matrix
   to the runs table, plus a per-provenance breakdown.
6. Never tune on heldout. Report weak results as they are.