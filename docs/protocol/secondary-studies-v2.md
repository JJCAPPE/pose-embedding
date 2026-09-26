# Locked secondary studies for motion retrieval

Result-blind specification, 2026-09-26. These are **descriptive secondary
studies**, distinct from the main 26-method, six-seed comparison. Their exact
settings are in `configs/benchmark-secondary.v2.json`. Selection binds that
file's raw SHA-256; `secondary-plan.json` resolves every recipe from the main
selected candidate before secondary training begins. No secondary outcomes
choose another learning rate, stopping step, split, condition or claim rule.

## Scope and counts

| Study | Matrix | New training |
| --- | --- | --- |
| Official one-shot | 26 methods × 6 seeds, clean official 20-anchor task | None; main final checkpoints |
| Query corruption | 2 methods × 6 seeds × 10 conditions × 2 retrieval tasks | None; clean main final checkpoints |
| Loss components | 3 lambda settings × 2 gamma settings × 6 seeds | 36 development and 36 final |
| Training robustness | 4 methods × 10 conditions × 6 seeds | 240 development and 240 final |

The four robustness methods are pure contextual, Contrastive, Multi-Similarity,
and MS with its miner. Pure contextual means lambda=1 and gamma=0, with no
contrastive or mean-similarity regularization. The ten conditions are clean;
label noise at 5/10/20%; pose replacement at 5/10/20%; and retained training
class fractions 25/50/75%. The full class set is the clean control.

There are **276 secondary training runs per stage, 552 across development and
final**, plus the separate main selection campaign and 156 main final runs.
All **432 final training runs** must finish before novel opening. The current
implementation requires independent immutable evidence for every secondary
training slot; no approximate main-run reuse or identity relabeling is allowed.

One-shot and corruption matrices share 12 clean official-query controls.
Their combined unique result count is 384; adding the 276 secondary-checkpoint
novel results gives **660 unique secondary evaluations**. The report expands
coverage for the shared controls without treating them as additional models or
independent observations. Counts are plans, not completed experiments or GPU
runtime forecasts. `secondary-coverage` exposes these counts programmatically.

## Relation to the original paper

[Liao et al., Section 4.4 and Figure 6](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf)
separate random training labels, replacement training images, and reduced
training classes; their experiment uses pure contextual loss and k=8.
Figure 7 varies contextual/contrastive mixing and the similarity regularizer.
These motivate the finite motion studies below. Query-coordinate corruption
is a separate motion robustness question and is not a substitute for training
label noise. The full internal algorithm changes in Appendix Table 5 are not
claimed as implemented by this six-cell loss-component factorial.

The paper retunes learning rates for its robustness experiments. This motion
study fixes the selected main learning-rate scale and selected main optimizer
step count for the corresponding base method. Pure contextual inherits the
selected Contextual recipe, and all loss-component cells inherit that recipe.
No further secondary grid is searched. This is an explicit schedule adaptation;
ablated configurations need not have their individually optimal learning rate.

## Training-only interventions

Robustness uses physical **P=4, K=8, batch 32**, retaining the paper's k=8 within
the declared motion batch. Loss components use the main P=8/K=4.
Every study fine-tunes the common MotionBERT and retrieves a 512-dimensional
common-head embedding. The main selected optimizer rate scale and stopping
step are fixed for each method. Development validation remains the same clean
20-action multi-positive task. Its curves are descriptive: the checkpoint is
always the last inherited step, never a new secondary best-score choice.

Each stage uses only its verified training partition: 80 development actions
or all 100 auxiliary final-training actions. `secondary-data-plan.json`
records source/observed identities, true and observed action labels, subset
membership, changed indices, realized corruption fraction and parent-order
hash. It is regenerated during verification, not trusted because it exists.

* **Label noise:** select exactly floor(rate × number of training clips) from a
  seeded random ordering; assign a uniformly drawn other training action.
  Actual label changes are guaranteed. Sampling uses the resulting observed
  labels, so each physical batch still has four observed classes and eight
  items each. All methods share this altered-label plan and batch prefixes.
* **Pose replacement:** select the same number of training identities, then
  draw an input from another training action and underlying performance.
  Keep the original observed supervision and replace only its pose source.
  Sources are confined to the current training partition. This is a declared
  motion analogue of image replacement, not newly scraped unlabeled motion.
* **Reduced classes:** use a seeded nested ordering of available training
  actions, retaining 20/40/60 of the development 80 and 25/50/75 of the final
  100. Every clip of each retained action stays. Validation and novel action
  membership and relevance remain unchanged.

Affected clip sets are nested across noise rates. Per-identity replacement and
label draws are stable for shared selected identities. The intervention seed
is derived from the paired run seed and fixed study-purpose identifiers;
Python's and PyTorch's global random streams are not advanced. The altered
supervision is sample-based; synchronized camera views may receive different
noisy labels. This deliberate synthetic-noise convention is recorded rather
than described as naturally occurring annotation noise.

## Loss-component factorial

Lambda is 0, the selected Contextual value, or 1. Gamma is 0 or the selected
Contextual value. Other selected Contextual parameters, initialization,
physical batches and stopping step remain fixed. The six cells distinguish
contrastive-only, contextual-only, their mixture, and each with the similarity
regularizer. Every cell is visibly labeled secondary and cannot fill a main
method slot.

## Query-only corruption and official one-shot

Reuse the existing v1 deterministic corruptions after common preprocessing:
Gaussian x/y jitter at 0.01/0.025/0.05 of median torso length; limb-first
complete-joint trajectory masks of 3/6/8 joints; and consecutive frame blocks
of 10/25/40 frames. Add a clean control. Confidence/absent-token behavior and
stable per-sample seeds remain the v1 implementations. Only query inputs are
corrupted; each task's gallery remains clean.

Contextual and Contrastive are evaluated on two tasks. **Official** uses the
official query set and 20 clean anchors, retaining synchronized anchor-performance
views. **Primary** uses all novel clips as queries against the full clean novel
gallery, with the main evaluator's per-query self and synchronized-performance
exclusions and multi-positive R@K, AP/mAP, mAP@R and MRR. Corruption never changes
identities, positive labels or exclusion sets. The legacy filtered 20-anchor
one-shot task remains historical and is not this v2 primary task.

Report the tasks separately. Do not apply synchronized-performance exclusion
to official one-shot, because it can remove the only positive anchor. One-shot
mAP equals MRR. Primary multi-positive mAP does not.

All 26 one-shot methods use their actual inference scorer. DIML's structural
score and AVSL's scorer are dispatched through the shared descriptor interface;
ordinary cosine cannot silently substitute for a custom method.

## Locks, outputs and reports

Sequence: full main selection → secondary recipe lock → complete secondary
development lock → secondary final training/lock. Main final training can run
alongside these sealed stages. Both the complete 156-run main final lock and
276-run secondary final lock are required before the single novel opening.
All training/selection commands still reject any existing opening ledger.
Main selection and main final collection reject secondary run identities.

Example commands use the canonical main selection config and artifact root:

```bash
pose-embed benchmark secondary-coverage
pose-embed benchmark secondary-plan --config configs/benchmark.selection.v2.yaml
pose-embed benchmark train --config configs/benchmark.selection.v2.yaml \
  --method contextual --seed 7 --secondary-cell robustness-context_only-label_noise-0.05 \
  --manifest-set MANIFEST --parity-evidence PARITY --output-dir RUN
pose-embed benchmark secondary-lock --config configs/benchmark.selection.v2.yaml \
  --phase development --runs ALL_276_DEVELOPMENT_RUNS
# Repeat declared cells with --phase final, then secondary-lock --phase final.
pose-embed benchmark secondary-evaluate --config configs/benchmark.selection.v2.yaml \
  --run RUN --task one_shot --manifest-set MANIFEST --parity-evidence PARITY --output-dir EVAL
pose-embed benchmark secondary-report --config configs/benchmark.selection.v2.yaml \
  --manifest-set MANIFEST --results ALL_660_UNIQUE_RESULTS --output-dir REPORT
```

The evaluation binds run/checkpoint, selected plan, full locks, input/parity,
query/gallery identities, scoring policy and condition. Rank evidence remains
private in the artifact root; public reports contain aggregate means, sample
standard deviations, all six seed values and hashes. No secondary interval,
p-value or superiority claim is inferred from the primary multiplicity plan.
A complete descriptive report requires every declared result; missing cells
remain missing and prevent a complete report.

Synthetic tests establish implementation and seal behavior only. Allocated
profiling and all scientific execution remain separate work; this change
launches no experiment and establishes no performance result.
