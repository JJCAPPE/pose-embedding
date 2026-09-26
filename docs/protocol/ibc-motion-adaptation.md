# IBC motion adapter

Result-blind implementation record, 2026-09-26. The novel test remains sealed.
`ibc` implements the backbone-retrieval variant of **Learning Intra-Batch
Connections for Deep Metric Learning**, Seidenschwarz et al., ICML 2021. This is
the MPN-plus-auxiliary-supervision row, not optional MPN retrieval. The paper's
[§§3.3–3.5](https://proceedings.mlr.press/v139/seidenschwarz21a/seidenschwarz21a.pdf)
define learned incoming attention, two residual normalization steps, and both
classification objectives.

## Source audit and recipe choice

The reference is pinned in `third_party/upstreams.toml` as `intra-batch` at
`a1ae3de8bf1ccedefb89258f24295beeec7e81a3`, fetched with the repository's upstream
script. Its [MIT license](https://github.com/dvl-tum/intra_batch/blob/a1ae3de8bf1ccedefb89258f24295beeec7e81a3/LICENSE)
attributes the Dynamic Vision and Learning Group. This adapter independently
implements the mathematics using PyTorch dense operations. No upstream source
or third-party graph code is copied, vendored, imported, or redistributed.
In particular, upstream's `MetaLayer` identifies a PyTorch Geometric origin;
neither it, `torch-scatter`, Apex, nor the bundled RAdam implementation is used.

The selected [CUB training configuration](https://github.com/dvl-tum/intra_batch/blob/a1ae3de8bf1ccedefb89258f24295beeec7e81a3/config/config_cub_train.yaml)
uses one message step and two attention heads. Cars uses a different depth;
we preregister the CUB recipe as the motion starting point, with parameters
bound in the method registry. No image performance is imported as motion evidence.

Audited source files are `net/{attentions,gnn_base,graph_generator,resnet,utils}.py`,
`utils/losses.py`, and `trainer.py`. The active numerical recipe includes:

- All directed batch edges, including self-edges. No neighbor threshold or
  correlation multiplier affects the selected attention calculation.
- A learned 512-to-512 projection before message passing. Each head has width
  256; query/key scores divide by its square root. Concatenated messages pass
  through a learned output projection. Attention projections use Xavier weights
  and zero biases.
- The reference's denominator is `1 + sum(exp(score))`. We implement this as a
  zero-logit, zero-value null message using a stable softmax. The printed paper
  describes ordinary softmax; this explicit source convention is preserved.
- Dropout 0.1 on attention probabilities, attention residuals, the hidden ReLU
  feedforward activations, and feedforward residuals. The feedforward width is
  four times the embedding dimension. Both residuals use affine LayerNorm
  with epsilon `1e-5`. The configured classifier `dropout_p=0.4` is unused by
  the selected source modules and is not added here.
- Refined classification uses BatchNorm1d with its zero bias frozen, then a
  bias-free class projection initialized with normal standard deviation 0.001.
  Auxiliary classification uses a biased linear projection of the **raw**
  backbone embedding. Both losses use temperature 0.2 and label smoothing 0.1;
  they are added with weight 1 each.

## Motion-specific changes and interfaces

MotionBERT plus the common action head replaces image ResNet-50 and its pooling.
The established temporal/person mean and 512-dimensional projection remain
paired with Contextual and Contrastive. `forward_raw(poses)` exposes the raw
projection in one encoder pass; ordinary `forward` applies the existing L2
normalization. The IBC criterion declares `requires_raw_embeddings=True`,
normalizes its graph input, and preserves raw magnitudes for auxiliary CE.

NTU action IDs map to the persisted contiguous 80 development or 100 final
training classes. A physical 8-by-4 batch supplies graph nodes. The shared
benchmark uses AdamW, its declared learning rate/weight decay and step-based
development selection instead of the source's RAdam, image augmentation,
dataset-specific batch 54, and 70 epochs. Those are explicit controlled motion
adaptations, not a claim to reproduce image scores. Fine-tuning and frozen
pilot tracks retain their existing meanings; all criterion parameters join
the optimizer in either track.

The criterion owns the input projection, MPN, classifiers, BatchNorm affine
state and running statistics. All are saved in the existing criterion
checkpoint; runtime validation re-creates the complete expected state shape.
Retrieval uses only normalized MotionBERT/head embeddings, so query output is
independent of the other evaluation clips. No graph or classifier sees
development retrieval candidates or novel clips.

## Verification and outstanding evidence

Synthetic tests cover hand-computed complete-graph messages, the null message,
self-edges, residual equations, permutation equivariance, smoothed CE,
raw-versus-normalized branches, both input gradients, trainable component
updates, BatchNorm restoration, missing checkpoint state, and unchanged cosine
inference. Existing methods remain tested through the common loss suite.

Scientific development scores, paired GPU runs, training memory/runtime, and
full-pool retrieval cost are still required. This implementation supplies a
callable adapter; it is not evidence that IBC works better or worse on motion.
