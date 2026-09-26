# Proxy Anchor + AVSL: motion adaptation

Recipe: `zhang2022_cub_motion_v1`, recorded result-blind on 2026-09-26.
The required row uses three 512-dimensional level descriptors and complete
AVSL hierarchical inference. Concatenation with cosine is a paper ablation
and cannot satisfy this row.

## Audited sources and licensing

The [paper and supplement](https://arxiv.org/html/2203.14932) define CAM
relations, momentum, reliability, correction, separate objectives and
attribution in Equations 1–11 and 15–25. The source is
[`zbr17/AVSL`, revision `fd2686e4f94a93da3c97c1b2067df9601f2803a0`](https://github.com/zbr17/AVSL/tree/fd2686e4f94a93da3c97c1b2067df9601f2803a0),
verified through the upstream manifest. Its MIT notice is retained in
`third_party/licenses/AVSL-MIT.txt`. The adapter header attributes the
embedder and collector files. No image backbone, data pipeline, GEDML code
or upstream trainer is vendored. Tests load the licensed cached classes as
oracles without importing their unrelated trainer/logging dependencies.

The CUB command in `examples/samples_avsl.sh` supplies the starting recipe.
Its learning rates differ from the paper's brief uniform-rate description;
the adapter follows that explicit command. Source/component parity is not
reproduction of image scores or a measured motion result.

## Three actual motion depths

One pass through the shared Apache-2.0 MotionBERT revision
`705d3a95354db8bdb696b3492e47a3b5537174ff` captures fused outputs of depths 3
and 4 using pre-forward hooks on spatial-temporal blocks 4 and 5. The usual
`get_representation` call provides depth 5 after norm/pre_logits. Hooks keep
the live graph and are removed in a `finally` block. A strict five-depth,
fused-branch contract prevents silent layer substitution. Intermediate
widths use `encoder.dim_feat`; final width follows the representation
contract. Tests deliberately use different widths (8 and 12).

At each depth, nine disjoint bins average confidence-positive frames for each
person/joint, with bounds `floor(i*T/9)` and `floor((i+1)*T/9)`. For the common
243-frame input these cover 27 processed frames of normalized clip time,
not fixed seconds. Person/bin forms the grid row; anatomical joint forms its
column. Two people and 17 joints yield 306 aligned positions at every depth,
so CAM correlations need no interpolation. This temporal pooling is a
declared compute adaptation. Hierarchy comes from actual encoder depths.
Empty bins are zero and invalid. An all-invalid branch has zero embedding
and certainty. These masks do not change the encoder's internal attention.

## Pooling, CAMs, links and inference

Each level uses masked mean-plus-max pooling and its own 512-output linear
projection, initialized Kaiming normal `fan_out` with zero bias. Every level
is L2 normalized separately. The concatenated 1536-vector is stored but is
never used for cosine ranking.

CAMs use source pooling linearization: add a spike at each channel's first
maximum in flat grid order, equal to the maximum times the number of valid
positions, then apply the same projection at every position. The valid CAM
average therefore reproduces the raw descriptor. The appendix divides tied
maxima among all ties; the pinned source chooses the first and this recipe
preserves that source behavior. Invalid positions have no spike or CAM mass.

Certainty preserves another source detail: subtract the minimum within each
row across valid joints, flatten, L1 normalize and take sample standard
deviation. Empty rows and fewer than two valid positions yield zero. CAMs,
certainty and relations are detached from encoder/projection gradients.

Relations are batch-mean inner products between L2-normalized flattened raw
CAMs of adjacent levels. Two matrices have axes `[lower_node,higher_node]`.
The first update copies observed relations; later updates use momentum `.5`.
A checkpointed update counter preserves initialization across resume, fixing
the source's unsaved initialization flag. Only the training objective updates
relations, exactly once per call; encoding and scoring never update them.

Inference ReLUs relations, retains the top-128 threshold mask per higher node,
and divides each column by `sum + 1e-8`. As in the source, all ties within
`1e-8` of the kth value survive; zero columns remain zero. There is no uniform
fallback that would invent connections.

For every pair, each level forms componentwise squared differences between
unit descriptors. Upper-level reliability is
`sigmoid(10 * (coefficient * std_query * std_gallery + bias))`, initialized
with coefficients one and biases zero. Starting at the lowest level, each
higher level combines its differences with corrected lower differences
projected through the relation matrix, weighted by reliability and its
complement. The corrected top-level sum is the distance. The callback returns
its negative for the evaluator's higher-score-first convention.

Attribution returns coefficients and original node differences whose weighted
sum reconstructs distance. For nonzero normalized columns, coefficient mass
is the per-level dimension up to the source epsilon. Zero columns do not
satisfy the paper's exact mass-conservation claim; this limitation is explicit.

The scorer copies descriptors and snapshots relations/reliability. Later
training mutations cannot change existing scores. Pair blocks are at most
8 by 128, on the snapshot's device and dtype, and return NumPy scores. No
gallery labels or batch updates enter scoring. The common evaluator retains
its exclusions, relevance definition and tie rule. Custom scoring permits
finite zero descriptors; ordinary cosine retains its nonzero-norm guard.

## Training and checkpoint state

Three independent proxy banks use the source's Kaiming normal initialization
with `a=sqrt(5)`. Distance Proxy Anchor uses alpha 16 and margins 1.8/2.2:
positive terms average over represented proxies; negatives average over all
training-class proxies. Level objective weights are `.5, 1, .5`. A fourth
Proxy Anchor objective uses hierarchical sample/proxy distance. Each proxy's
certainty is the batch mean certainty for its level, as in the source.

The final objective detaches descriptors, proxies, CAMs and links and trains
only reliability. The three level objectives train encoder, projections and
proxies. Tests verify both directions of this gradient separation. AdamW
uses epsilon `1e-8`, weight decay `.0001` and named groups:

| Group | Learning rate |
| --- | ---: |
| Encoder | .00001 |
| Projection heads | .00055 |
| Reliability | .00011 |
| Proxy banks | .00011 |

Five warmup epochs freeze the encoder. Each epoch is the ceiling of actual
training records divided by the physical batch size. Selection eligibility
also covers the larger final-training population's warmup; the update budget
includes warmup. Capacity profiles explicitly omit warmup execution and
exercise the full encoder, recording that omission.

The declared motion schedule halves rates every ten total training epochs,
including warmup, preserving moments across the phase boundary. The source
command delegates exact warmup/scheduler control flow to GEDML; the unported
trainer has no parity claim. Motion retains the benchmark step budget and
development selection. Source gradclipper settings are preserved: norm ten
separately for encoder, projections and combined collector (reliability plus
proxies).

Model checkpoints contain encoder, projections, reliability, relation buffers
and update counter; criterion checkpoints contain proxies. Optimizer state
contains all named groups, moments and rates. Recipe provenance includes
population, warmup, schedule and profile behavior. Restoring only concatenated
projection weights is insufficient for AVSL retrieval.

## Storage, cost and verification boundary

Float32 storage per clip is 1536 embedding values plus 1536 CAM standard
deviations: 12,288 bytes before IDs/archive overhead. Relations occupy
2,097,152 bytes, reliability 8,192 bytes and the update counter eight bytes.
At width 512, projection heads contain 787,968 parameters; reliability adds
2,048 and proxies add `3 * number_of_training_classes * 512`. Full CAMs are
recomputable for attribution and are not needed in retrieval archives.

Dense hierarchy propagation uses two 512-by-512 matrix products per pair.
Pair blocks bound memory, not total computation. Actual scorer latency,
descriptor storage and GPU memory must accompany accuracy; cosine cost
cannot stand in for AVSL cost.

Component/source parity, real-DSTformer gradients, checkpoint restoration and
chunked scorer tests are review evidence. Shared descriptor-pipeline
integration, allocated-node development checks and GPU profiles remain
required. No GPU/data result or superiority claim is made here, and the full
required roster and six selected seeds still gate novel-test access.

## Integrated scoring arithmetic and checkpoint verification

Both online retrieval and descriptor replay execute the inference graph on CPU
in float64, independent of training device. This fixes the arithmetic used for
exact tie ordering and rank replay. Descriptor extraction remains on the run
device; CPU scoring time is measured separately and must enter the forecast.
Checkpoint validation independently reconstructs every named optimizer group,
learning rate, AdamW moment/count and the persistent relation-update counter,
including warmup-preserved head/proxy moments and post-warmup encoder updates.
