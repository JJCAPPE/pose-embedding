# Third-party notices

This repository does not currently grant a repository-wide reuse license.
Third-party materials retain their original copyrights and licenses.

## Contextual Similarity Optimization

The contextual loss implementation in `src/pose_embed/losses/contextual.py` is
an auditable adaptation of the equations described in:

> Liao, N., Tsiligkaridis, T., and Kulis, B. “Supervised Metric Learning to Rank
> for Retrieval via Contextual Similarity Optimization.” ICML 2023.

Paper: https://proceedings.mlr.press/v202/liao23b.html

The unlicensed contextual-repository snapshot at commit
`8433dcb67c2205c0e30ec07ed1e5b2fb92da016d` is used only as behavioral evidence
that the gated comparison composes `MultiSimilarityMiner()` and
`MultiSimilarityLoss()`. No source is copied from that repository. The executable
comparison uses the public API of the separately licensed
`pytorch-metric-learning==2.9.0`, pinned in this project's dependency lock. To
avoid inheriting future library defaults silently, the registered composition
passes every controlled value explicitly: loss alpha 2, beta 50, base 0.5;
miner epsilon 0.1; and normalized cosine distance with p=2 and power=1.

## MotionBERT

The action-head shape and pooling semantics in
`src/pose_embed/models/action_head.py` are adapted from the MotionBERT
`ActionHeadEmbed` implementation:

> Zhu, W. et al. “MotionBERT: A Unified Perspective on Learning Human Motion
> Representations.” ICCV 2023.

Paper: https://openaccess.thecvf.com/content/ICCV2023/html/Zhu_MotionBERT_A_Unified_Perspective_on_Learning_Human_Motion_Representations_ICCV_2023_paper.html

Upstream repository: https://github.com/Walter0807/MotionBERT

No MotionBERT checkpoint or NTU RGB+D sample is redistributed here. Before any
third-party source is copied or released, inspect and preserve its exact license
and attribution terms.
