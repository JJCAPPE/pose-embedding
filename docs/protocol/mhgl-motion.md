# MHGL: declared motion adaptation

Audit and implementation date: 2026-09-26. Recipe identifier:
`ebrahimpour2022_printed_equations_motion_v1`. This records a result-blind
adaptation of MHGL; it does not establish reproduction of image scores or
authorize novel-test access.

## Sources and equation convention

The source is Ebrahimpour, Qian and Beach, *Multi-Head Deep Metric Learning
Using Global and Local Representations*, WACV 2022. The [complete arXiv
paper](https://arxiv.org/pdf/2112.14327), including its supplementary section,
was read. Equations 1–7 and the implementation details in §4.2 were checked;
Equation 6 was additionally inspected on the rendered PDF page 4. The
[author publication page](https://mkebrahimpour.github.io/publications.html)
links the short and long papers. No official implementation with an
established reuse license was found. `benchmark/mhgl.py` is an independent
implementation of the published mathematics; no MHGL source code is copied.

**Equation 6 prints a plus sign in the negative exponent:**

```
MS = mean_i [ log(1 + sum_positive exp(-gamma * (S_ij - sigma))) / gamma
            + log(1 + sum_negative exp(beta * (S_ij + sigma))) / beta ]
gamma = 2; beta = 50; sigma = 1
```

This differs from the usual Multi-Similarity negative margin convention.
The supplementary section contains no correction. This adapter follows the
printed equation literally and binds
`negative_margin_convention=printed_similarity_plus_sigma` into its recipe.
It must be described as this declared variant; numerical parity with an
unavailable official implementation is unverified. Substituting a minus sign
requires an explicit result-blind amendment, a new recipe identity and new
run/selection locks. It cannot happen after novel outcomes are inspected.

The other objective is Equation 5 Proxy Anchor, with `alpha=32`, `margin=.1`:
the positive term averages over proxies present in the batch, and the
negative term averages over all training-class proxies. Equation 7 is
`MS + .03 * PA`. Embeddings and proxies are unit normalized for similarity.
MS uses every same-label non-self positive and every different-label
negative. No extra miner is introduced: the paper does not specify one in
this recipe and states that tuple sampling is not tuned. Labels are a fixed
global map of training actions. A physical batch must contain at least two
classes and at least two examples from each class.

## Two actual encoder feature levels

The shared MotionBERT source remains the Apache-2.0 revision
`705d3a95354db8bdb696b3492e47a3b5537174ff` already recorded in
`third_party/upstreams.toml`. Its declared pretraining architecture has five
DSTformer depths, fused spatial/temporal branches, 512 feature channels and
512 final representation channels. The input, checkpoint, preprocessing,
physical batch, data split and seeds are inherited from the common benchmark.

| Branch | Encoder tensor | Motion token grid | Projection |
| --- | --- | --- | --- |
| Local | Fused output of depth 4, before depth 5 and final norm/pre_logits | Each person × 9 temporal bins × each joint | 512 to 256 |
| Global | Depth 5 output after upstream norm and pre_logits | Each person × 3 temporal bins × each joint | 512 to 256 |

The local tensor is captured by a temporary pre-forward hook on the fifth
spatial-temporal block. The hook receives the previous depth's already-fused
tensor. The ordinary `get_representation` call supplies the global tensor.
There is one encoder pass, no recomputation and no detach of the local
tensor. A `finally` block removes the hook on success or failure. A strict
five-depth, fused-branch architecture check prevents silently selecting the
wrong layer in another encoder. Local width is read from `encoder.dim_feat`;
global width comes from the loaded representation contract. They are not
assumed equal: the actual-DSTformer test uses widths 8 and 12.

This replaces the paper's ResNet conv4/conv5 levels with two actual motion
depths. It also replaces the paper's 14×14 and 7×7 image grids with smaller
motion grids. Nine and three bins are declared compute choices, not paper
hyperparameters or anatomy learned from novel data. Every clip has the
same 243-frame common preprocessing: the bins therefore cover fixed
intervals of normalized clip time (27 and 81 processed frames), not fixed
seconds of physical duration. Joint and person identities remain distinct
tokens. This preserves spatial joints at both levels while giving the local
branch a finer temporal grid. No additional resampling of raw motion occurs.

## Masking, attention and pooling

Confidence greater than zero defines a valid input person/frame/joint token.
For bin `i` of `n`, frame bounds are `floor(i*T/n)` and
`floor((i+1)*T/n)`. Its feature is the mean of valid frames for that same
person and joint. A bin with no valid frames is zero and invalid. Empty
intervals (possible in short fixtures) obey the same rule. The encoder itself
retains the shared preprocessing and token-attention behavior; confidence
masking here does not claim to change upstream encoder attention.

Each level has its own second-order attention module. Four independently
learned pointwise linear maps implement query, key, value and output.
All use the full input channel width because the paper leaves its optional
channel reduction unspecified. In row-token notation, Equations 1–2 become
`A=softmax(Q K^T)` and `F_refined=F + output(A V)`, with `zeta=1`.
There is no transformer `sqrt(d)` scaling or shared attention across levels.
Invalid keys receive no mass; invalid queries produce zero output. An
all-invalid map has exact zero attention mass and finite zero pooled output.

Equation 4 is the sum of masked global average and masked global maximum.
Each branch then receives its own learned linear projection to 256 dimensions
(the paper calls these whitening transforms). Concatenation gives 512
dimensions, followed by one L2 normalization for retrieval. No whitening
statistics from validation or novel data are fitted. An empty branch has
zero pooled features before its projection; a trained projection bias can
therefore still produce a finite nonzero branch descriptor.

The paper does not establish initialization for these layers in the inspected
text. All added linear weights use Xavier uniform and biases start at zero,
explicitly bound as a motion choice. Class proxies start with independent
standard-normal entries as specified by the paper's normal initialization;
the unspecified scale is fixed at one. The common seed determines all draws.

## Optimization and stored state

AdamW uses three separately named, checkpointed parameter groups:

| Group | Learning rate | Contents |
| --- | ---: | --- |
| Encoder | .0001 | Shared MotionBERT, excluding its unused pose-regression head |
| Retrieval head | .0001 | Both attention modules and both linear projections |
| Proxies | .01 | One trainable vector per training action |

The default epsilon is `1e-8`. Weight decay uses the benchmark's declared
common value; the inspected MHGL text does not supply a separate decay value.
The paper reports 20 image epochs. Motion uses the benchmark's result-blind
step budget and development Recall@1 selection, with no extra warmup. This
is a declared schedule adaptation, not a claim of matching image epochs.
Frozen-encoder checks are supplementary capacity tests; the main comparison
fine-tunes the encoder. When frozen, its parameters receive no gradients and
its optimizer rate is zero, while both branches and proxies continue learning.

Model checkpoints contain both attention branches and projections as well as
the encoder. Criterion checkpoints contain proxies. Optimizer checkpoints
contain the three groups, stable parameter names and all AdamW moments.
The inference path uses both encoder levels and both learned branches but
never the class proxies or a batch-dependent retrieval graph. Query embeddings
must be independent of other evaluation-batch members.

## Cost and verification boundary

For two people, 17 joints and the declared bins, local and global attention
have 306 and 102 tokens. Their attention matrices contain 104,040 elements
per sample in total: 416,160 bytes in float32 (about .397 MiB). A physical
batch of 32 needs about 12.7 MiB for one copy of these matrices. This is
only a lower bound: logits, backward state, projections, captured encoder
activations and optimizer state add substantial memory. Full-width attention
is quadratic in tokens and linear in channels; projection cost is also
linear in tokens and quadratic in channels. The two attention modules plus
projections add 2,363,904 trainable parameters at width 512; class proxies
add `num_training_classes * 512`. The local gradient enters depth 4 directly;
the global gradient additionally traverses depth 5 and pre_logits.

Component tests compare attention and both losses to direct small equations,
verify masks and empty bins, distinguish local/global widths, and use the
actual pinned tiny DSTformer to check fused depth capture and both gradient
paths. Training tests cover frozen/fine-tuned optimization, all three groups,
checkpoint restoration, and evaluation batch independence. These CPU checks
provide implementation evidence, not a motion retrieval result or GPU memory
profile. Factory/runner integration, declared recipe hashing, researcher
review and an allocated-node development run/profile are required before the
registry can claim a fully validated runnable method. The full suite and all
six selected seeds remain required before opening the novel test.

Local verification: `test_mhgl.py`, `test_benchmark_runner.py`,
`test_models_and_sampler.py` and `test_benchmark_losses.py` together passed
54 tests, including 10 MHGL cases, against the fetched pinned MotionBERT
checkout. Ruff lint, Ruff format checks and `git diff --check` passed for the
adapter changes. No GPU experiment or dataset retrieval result was produced.
