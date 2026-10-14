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

The original Week 3/4 design gate authorizes auxiliary engineering only.
[Decision 0006](../decisions/0006-v3-execution-completion-amendment.md) requires
completion of the full execution path in one successor release under
`study-v3/revisions/execution-r1/`, retaining the original release and evidence.
Its new design lock binds the predecessor and explicitly compares unchanged
scientific fields. The October 12 authorized
[ADR0007](../decisions/0007-safe-validation-reuse-and-stage-capacity.md) requires
another immutable successor, `study-v3/revisions/execution-r2/`, after the
measured execution-r1 capacity no-go. Both earlier releases and their evidence
remain unchanged. The same dataset seal protects all releases and all
historical protocol versions. New interfaces or passing fixtures do not grant
selection, final-training or novel access by their existence.

1. Before fresh caches/pilots: resolve preparation; audit all historical roots;
   freeze complete design/pilot protocol and cache-affecting release.
2. Preserve the completed Week 4 release and its parity, five caches and three
   full pilots. Before successor admission, rerun fresh parity, both full
   final-training extraction repeats, the other three caches and all three
   complete pilots under the new digest; independently validate their evidence.
3. By October 18: complete the fixture-to-report rehearsal, deterministic
   40–48-row development geometry panel and two-process replay, all nine full
   development encodings and 27 pilot-head projections/results, and measured
   capacity/seal evidence. Bind the allocation calendar, researcher availability
   and exact attempt/failure rules. Only the complete measured admission may
   append selection authorization against the fixed successor protocol.
4. After clean selection and nine fresh final heads: selected configurations,
   complete checkpoint/attempt bindings and exact final matrix; independently
   audit before the researcher-controlled final lock and atomic dataset opening.

ADR0007 permits successful deterministic numerical validation proof reuse only
inside one guarded command. Every hit fully rehashes transitive bound contents
and matches validator/options and protocol/design/source/runtime identities.
Dynamic seals, authorization/time, attempt inventories and resource/calendar
checks stay fresh. Independent recertification starts empty; changed inputs,
failed/partial checks and mutable caller inputs cannot yield stale success.
Store successful proof markers only; do not cache mutable result objects.
No cross-command or persistent proof cache is authorized. The precise acceptance
and mutation tests are in ADR0007. The implementation passed independent review
and the stable full local suite (1,373 tests, two historical AVSL skips) before
source release `f101f0e9d9bd64275d2088deab1b0bdcfcc53620` was frozen and pushed.
The separate SCC installation and allocated CPU rehearsal 8044010 passed
independent completion review: 128 checks, no failures or skips, successful
194-second accounting, nine resource samples and intact seals. The retained
receipt SHA-256 is `963babe02eba70d34f3f9c9aa47af21145de387ca4d5a1ad6ccf9c226fb43381`.
Preparation 8045152 passed independent completion review: successful 44-second
accounting, three commands, seven resource samples, both seals, all eight
original manifest identities and original → r1 → r2 scientific equality.
Its receipt SHA-256 is `0a3823e66a97192c5665185edbb908bf5b44c6dd9b451328d95d96476a84d785`;
the new protocol SHA-256 is
`18f7d17fa81e7ae3a6b1e5deddf42d9eda589d96e5a13968188a8ce275bfb95f`.
Supplementary CPU checks 8048540 completed October 13 at 08:31:43.006302 UTC
on apolkovnikov-pub@scc-h30: 86 checks passed without skips, successful
87-second accounting, three commands, seven resource records and both seals.
Independent review completed at 20:43:00.762966 UTC, verifying 108 metadata
bindings, 616 source bindings and actual locked-ID dependence tables for
18,929 development queries and 18,884 primary novel IDs, each over 20 actions.
Novel poses and outcomes remained unopened. Receipt
`week5-r2-additional-verification/20261013T204221Z/verification.json` has
SHA-256 `7703859e50361123de9054fba446c8384d423b8c549b69eab92720314c46c3d2`.
Geometry job 8070391 was submitted at 20:46:55.956765 UTC and initially
observed queued with four CPU slots at 20:49:22.424937 UTC. Its launch receipt
`week5-r2-launches/20261013T204651Z/launch.json` retains SHA-256
`a8c55f5a6054996d49cb2abab304a8b8925914a4cf0495a2f0368f84e4177452`.
The due inspection at 22:05:07.547370–22:05:19.824007 UTC found terminal
failure: bpnlab-pub@scc-kc1, four OMP slots, 20:51:02–20:54:51 UTC,
229 scheduler seconds, accounting failed=0/exit_status=1. The tracked checker
and exact within-revision repeats passed, but the external wrapper rejected
fixed cross-revision identity. No successor geometry completion is accepted.
Metadata diagnosis found 2,051 candidate own_scale scalars differed; the fixed
43 panel IDs, selection and manifests remained unchanged. All 43 clean tensor
hashes matched. Four selected scales and 129 coordinate-jitter hashes differed
across revisions; all 430 hashes were exact within each revision.
Diagnosis `week5-r2-geometry-diagnosis/20261013T220749Z/diagnosis.json` has
SHA-256 `d9d8b549c159206754d8f8b21eaaac1e6b5f656dee54959c23611717aa70534b`;
discriminator `week5-r2-geometry-diagnosis/20261013T221341Z/clean-tensor-discriminator.json`
has SHA-256 `f0dc0f44ba52c114e76b95ac044dd1ed63fd14fc62c8e1b9efd57c80f886ddcb`.
At that earlier geometry checkpoint, CPU dispatch was an untested recovery hypothesis. Separate native/default diagnostic
job 8072666 was submitted October 13 at 22:49:45.058490 UTC after 127 local
checks passed (60 parent, 27 worker, 40 launcher). Initial inspection at
22:52:26.185888–22:52:38.052404 UTC observed queued (qw), four slots, with
no operation, log or resource records. No numerical diagnostic result was produced.
Launch `week5-r2-launches/20261013T224936Z/launch.json` has SHA-256
`91358af8b0e0f3c04765c7fd9f5d4d5264c32cbb7dbaec2c5a2f7dfa917332a3`.
Its diagnostic-only 1-GiB bound comes from 67,480,406 bytes of metadata/log/source
bindings; the existing 17,675,344-byte archive is read only and never copied.
Fresh quota/filesystem reserve passed; this does not establish campaign capacity.
The October 13 at 8:00 PM EDT check was not executed after SSH disconnected;
no result was inferred during the gap. After access was restored, inspection
on October 14 at 19:40:13.233256–19:40:25.519918 UTC found diagnostic 8072666
failed before its parent started: neuro-pub@scc-h32, four OMP slots,
October 13 at 22:54:00–22:54:02 UTC, two scheduler seconds,
accounting failed=0/exit_status=1. SGE copied the wrapper to its spool directory;
the helper lookup used that directory and failed before either worker ran.
Independent metadata-only review at 19:56:38.194670 UTC verified zero operations,
resource records or worker outputs and 139 artifact/617 external/616 source bindings.
No CPU capability comparison ran in job 8072666; the geometry cause remains unproven.
Failure receipt `week5-r2-geometry-runtime-failure-verification/20261014T195626Z/verification.json`
has SHA-256 `c9e2d25740334923a537c36c82b0d2574f6b90a74b7d45ebf26ddc0c3aac371d`.
A separate reviewed operational remedy derives the unchanged parent helper from
the canonical bound input packet directory. Its 64 focused checks and review
passed; the original parent/worker and scientific settings/tolerances are unchanged.
New immutable tools `study-v3/operations/week5-r2-geometry-runtime-diagnostic-remedy-tools/20261014T200830Z` were staged and verified
October 14 at 20:08:33.599282 UTC. Tools manifest SHA-256
`c6404952ea81aa28b04c2603b6b4b7190cc85c1c759ff08410ee2dd7f63c1d77`; input packet SHA-256
`32289c531a0330f93dad42b7974022181eb494d775d6b70825a80a7a1877d716`; staging verification SHA-256
`ae31768ad55b7107b113c581aa6aff0e8690f7e1b86ecdd575a40bd72dd87316`.
At the staged checkpoint on October 14 at 20:08:33.599282 UTC, the launcher
had not been executed. That checkpoint and the earlier 4:41 PM EDT launch/check
boundary remain historical. The new guarded launcher executed once:
diagnostic remedy job **8102231 was submitted October 14 at 20:43:11.969137 UTC**.
The fresh pre-submit scheduler check completed by 20:43:10.988132 UTC with no
active jobs; it precedes submission and does not establish the new job state.
Launch `week5-r2-launches/20261014T204308Z/launch.json` has SHA-256
`82427510eb77a8bc0875753d343783a1e9a383f05bef736aa2c01654ee4037f2`; submission intent SHA-256
`7c690ce8410753e592a06c555dfb87c4b638ca28e344552a1d246c8c2fdeee6d`.
Independent submission-metadata review at 20:50:34.444145 UTC rehashed 763 metadata
and 616 frozen-source bindings, checked the packet/intent/command and both launch seals.
Receipt `week5-r2-geometry-runtime-remedy-submission-verification/20261014T205034Z/verification.json`
has SHA-256 `63aa23c6e514f9cd1757021354fa1262b8f48f89af10e8a8015259e885dbb471`.
Fresh quota 826,630,000,000 bytes and filesystem free 994,956,017,664 bytes passed
the diagnostic-only reserve. Its 1-GiB bound derives from 67,481,168 bytes of
metadata/log/source/receipt allowances; the existing 17,675,344-byte archive is
read only in allocation, with no copy. This does not establish campaign capacity.
The request remains four OMP CPU slots, 32 GiB, 30 minutes, no GPU and the
reviewed Gold-6426Y/AVX2 selector. At the submitted-only checkpoint, no post-submission state or result had been
observed; the earlier 5:45 PM EDT (21:45 UTC) first-check boundary is historical.
Actual inspection on October 14 at 22:25:31–22:25:43 UTC found completed diagnostic
remedy job **8102231**, completed at **20:49:21.682189 UTC**. Accounting records
neuro-pub@scc-ke1.scc.bu.edu, four OMP slots, failed=0/exit_status=0,
**17 whole-job CPU wall seconds and 9.340 actual CPU seconds**.
Independent completion review at 22:34:10.047781–22:34:14.167272 UTC verified
both seals, two unchanged worker commands, dispatch evidence, the final wrapper
marker, six resource records and 184 artifact/617 external/616 frozen-source bindings.
Receipt `week5-r2-geometry-runtime-remedy-queue-record-verification/20261014T223409Z/verification.json`
has SHA-256 `f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36`.
The four-case recovery hypothesis is **unsupported**: native AVX512 exactly
matched the failed-fresh four scales, 40 tensor hashes and 36 damage rows.
DEFAULT recovered the original four scales but only **36/40 tensor hashes and
32/36 damage rows**. Clean and all masking records matched the original; four
residual jitter hash/damage-row differences across two cases remain. This does
not establish the complete geometry cause or a permanent CPU profile.
The first completion verifier rejected only the allocation QUEUE representation
and produced no accepted receipt; its source and failure remain preserved.
The reviewed replacement accepts the scheduler's bare queue name with a
separately verified host, or its exact qualified forms. Host, job, PE, slot,
thread, scientific and numerical checks remain unchanged; 93 focused tests,
Ruff/format and independent review passed.
Geometry and every dependent stage, full allocated A/corruption replay,
scientific admission and measured CPU/GPU capacity remain held. No new profile,
helper or job is claimed. Do not execute the launcher again.
Next permitted scheduler/preflight check: **October 14, 2026 at 7:27 PM EDT (23:27 UTC)**,
under the hourly limit. Its output can only be diagnostic metadata;
it cannot produce eligible scientific artifacts or pass a gate. Source,
scientific settings and tolerances remain frozen; there is no blind geometry retry.
Preparation and fixture rehearsal grant no scientific admission.

The successor must freshly regenerate parity, five caches/two full repeats,
three complete pilots, panel/repeat evidence, nine corrupted development paths
and projections/results, full report rehearsal and timing/admission evidence.
Retain original source/identity/fallback bytes and byte-identical ordered
manifests only through validated bindings. Do not relabel predecessor sidecars,
reuse prior heads as successor pilots/finals, or mix release artifacts.

Successor capacity uses schema-2 CPU/GPU job-duration and remaining-work maps
with classified dated windows. Count all CPU/I/O overhead inside a GPU command
as GPU allocation time. Require both classes to fit, one subprocess and global
non-overlap, slack, queues, resources, storage and deadlines. Fresh opening
checks the actual GPU job against the GPU bound and still checks both remaining
evaluation calendars. Old scalar receipts are historical, not auto-converted
admission. This authorization creates no new gate pass or novel access.

Storage uses `available >= 200*2**30 + 1.25*remaining_peak_bytes`, with available
space the smaller of filesystem and project-quota remainder. The October 9
120-decimal-GB planning envelope covered the earlier generations. Inventory all
retained bytes and execution-r2 additional peaks before admission; no new numeric
envelope or capacity pass is assumed. In the forecast, existing files already
reduce current free space and must not be counted again as remaining work. The original 100 GB
envelope remains historical. Preserve every historical and
failed artifact; deleting evidence is not a storage remedy. Existing caches
establish historical feasibility only. No current document, template or passed
unit test asserts that successor GPU pilots or measured capacity exist. Record
the researcher's confirmed normal and contingency availability separately from
actual work logs and verify the complete dated schedule before admission.
