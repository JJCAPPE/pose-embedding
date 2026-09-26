# HIST motion adaptation

Recorded result-blind, September 26, 2026. No novel evaluation is authorized.
The adapter independently implements the distribution, semantic-incidence,
hypergraph propagation and classification equations 2–8 in
[Lim et al., CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/papers/Lim_Hypergraph-Induced_Semantic_Tuplet_Loss_for_Deep_Metric_Learning_CVPR_2022_paper.pdf).
The reference repository has no discovered license and remains reference-only;
no source is copied, adapted, imported or redistributed.

## Declared recipe

Each training class has a learned mean and diagonal log covariance. Distribution
cross-entropy uses all training classes. Only classes present in a batch define
hyperedges: positive incidence is one, negative incidence decreases with squared
Mahalanobis distance. Symmetric degree normalization supplies two graph layers.
Graph classification and distribution cross-entropy both reach the encoder.

The [supplement, A.2 and Table 3](https://openaccess.thecvf.com/content/CVPR2022/supplemental/Lim_Hypergraph-Induced_Semantic_Tuplet_CVPR_2022_supplemental.pdf)
provides the ResNet/CUB starting recipe: hidden width 512, temperature scale 32,
incidence scale 1.1, graph weight one; Adam rates 0.00012 for the model, 0.1 for
distributions and 0.0006 for the graph, with decay 0.00005. One complete epoch
warms the new components. Main-phase learning rates halve every five epochs.
Epoch length is `ceil(training_records / physical_batch_size)`. Warmup moments
are preserved. Selection excludes checkpoints that would precede full warmup
on the larger final-training population.

Audited numerical conventions are recorded against the pinned
[reference revision](https://github.com/ljin0429/HIST/tree/e7d650c80460f464c55bcdc2262d785923c50dc4):
unit features/means for distribution distances, log covariance clipped to [0,6],
He-normal distribution initialization; graph hidden BatchNorm and leaky ReLU
slope 0.1. The graph receives raw head outputs. Stable cross-entropy retains
all samples, including those whose naive exponential would underflow.

## Motion changes and evidence

The image backbone is replaced by MotionBERT. Confidence-positive final tokens
are pooled across people, time and joints using mean plus maximum, then projected
to 512 dimensions and normalized by non-affine LayerNorm. An empty valid-token
set pools to zero. Retrieval additionally normalizes to unit length and uses
cosine; graph/distributions participate only in training. The common physical
P=8,K=4 batch replaces ordinary random image sampling. Six paired seeds and
development-only step selection replace the image experiment's evaluation loop.
MotionBERT LayerNorm remains trainable; the image BatchNorm freeze has no direct
counterpart in that backbone.

Profiles execute the post-warmup backward pass without claiming warmup completion.
Tests check explicit degree matrices, diagonal covariance distances, positive and
negative incidence, both supervision paths, masking/pooling order, batch
permutations, warmup state retention, scheduler boundaries, exact restoration,
and rejection of missing optimizer moments. GPU feasibility and development
performance remain unmeasured for this adapter.
