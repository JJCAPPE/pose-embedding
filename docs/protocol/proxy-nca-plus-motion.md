# ProxyNCA++ motion adapter

Status: independently implemented and covered by CPU component/integration
tests. **No SCC GPU feasibility result or image-to-motion performance claim is
established by these tests.** This is a result-blind adapter declaration before
novel-test access; the complete 26-method final gate remains in force.

## Source and preserved ingredients

The objective implements the all-proxy assignment probability in equations 4–6
of [Teh et al. (2020)](https://arxiv.org/abs/2004.01113). Every training-class
proxy, including the positive proxy and classes absent from the physical
batch, participates in the denominator. Embeddings and proxies are normalized;
the logits are negative squared distances divided by `T=1/9`.

The adapter preserves class-balanced physical batches, max pooling,
non-affine LayerNorm, normal proxy initialization with standard deviation
`1/8`, and faster proxy optimization. The CUB reference recipe uses Adam with
`eps=1`, zero weight decay, learning rate `0.004` for the backbone/head and
`400` for proxies. The reference implementation also uses five head/proxy
warmup epochs, a fresh optimizer for the main phase, and gradient-value
clipping at 10 on model parameters; proxy gradients are not clipped.
[Pinned configuration](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/config/cub.json),
[training reference](https://github.com/euwern/proxynca_pp/blob/217233d29a89a89766658396a598b896d17a5814/train.py).

The implementation was written independently from these equations and factual
recipe settings. No upstream source was copied or vendored, so this change
does not add an upstream checkout or imply a new repository license. The
official source remains an MIT candidate for any later permitted reuse.

## Declared motion choices

- MotionBERT produces `[batch, people, frames, joints, channels]` tokens.
  A token is eligible for pooling exactly when its preprocessed input
  confidence is greater than zero. Max pooling reduces the people, time and
  joint axes together, channel by channel. Invalid tokens cannot win a maximum
  merely because valid token features are negative.
- If every token in a sample is invalid, use a zero pooled feature. LayerNorm
  and the learned linear projection still apply; a finite resulting embedding
  is retained under the shared input policy. This fallback does not invent a
  valid pose or silently remove a sample.
- Apply non-affine LayerNorm to the pooled representation, then a linear
  projection to 512 dimensions, then L2 normalization for retrieval. This
  changes the common MotionBERT action head, which flattens joint features.
  Head initialization is therefore paired within the same head recipe and
  dimension. Encoder initialization, training identities/batches and
  evaluation conditions remain paired across recipes.
- Fine-tuning freezes the encoder for all warmup updates and enables encoder
  gradients at the first main update. The unused pretrained pose-regression
  head stays frozen. The supplementary frozen track keeps the encoder frozen
  throughout. Main-phase optimizer state starts fresh, matching the reference
  phase transition; no warmup moments are accidentally carried forward.
- An epoch means `ceil(training_record_count / physical_batch_size)` updates
  of the shared deterministic class-balanced sampler. Five complete epochs
  are required. The declared total step budget includes these warmup updates;
  it must include at least one subsequent main update. The reference's epoch
  counts describe warmup separately; manifests make our total-update
  convention explicit.
- Development selection also excludes steps that would be within warmup on
  the larger final auxiliary-training population. This avoids selecting a
  checkpoint budget that cannot complete final-training warmup.
- The motion adapter uses constant learning rates and the benchmark's
  validation R@1 checkpoint selection. The reference image training uses a
  validation-dependent scheduler and a combined NMI/R@1 criterion. This is an
  explicit shared-protocol adaptation, not a claim of identical image training.
  All parameters, this policy, and population-dependent boundaries are bound
  in the run identity.

The current 1,000-step priority configuration is preserved. It is deliberately
rejected for scientific ProxyNCA++ runs whenever shorter than the complete
warmup. `configs/benchmark.selection.v2.yaml` supplies a separate development
configuration with a common 50,000-update ceiling and 1,000-update validation
interval for all methods. It is a development budget, not an approved final
selection campaign or an estimate of GPU affordability. Actual GPU profiling
and the complete tuning ledger are still required before that campaign.

## Profiling and checkpoints

ProxyNCA++ profiles are labeled `post_warmup_capacity`. They initialize the
main optimizer and execute actual encoder backward when the configured track
is fine-tuning. They do **not** claim to have executed the five warmup epochs
or to approximate a converged model. Their scientific-use flag remains false.
Histories record training phase and encoder-gradient presence; telemetry
records encoder-backward step count and measured memory/time.

Checkpoints contain encoder/head state, all global proxies, named Adam
parameter groups and moments, and the selected warmup/main update counts.
Validation checks the correct head shape, proxy shape, optimizer group recipe,
moment shapes/counts, and complete phase boundary. Evaluation reconstructs
the same head and loads it strictly before opening the novel-test gate.
The inference scorer remains the benchmark's normalized-embedding scorer.

## Verification and outstanding evidence

Tests cover the analytical all-proxy loss and gradients, confidence masking,
negative feature values, all-invalid fallback, LayerNorm/projection order,
optimizer membership and exact restoration, complete warmup transition,
frozen-track behavior, real profile backward, immutable run roundtrips,
incompatible checkpoint rejection, and pairing across declared head recipes.

Still required: an allocated-node GPU profile with verified licensed inputs,
development tuning under the common budget, all six paired selected runs,
and the remaining method adapters. No test or registry update opens the novel
set or establishes that ProxyNCA++ or Contextual is better in motion retrieval.
