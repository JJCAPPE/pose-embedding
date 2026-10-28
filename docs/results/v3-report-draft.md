# Robust human-motion retrieval from noisy pose sequences

Result-independent report draft, October 28, 2026. The methods below describe
the declared study; selection, final training and novel evaluation remain
pending. This document adds no experiment, analysis rule or execution
authorization. The [canonical plan](../../plan/research-plan.v3.md), its
[machine-readable counterpart](../../plan/research-plan.v3.json), the
[protocol](../protocol/protocol-v3.md) and the
[report template](../protocol/v3-report-template.md) control the study.

## Abstract

This study will test whether a full contextual metric-learning recipe reduces
the loss of one-shot action-retrieval accuracy when pose queries are corrupted,
relative to a standard contrastive recipe. The experiment will use NTU RGB+D
120 HRNet-derived 2D poses, a frozen generic MotionBERT encoder and an identical
trainable linear head for each recipe. Three paired seeds, physical batches of
eight actions with four examples each, and 20 training epochs will hold the
training budget fixed. Learning rates will be selected using clean,
class-disjoint development retrieval. Nine fresh final heads will then be
locked before one authorized novel-test opening. The clean gallery will contain
one official exemplar per novel action; query stress will comprise nested
coordinate jitter, joint masks and frame masks. The primary effect will compare
clean-to-corrupt top-1 degradation across nine fixed corruption conditions,
with a conditional performance-group bootstrap. Absolute corrupted accuracy
will be reported alongside degradation because a smaller drop can accompany
lower retrieval accuracy. Results are pending. The study will support claims
about these complete recipes under the declared synthetic stress mixture, with
supervised contrastive results reported descriptively.

## Research question and related work

The research question is whether the full contextual transfer recipe reduces
clean-to-corrupt one-shot top-1 degradation relative to the standard contrastive
recipe. One-shot retrieval here means ranking a fixed gallery containing one
clean example for each previously unseen action. Training uses auxiliary
actions; the final comparison uses separate novel actions.

Liao, Tsiligkaridis and Kulis define contextual similarity through within-batch
neighborhoods, including common neighbors and non-neighbors followed by
reciprocal-neighbor expansion. Their complete objective combines contextual
similarity, contrastive loss and a mean-similarity regularizer. Their robustness
experiments concern training-label or training-image perturbations and withheld
classes; they do not establish robustness to corrupted pose queries. This
study will transfer their objective to a different input and evaluation
setting. The coefficients and method-specific margins follow the paper's
appendix recipes, with the provenance and implementation conventions recorded
in the [local source notes](../protocol/contextual-v3-source-notes.md).
([Liao et al., ICML 2023, Sections 3, 4.4 and Appendices G/H.5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf))

MotionBERT provides a pretrained motion representation and reports experiments
that train task heads over a frozen encoder. Its pretraining already includes
pose masking and noise. The proposed experiment therefore asks about the
additional effect of head-training recipes on this representation. It cannot
attribute all robustness to the head objective or treat MotionBERT's published
accuracy as a target for the present protocol.
([Zhu et al., ICCV 2023, Sections 3.3 and 4.6](https://arxiv.org/html/2210.06551))

Supervised contrastive learning supplies a third, descriptive reference. The
declared implementation uses a single view per example and temperature 0.07;
these are study adaptations, not a reproduction of the original image-training
pipeline. ([Khosla et al., NeurIPS 2020](https://papers.nips.cc/paper_files/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf))

The paired design and complete search ledger address two further comparison
issues: results can vary with initialization and data sampling, and the search
budget affects which configuration wins. The study will retain all candidates,
failures and costs. These motivations do not establish that three seeds are
sufficient for population-wide conclusions or validate this study's exact
bootstrap assumption. The supporting evidence is summarized in the
[amendment source research](../protocol/upcoming-amendment-source-research-2026-10-09.md).
([Bouthillier et al., MLSys 2021](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf);
[Dodge et al., EMNLP 2019](https://aclanthology.org/D19-1224/))

## Data and fixed retrieval episodes

The adopted source contains 113,945 usable HRNet-derived pose annotations and
535 disjoint missing-skeleton exclusions, accounting for 114,480 nominal
captures. The model will consume 2D pose estimates and confidence values,
rather than NTU's raw 25-joint Kinect skeletons. Source hashes, ordered
identities, the missing list and upstream versions are bound by the protocol.
The [source audit](../protocol/ntu-input-source-research.md) records the input
provenance and the distinction between public split membership and the
authors' separately packaged one-shot file.

The official novel actions are 1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67,
73, 79, 85, 91, 97, 103, 109 and 115. Their 20 official gallery exemplars and
gallery order remain fixed. Development-validation actions are 2, 8, 14, 20,
26, 32, 38, 44, 50, 56, 62, 68, 74, 80, 86, 92, 98, 104, 110 and 116.
Selection training will use the remaining 80 auxiliary actions; final training
will use all 100 auxiliary actions. Exact exemplar IDs appear in the
[configuration](../../configs/protocol.v3.yaml), with ordered role manifests
bound in the resolved protocol.
([NTU official one-shot definition at the pinned source commit](https://github.com/shahroudy/NTURGB-D/blob/ac2ebc87e6e9777ea6bac67e65e53b325b903f74/README.md#evaluation-protocol-of-one-shot-action-recognition-on-ntu-rgbd-120))

| Role | Actions | Captures or queries |
| --- | ---: | ---: |
| Selection training | 80 | 76,013 |
| Development gallery | 20 | 20 |
| Development primary queries | 20 | 18,929 |
| Final auxiliary training | 100 | 95,001 |
| Novel gallery | 20 | 20 |
| Novel primary queries | 20 | 18,884 |
| Novel exact-official queries | 20 | 18,924 |

Primary queries exclude each gallery exemplar and every synchronized camera
view of its underlying performance. A performance is identified by setup,
performer, repetition and action; camera is deliberately absent from that key.
The exact-official secondary definition excludes only the exemplar itself.
Both ordered query lists are fixed from metadata, without assuming that every
performance has three views. The development episode retains its existing
anchors: within each action, the original rule minimizes
`SHA256("protocol-v1|dev-anchor-v1|" + sample_id)`. The historical prefix and
selected identities will remain unchanged.

Deterministic preprocessing will produce float32 tensors with shape
`[2 people, 100 frames, 17 joints, 3 channels]`, where the channels are x, y and
confidence. Processing applies camera normalization, person tracking,
COCO-to-H36M joint conversion, uniform temporal sampling, missing-person
padding and spatial normalization, in that order. A derived joint's confidence
is the minimum confidence of its source joints. Random movement is disabled.
This local confidence correction is explicit; encoder parity compares the
same local tensor on both paths and does not imply byte-identical upstream
confidence preprocessing.

## Models, pairing and selection

The generic pretrained MotionBERT encoder will remain frozen and in evaluation
mode. Pooling over time and people leaves 17 × 512 = 8,704 features. Each recipe
will train the same biased linear projection from 8,704 to 2,048 values,
followed by L2 normalization. The head has 17,827,840 trainable parameters and
zero dropout.

| Recipe | Declared objective and settings |
| --- | --- |
| Standard contrastive | Cosine-margin contrastive loss; positive margin 0.9, negative margin 0.6 |
| Full contextual | `0.4 L_context + 0.6 L_contrast + 0.1 L_reg`; positive/negative margins 0.75/0.6; neighborhood size 4; epsilon 0.05; straight-through comparison-gradient alpha 10; mean-similarity target 0.25 |
| SupCon | Single-view supervised positive log-softmax; temperature 0.07, without an additional temperature multiplier |

The contextual implementation will fit Equation 5's same-label target and use
`max(2 - 2*cosine, 0)` distances, including self in neighborhood selection.
The kth thresholds and first-stage counts are detached from differentiation.
The reciprocal-expansion denominator remains differentiable and is clamped to
at least one; the output is symmetric. Off-diagonal contextual squared error
is divided by the full batch size squared. Positive and negative contrastive
hinges use separate means over strictly active pairs, with empty sets
contributing zero. The regularizer includes diagonal similarities. These
conventions, including the prescribed heuristic backward rule, are fixed
before training. The comparison changes the positive margin and adds a
regularizer as well as contextual similarity, so any effect belongs to the
full recipe.

Each run will use exactly 20 epochs, float32 features and parameters, and
constant-rate AdamW with betas `(0.9, 0.999)`, epsilon `1e-8`, no AMSGrad and
weight decay `1e-4` on both weight and bias. There will be no augmentation,
scheduler, gradient clipping, mixed precision, early stopping or best-epoch
choice. The duration defines the comparison budget; it does not establish
convergence or pose-optimal hyperparameters.

Seeds 7, 17 and 29 will pair the default linear initialization and ordered
physical batch plans across recipes and learning-rate candidates. Each batch
contains eight actions and four examples per action. An epoch contains
`ceil(N/32)` balanced batches with shuffled queues and modular cycling; it
does not promise exactly one visit to every training example. Gradient
accumulation cannot replace the physical 32-example batch because contextual
neighborhoods depend on the examples present together.

Before selection, one seed-7, learning-rate-`3e-4` engineering pilot per recipe
must complete 20 epochs on all 76,013 development-training rows. These pilots
will supply wiring, numerical-health, replay and capacity evidence; they are
ineligible for model selection. Real-data accuracy has no acceptance floor.
Finite losses, gradients and parameters, nonzero projections, normalization
error at most `1e-5`, and full-query variance greater than `1e-6` remain required.
The constructed learnable fixture has its separate prescribed 100% retrieval
check after 1,000 updates.

Selection will comprise 27 fresh runs: three recipes × three learning rates
`{1e-4, 3e-4, 1e-3}` × three seeds. Within each recipe, eligible rates require
all three valid seeds and will rank by unrounded mean epoch-20 clean
development top-1, then mean reciprocal rank, then the lower rate. Corrupted
scores will not select a rate, recipe or duration. Every attempt and failure
will remain in the ledger; no replacement seeds or two-seed means are allowed.
After locking the selected rates, nine fresh heads will train on all 95,001
auxiliary rows. All nine epoch-20 checkpoints and their provenance must be
locked before novel opening. Pilot and selection heads cannot become final
heads.

## Query corruptions

Only queries will be corrupted, after complete deterministic preprocessing and
before the frozen encoder. Every family will start from the clean tensor; the
gallery will remain clean and families will not be composed. There will be no
post-corruption clipping, normalization, interpolation or frame deletion.

| Family | Three fixed severities | Shared realization within a query |
| --- | --- | --- |
| Coordinate jitter | 0.01, 0.025 and 0.05 times clean torso scale | One CPU float32 Gaussian x/y field, scaled at each severity; only originally positive-confidence observations change |
| Joint masking | 3, 6 and 8 joints | One shuffled order of five fixed anatomical groups; increasingly long joint prefixes have x/y/confidence zeroed across people and frames |
| Frame masking | 10, 25 and 40 frames | Nested intervals; all people, joints and channels are zeroed within each interval |

For each sample and family, SHA-256 will hash
`"protocol-v3\0" + sample_id + "\0" + family`. The first eight digest bytes,
interpreted unsigned and big-endian, define `u`; `u & (2**63 - 1)` supplies the
generator seed. Severity is absent from the message. For frame length `L`,
the start index is `(u * (101-L)) // 2**64`. Joint masks shuffle the fixed
groups once, preserve their internal order and do not substitute visible
joints for already absent ones. Jitter leaves confidence, missing observations
and padding unchanged. Severity zero must return a byte-identical clean copy.

Torso scale is the lower median positive finite distance between shoulder and
hip midpoints over clean observations with all four required confidences
positive. A query without a valid scale will use the previously measured,
training-only fallback `0.6601371765136719`, with its original contributing
identity/value evidence. The fallback will not be recomputed from development
validation, all-100-action training or novel data. Fixed-panel repeats and
full-query telemetry must verify the operators and record actual displacement,
newly masked observed support, undefined damage and fallback use. These checks
will not tune severity or remove difficult queries.

## Locked evaluation and analysis

Cosine retrieval will use fixed gallery order to resolve ties. Each result
cell will contain query-weighted top-1, mean reciprocal rank (MRR) and recall
at five (R@5). There is one relevant exemplar per query, so mean average
precision equals MRR and will not count as separate evidence. The complete
matrix contains 3 recipes × 3 seeds × 10 conditions × 2 query definitions =
180 cells. Ten conditions means clean plus nine corruptions.

For primary-query top-1 accuracy, define:

```text
drop(m, s, c) = clean_top1(m, s) - corrupt_top1(m, s, c)
Delta = (1/27) * sum over 3 seeds s and 9 corrupted cells c of
        [drop(contextual, s, c) - drop(contrastive, s, c)].
```

Negative Delta means that the full contextual recipe degraded less. Queries
have equal weight within each cell; the three seeds and nine corruption
conditions have equal weight. This fixed mixture does not estimate how often
those corruptions occur in practice.

The primary interval will use 10,000 paired bootstrap replicates from
`numpy.random.Generator(PCG64(2026))`. Within each fixed action, each replicate
will sample the original number of performance groups with replacement and
include all available camera views of each sampled group, with multiplicity.
One draw will apply to every recipe, seed and condition. The statistic will
sum per-query paired effects and divide by the sampled query count, preserving
unequal view counts rather than giving groups or actions equal weight. The
two-sided 95% percentile interval will use linear 0.025 and 0.975 quantiles;
seeds and actions will not be resampled.

The interval is conditional on the trained heads, three seeds, fixed actions,
anchors, query definitions and realized synthetic corruptions. It assumes
performance groups are exchangeable within each action. Repeated performances
from the same person may remain dependent. It supplies no population
uncertainty over arbitrary training seeds, actions, participants, anchors or
natural camera errors. This caveat will accompany the interval in the final
results, with metadata summaries of view counts and performer concentration.

The single confirmatory statement, smaller clean-to-corrupt top-1 degradation
under the declared mixture, will be supported only if the interval's upper
bound is below zero. An interval containing zero will be reported as
inconclusive, without an equivalence or no-effect claim. An interval wholly
above zero will favor greater contextual degradation. Clean accuracy and
absolute corrupted accuracy will appear beside the effect, with the identity:

```text
Delta = mean clean contextual accuracy - mean clean contrastive accuracy
      - (mean corrupted contextual accuracy - mean corrupted contrastive accuracy).
```

All differences will be reported in percentage points. One point corresponds
descriptively to ten correct retrievals per 1,000 queries; this is not a
practical-effect threshold. SupCon, exact-official queries, individual
corruption cells, all three seed effects and 20 leave-one-action-out effects
will remain descriptive. Leave-one-action-out analysis removes that action's
queries while retaining every gallery anchor and the original ranks. No
additional superiority test or post-opening extension is planned.

## Results pending

No final score, selected rate, interval or comparative conclusion is available
in this draft. The following entries will be filled only from the complete,
validated locked run set.

Top-1 accuracy is reported as a percentage; differences, drops and intervals
are reported in percentage points.

| Primary-query quantity | Contrastive | Full contextual | Contextual minus contrastive |
| --- | --- | --- | --- |
| Mean clean top-1 | Pending | Pending | Pending |
| Mean corrupted top-1 over nine conditions | Pending | Pending | Pending |
| Mean clean-to-corrupt drop | Pending | Pending | Pending Delta |
| Conditional 95% interval for Delta | Not applicable | Not applicable | Pending |

The final report will also contain the full selection ledger, all 180 result
cells, SupCon summaries, every seed and corruption curve, leave-one-action-out
effects, dependence/damage/fallback summaries, wall time, memory and retained
failures. The [existing report command](README.md#pose-embed-report-build)
defines the reproducible summary, primary-analysis, curves, error-analysis,
telemetry and failure artifacts. No synthetic rehearsal output or historical
pilot score will fill a final-result entry.

## Reproducibility, access and current status

The study binds source, dependencies, preprocessing, encoder checkpoint,
ordered manifests, initial states, batch plans, protocol and result provenance.
The declared software includes Python 3.11, PyTorch 2.9.1 and NumPy 2.4.6,
deterministic algorithms, CUDA workspace configuration before CUDA
initialization and disabled TF32. The report builder will revalidate the
complete 180-cell matrix and reconstruct retained ranks from the bound feature
artifacts before deriving metrics. Independent recertification must reproduce
the required summaries and figures.

The frozen execution source is `f101f0e9d9bd64275d2088deab1b0bdcfcc53620`.
[ADR0007](../decisions/0007-safe-validation-reuse-and-stage-capacity.md) permits
command-local reuse of completed numerical proofs with fresh content hashing,
while preserving independent recertification and dynamic checks.
[ADR0008](../decisions/0008-runtime-baseline.md) establishes exact repeatability
and pairing within a declared prospective runtime rather than equality with
all predecessor runtime-derived bytes.
[ADR0009](../decisions/0009-updated-kernel-baseline.md) authorizes a kernel
update to `4.18.0-553.177.1.el8_10.x86_64`, retaining actual Gold-6426Y hardware,
native AVX512, four numerical threads, the L40S target and the remaining
profile fields. Fresh initialization/geometry, GPU/cache, paired-pilot/replay,
corruption, timing, admission and capacity evidence is still required.

As of this October 28 draft, SCC jobs are on hold at the researcher's
instruction while additional space is pending. The October 25 execution
record documents the storage blocker; this draft makes no fresh capacity
measurement. Earlier CPU, GPU and five-cache acceptance remains valid for its
original inputs and is historical evidence for the new profile. It does not
admit the updated-kernel campaign. Selection, final training, novel opening
and Week 5 closure remain pending. Current operational evidence belongs in
the [existing execution record](../protocol/week-5-execution.md), rather than
being inferred from this narrative.

Before novel loading, the final lock must bind all nine heads, exact query and
gallery lists, evaluation plan and complete provenance. A single atomic
dataset-level opening event applies across protocol versions; training and
selection are prohibited afterwards. Historical aggregate loading deserialized
the shared annotation container before auxiliary selection. The historical
seal claim concerns absence of novel retrieval preprocessing, representations,
scores and outcome-informed tuning; it does not claim that novel pose bytes
were never deserialized. The auxiliary-only preparation and historical access
audit remain part of the required evidence.

Licensed inputs remain under `POSE_EMBED_DATA_ROOT`; checkpoints, caches,
predictions and full run records remain under `POSE_EMBED_ARTIFACT_ROOT`.
Only permitted code, configuration, manifests, hashes and compact summaries
will enter the public repository. The unlicensed contextual repository is
reference-only; its code cannot be copied or adapted. Permitted MotionBERT
compatibility code retains its upstream attribution and license notices.

## Limitations and permitted conclusions

The experiment compares full transfer recipes, so it cannot isolate contextual
neighborhoods from the different positive margin and regularizer. The fixed
20-epoch horizon and three-rate grid define a bounded search, not convergence
or a global optimum. The omitted regularizer-only control will remain omitted.
This frozen v3 study does not complete the historical 26-method fine-tuned v2
benchmark; that implementation and its evidence remain separate historical scope.

One dataset, one fixed split, one set of official anchors and three seeds
restrict the result's scope. The conditional interval does not account for all
these choices, and repeated-performer dependence may remain within the query
set. Neither a positive result nor a narrow interval establishes general
algorithm superiority.

The corruptions modify preprocessed tensors. They do not reproduce natural
camera occlusion, a changed pose estimator or frame recovery. MotionBERT was
already pretrained with masking/noise, so the result concerns an additional
head-recipe effect. Smaller degradation can also coexist with lower absolute
corrupted accuracy; both must inform interpretation.

A valid null or negative result will complete the scientific comparison just
as a positive result would. Failure to pass capacity or validity gates will
instead require an explicit blocked-study account. A prepared implementation
or report draft alone is not a completed empirical study.
