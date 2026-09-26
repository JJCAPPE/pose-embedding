# Protocol v2: metric learning for human-motion retrieval

Status: **researcher-directed scope revision; implementation and final lock are
pending**. The machine-readable design and method identities are in
`configs/benchmark.v2.yaml` and `configs/benchmark-methods.v2.json`. This document
and `docs/decisions/0003-motion-retrieval-v2.md` supersede the v1 three-method
robustness question. The original prospectus, v1 protocol, input amendments,
completed work and run artifacts remain historical evidence.

## Question and sequence

Does the contextual similarity method improve motion retrieval relative to the
methods compared in its image-retrieval paper? Multi-Similarity (MS) and MS with
its miner are separate comparators, not names for the contextual method.

The first implementation and GPU priority is **Contextual versus its exact
contrastive component on development data**. Verify mathematics, gradients,
overfitting, pairing, real backward memory and runtime before broadening. This
engineering phase cannot open the novel test or establish a final scientific
claim. Its selection trials must be accounted for in the later equal-budget
ledger. A null or negative result is a valid outcome.

After that priority phase, implement every declared method, run the complete
selection campaign, retrain the entire final roster, and only then open the
novel test once. The v1 post-test MS stretch exception does not apply to v2.

## Required coverage and faithful adaptations

There are 26 configurations: Contrastive, Contextual, Triplet, MS, MS + miner,
Proxy Anchor, Proxy NCA, ROADMAP, NT-Xent, FastAP, SmoothAP, normalized softmax,
Proxy NCA++, SupCon, DRML, DIML, DiVA, IBC, S2SD, Proxy NCA + Metrix,
PA + Metrix, MS + Metrix, HIST, MHGL, PA + AVSL, and Contextual at 1,536 dimensions.
The registry is authoritative for stable identifiers, exact parameters, paper
sources, implementation status and blockers.

The main 512-dimensional table contains 24 configurations. PA + AVSL and
Contextual at 1,536 dimensions form a separate matched comparison. Do not rank
methods across dimensions as though embedding size were controlled. Preserve
method-specific architecture, local features, auxiliary supervision, mixing,
hierarchy and graph operations where required. A generic scalar loss is not an
implementation of an architecture method. Blocked methods stay visible and
prevent a claim of complete replication; scope changes require a recorded
result-blind amendment before test opening.

The paper reproduced selected loss baselines and quoted other published image
results. This project must generate its own motion results for every declared
configuration; image scores cannot fill missing motion rows. The change of
modality is an adaptation, and a single NTU dataset cannot establish superiority
across all motion datasets.

## Shared model, data and paired training

Use a common pretrained MotionBERT backbone and fine-tune it for the main study.
The current development-only configuration may use the frozen backend for a
supplementary plumbing pilot; it does not satisfy the main fine-tuning gate.
Loss-only methods share the same pooling, linear embedding head, normalization,
augmentation and optimizer conventions except for explicitly justified published
method parameters. Architecture methods disclose their required changes and
additional costs. Start from physical P=8, K=4 and measure a real backward pass
for all methods before freezing a common batch per comparison group. Gradient
accumulation does not create the neighborhood of a larger physical batch.

Use six paired seeds. Pair backbone initialization, head initialization within
each dimensionality group, training identities, physical batches and applicable
augmentations. Auxiliary parameters use deterministic recorded initialization.
Declare equal selection budgets and method-specific grids before comparing
results. Checkpoint selection, stopping, ties and operational retry rules must
be fixed on development data.

Preserve the verified usable NTU input inventory of 113,945 HRNet annotations
plus 535 official missing-skeleton exclusions and all adopted source/checkpoint
hashes. Preserve the 80 training / 20 development auxiliary action split and
separate official 20 novel actions. Train final models on all 100 auxiliary
classes after selection. Do not choose new classes after seeing novel results.

The existing deterministic input adapter, source verification and licensing
boundary remain applicable subject to explicit v2 compatibility checks. Frozen
8,704-value pre-head caches cannot substitute for raw model inputs in end-to-end
fine-tuning. Preserve them as supplementary frozen-pilot artifacts under their
original protocol and encoder hashes.

## Primary retrieval problem and metrics

The primary task is clean multi-positive retrieval among held-out action classes.
Freeze gallery/query construction using sample identifiers and performance groups
without viewing novel retrieval scores. Relevance means the same action class.
For each query exclude itself and every synchronized camera view of the same
underlying performance from eligible candidates. Each retained query must have at
least one relevant candidate. Bind candidate identities, relevance counts,
exclusion rules and deterministic tie handling in the final evaluation lock.

R@1 is primary. Report R@2, R@4, R@8, mAP and mAP@R, plus per-query evidence and
all six seeds. R@K is a hit among the first K eligible ranked candidates; AP uses
all eligible relevant items in its denominator. AP@R evaluates the first R
eligible candidates where R is the query's eligible relevant count. Freeze
query/class aggregation before selection. Add hand-calculated fixtures with
multiple positives, unequal relevant counts, self matches, synchronized views,
ties and an empty-eligibility failure. V1 one-positive fixtures cannot certify
these metrics.

The official one-shot protocol, frozen-encoder pilot, corruption curves and
contextual ablations are supplementary. Their settings and run matrices must be
declared before novel outcomes are viewed. One-shot mAP equals MRR; multi-positive
mAP does not. Report each task separately.

## Estimand and claims

Report mean R@1 and its six-seed variation for every configuration, then paired
Contextual-minus-comparator R@1 differences within dimensionality groups. The
priority comparison is Contextual versus Contrastive. Report MS and MS + miner
explicitly rather than treating either as an assumed winner.

The specified analysis is `configs/benchmark-analysis.v2.json`, whose raw SHA-256
is bound by selection, final-run and opening locks. Use 20,000 paired bootstrap
replicates with random seed 20260924: resample the six training seeds together
across methods, then resample underlying performance clusters within each of the
fixed 20 actions. Keep all synchronized query views together with their original
query weights; the eligible gallery remains fixed. Compute each replicate as a
query-weighted mean, followed by an equal mean over sampled training seeds.

Report raw 95% percentile intervals descriptively and Bonferroni simultaneous
95% intervals for the complete 24-comparison R@1 family (23 comparisons at 512
dimensions and the matched AVSL comparison at 1,536). A positive comparative
claim requires a simultaneous lower bound strictly above zero. Bootstrap
coverage is approximate and conditional on these fixed actions and gallery.
Secondary metrics receive means, sample standard deviations and every seed;
they do not authorize additional confirmatory claims. The final gate rejects
missing or changed analysis settings. Publish null/negative effects, failures
and resource costs as well as positive effects.

## Test seal, artifacts and failed runs

All 26 selected configurations and six seeds require **156 verified final runs**
before novel-test opening. Every selection decision and all training precede the
first novel outcome. The final lock must cross-bind protocol, method registry,
selected configurations, sources, complete evaluation manifests, code,
dependencies, initialization, physical batch plans, checkpoints and immutable
run records. Missing methods, unknown registry status, incomplete run coverage,
changed hashes or an unsealed statistical plan must fail closed.

Use a new v2 artifact namespace under `POSE_EMBED_ARTIFACT_ROOT`. Never overwrite
v1 locks, caches or results. Existing v1 commands and the historical 180-row
robustness matrix do not certify v2. Until the complete v2 final validator and
runner exist, final v2 evaluation remains unavailable. The development-only
priority runner cannot accept novel classes or bypass this gate.

Archive attempts before execution and outcomes afterward. Retry documented
operational failures only in a new directory with the same scientific settings;
record the cause. Scientific parameter changes return to development and require
an amendment before test opening. Never use the upstream loop that tests novel
classes each epoch. Licensed inputs, weights, caches and full artifacts remain
outside Git; only permitted manifests, hashes, configs and compact summaries are
committed.

## Existing work, governance and feasibility

Input verification, immutable class manifests, the SCC frozen-forward profile and
Week 3 software evidence are reusable foundations. They do not prove v2
fine-tuning feasibility, broad implementation parity, multi-positive correctness
or final results. The tracker preserves their historical completion and adds
separate uncompleted v2 gates.

Independent researcher governance applies. BU determination was confirmed by the
researcher on September 24; see `docs/compliance/computational-research-scope.md`.
Actual researcher hours remain unprovided, and no week is closed by this amendment.
The 14-week public schedule is a provisional horizon. Resource measurements must
include the 156 final runs, all selection trials, implementation work, evaluation
and storage. If the full scope exceeds that horizon, record a dated continuation
while preserving required coverage and the novel-test seal.
