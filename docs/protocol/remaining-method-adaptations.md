# Required remaining motion method adaptations

Source audit date: 2026-09-26. This document completes the implementation map
for the required suite in `configs/benchmark-methods.v2.json`; it does not
authorize final-test access. The registry currently contains **26 required
configurations: 14 implemented and 12 blocked**. A working priority pair is
development evidence, and does not complete the requested comparison.

The scientific target is Contextual Similarity against all methods represented
in the original paper's comparison tables, adapted to motion. Method IDs stay
stable even when the source audit resolves a shortened table label. In
particular, `proxy_nca_metrix` denotes **ProxyNCA++ + Metrix/feature** and `s2sd`
denotes **R-Margin + S2SD**, as established below. All rows use 512 retrieval
dimensions except the matched AVSL/Contextual 1536 comparison.

## Shared completion requirements

For each blocked row, completion requires:

1. Record the exact paper variant, component equations, source revision,
   licenses and dependency audit. Any reused source must go through
   `third_party/upstreams.toml` and `scripts/fetch_upstreams.py`, with notices.
   A public repository without a discovered license remains reference-only;
   use an independent implementation from published mathematics or obtain
   permission before adapting its source.
2. Declare the motion representation, pooling/masking, trainable components,
   output dimension, objective, sampler, optimizer groups, warmup/schedule,
   inference scorer and additional stored state. Record every image-to-motion
   change before observing novel outcomes. Paper constants are starting
   recipes, not evidence that they are appropriate motion hyperparameters.
3. Add mathematical/component tests and a small development run proving that
   every required trainable component updates and checkpoint restoration is
   exact. Profile real optimizer steps and retrieval, including extra state
   and scorer cost, on an allocated GPU node.
4. Apply the same result-blind tuning budget, shared input/split contract,
   physical class-balanced batches and paired seeds. Distinguish common-head
   objective comparisons from methods requiring a different head or scorer;
   report their parameter, memory and runtime differences.
5. Change `blocked` only when the actual motion adapter is callable by the
   runner and validated. Hash the resulting registry/configuration and bind
   it to selection and final-run records. The full selected 26-by-6 suite is
   required before the final gate can open; unresolved rows cannot silently
   disappear from the denominator.

The existing scalar `build_loss(embeddings, labels)` interface is sufficient
for implemented embedding objectives. Several remaining methods also require
features from the encoder, multiple output heads, training state or custom
inference. Add only the interfaces needed by the selected adapter. Avoid
representing those methods with an unrelated scalar loss under their names.

## Source and license inventory

These are observed revision candidates, **not yet approved/pinned dependencies**.
MIT entries require a component and transitive-source audit; a top-level MIT
file does not establish the rights of every bundled dependency. No source was
copied as part of this audit.

| Required ID(s) | Official source candidate and observed revision | Observed reuse status |
| --- | --- | --- |
| `proxy_nca_pp` | [euwern/proxynca_pp](https://github.com/euwern/proxynca_pp/tree/217233d29a89a89766658396a598b896d17a5814), `217233d29a89a89766658396a598b896d17a5814` | [MIT](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/LICENSE) |
| `drml` | [zbr17/DRML](https://github.com/zbr17/DRML/tree/55afbdc1144c06bcb1e81d76490217b239247556), `55afbdc1144c06bcb1e81d76490217b239247556` | No license/notice file discovered; reference-only |
| `diml` | [wl-zhao/DIML](https://github.com/wl-zhao/DIML/tree/c15dbea696f68ddf889dcacfcaacd315d16a34ac), `c15dbea696f68ddf889dcacfcaacd315d16a34ac` | No license/notice file discovered; reference-only |
| `diva` | [Confusezius/DiVA](https://github.com/Confusezius/ECCV2020_DiVA_MultiFeature_DML/tree/e5713049fa446d3180b4ca122963697ee16ee9f9), `e5713049fa446d3180b4ca122963697ee16ee9f9` | No license/notice file discovered; reference-only |
| `ibc` | [dvl-tum/intra_batch](https://github.com/dvl-tum/intra_batch/tree/a1ae3de8bf1ccedefb89258f24295beeec7e81a3), `a1ae3de8bf1ccedefb89258f24295beeec7e81a3` | [MIT](https://github.com/dvl-tum/intra_batch/blob/a1ae3de8bf1ccedefb89258f24295beeec7e81a3/LICENSE) |
| `s2sd` | [MLforHealth/S2SD](https://github.com/MLforHealth/S2SD/tree/1ef26e4e273019575f3b5dfbb789fa4952eb9646), `1ef26e4e273019575f3b5dfbb789fa4952eb9646` | [MIT](https://github.com/MLforHealth/S2SD/blob/1ef26e4e273019575f3b5dfbb789fa4952eb9646/LICENSE) |
| `proxy_nca_metrix`, `proxy_anchor_metrix`, `multi_similarity_metrix` | [billpsomas/metrix](https://github.com/billpsomas/metrix/tree/b6797035fd82baf46ad89f8856721ae01afdf4f0), `b6797035fd82baf46ad89f8856721ae01afdf4f0` | [MIT](https://github.com/billpsomas/metrix/blob/b6797035fd82baf46ad89f8856721ae01afdf4f0/LICENSE) |
| `hist` | [ljin0429/HIST](https://github.com/ljin0429/HIST/tree/e7d650c80460f464c55bcdc2262d785923c50dc4), `e7d650c80460f464c55bcdc2262d785923c50dc4` | No license/notice file discovered; reference-only |
| `mhgl` | [Author publication page](https://mkebrahimpour.github.io/publications.html) links the paper and longer version | Official implementation/reuse license not established |
| `proxy_anchor_avsl` | [zbr17/AVSL](https://github.com/zbr17/AVSL/tree/fd2686e4f94a93da3c97c1b2067df9601f2803a0), `fd2686e4f94a93da3c97c1b2067df9601f2803a0` | [MIT](https://github.com/zbr17/AVSL/blob/fd2686e4f94a93da3c97c1b2067df9601f2803a0/LICENSE) |

## 1. ProxyNCA++ — first implementation priority

**Required recipe.** The six enhancements are all-proxy assignment probability,
temperature scaling, class-balanced sampling, global max pooling, non-affine
LayerNorm and fast proxies. The loss is cross-entropy over negative squared
distances between unit embeddings/proxies divided by temperature; the positive
proxy is included in the denominator. The paper uses `T=1/9`.
[Teh et al., §§3–4](https://arxiv.org/html/2004.01113).

The official CUB configuration uses batch 32 with 8 classes/4 examples,
Adam with `eps=1`, zero weight decay, backbone/head learning rate `0.004`
and proxy learning rate `400`. The proxy initialization is normal with
standard deviation `1/8`. Pooling precedes non-affine LayerNorm and the
embedding linear layer. Training includes five head/proxy warmup epochs with
backbone learning rate zero. These unusual optimizer values are real source
settings, not recommended untuned motion values.
[Config](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/config/cub.json),
[model](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/networks.py),
[loss](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/loss.py),
[training](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/train.py).

**Motion work.** Implement a declared max-pooling operation on MotionBERT
spatiotemporal tokens, including absent-person/padding handling, followed by
non-affine LayerNorm and a 512-dimensional projection. Add method-specific
optimizer groups and warmup/schedule identity. Test the loss against a small
hand-computed softmax, proxy updates and restored optimizer state, masking,
pooling order and frozen/fine-tuning behavior. Merely changing the scale of a
Proxy NCA loss while retaining the common head/optimizer is a loss ablation.

**Dependency/effort.** Bounded head, loss and optimizer integration; no custom
retrieval scorer. This also supplies the base of `proxy_nca_metrix`.

## 2. DRML with Proxy Anchor

**Required recipe.** The screenshot's DRML result is the Proxy Anchor variant.
DRML learns four 128-dimensional individual branches, eight meta-relation
branches, reconstruction-based assignment to individual branches, and a graph
updater producing the concatenated 512-dimensional retrieval embedding.
It optimizes reconstruction, ensemble and final embedding objectives; simply
concatenating independent heads omits the relational method.
[Zheng et al., §3, §4.2 and Tables 1–4](https://arxiv.org/html/2108.10026).

**Motion work/tests.** Independently implement the equations over pooled
motion features unless reuse permission is obtained. Verify assignment ties,
graph construction and relation gradients, all three loss components,
512-dimensional output and batch-independent inference. Declare the pooled
input and optimizer groups. Dependency: multi-head output and reconstruction
training support; no query-gallery graph is needed at inference.

## 3. DIML structural matching

**Required recipe.** Structural similarity uses optimal transport between local
feature maps, cross-correlation marginals and multiscale matching. It can
enhance existing trained embeddings or participate in training. The exact
published baseline/scale recipe producing the screenshot's row remains to be
resolved before implementation is approved; the inspected arXiv version and
README are insufficient to lock that identity.
[Zhao et al., §3](https://arxiv.org/pdf/2108.05889),
[official README](https://github.com/wl-zhao/DIML/blob/c15dbea696f68ddf889dcacfcaacd315d16a34ac/README.md).

**Motion work/tests.** Specify spatial joint and temporal token granularity,
cross-person alignment, masked marginals, transport solver tolerance, scales,
and any candidate shortlist. Preserve local descriptors and implement the
pairwise scorer. Verify marginal sums, transport constraints, finite zero-mass
handling, small exact matching cases, and chunked/un-chunked retrieval parity.
Dependency: independent/licensed implementation plus local-token storage and
custom scoring. Report descriptor storage and scoring cost alongside the
nominal 512-dimensional descriptor; cosine alone does not implement DIML.

## 4. DiVA

**Required recipe.** Four complementary branches learn class-discriminative,
shared, intra-class and sample-specific features. The last uses DaNCE;
gradient-reversal decorrelation separates auxiliary features from the
discriminative branch. The 512-dimensional configuration combines four
128-dimensional branches; margin objectives and distance-weighted sampling
are part of the reported setup. DaNCE also requires its momentum/memory state.
[Milbich et al., §3 and §4](https://arxiv.org/html/2004.13458).

**Motion work/tests.** Define two action-preserving motion views for the
sample-specific task, implement the distinct task samplers and objectives,
and preserve queue/momentum state in checkpoints. Verify gradient-reversal
signs, label constraints per task, queue isolation from validation/novel data,
and 512-dimensional concatenation. Dependency: independent implementation,
multi-head training and deterministic motion augmentation/state handling.

## 5. IBC

**Required recipe.** The screenshot's 70.3/88.1/81.4 scores correspond to learned
intra-batch message passing, cross-entropy on refined features, and auxiliary
cross-entropy on the backbone embedding. Retrieval uses backbone embeddings.
Applying the message-passing network to nearest-neighbor batches at inference
is a separate optional experiment, not required to reproduce this row.
[Seidenschwarz et al., §§3.3–3.5 and Tables 3–4](https://proceedings.mlr.press/v139/seidenschwarz21a/seidenschwarz21a.pdf).

**Motion work/tests.** Add the attention/message-passing and classifier modules
on clip embeddings, preserving auxiliary supervision. Check batch permutation
equivariance, both supervision paths, gradient propagation through the
encoder when enabled, and that query embeddings are independent of evaluation
batch composition. Dependency: a training-only contextual module and global
class-ID classifier mapping; no new inference scorer for the main row.

## 6. S2SD with R-Margin

**Required recipe.** The screenshot's 70.1/89.5/80.0 row is **R-Margin + S2SD**,
not default Multi-Similarity + S2SD. The SOTA table uses MSDFA for CUB/Cars
and MSDF for SOP: multiple target embedding branches, similarity distillation
and feature distillation, with added pooling in the A variant. The main paper
reports target dimensions `[512,1024,1536,2048]`, two-layer MLPs, temperature 1,
and delayed feature distillation; those choices require checking for the
selected 512-dimensional motion student.
[Roth et al., §§3–5 and Table 2](https://proceedings.mlr.press/v139/roth21a/roth21a.pdf).

R-Margin includes distance-weighted negative sampling, trainable class
boundaries, and randomly exchanging negative/positive samples. The supplement
reports dataset-specific switching probabilities and detaches teacher
similarities for distillation while still training teachers with their own
objectives. These details must be preserved explicitly.
[Supplement §§B and E](https://proceedings.mlr.press/v139/roth21a/roth21a-supp.pdf).

**Motion work/tests.** Declare the motion variant and target dimensions before
novel access, implement margin/sampling state and all branches, and select
only the student at inference. Verify teacher stop-gradient direction,
teacher learning through its own objective, class-boundary optimizer state,
switching reproducibility and feature-distillation activation. Dependency:
multi-output training, pooled feature access, and margin/sampler integration.

## 7–9. Three Metrix/feature rows

**Required recipe.** These are **feature mixup**, not embedding-only mixup.
Metrix interpolates binary positive/negative relationships and weights the
positive/negative contributions inside the objective. Clean anchors and
positive-negative or anchor-negative mixing are used; the paper's defaults
include `Beta(2,2)` interpolation and mixup strength `0.4`. Table 2 resolves
the screenshot's shortened “Proxy NCA + Metrix” label to **ProxyNCA++**.
[Venkataramanan et al., §§3, B.2 and Table 2](https://arxiv.org/html/2106.04990).

| Required ID | Adapter dependency | Required distinguishing check |
| --- | --- | --- |
| `proxy_nca_metrix` | Complete ProxyNCA++ adapter, intermediate feature mixing and its mixed-target objective | All-proxy denominator and temperature remain correct under mixed targets |
| `proxy_anchor_metrix` | Proxy Anchor plus intermediate feature mixing and weighted pair contributions | A mixed example contributes to both appropriate positive and negative terms |
| `multi_similarity_metrix` | Multi-Similarity plus intermediate feature mixing and weighted pair contributions | Weights occur within the correct nonlinear positive/negative reductions |

**Motion work/tests.** Fix the encoder layer and subsequent layers used for
mixing; pooled final embeddings cannot silently replace intermediate tokens.
Declare temporal alignment, person padding and label interpolation. Check
mixing endpoints, deterministic choices, soft-target arithmetic and every
branch's gradients. Keep synthesized representations in training only.
Dependency: one shared feature-mixing mechanism plus three separately tested
objectives, with the ProxyNCA++ row depending on section 1.

## 10. HIST

**Required recipe.** HIST treats batch samples as hypergraph nodes and
class-specific semantic tuplets as hyperedges, learning through hypergraph
node classification. It is not a pairwise graph loss. The official README
also exposes separate learning-rate controls for the hypergraph component.
[Lim et al., paper landing page](https://openaccess.thecvf.com/content/CVPR2022/html/Lim_Hypergraph-Induced_Semantic_Tuplet_Loss_for_Deep_Metric_Learning_CVPR_2022_paper.html),
[official README](https://github.com/ljin0429/HIST/blob/e7d650c80460f464c55bcdc2262d785923c50dc4/README.md).

**Motion work/tests.** Complete the equation-level paper/supplement audit
before coding: the full PDF was inaccessible through the browsing fetch
during this audit. Resolve incidence weights, normalization, trainable class
state and exact inference path. Independently implement the method or obtain
reuse permission. Test tiny hypergraphs, degrees/normalization, batch
permutations, class mappings and all optimizer groups. Dependency: hypergraph
training module and source-equation verification. No verified adapter exists.

## 11. MHGL

**Required recipe.** The method combines local and global feature levels,
second-order attention, pooled/concatenated descriptors, and a hybrid
Multi-Similarity plus weighted Proxy Anchor loss. Its image implementation
uses different ResNet depths for the two levels, and faster proxy learning.
The local/global architecture must accompany the hybrid loss.
[Ebrahimpour et al., §§3–4](https://arxiv.org/html/2112.14327).

**Motion work/tests.** Choose and document two MotionBERT feature levels,
token meanings, pooling and a total dimension of 512. Implement the published
attention and hybrid objective independently; confirm equation conventions,
loss weights and proxy optimizer groups during the detailed recipe audit.
Test second-order attention on small examples, local/global gradients,
concatenation dimension and separate loss components. Dependency: intermediate
encoder access and independent implementation; no official licensed code
source was established by this audit.

## 12. Proxy Anchor + AVSL

**Required recipe.** Three feature levels each produce 512-dimensional
descriptors and receive loss constraints. AVSL learns momentum-updated
relations and reliability-based similarity inference across levels.
Concatenation followed by ordinary cosine is an explicit ablation in the
paper, not complete AVSL. The 1536-dimensional accounting matches the
Contextual comparison row, but AVSL also needs its relation/scoring state.
[Zhang et al., §3, §4.2 and Table 2](https://arxiv.org/html/2203.14932).

**Motion work/tests.** Declare three MotionBERT levels, how local tokens map
to similarity nodes, attribution/reliability computation, the exact
Proxy Anchor distance convention, and hierarchical inference. Persist all
momentum/graph state and make gallery/query scoring chunkable. Verify
attribution sums, known reliability cases, graph-state restoration,
per-level gradients and scorer chunk parity. Dependency: multi-level encoder
features, multiple training losses and a custom pairwise retrieval scorer.
Report full stored state and inference cost against Contextual 1536.

## Implementation order and completion evidence

Proceed with ProxyNCA++ first because it establishes a concrete head/optimizer
adapter and unlocks one Metrix dependency. IBC and the shared Metrix mechanism
can then be developed independently. S2SD requires explicit margin/sampling
and teacher-state support. DRML and DiVA require independent multi-head
implementations unless licensing is resolved. DIML, MHGL and AVSL share a need
for audited intermediate motion features; DIML and AVSL additionally require
scorer support. HIST needs its equation audit before an implementation is
considered reviewable. This is dependency order, not a license to omit rows.

For each method, retain a compact evidence record linking the recipe,
source/license audit, component tests, development run, GPU profile and exact
adapter/configuration hashes. Record the unresolved decisions above as
blockers until resolved. Do not claim paper replication, complete comparison,
or superiority while required adapters or final evaluations remain missing.
