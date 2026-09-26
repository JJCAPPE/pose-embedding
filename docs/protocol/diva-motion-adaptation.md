# DiVA: independently implemented motion adaptation

Result-blind recipe, 2026-09-26. The target is **Margin, DiVA, ResNet-50,
512 dimensions**, Table 2 of [Milbich et al.](https://arxiv.org/abs/2004.13458):
image R@1 69.2/87.6/79.6 on CUB/Cars/SOP. These identify the variant, not motion
results. Registry ID `diva`; recipe `milbich2020_cub_motion_corrected2021`.

## Source and rights

Primary mathematics: [paper](https://arxiv.org/pdf/2004.13458),
[official proceedings](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123530579.pdf).
No separate supplement was linked from the inspected official entry or arXiv;
this record makes no claim of a verified supplementary recipe.

The [author repository](https://github.com/Confusezius/ECCV2020_DiVA_MultiFeature_DML/tree/e5713049fa446d3180b4ca122963697ee16ee9f9)
is pinned in `third_party/upstreams.toml` at
`e5713049fa446d3180b4ca122963697ee16ee9f9`, fetched through the resolver only
for audit. No license was discovered: **reference-only**. No upstream source
was copied, adapted, vendored or imported. This is an independent mathematical
implementation with the explicitly declared conventions below.

## Representation and objectives

Four biased linear projections receive the common MotionBERT action-head
aggregation: average over time and people, flatten 17 joint features to 8704
inputs at width 512. This replaces image pooling and inherits the common
head's treatment of padded people; it does not substitute masked pooling.
Each output is an independently normalized 128-vector.

| Branch | Triplet/target | Sampling |
| --- | --- | --- |
| Discriminative | `y_a = y_p != y_n` | Uniform positive; inverse-density negative |
| Shared | Three different classes | Inverse-density positive and negative |
| Intra-class | Three distinct items, same class | Uniform positive and negative |
| Sample-specific | Second view of same clip | DaNCE against momentum memory |

Shared sampling enforces the paper's three original class labels; the audited
author random-label convention does not guarantee that property. Intra-class
sampling uses distinct items instead of possible replacement sampling. These
are explicit differences. Physical batches require P>=3, K>=3; the benchmark
retains its paired 8-by-4 optimization batches.

Three independent class-dependent beta vectors start at 1.2; gamma=0.2.
Margin loss sums `[d_ap-beta_a+gamma]+ + [beta_a-d_an+gamma]+`, divided by the
number of triplets with **either** hinge active. Both-active triplets count
once with both terms retained, recording the historical author reduction.
Distances add `1e-8` before the square root. The paper's setup calls gamma and
beta fixed while the baseline discussion also specifies a learnable margin;
this recipe explicitly chooses learned beta.

Inverse-density sampling uses `q(d)^-1 = d^(2-D)*(1-d^2/4)^(-(D-3)/2)` on
detached embeddings, distance floor 0.5, and a private CPU generator.

Three 128→512→128 ReLU networks map auxiliary features toward discriminative
features. Negative squared elementwise-product correlation is averaged over
samples **and dimensions**, weighted by rho=1500. Gradient reversal on both
input branches lets the networks maximize correlation and embeddings minimize
it. Dimension averaging is the declared author convention, distinct from an
unnormalized squared-norm interpretation of the paper formula.

Total loss: discriminative margin + 0.3*(shared margin + intra-class margin +
DaNCE) + adversarial decorrelation. Retrieval normalizes the concatenation
`[0.5*disc, shared, intra, sample]`: CUB's double auxiliary embedding amplitude,
with squared cosine contributions 0.25/1/1/1. Retrieval is batch-independent
512-vector cosine; memory and auxiliary networks are training-only.

## DaNCE and motion conventions

* Temperature is the **paper's 0.1**; the audited author example uses 0.01.
* The paper's inverse-density cap lambda is unspecified. The author's 2021
  README documents a weighting correction (`diva_fixed`). This recipe names
  the **corrected-author-2021 convention**: detached inverse-density log
  weights, subtract each query maximum, exponentiate, zero distances above
  1.4, clamp at `1e-45`, normalize each query row. All-outside rows become
  uniform. Weights multiply negative cosine logits. This is explicitly not
  a claim to recover an unspecified lambda or literal original recipe.
* The positive cosine has weight one and is included in the softmax denominator
  alongside weighted negatives; all logits divide by temperature. Positive
  and memory keys are detached.
* Two motion views independently draw a whole-trajectory rotation [-5°,5°],
  scale [0.9,1.1], x/y translation [-0.05,0.05]. A clip's transform is shared
  over time, joints and people. Confidence, absent tokens, temporal order,
  joint/person identity are preserved. No flip or temporal crop is used.
  These are declared action-preserving motion adaptations. Augmentation and
  triplet sampling share a checkpointed private RNG, leaving global draws and
  optimization batch plans unchanged.

## Memory, optimizer and evidence

The momentum encoder/sample projection start as exact online copies, remain
without gradients and in evaluation mode. Momentum is 0.9. Memory contains
30 physical batches, or 960 128-vectors at batch 32. A separate immutable
`memory-plan.json` records first seeded training batches and binds the
optimization batch-plan hash. Bootstrap uses only the current training
partition, forward passes and no optimizer/EMA updates. Its criterion digest,
full count and zero counters enter `memory-initialization.json`.

Each step computes old momentum keys, updates the online model, updates EMA
`0.9*old+0.1*online`, then enqueues the pre-update keys. Queue item indices and
global action labels allow verification against the training history. The
instance task permits same-action memory negatives. Validation/novel clips
never populate memory. Frozen supplementary runs retain an exactly frozen
momentum encoder while the momentum projection still updates.

Adam has named encoder, four-head and decorrelation groups with LR `1e-5`,
weight decay `5e-4`, epsilon `1e-8`; beta uses LR `5e-4` and zero decay. Common
motion step budgets and development R@1 selection replace image epoch budgets;
there is no implicit image schedule. Fine-tuning is the primary track.

Checkpoints persist online/EMA weights, all auxiliary parameters, queue,
indices/labels, ring position/count, completed updates, RNG, training-identity
digest, Adam moments/group names and phase. Safe segmentation follows
`after_optimizer_step`. Resume restores state then rebinds verified training
records without another bootstrap. Nonpersistent `training_labels` is rebuilt;
pending forward state must be empty. Inference does not update memory or EMA.
The verifier reconstructs queue history, partition identity, counters and
exact optimizer mappings, rejecting altered state even after outer rehashing.

## Validation boundary

Synthetic tests cover analytical values, task constraints, reversal signs,
view preservation, all branch/auxiliary gradients, EMA arithmetic, train-only
memory, exact restored updates, full runner evidence and deliberate tampering.
These do not establish GPU capacity or scientific performance.

Allocated-GPU profiling must fill the actual 960-item memory and run the full
momentum encoder and two-view optimizer path. Telemetry records bootstrap time
and peak memory separately, queue count, momentum parameter count and training
peak memory. No automatic batch/queue reduction or objective substitution is
allowed. Novel evaluation still requires the complete 26-by-6 final gate and
locked statistical plan.
