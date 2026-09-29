# Frozen one-shot pose robustness: protocol v3

The [final v3 plan](../../plan/research-plan.v3.md) and
[Decision 0004](../decisions/0004-frozen-one-shot-v3.md) govern the active December
study. The original prospectus and v1/v2 protocols, code and evidence remain
historical records. They are not permission to execute the new study. Independent
research governance applies; no advisor sign-off is required.

## Complete design and measured preparation

[`configs/protocol.v3.yaml`](../../configs/protocol.v3.yaml) specifies the complete
scientific design and starts as a **non-executable template**. It explicitly
contains `status: template` and `preparation: null`; validation of its syntax is
not a design freeze. Preparation must bind real, immutable auxiliary-container,
source-inventory, ordered-identity and fallback-evidence files, the fallback
value, generic encoder checkpoint and pinned upstream hashes. The resolved
protocol is written below the stable canonical `POSE_EMBED_ARTIFACT_ROOT` as
`study-v3/locks/protocol.v3.json`. The design/pilot lock binds its full canonical
hash, all eight role-specific manifests, the historical artifact-root registry,
and every cache/pilot implementation and dependency file, including the training
runner, sampler, objectives and clean retrieval evaluator. Missing files, changed
hashes, unresolved preparation, altered roles or changed identities fail closed.

Preparation is restricted to the authorized auxiliary source. The shared pickle
historically deserialized every annotation before auxiliary selection. This is
recorded as a packaging fact; it does not establish that novel pose bytes were
never deserialized. Preparation creates a verified auxiliary-only container
without exposing novel annotations to preprocessing, diagnostics or model code.
Scientific novel loading remains unavailable until the later final authorization
and dataset-level atomic opening pass. An earlier genuine novel representation
or outcome access blocks confirmatory execution across every protocol version.

All source identities and processing are retained: 113,945 usable captures plus
535 missing captures; 20 official novel anchors; 18,924 exact-official and 18,884
primary queries. Selection uses 76,013 rows from 80 actions. Final heads use
95,001 rows from all 100 auxiliary actions. The development episode retains its
20 galleries, 18,929 primary queries, and the historical
`protocol-v1|dev-anchor-v1|` anchor prefix. The official gallery order is fixed.
No subset contingency, reselected episode, or historical-cache relabeling exists.

## Fixed recipes and selection

Train a biased `Linear(8704, 2048)` and L2-normalize its output over a frozen,
evaluation-mode generic MotionBERT encoder. The head has 17,827,840 parameters,
zero dropout and float32 parameters/features. Physical batches contain eight
classes and four examples per class. Gradient accumulation cannot substitute.

| Recipe | Fixed settings |
| --- | --- |
| Contrastive | Positive/negative cosine margins 0.9/0.6 |
| Full contextual | `0.4 L_context + 0.6 L_contrast + 0.1 L_reg`; margins 0.75/0.6; neighborhood 4; epsilon 0.05; STE alpha 10; mean-similarity target 0.25 |
| SupCon | Single-view positive log-softmax; temperature 0.07; no extra temperature multiplier |

Context fits Equation 5's same-label target, includes self in neighborhood
selection, uses `max(2-2*cosine,0)`, detached kth thresholds and first-stage counts,
a non-detached reciprocal denominator clamped to at least one, and symmetric
output. The off-diagonal contextual squared error is divided by `n²`. Positive
and negative hinges use separate strictly-active means; empty sets contribute
zero. The regularizer includes the diagonal. These are transfer recipes, not
pose-tuned optima; the comparison does not isolate the contextual term.

Every scientific run lasts 20 epochs. AdamW uses betas `(0.9,0.999)`, epsilon
`1e-8`, no AMSGrad, and weight decay `1e-4` on weight and bias. No scheduler,
augmentation, clipping, early stopping or mixed precision is allowed. The
protocol pins Python 3.11, PyTorch 2.9.1 and NumPy 2.4.6; deterministic algorithms,
CUDA workspace configuration before CUDA initialization, and disabled TF32.
Paired seeds are exactly 7, 17 and 29. Ordered physical batch plans and initial
head states are paired across every arm/rate within a seed.

The [27 experiment configurations](../../configs/experiments/v3) span three arms,
three learning rates `{1e-4,3e-4,1e-3}` and three seeds. All three valid seeds are
required per eligible candidate. Rank unrounded epoch-20 clean development
mean top-1, then mean MRR, then lower learning rate. Retain every attempt and
failure; no seed replacement, favorable retry, two-seed mean or corrupted-score
selection is permitted. Nine fresh all-100-action heads follow selected-rate
locking. Multi-Similarity, the 26-method v2 roster, fine-tuning and the optional
regularizer control are outside this study.

## Engineering pilots

The immutable design lock specifies one 20-epoch pilot per arm, seed 7 and
learning rate `3e-4`, using all 76,013 development-training rows. Pilots cannot
enter learning-rate selection or the final run set. Retain epoch 5/10/15/20
weights and complete clean development scores, plus epoch-zero diagnostics.
Every update must have finite losses, gradients and parameters; projections
must be nonzero. At diagnostic epochs 0/5/10/15/20, maximum normalization error
is `1e-5` and full-query float64 variance must exceed `1e-6`. There is no real
accuracy floor. Fixed 32-row/eight-label fixtures must achieve 100% self-excluded
same-label nearest-neighbor retrieval in 1,000 updates for each arm.

## Corruption and analysis conventions

Only queries are corrupted after the complete deterministic preprocessing and
before the frozen encoder. Every family starts from its own clean tensor;
no post-corruption clipping, normalization, interpolation or frame deletion
occurs. Severity is excluded from the UTF-8 seed message
`protocol-v3\0<sample_id>\0<family>`. SHA-256's first eight bytes define unsigned
big-endian `u`; `u & (2**63-1)` seeds the generator.

- Jitter shares one CPU float32 Torch Gaussian x/y field across fractions
  0.01/0.025/0.05 of the clean lower-median positive finite torso scale. It
  affects only originally positive-confidence observations. Missing/padded
  observations and all confidence values stay unchanged.
- Joint masks shuffle the fixed five anatomical groups once with
  `random.Random(seed63)`, retain within-group order and zero prefixes of 3/6/8
  joints. Already absent joints are not replaced.
- Frame masks of length 10/25/40 start at `(u * (101-L)) // 2**64`; the intervals
  are nested and all people/joints/channels are zeroed within them.

Severity zero is a byte-identical copy. The fixed fallback torso scale is the
lower median of valid **sample-level** scales from the 80-action clean training
set only. Its complete contributing-ID/value/hash evidence is measured and
bound before design freeze. No valid positive fallback is a failed gate.

The primary effect averages contextual-minus-contrastive clean-to-corrupt top-1
degradation over fixed three seeds and nine cells, with query weighting within
each cell. Negative means less contextual degradation. Resample performance
groups `(setup,performer,repetition,action)` independently within each fixed
action, retaining every available view and sampled multiplicity. Reuse each draw
across all paired conditions, sum per-query effects and divide by sampled query
count; neither groups nor actions are forced equal weights. Use 10,000
`Generator(PCG64(2026))` replicates and 95% percentile quantiles with linear
interpolation. Never resample seeds or actions. Leave-one-action-out removes
that action's queries only, preserving all galleries and original ranks.

The interval is conditional on the fixed trained heads, seeds, actions,
anchors, queries and realized corruptions. Support the single confirmatory
claim only if its upper bound is below zero. Report clean and absolute corrupted
accuracy, all seeds/cells, fallback frequency, failures/cost and descriptive
sensitivity. SupCon and exact-official results are descriptive. A null or
negative result completes the scientific objective.

## Staged authorization and remaining calendar

The typed design gate is implemented for Week 3. The selection authorization,
180-cell evaluation plan, nine-run final set and final-lock schemas/templates
are declared now. They do not authorize execution by their existence. Selection
and novel execution remain fail closed until later independent evidence audits
implement and verify the complete measured cross-bindings. Those later campaign
authorizers are isolated from the frozen cache-producing interface; they must
bind unchanged design/code inputs and never weaken historical artifact checks.

1. Before fresh caches/pilots: resolve preparation; audit all historical roots;
   freeze complete design/pilot protocol and cache-affecting release.
2. October 5–11: fresh parity, two final-training extraction repeats, the three
   other clean caches, loss/backward/learnable fixtures, and three full pilots.
3. By October 18: all nine development corruption paths, analysis fixtures,
   complete pilot/capacity/seal evidence, allocation calendar and researcher
   availability. Append selection authorization against the unchanged protocol.
4. After clean selection and nine fresh final heads: selected configurations,
   complete checkpoint/attempt bindings and exact final matrix; independently
   audit before the researcher-controlled final lock and atomic dataset opening.

Storage uses `available >= 200*2**30 + 1.25*remaining_peak_bytes`, with available
space the smaller of filesystem and project-quota remainder. The initial
100-decimal-GB envelope already includes slack. Preserve every historical and
failed artifact; deleting evidence is not a storage remedy. Existing caches
establish historical feasibility only. No current document, template or passed
unit test asserts that GPU pilots, capacity or researcher availability exist.
