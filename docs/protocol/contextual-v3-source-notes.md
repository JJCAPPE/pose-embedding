# Contextual metric learning: source notes for v3 scoping

These notes inform a prospective, result-blind v3 protocol. They do not replace a
locked protocol or authorize opening the novel test. The primary source is
[Liao, Tsiligkaridis, and Kulis (ICML 2023)](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf),
especially Section 3, Equations 1–7 and Algorithm 1; Section 4.4; Section 5;
and Appendix E.3. The local [final prospectus](../proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf)
sets the motion study's intended question.

## What the paper establishes

- The proposed contextual similarity is computed from **within-batch neighbors**
  of normalized embeddings. It combines common neighbors and common
  non-neighbors, then performs reciprocal-neighbor query expansion. The
  neighborhood comparison uses a specified heuristic backward gradient. The
  contextual term fits that similarity to same-label indicators off the
  diagonal. The authors use balanced class batches and set neighborhood size
  `k` equal to the number of samples per class, with at least four in their
  experiments. [Paper, Section 3](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
- The full published objective is `λ L_context + (1−λ) L_contrast + γ L_reg`.
  `L_reg` targets the batch's mean cosine similarity; it is a distinct component,
  not part of contextual similarity. The paper reports that mixing contextual
  and contrastive terms works better than either alone in its image ablations.
  [Paper, Equations 5–7, Figure 7 and Appendix Table 5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
- Its controlled image comparisons hold the backbone and training setup common
  for reproduced loss baselines and tune learning rates separately. Several
  other published baselines in its tables were taken from their original papers.
  The paper reports R@1 and mAP; those image results are not motion estimates.
  [Paper, Section 5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
- The reported robustness tests perturb **training labels or training images**
  and withhold training classes. They do not establish robustness to missing or
  displaced pose joints and frames in novel retrieval queries. That is the
  prospectus's new empirical question. [Paper, Section 4.4](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf);
  [prospectus](../proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf).

## Minimum faithful motion adaptation

1. Keep the prospectus's frozen pretrained MotionBERT encoder, identical
   trainable head, one clean gallery exemplar per unseen action, class-disjoint
   development actions, paired initializations/batches/seeds, and prespecified
   query-only pose corruptions. This tests transfer of the *objective* to pose
   retrieval; it is not an end-to-end reproduction of the paper's image training.
   [Prospectus, Methodology](../proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf);
   [paper, Sections 3 and 5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
2. Implement the contextual formula from the paper's equations, including its
   neighbor-count convention, reciprocal query expansion, stop gradients, and
   heuristic backward rule. Use a physical balanced batch with at least four
   samples per class; gradient accumulation cannot reproduce its batchwise
   neighborhoods. Verify values and gradients on small hand-calculated cases
   before scientific training. [Paper, Section 3 and Appendix E.3](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
3. Make the **primary pragmatic comparison** full contextual recipe versus its
   contrastive-only component under matched representation, budget, selection
   rule, and retrieval scoring. Retain supervised contrastive as the prospectus's
   required secondary baseline. An additional contrastive arm with the same
   mean-similarity regularizer would help distinguish gains due to contextual
   similarity from gains due to `L_reg`; without it, attribute an effect to the
   *full recipe*, not uniquely to neighborhoods.
   [Paper, Equations 5–7 and Appendix Table 6](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf);
   [prospectus](../proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf).
4. Select objective-specific settings on clean development retrieval only and
   lock all seeds, corruption cells, metrics, manifests, code, and claim rules
   before one novel-test opening. Report clean and each corrupted **absolute**
   top-1 score as well as clean-minus-corrupt degradation, because a weaker
   clean model can have a smaller drop without better corrupted accuracy.
   Report every seed, compute and failures, and retain null or negative results.
   [Prospectus, Methodology](../proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf).

The current local v1 protocol already specifies the principal split, frozen
encoder, P=8/K=4 batch, three paired seeds and nine query-corruption cells in
[`configs/protocol.v1.yaml`](../../configs/protocol.v1.yaml). Its contextual
weight (`λ=0.2`) and target similarity (`0.0`) are motion-study choices, not
the paper's main 224-pixel image setting (dataset-specific `λ`, typically
`0.8–0.9` in Figure 7; fixed target `0.3`). The paper's separate 256-pixel
appendix experiment instead uses a cross-dataset recipe with `λ=0.4` and
target `0.25`. A v3 plan should justify or select motion values on development
data without using novel outcomes. [Paper, Section 5, Figure 7, and Appendix G](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).

The paper's Appendix H.5 uses a positive contrastive margin of `0.9` for its
contrastive-only baseline, versus `0.75` for the contextual recipe with
similarity regularization. It warns that `0.75` may be too small for the
unregularized baseline. A motion comparison should either declare these
method-specific settings or justify a shared margin; it should not silently
give the baseline the contextual margin. [Paper, Appendix H.5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).

The pinned [contextual repository](../../third_party/upstreams.toml) is marked
unlicensed and reference-only. These notes summarize the publication; no
upstream implementation should be copied, vendored, or adapted without rights
clearance.
