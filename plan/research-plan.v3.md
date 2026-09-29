# Final v3 plan: frozen one-shot pose robustness

Date: **2026-09-29**. Delivery: **2026-12-18**. Status: **final planning
decision; implementation and measured campaign gates remain to be completed**.
This document replaces the v3 draft. [Decision 0004](../docs/decisions/0004-frozen-one-shot-v3.md)
records the change of direction from v2. It does not constitute a final-test
lock, a completed experiment, or a change to the deployed tracker.

Following the [final prospectus](../docs/proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf),
the December study asks whether a **full contextual training recipe reduces
one-shot retrieval degradation relative to a standard contrastive recipe**
when only novel pose queries are corrupted. Use one dataset, a frozen generic
MotionBERT encoder, three required objectives, three paired seeds, a fixed
20-epoch budget, and nine synthetic corruption conditions. A null or negative
result completes the scientific objective.

## 1. Final decisions

| Item | Decision |
| --- | --- |
| Required methods | Contrastive, contextual, and single-view supervised contrastive (SupCon) |
| Confirmatory comparison | Full contextual recipe versus standard contrastive recipe |
| Representation | Frozen MotionBERT; biased linear 8,704-to-2,048 head; L2-normalized output |
| Physical batch | Eight classes, four examples per class; 32 examples; no accumulation substitute |
| Paired seeds | 7, 17, 29 |
| Duration | **20 epochs for every pilot, selection run, and final run** |
| Selection | Three learning rates per arm, each evaluated with all three seeds; clean development only |
| Required campaign | Three engineering pilots + 27 selection runs + nine fresh final heads |
| Novel evaluation | One clean gallery; clean plus nine corruptions; primary and exact-official queries; 180 result cells |
| Uncertainty | Conditional, within-action performance-cluster bootstrap; fixed seeds/actions/anchors |
| Optional control | **Omitted from this December study**, before any new pilot or selection score |
| Cache policy | Fresh v3-bound caches; historical caches and sidecars remain unchanged |

Fixing 20 epochs removes the draft's adaptive plateau rule, including its
failure to distinguish a plateau from a decline. The pilots measure the whole
declared duration. Their learning curves are reported as fixed-budget
diagnostics; this plan does not claim that 20 epochs establishes convergence.
If the 20-epoch campaign does not fit, stop for a documented, result-blind
amendment before selection. There is no automatic reduction to ten epochs.

The regularizer-only control is omitted to bound implementation, storage, and
researcher work. Its omission is a scope/capacity decision, not a negative
experimental result. Do not add it after viewing scores. The 26-method v2
benchmark, encoder fine-tuning, Multi-Similarity, extra datasets, alternative
batch sizes, and real pose-estimator shifts are future studies. Preserve their
existing code and evidence; do not describe this study as completing v2.

## 2. Evidence and integration base

The local checkout inspected for this plan is `c60c0fe` with existing
uncommitted Week 3 and v3 work. Remote `main`, independently checked on
September 29, is `47ca528a99048278693e28019f52d8e924d7e270`. Implement v3 in a
clean worktree based on that commit or a reviewed successor. Do not reset,
merge over, or copy the dirty local tree wholesale. Reconcile useful local
changes against already committed Week 3 work individually.

The committed [Week 3 execution record](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/week-3-scc-execution.md)
and [compact evidence](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/week-3-scc-evidence.json)
establish two byte-identical 95,001-row clean frozen extractions on an L40S:
1,758.60 and 1,765.83 seconds, 3,315,915,790 bytes each. Development caches
contain 76,013 training rows, 20 gallery rows, and 18,929 primary query rows.
This establishes the clean extraction path, not head-training or corruption
runtime. The v2 fine-tuning forecast is not a v3 runtime estimate.

A fresh, read-only inspection through the authorized `remote` tmux session
observed the following; no GPU job or dataset inference was launched:

| Observation | Evidence at inspection time |
| --- | --- |
| Project quota, 2026-09-29 17:22:14 UTC | `/projectnb/textconv`: 18,527.20 / 18,800 GB used; **272.80 GB free**, conservatively interpreting displayed GB as decimal |
| Filesystem space, 17:26:02 UTC | 399,452,930,048 bytes free; project quota is the tighter limit |
| Required reserve | **200 GiB = 214,748,364,800 bytes** |
| Space above reserve | **58,051,635,200 bytes**, approximately 54.06 GiB |
| Scheduler | No jobs listed for the researcher by `qstat`; this is not a reserved allocation |
| Opening records | No opening ledger found in the active project artifact tree or historical home artifact tree; canonical v1/v2 lock directories absent; bounded release/repository-artifact scan also found none |
| Local records | No opening ledger found in the existing artifact directories of the inspected Git worktrees |

These are time-specific observations. Before pilots, selection, and opening,
repeat the audit against a registered list of every historical local/remote
artifact root and release. An unreadable or unresolved root blocks the seal
gate. Absence in the inspected locations is not proof about an unknown copy.

**Seal terminology:** the current aggregate loader deserializes and validates
all annotations in the shared pickle before selecting auxiliary examples.
Historical evidence therefore supports no novel preprocessing for retrieval,
embedding, visualization, scoring, or tuning access; it cannot establish that
novel pose bytes were never deserialized. Record this packaging fact in the v3
decision. No novel poses or outcomes were read by this planning inspection.
For the new final extraction path, authorization and atomic opening must occur
before the call that deserializes novel inputs. Auxiliary container preparation
must be documented separately and must expose only authorized auxiliary IDs to
preprocessing, diagnostics, or model code. If the historical audit discovers
actual novel representations, scores, or outcome-informed decisions, halt:
a fresh namespace cannot restore a sealed confirmatory test.

## 3. Dataset and fixed episode

Retain the adopted source contract: 113,945 usable HRNet annotations and 535
disjoint official missing-skeleton exclusions reconcile to 114,480 nominal
captures. Bind the exact aggregate, missing list, source inventory, pinned
NTU protocol, checkpoint, and upstream hashes. The original adopted input
protocol hash is
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
It remains historical provenance, not authorization to execute v3.

- Novel actions: `1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85,
  91, 97, 103, 109, 115`; retain all 20 official exemplars exactly.
- Development-validation actions: `2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62,
  68, 74, 80, 86, 92, 98, 104, 110, 116`.
- Selection training uses the other 80 auxiliary actions. Final training uses
  all 100 auxiliary actions. There is no training-subset contingency.
- Preserve the validated development anchor/query **identities**. Its original
  anchor rule minimizes `SHA256("protocol-v1|dev-anchor-v1|" + sample_id)`
  within each action. Do not change that prefix to obtain new v3 anchors.
  The historical episode hash is
  `88f30f96e35dedfd34b42f8e8ee2b561db44bbaf1f93d82d0522ffe011abba46`.
  Generate v3-bound manifests with the same ordered IDs and exclusion rule;
  retain the original episode and hash as provenance.
- Primary queries exclude the gallery sample and **all synchronized views of
  its underlying performance**, keyed by setup, performer, repetition, action.
  The exact-official secondary set excludes the exemplar itself only.
  Derive and lock both exact lists/counts from metadata before opening.

The [existing manifest audit](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/ntu-manifest-audit.v2.md)
records 18,944 usable novel rows, **18,924
exact-official queries**, and **18,884 primary queries**. Verify these counts
and exact ordered IDs against the bound manifests; do not reconstruct the
primary set by assuming three views per performance. Keep the gallery order
fixed for deterministic cosine ties.

Use the adopted deterministic `[2 people, 100 frames, 17 H36M joints, 3 channels]`
float32 tensor: camera normalization, tracking, COCO-to-H36M conversion,
uniform temporal sampling, missing-person padding, then spatial normalization.
Derived-joint confidence is the minimum source confidence. Random movement is
off. Preserve the declared local confidence correction; do not claim upstream
confidence preprocessing is byte-identical. Encoder parity uses the same local
input tensor on both paths.

## 4. Fixed model, recipes, and training

The generic pretrained MotionBERT checkpoint remains frozen and in evaluation
mode. Pool its representation over time and people, retaining 17 × 512 =
8,704 pre-head values. Train a biased `Linear(8704, 2048)` followed by L2
normalization: **17,827,840 trainable parameters**. Dropout is zero.

| Parameter | Contrastive | Contextual | SupCon |
| --- | --- | --- | --- |
| Loss | Standard cosine-margin contrastive | `0.4 L_context + 0.6 L_contrast + 0.1 L_reg` | Single-view supervised positive log-softmax |
| Positive / negative margins | 0.9 / 0.6 | 0.75 / 0.6 | Not applicable |
| Context neighborhood / epsilon / STE alpha | Not applicable | 4 / 0.05 / 10 | Not applicable |
| Target mean similarity | Not applicable | 0.25 | Not applicable |
| Temperature | Not applicable | Not applicable | 0.07; no additional temperature multiplier |

These are **fixed transfer recipes**, not starting settings to adjust after
diagnostics. The contextual coefficients and different contrastive-only
positive margin follow [Liao et al., Appendices G and H.5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
Batch 32, dimension 2,048, and 20 epochs are pose-study adaptations. The source
image results do not validate these as pose optima. SupCon's single-view
temperature-0.07 implementation is also an adaptation of the
[original method](https://papers.nips.cc/paper_files/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf).
Neither comparison isolates the contextual term from margins and regularization.

Lock the numerical implementation before pilots:

- Context fits **Equation 5's same-label target `y`**, resolving the conflicting
  printed Algorithm 1. Normalize embeddings; use squared distance
  `max(2 - 2*cosine, 0)` and include self in neighbor selection.
- Retain detached kth-distance thresholds and first-stage neighbor/non-neighbor
  counts, the prescribed constant-alpha comparison backward, reciprocal
  expansion with its **non-detached denominator**, and symmetric output.
  Average the off-diagonal contextual squared error over all `n²` entries.
- Average positive and negative contrastive hinges separately over strictly
  active pairs. Empty active sets contribute zero. The mean-similarity
  regularizer includes the diagonal. Explicitly specify the existing
  denominator clamp to at least one for empty complements as a finite local
  convention, and test degenerate/tied neighborhoods.
- Derive independent hand-calculated labeled forward **and backward** fixtures
  from the paper. Do not use an implementation mirroring production as the
  sole oracle. Ordinary finite-difference checks cannot validate an
  intentionally heuristic discontinuous comparison gradient.
- The unlicensed contextual repository remains reference-only. Do not copy,
  adapt, vendor, or redistribute its code. Preserve permitted MotionBERT
  compatibility-port headers, attribution, and license files.

All arms use float32 features/parameters and constant-rate AdamW:
`betas=(0.9, 0.999)`, `eps=1e-8`, `amsgrad=False`, weight decay `1e-4` on
weight **and bias**; no scheduler, mixed precision, clipping, or augmentation.
Pin the PyTorch implementation/runtime and deterministic settings, including
CUDA configuration before any CUDA initialization. Use PyTorch linear default
initialization under each paired seed and archive its state hash.

Retain the physical `P=8, K=4` sampler. An epoch is `ceil(N/32)` batches;
epoch randomness is derived from seed plus epoch, with class/example queues
shuffled at the epoch start and modular cycling within the epoch. It is a
balanced sampling budget, not a promise that every sample is visited once.
Persist the exact ordered batch plan. Pair it and the initial head state
across arms and learning-rate candidates within a seed.

### Engineering pilots and health criteria

Before fresh parity/cache generation and the first scientific pilot, freeze
the **complete canonical v3 protocol**: recipes, numerical conventions, fixed
duration/grid, exact identities, corruption/analysis semantics, and fallback
value/evidence binding. Calculate that fallback from authorized auxiliary
poses during preparation. Freeze the pilot specification against this same
protocol hash with 20 epochs, seed 7, and learning rate `3e-4`.
Run one pilot for each arm on the full 76,013-row development
training set. Save immutable weight snapshots and complete clean development
scores at epochs **5, 10, 15, 20**, plus epoch-zero diagnostics. Pilots are
explicitly ineligible for learning-rate selection, even where settings match
a candidate. Final selection runs are fresh attempts.

Required wiring checks use a fixed constructed 32-row, eight-label learnable
fixture, paired initialization, and physical batches. In 1,000 updates at the
pilot optimizer settings, each arm must remain finite and reach 100%
self-excluded same-label nearest-neighbor retrieval. This checks memorization
of a deliberately learnable fixture; there is **no required accuracy floor on
real development data**.

On real pilots require finite losses, gradients, and updated parameters at
every step, the exact prescribed update count, and nonzero projected vectors.
At epochs 0/5/10/15/20, require normalized-vector error at most `1e-5` and
`mean_q ||z_q - mean(z)||² > 1e-6` on the complete development query set,
summarized in float64. This screens total numerical collapse; it does not
establish a useful representation or justify tuning. Zero individual
gradients from inactive terms are allowed.

Archive loss-component magnitudes, active positive/negative hinge fractions,
neighborhood and reciprocal counts, empty-complement counts, gradient norms,
embedding variance, cosine quantiles, and actual timing/memory/checkpoint
bytes. Use fixed diagnostic sampling points, including the first batch and
each epoch boundary. Poor accuracy, continued learning, or overfitting curves
are reportable findings, not permission to change recipes or pick an epoch.
A nonfinite/collapse or mathematical failure blocks selection until corrected
under the amendment policy.

### Selection and final training

Run `3 arms × {1e-4, 3e-4, 1e-3} × {7,17,29} = 27` development runs at
20 epochs. Rank candidates separately within each arm by **mean epoch-20
clean development top-1 across all three seeds**; exact ties prefer mean
MRR, then the lower learning rate. Use unrounded metric values for ranking.
There is no best-epoch selection, early stopping, or corrupted-score selection.

A candidate needs three valid seeds. An unresolved numerical failure makes
that candidate ineligible; a two-seed mean cannot compete. Finish the
declared attempt matrix and retain all failures. If an arm has no valid
candidate, stop for a result-blind amendment. Report any unequal number of
eligible candidates; all arms retain the same attempted selection budget.

Lock the three selected configurations, selection evidence, and timestamp.
Train nine **fresh** heads on all 95,001 auxiliary rows, at 20 epochs, with
the selected rates and the three paired seeds. Retain the epoch-20 checkpoint;
do not choose a checkpoint using novel data. Do not reuse a pilot/development
head as a final head.

An infrastructure retry uses the identical configuration, seed, initialization,
and batch plan in a new attempt directory, from scratch. No resumable optimizer
state or v2 segmentation framework is required for v3. Verify complete runs
fit an allocation before selection. Preserve every attempt, including failed
or partial output. A verified implementation defect requires a dated
result-blind correction and rerunning every affected comparison, not only the
unfavorable arm. Parameter changes require a new declared protocol/grid.

## 5. Nested corruptions

Corrupt **only queries**, after the complete deterministic preprocessing above
and before the frozen encoder. Each family starts from the clean tensor;
families are never composed. The gallery stays clean. No deletion of frames,
interpolation, extra normalization, or clipping follows corruption.

Hash UTF-8 `"protocol-v3\0" + sample_id + "\0" + family` with SHA-256.
Let `u` be the unsigned big-endian integer from the first eight digest bytes,
and `seed63 = u & (2**63 - 1)`. Family names are
`coordinate_jitter`, `joint_mask`, `frame_mask`. **Severity is excluded**.
Pin generator/runtime versions and archive corruption-spec and output hashes.

| Family | Exact operator |
| --- | --- |
| Jitter | Draw one CPU float32 Gaussian x/y field per sample with a Torch generator seeded by `seed63`. Multiply the same field by `0.01`, `0.025`, or `0.05` times its clean torso scale. Add only where original confidence is positive; leave confidence and all missing/padded observations unchanged. |
| Joint masks | Shuffle the existing ordered groups `[(11,12,13),(14,15,16),(1,2,3),(4,5,6),(0,7,8,9,10)]` once using pinned Python `random.Random(seed63)`. Concatenate groups, retaining within-group order; take the first 3, 6, or 8 joints. Zero all their x/y/confidence values across people and time. Do not replace already absent joints with visible ones. |
| Frame masks | For length `L` in `{10,25,40}`, set `start = (u * (101-L)) // 2**64`. Zero `[start,start+L)` across people/joints/channels. These intervals are nested and each length has an approximately uniform marginal start position. |

Severity zero returns a byte-identical copy without needing a torso scale.
For jitter use the lower median positive finite distance between shoulder
midpoint (joints 11/14) and hip midpoint (4/1), over clean person/frame
observations whose four confidences are positive. When a sample has no valid
own scale, use one fixed fallback: the lower median of valid **sample-level**
scales from the 80-action clean development-training set. Calculate it once,
record the contributing IDs/count/hash and value, and freeze it before pilots.
Do not recompute it from validation, all-100 final training, or novel queries.
If no positive training fallback exists, the preselection gate fails.

Geometry audits use a fixed development panel selected before viewing scores.
Verify unchanged shapes, exact mask counts and nesting, one shared jitter
field, severity-zero identity, missingness preservation, boundary frames,
two-person behavior, own-scale failure/fallback, and deterministic repeats in
fresh processes. Record nominal damage and newly masked previously observed
joint-frame/person observations, including zero-effective-damage cases.
Report fallback frequency; never drop a troublesome novel query or redraw its
corruption. A nonfinite source/artifact defect stops the relevant gate rather
than silently excluding a sample.

By October 18, run all nine full-size development query corruption paths and
retain their artifacts. Time one full-size pass per family at maximum severity
end to end, including source verification, preprocessing, encoder, serialization,
projection of the three pilot heads, and complete retrieval. The other cells
verify complete identities, invariants, and deterministic outputs. Corrupted
development scores may be logged as evaluator evidence but cannot select
recipes, severities, learning rates, or duration.

These are post-preprocessing tensor stress tests, not actual camera occlusion,
frame recovery, or a new pose estimator. The experiment measures incremental
head-objective effects on an encoder already pretrained with pose masking/noise.

## 6. Locked analysis

Use cosine retrieval and query-weighted top-1, MRR, and R@5, with a fixed
gallery ordering for score ties. With one relevant exemplar, mAP equals MRR;
do not present it as independent evidence. Report every method, seed,
clean/corrupted cell, and both query definitions.

For the primary query set define

```text
drop(m,s,c) = clean_top1(m,s) - corrupt_top1(m,s,c)
Delta = mean over 3 seeds and 9 cells of
        [drop(contextual,s,c) - drop(contrastive,s,c)].
```

Negative Delta means less degradation for the contextual recipe. Queries have
equal weight within each cell; seeds and the nine cells each have equal weight.
The nine-cell mixture is a prespecified synthetic stress mixture, not an
estimate of real-world corruption prevalence.

Freeze the following analysis before selection and rehash it at opening:

1. Compute a per-query effect by averaging the paired correctness-drop
   difference over the fixed three seeds and nine cells.
2. Group queries by `(setup, performer, repetition, action)`. Sort actions,
   group keys, and sample IDs deterministically. In each bootstrap replicate,
   independently within each of the 20 fixed actions, sample its original
   number of groups with replacement. Include every available camera view of
   a sampled group, with multiplicity.
3. Apply that **same draw** to every seed, method, clean/corrupted condition,
   and cell. Divide the summed per-query effects by the sampled number of
   queries. Do not average group means equally: groups can have unequal
   view counts. Do not force equal action weights.
4. Use 10,000 replicates from `numpy.random.Generator(PCG64(2026))` and a
   two-sided 95% percentile interval, quantiles 0.025/0.975 with
   `method="linear"`. **Do not resample seeds or actions.**
5. Also report all three seed effects, all nine cell effects/curves, and all
   20 leave-one-action-out effects. For the last, remove that action's query
   observations only; retain all 20 gallery anchors and the original ranks.
   Report the range and sign changes descriptively, without new tests.

This interval is conditional on the trained heads, three seeds, official
actions/anchors, query definitions, and realized synthetic corruptions. Its
resampling assumption is exchangeability of performance groups within a fixed
action. It does not provide uncertainty over arbitrary seeds, actions,
participants, anchors, or real camera errors; repeated performances from a
person may still be dependent. Ten thousand replicates do not create more
independent training seeds.

Support the one confirmatory statement, **smaller clean-to-corrupt top-1
degradation under the declared mixture**, only if the interval's upper bound
is below zero. Otherwise report a null or contrary result. Always accompany
it with clean accuracy, absolute corrupted accuracy, and the descriptive
contextual-minus-contrastive corrupted accuracy difference. A smaller drop
does not establish better corrupted retrieval. SupCon, exact-official queries,
per-cell differences, seed variation, and sensitivities are descriptive:
no additional superiority tests, cherry-picked winning cells, or causal
attribution uniquely to contextual neighborhoods.

## 7. Concrete architecture work

The committed architecture already retains the frozen pipeline next to the
separate v2 benchmark. Extend that path rather than route this study through
v2 fine-tuning. These are required changes, not claims that the current CLI
already supports v3.

| Work package | Existing modules and concrete change | Acceptance check |
| --- | --- | --- |
| A. Version and validate v3 | Add `configs/protocol.v3.yaml`, v3 evaluation/lock/run-set templates, experiment configs, and a v3 tracker plan. Update `config.py`, `protocol.py`, CLI dispatch, `AGENTS.md`, and public protocol bundle using explicit v3 validation. Current v1 literals/shared-margin/six-grid checks cannot accept this plan. Keep v1/v2 scientific settings unchanged. | Valid v3 accepted; changed margins, seeds, duration, grids, IDs, roles, missing locks, and cross-version artifacts rejected; historical suites still pass. |
| B. Authorize the dataset once | Extend shared seal checks across legacy training/extraction, `benchmark/runtime.py`, v2 locks, and v3 entrypoints. Register historical roots. Keep one canonical artifact root; put v3 below `study-v3/`, not in a replacement environment root. Add an immutable dataset-level opening record shared across versions. | Existing v1/v2 opening blocks v3; v3 opening blocks old training/selection commands; unknown roots fail closed; concurrent first opens cannot create inconsistent authorizations. |
| C. Complete pilot/training path | Extend `training/runner.py` with an explicit engineering stage, epoch snapshots, full clean development scoring, deterministic CUDA initialization, health diagnostics, and timing; update strict manifest validators together. Reuse `models/action_head.py` and `training/sampler.py`. | Exact pilot and sweep update counts, paired init/batch hashes, pilot exclusion from selection, finite/overfit checks, and three-seed failure/tie handling. |
| D. Extend frozen extraction | In `motionbert_inputs.py`, `motionbert_features.py`, `features.py`, `artifacts.py`, and CLI, add authorized v3 development-corruption and novel roles/conditions. Separate metadata/hash verification from annotation loading. Add corruption implementation and fallback evidence to cache provenance; current clean-only code digests omit the operator. Reuse pooling/encoder and exact source identities. | Wrong role/condition/split fails; no novel loader call before atomic authorization; all conditions/IDs pair across heads; fixture outputs remain scientifically forbidden. |
| E. Corruption/analysis/report | Version the operators in `corruptions/pose.py`; add fixed fallback evidence. Add a v3 engineering-evaluation mode for declared corrupted development cells, explicitly ineligible for selection; retain the clean-only selection evaluator. Extend `evaluation/analysis.py` from globally pooled groups to within-action resampling. Update runner/report schema and completeness verification for v3. | Hand-ranked fixtures, unequal-view cluster weights, fixed-seed bootstrap, LOAO with fixed gallery, 180 unique authorized rows, and figures reproducing from ranks. |
| F. SCC and tracker | Add a v3 Grid Engine launcher with clean-release checks, external logs, quotas, immutable attempts, and complete measured timing. Add a guarded tracker migration plus matching app fallback/protocol deployment after the scientific bundle is settled. | Job exits/logs bound; no login-node compute; tracker preserves live versions/progress/RLS/ownership; public loaders expose only safe plan/progress fields. |

Finish and commit the extractor, preprocessing, corruption operators, config,
dependency, and artifact validation interfaces **before fresh scientific cache
creation**. Current
cache provenance binds those code paths and the dependency lock; a later
correction may require fresh parity/extraction. Do not weaken a digest check
to keep using an invalidated cache. The October 18 gate adds evidence and
selection authorization against the **unchanged protocol digest**; it does not
edit the protocol under existing pilot artifacts. A correction to that digest
or cache-affecting code requires regenerating affected caches and rerunning
affected pilots before the gate passes. Schedule this work and retain
superseded artifacts in the capacity ledger.

Fresh v3 auxiliary caches are chosen over a cross-protocol adoption wrapper.
Regenerate matching v3-bound manifests without changing sample identities;
run encoder parity and two fresh-process final-training extractions on the
same GPU. Retain both for repeatability, plus development train/gallery/query
caches. Bind the original source/checkpoint hashes in the new sidecars.

For final evaluation, encode the union of eligible novel queries **once per
condition**, then write **two immutable role-specific pre-head cache files**
from those rows: exact-official and primary. The primary file is an exact
ordered subset selected by its locked manifest, with matching feature rows
verified during export. This deliberately retains duplicate rows so existing
head application and role validation need no shared-view abstraction. No
additional encoding is needed to change query definition. All nine heads
reuse these pre-head caches. Apply each checkpoint to
clean gallery and all query conditions, preserving existing byte/provenance
validation and checkpoint-bound normalized embeddings. The 180 result cells
are **not** 180 encoder passes: the semantic encoder workload is one clean
gallery plus ten query conditions, with batching/sharding as recorded.

The current projector and artifact revalidation include CPU projection and
repeated hashing. Include their wall time and temporary memory in measurements;
do not assume the GPU extraction rate predicts end-to-end evaluation.

## 8. Capacity gates

The fixed campaign has the following head-update count under the existing
sampler. Counts are not GPU-hour estimates.

| Stage | Runs | Updates per run | Total updates |
| --- | ---: | ---: | ---: |
| Engineering pilots, 76,013 rows | 3 | 20 × 2,376 = 47,520 | 142,560 |
| Development selection, 76,013 rows | 27 | 47,520 | 1,283,040 |
| Final training, 95,001 rows | 9 | 20 × 2,969 = 59,380 | 534,420 |
| **Required total before retries/fixtures** | **39** | | **1,960,020** |

Target one allocated L40S, the measured extraction hardware; validate the exact
head-training and corruption workload there. A different accelerator requires
repeatability, memory, and runtime checks before inclusion in the paired run
schedule. Keep complete jobs within their approved wall limits. The current
launcher requests four CPU slots and 32 GiB aggregate host memory; confirm
that is sufficient for full arrays, serialization, and projection rather than
assuming from GPU memory alone.

Before selection, create an immutable capacity report that includes:

- All three complete pilot times, checkpoint/validation/I/O time, CPU and GPU
  memory peaks, scheduler queue/setup observations, and actual saved bytes.
- The complete corrupted development passes, projection for all pilot heads,
  source/provenance checking, and one-shot scoring. Measure at least one
  timing segment with all 95,001 auxiliary feature rows resident for
  final-training memory/extrapolation. Update only fixed 80-action training
  batches, keeping held-out labels out of optimization. This is separate
  timing-only engineering outside the 39 scientific runs; record its extra
  steps/bytes, and make its weights ineligible for selection or final results.
  No novel inputs or scores are needed.
- A dated GPU allocation calendar specifying access windows, job limits,
  queue allowance, and planned concurrency. An empty queue or prior access
  is not an allocation commitment.
- Researcher-confirmed available hours against the work packages and final
  analysis. The inherited 77 planned hours in Weeks 4–14 and zero recorded
  actual minutes are not evidence of remaining availability or no past work.

Forecast remaining training per arm from its measured update cost and fixed
validation/checkpoint overhead; use the slower pilot/full-size timing for
that arm and include initialization, hashing, scoring, and report regeneration.
Count every fresh extraction, integrity scan, retained attempt, and measured
CPU stage. **Multiply remaining compute/wall-work estimates by at least 1.25**,
then add the allocation calendar's queue/setup delays. Apply the same minimum
25% slack to remaining researcher work. The resulting schedule must finish
final heads and locks by November 29, full novel evaluation by December 6,
and preserve December 7–18 for analysis/delivery. Do not launch overlapping
jobs beyond the demonstrated GPU, host-memory, or storage budget.

Storage uses bytes, not ambiguous GB labels. Let

```text
available = min(filesystem_free_bytes, project_quota_remaining_bytes)
required = 200 * 2**30 + 1.25 * forecast_remaining_peak_bytes
pass iff available >= required.
```

The initial planning envelope is **100 decimal GB of incremental space,
including slack**, while retaining the 200 GiB reserve. It deliberately keeps
the role-specific files expected by the existing architecture. The following
uncompressed payload estimates include float32 features, int64 labels, and
20-character Unicode sample IDs; compression is not credited.

| Retained v3 outputs | Estimated decimal GB |
| --- | ---: |
| Five fresh clean caches, including both final-training repeats | 9.9464 |
| Nine development corruption pre-head caches | 5.9463 |
| Ten exact-official plus ten primary novel pre-head caches and clean gallery | 13.1980 |
| 39 development gallery/query projection pairs: 12 pilot snapshots + 27 selection endpoints | 6.1193 |
| 180 role-specific final query projections and nine reusable clean gallery projections | 28.1768 |
| 48 head checkpoints: 12 pilot snapshots + 27 development + nine final | 3.4229 |
| Conservatively bounded physical batch-plan files | 1.0666 |
| **Planned payload subtotal** | **67.8763** |
| Metadata, per-query results, retained failures, and temporary-file allowance | **10.0000** |
| Subtotal and allowance multiplied by 1.25 | **97.3454** |
| **Rounded incremental capacity requirement** | **100.0000** |

The roughly 4.14 million development/final per-query result rows are covered
by the allowance, not assumed free. Pilot epoch-zero diagnostics do not retain
another full embedding cache; compute their summaries in memory. At epoch 20,
retain one checkpoint artifact per pilot and reference it from both the epoch
record and completion record rather than copying it. The 10 GB allowance is
bounded, not permission for unlimited failed attempts. Replace estimates with
actual bytes at the October gate, including all new artifacts already created.

**The observed quota does not pass this initial gate.** Reserve plus the
100 GB envelope requires **314.7484 GB free**, versus 272.80 GB observed:
approximately **41.95 GB more accessible space** is needed. Obtain additional
quota or a documented, authorized artifact allocation before committing the
full campaign. If capacity is provided at a new canonical root, preserve and
register old roots, copy/verify required immutable inputs without relabeling,
and account for the transfer and duplicate storage. Do not treat filesystem
free space beyond the project quota as usable capacity. A reduced-storage
architecture would be a separately verified implementation change, not an
assumption in this plan.

The peak forecast includes all yet-to-be-created retained checkpoints,
intermediate pilot weights, batch plans, clean/corrupted pre-head caches,
primary/official duplicates, projected embeddings, ranks, logs, failed attempts,
immutable output staging, and reports. Already present files are reflected in
the current free-space reading, not counted twice. After work begins, use the
remaining measured forecast rather than demanding the initial 100 GB again.
Retain original v1/v2
artifacts; deleting evidence is not a capacity remedy. Recheck before each
large job and before opening, and stop new work if the reserve would be crossed.
The September 29 observation permits at most **46.44 decimal GB of additional
unmargined peak work** under this formula; it does not reserve that amount.

**October 18 go/no-go:** all three objectives mathematically verified; three
complete, valid 20-epoch pilots; unchanged fixed development episode; nested
corruptions and fallback validated; full development extraction/projection/
scoring verified; analysis tested; every historical seal audit resolved; and
the complete measured schedule/storage/availability forecast passes. Otherwise
stop before the sweep and record a result-blind amendment. Do not reduce a
single method's budget, discard seeds/cells, or claim a completed comparison.

## 9. Locks, opening, and failures

Keep `POSE_EMBED_DATA_ROOT` for licensed inputs and a stable absolute
`POSE_EMBED_ARTIFACT_ROOT` for all scientific records. Resolve all v3 outputs
under its `study-v3/` namespace and locks below that namespace. The shared
dataset-level opening record remains at the canonical root and binds the
source inventory/physical-source hashes and the historical-root audit. Neither
a caller-selected ledger nor a different study namespace bypasses it.

Use a staged lock sequence to avoid circular prerequisites:

1. **Before fresh parity/caches and pilots:** complete immutable v3 protocol
   and design/pilot specification with fixed recipes, 20 epochs, identities,
   numerical/corruption/analysis conventions, fallback binding, finite LR
   grid, hashes, and the omitted control decision. It authorizes auxiliary
   engineering only. Freeze all cache-affecting code in the release.
2. **By October 18, before selection:** append an immutable selection
   authorization binding that same protocol digest to corruption/analysis
   verification, pilot records, the complete run matrix/manifests, and the
   capacity decision. The scientific protocol is unchanged. There are no
   final checkpoint hashes yet; this is not a test-opening lock.
3. **After selection/final training:** selected configs and timestamps; nine
   final checkpoint/run-manifest hashes, seeds, initializations/batches,
   source/checkpoint/input-contract bindings, code/dependency hashes, exact
   primary/official/gallery IDs, evaluation plan and complete final-run-set.
   Record the researcher-controlled final lock only after its dependencies.
4. **Immediately before opening:** validate the complete cross-binding and
   all prior ledgers, verify no scientific training remains active, recheck
   capacity, and atomically create the immutable dataset opening event and
   its v3 authorization. Coordinate creation so a partial/crashed transaction
   fails closed and can only complete the identical lock, never a new one.
   **Only then** invoke the novel annotation loader/preprocessor/encoder.
5. **After opening:** every extraction shard, head application, evaluation
   cell, and report must match the same source, protocol, run-set, opening,
   cache, code, checkpoint, and corruption bindings. All scientific training
   and selection for this study/source are forbidden across v1/v2/v3 paths.

A crash after the opening event does not reseal the data. Preserve the attempt
and retry only the identical authorized operation and inputs. Missing/malformed
required cells remain visible and prevent a complete report. A scientific or
implementation defect discovered after opening cannot be repaired by silently
changing the confirmatory pipeline: preserve results, explain the limitation,
and label any necessary corrected analysis as a post-opening deviation.

## 10. Execution calendar and verification

| Deadline/window | Required output | Check that closes the stage |
| --- | --- | --- |
| Sep 29–Oct 4 | Clean implementation base; complete v3 protocol/pilot specification, corruption operators/fallback, versioned validators, shared seals, source access separation, pilot instrumentation | Cache-affecting code/config frozen before extraction; historical artifacts untouched; old/v3 protocol and seal tests pass; no novel representation/outcome access |
| Oct 5–11 | Loss value/backward fixtures, paired sampler/init checks, learnable-fixture checks, fresh parity/caches, three full 20-epoch pilots | Every pilot complete with four checkpoint/score records and diagnostic/timing evidence; source/extractor code hashes stable |
| Oct 12–18 | Nested corruption/fallback audit, nine full development conditions, analysis fixtures, allocation/availability/storage report | All October go/no-go requirements pass before selection; otherwise record blocker/amendment |
| Oct 19–Nov 1 | 27 clean-development selection runs and selected rates | Complete attempt ledger; three valid seeds per selected candidate; exact ranking rule reproduced |
| Nov 2–15 | Nine fresh all-100-action final heads | Paired 20-epoch runs, immutable checkpoints, complete source/config/code provenance |
| Nov 16–29 | Independent evaluator/run-set/lock audit; report skeleton, figure templates and reproduction checks on development data | All nine heads locked; exact 180-cell matrix and query lists fixed; current capacity/seal checks pass; Thanksgiving retained for recovery |
| Nov 30–Dec 6 | One authorized novel extraction/evaluation campaign | 180 unique finite provenance-valid cells; per-query ranks reproduce every metric; all operational attempts retained |
| Dec 7–13 | Conditional interval, absolute-score/degradation curves, per-seed/LOAO tables, cost/limitations, report/poster draft | All analysis and figures regenerate from locked records; claims follow the prespecified rule |
| Dec 14–18 | Independent reproduction smoke test, final report/poster and permitted archive; tracker reconciliation | Deliverables complete, limitations explicit, no licensed data/checkpoints/private records in Git |

Test the implementation in layers. Python changes require locked dependency
sync, `python scripts/verify_workspace.py`, Ruff lint/format checks and the
relevant unit/integration suite, followed by the complete Python suite before
the scientific release. Required fixtures cover loss values/backward rules,
sampler pairing, pilot exclusion, failed-candidate selection, corruption nesting,
fallbacks, unequal-view bootstrap weighting, fixed gallery sensitivity,
cross-version seal denial, first-open ordering/concurrency, provenance mutation,
and report matrix completeness. Run scheduler shell syntax checks and GPU
parity/repeatability on the allocated hardware.

For tracker changes run its lint, typecheck, tests, build, local database reset,
database tests and security advisors. Migrate the public v3 plan with expected
row versions, returned-row conflict checks, trigger-managed version increments,
RLS and private ownership preserved. Preserve hosted task evidence and actual
minutes. Closed-week changes require an explicit audited reopen reason;
future-week plan adoption does not silently rewrite closed history. Verify
hosted Auth sign-up/redirect restrictions before enabling editing. Publish the
matching fallback and protocol bundle; do not merely redeploy an older app.

No tracker migration/deployment, experiment, or scientific code modification is
performed by this planning document. The independent-research governance and
recorded BU determination remain in force; no advisor approval is required.
Reconcile dataset-terms acceptance with private evidence, and do not invent
researcher time, approvals, or completed gates.

## 11. Completion criterion

The study is complete when the three selected recipes have nine verified final
heads, all 180 declared result cells reproduce from locked per-query evidence,
the conditional primary analysis and all descriptive tables/curves regenerate,
and the December report/poster explains absolute performance, seed variation,
cost, failures, adaptations, and limits. Deliver permitted code, configs,
manifests, compact summaries, source/license notices, and reproduction
instructions. Keep licensed poses, checkpoints, caches, full artifacts, and
private governance records outside Git.

The final answer can be positive, null, or negative. If a capacity or validity
gate prevents the declared campaign, deliver an honest blocked-study record
and amendment; that is not a completed empirical comparison. This is a final
execution design with explicit go/no-go rules, not evidence that unmeasured
GPU work or researcher availability has already been secured.
