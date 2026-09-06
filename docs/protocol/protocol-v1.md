# Protocol v1: noisy one-shot pose retrieval

Status: **scientifically specified, not advisor-locked**. The machine-readable
source of truth is `configs/protocol.v1.yaml`.

## Question and outcome

Given one clean reference per unseen NTU RGB+D 120 action, determine whether a
contextual-plus-contrastive training objective reduces the top-1 retrieval drop
caused by pose corruption relative to its contrastive-only component. A null or
negative result is a valid successful outcome.

## Fixed comparison

- Frozen MotionBERT encoder in evaluation mode and an identical
  MotionBERT-compatible 2,048-dimensional normalized action head.
- Core losses: contrastive-only, supervised contrastive, and full contextual
  plus contrastive. Three paired seeds use identical initial heads and physical
  P=8, K=4 batch plans.
- Tune only on the 20 class-disjoint development actions A2, A8, ..., A116.
  Retrain on all 100 auxiliary actions only after settings are frozen.
- Evaluate the official 20 novel actions A1, A7, ..., A115 once. The primary
  query set excludes every synchronized camera view of the anchor performance;
  the exact official query set is a secondary comparability result.
- The clean one-shot gallery never receives corruption. Query corruptions are
  three torso-scaled jitter levels, three whole-joint mask counts, and three
  consecutive-frame mask lengths. Their deterministic seed is derived from
  sample ID, family, and severity.

The official protocol is pinned to NTURGB-D repository commit
`ac2ebc87e6e9777ea6bac67e65e53b325b903f74`, not to a moving branch. Its exact
one-shot exemplars are:

```text
S001C003P008R001A001  S001C003P008R001A007
S001C003P008R001A013  S001C003P008R001A019
S001C003P008R001A025  S001C003P008R001A031
S001C003P008R001A037  S001C003P008R001A043
S001C003P008R001A049  S001C003P008R001A055
S018C003P008R001A061  S018C003P008R001A067
S018C003P008R001A073  S018C003P008R001A079
S018C003P008R001A085  S018C003P008R001A091
S018C003P008R001A097  S018C003P008R001A103
S018C003P008R001A109  S018C003P008R001A115
```

The source inventory is expected to describe all 114,480 NTU RGB+D 120 source
samples. A smaller convenience subset is never sufficient to authorize final
evaluation. If the authorized HRNet-derived release legitimately has a
different complete inventory, that discrepancy requires a documented protocol
amendment before the novel test is opened.

## Input tensor convention

The corruption boundary is the deterministic, pre-encoder MotionBERT tensor
`[people, 100 frames, 17 H36M joints, x/y/confidence]` in `float32`. Raw HRNet
COCO17 coordinates are camera-normalized, people are tracked, coordinates and
confidence are converted to the explicitly listed H36M17 order, frames are
uniformly sampled, a missing second person is zero-padded, and spatial
normalization is applied. Derived joint coordinates use the arithmetic mean;
their confidence uses the minimum source confidence. Random movement is off.
This confidence conversion is a deliberate local correction. Compatibility
with the pinned upstream is tested layer by layer, but the project does not
claim byte-for-byte parity for the upstream confidence preprocessing. Encoder
parity is checked by feeding the same declared local tensor to both encoder
paths.

H36M torso scale uses shoulders 11/14 and hips 4/1. Jitter changes x/y only.
It is applied only where confidence is positive, so padded or already-missing
observations stay missing.
Joint and frame masks set x, y, and confidence to zero without changing shape.
All exact joint sources, groups, levels, and operation order live in the hashed
machine-readable protocol.

## Primary estimand

For each method, seed, and corruption cell, compute clean top-1 minus corrupted
top-1. The primary effect is the equally weighted mean of contextual degradation
minus contrastive-only degradation across three seeds and nine cells. Estimate a
95% paired interval from 10,000 bootstrap samples clustered by setup, performer,
repetition, and action. Contextual robustness is supported only when the upper
bound is below zero. Clean performance and every seed/cell are always reported.

## Test seal

The official novel test remains sealed through tuning. All scientific lock
locations are derived from the absolute `POSE_EMBED_ARTIFACT_ROOT` and the
relative paths inside the hashed protocol; training and evaluation do not
accept a caller-selected ledger path. Before the test can be opened:

1. Verify the protocol and print its canonical SHA-256 digest.
2. Copy the matrix-only `configs/evaluation-plan.v1.yaml` template to
   `$POSE_EMBED_ARTIFACT_ROOT/locks/evaluation-plan.v1.yaml`, change its status
   to `locked`, and bind the source inventory, anchor, official-query, and
   primary-query manifests by raw SHA-256, exact ordered sample IDs, and count.
3. In Week 7, record the result-blind selected config for each core method and
   its selection timestamp. Selection binds a digest of the hyperparameters
   excluding only the run name and paired seed. The protocol binds the
   Multi-Similarity configuration by the same seed-independent digest, so its
   optimizer or objective settings cannot change after test opening. After Week
   8 creates all nine runs, complete
   `$POSE_EMBED_ARTIFACT_ROOT/locks/final-run-set.v1.json` from
   `configs/final-run-set.template.json`. It binds each of the nine resolved
   seed-specific config files, checkpoint/run-manifest records, paired batch
   plans and initializations, and the training, evaluation, sampler, corruption,
   and analysis code digests. The validator parses every config and checkpoint,
   rather than trusting its filename or a self-reported manifest value. This
   finalization adds hashes; it does not permit selection using test data.
4. Copy `configs/protocol-lock.template.json` to
   `$POSE_EMBED_ARTIFACT_ROOT/locks/protocol-lock.v1.json`; fill every plan,
   manifest, run-set, protocol, and approval field. The lock timestamp must be
   at or after run-set finalization, and future timestamps are rejected.
5. Run `pose-embed protocol verify --require-locked`. The command resolves all
   three files from the canonical artifact root and verifies their complete
   cross-binding. It also prints the current component code digests.
6. Run `pose-embed evaluate --mode final` without lock or ledger path flags.
   On the first test opening it validates the four exact manifests, the complete
   114,480-row canonicalized source inventory, every declared per-sample file,
   and the selected config, checkpoint, batch plan, metrics, attempt, outcome,
   run manifest, and code hashes. The first attempt atomically creates
   `$POSE_EMBED_ARTIFACT_ROOT/locks/test-opening.v1.json`; later cells must match
   its protocol-lock, evaluation-plan, final-run-set, source-inventory digest,
   source-file count, and source-file digest. Later cells do not rescan all
   114,480 licensed inputs: they consume and rehash the immutable feature caches
   whose sidecars bind the already-verified source inventory. This command
   remains deliberately unavailable for the upstream aggregate HRNet pickle
   until the Week 2 trusted importer has hash-verified it and produced that
   canonicalized inventory. Extra, missing, renamed, or byte-changed source
   files fail the initial opening; changes after opening cannot alter the
   already-hashed caches and should be detected by a separate storage audit.

Changing protocol content invalidates the lock. Do not update the lock after
examining novel-test results. Scientific training requires the canonical
artifact root and is forbidden after its opening ledger exists, so omitting a
command-line argument cannot bypass the test seal.

## Artifact authorization

Every feature/embedding NPZ requires a sibling `.npz.manifest.json`. The sidecar
binds the protocol, source manifest, ordered sample IDs, preprocessing, upstream
implementation, frozen-encoder checkpoint, trained-head checkpoint, base cache,
artifact bytes, shape, dtype, role, split, condition, and scientific-use status.
Consumers recompute these hashes and reapply the locked head to the validated
base cache, requiring the archived embeddings to match exactly; embedded NPZ
metadata is not an authorization source. Training accepts only
`training` roles from auxiliary splits. Development evaluation accepts only
clean development-validation gallery/query roles. Final evaluation accepts only
clean novel anchors and the matching primary or official novel-query role, and
checks exact identity and synchronized-performance exclusions.

Artifact validation and cosine ranking reject NaN and positive/negative
infinity before any result can be written. Every result uses a strict schema
whose aggregate metrics must reproduce from its per-query ranks. Final rows
also record the protocol lock, evaluation plan, run set, opening ledger,
checkpoint, and both feature-sidecar hashes. A report can mark the core matrix
complete only for 180 unique, finite, exactly authorized cells. Report building
rehashes every recorded provenance input, revalidates the nine run directories
and both feature caches, and verifies that the ordered per-query identities
match the locked manifests. A JSON row with plausible numbers but missing or
changed source artifacts cannot certify the matrix.

`pose-embed features extract` creates a pre-head cache. Retrieval never consumes
that cache as if it were a trained method. Use `pose-embed features apply-head`
with the exact `head.pt` and `run-manifest.json` to produce the normalized,
checkpoint-bound gallery or query embeddings accepted by evaluation.

The included fixture extractor is deliberately synthetic and permanently marks
its outputs `scientific_use_allowed: false`. It requires an explicit
`--allow-fixture` switch for debug training/evaluation and can never produce a
final scientific result. Real MotionBERT extraction remains blocked until the
authorized checkpoint, adapter, upstream checkout, and numerical parity checks
exist. The exact implementation and exit checks are listed in
`docs/protocol/motionbert-adapter-gate.md`.

## Failed runs and amendments

A training attempt creates immutable `attempt.json` before device setup or the
optimization loop and immutable `outcome.json` on success, non-finite loss, or
another exception. A failed run is rerun only in a new directory with the same
method, seed, configuration, initialization, and batch plan after documenting
the operational cause. Scientific parameter changes
return to development validation and require a protocol amendment. Week 5 may
change corruption magnitudes only for a documented geometric defect—not based on
retrieval scores—and must freeze them before method selection.

Multi-Similarity is exploratory only. Its loss alpha/beta/base, miner epsilon,
normalized cosine distance, distance p/power, and library version are explicit
in both protocol and experiment config. The protocol also binds the complete
seed-independent experiment digest, including learning rate, weight decay,
dimensions, epochs, and physical batch settings. It may run after the one-time
core test opening because it is a separately labeled post-core analysis, but
only after all four gates are verified. Copy
`configs/stretch-gates.template.json` to the canonical
`$POSE_EMBED_ARTIFACT_ROOT/locks/stretch-gates.v1.json`; its evidence paths are
relative to that `locks` directory. Build the core report directly under
`$POSE_EMBED_ARTIFACT_ROOT/locks/core-report/`. The matrix and figure gates must
both bind that report's `summary.json`: authorization reruns full result
provenance validation, recomputes the primary analysis, and regenerates the
expected SVG in memory, and re-derives failure status from every preserved
final-training `attempt.json`/`outcome.json` before accepting any of the three
completion gates. Also bind the locked evaluation plan, final run set, and
opening ledger.
Exploratory evaluation produces a separate 60-row matrix (one method, three
paired seeds, ten conditions, two query definitions); it can never replace,
alter, or be mixed into the confirmatory 180-row core report.

## Required sign-offs

Use `docs/protocol/week-1-evidence-template.md` to collect the public-safe
approval, access, checksum, and GPU evidence without placing secrets or licensed
inputs in the repository.

- [ ] Advisor approves the research question, primary estimand, action splits,
      query exclusion, corruption family/levels, test seal, and failed-run rule.
- [ ] BU provides the applicable human-subjects/data-governance determination.
- [ ] Dataset terms are accepted and authorized files are stored outside Git.
- [ ] GPU model, scheduler, CUDA/driver compatibility, quota, and job limits are
      recorded.
