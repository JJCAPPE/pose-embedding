# DIML motion adaptation: fixed MS + miner variant

## Source identity and scope

The required `diml` row is implemented as the explicitly named
`motion_ms_miner_512_time_anatomy_v1` recipe. This choice is fixed before novel
outcomes. It is a motion adaptation of DIML, not a claim to reproduce every
image configuration with one training recipe.

The [ICCV paper](https://openaccess.thecvf.com/content/ICCV2021/papers/Zhao_Towards_Interpretable_Deep_Metric_Learning_With_Structural_Matching_ICCV_2021_paper.pdf)
Table 4 associates CUB 68.15 with MS + DIML, and Cars 87.01 with Proxy Anchor +
DIML, both 512-D. Its Table 2 associates SOP 79.26 with Margin + DIML; §4.1 uses
128-D unless specified otherwise. The contextual paper's rounded row therefore
mixes base losses, and its blanket 512-D caption does not resolve the SOP
source discrepancy. These scores must not be treated as one exact recipe.

DIML Eqs. 2–9 define local cosine costs, entropic transport, and cross-correlation
marginals. [Supplement A](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Zhao_Towards_Interpretable_Deep_ICCV_2021_supplemental.pdf)
uses a 4×4 local map, entropy coefficient 0.05, and global shortlist 100 followed
by the sum of global and structural similarities. The selected variant uses
ordinary MS + miner training and DIML after training; optional structural-loss
training is outside this fixed variant.

The official repository is unlicensed/reference-only at the revision in
`third_party/upstreams.toml`. The implementation was written independently from
the published mathematics. No upstream implementation source was copied or
adapted; no image numerical-parity claim is made.

## Declared motion conventions

- MotionBERT's final `[person,time,joint,channel]` tokens supply the features.
  Confidence greater than zero marks valid input tokens. A masked global mean
  across people, time, and joints replaces image global average pooling.
- Four consecutive temporal bins use integer boundaries `i*T//4`. Four
  nonoverlapping H36M-17 groups are torso/head `{0,7,8,9,10}`, left arm
  `{11,12,13}`, right arm `{14,15,16}`, and legs `{1,2,3,4,5,6}`. Their Cartesian
  product gives 16 local sites; these replace image ROI-aligned spatial cells.
- Each site averages valid tokens over its people, frames, and joints. People
  are pooled symmetrically; no actor identity or cross-person correspondence is
  inferred. Temporal bins retain coarse order while transport can match across
  any local sites. This differs from image spatial geometry and must be stated
  when interpreting results.
- One biased linear projection from token channels to 512 dimensions is shared
  by the global and all local descriptors. Global output is L2 normalized for
  MS + miner training. Local outputs are normalized when forming cosine scores.
  This shares learned parameters without an auxiliary local projection.
- All-invalid global/site outputs are zero even if projection bias is nonzero.
  Empty temporal bins are invalid. Invalid local sites receive zero mass.
- A source site's marginal uses its own local vector against the target global
  vector; the reverse marginal uses target local against source global. This
  follows the cross-correlation prose and resolves Eq. 8's inconsistent
  source/target superscripts dimensionally. ReLU is followed by normalization;
  if every valid correlation is nonpositive, mass is uniform over valid sites.
  If either sample has no valid local sites, structural similarity is zero.
- Costs are `1 - cosine`. A double-precision log-domain Sinkhorn solver uses
  entropy 0.05, marginal tolerance `1e-7`, and at most 10,000 updates. A pair's
  first converged plan is frozen independently of its processing chunk.
  Nonconvergence raises an error; no silent lower-precision or cosine fallback
  is allowed.
- Self and every synchronized camera view are excluded **before** taking the
  global cosine top 100 eligible candidates. The prefix is reranked by
  `global cosine + transport-weighted local cosine`; the rest keep global
  order. A constant offset of four encodes prefix priority without changing
  within-prefix scores. Exact score ties retain gallery manifest order.
- Query and pair chunk sizes change working memory, not eligible candidates or
  ranking rules. Pair chunks default to 64. Loss, scoring, and numerical settings
  are recorded in the hash-bound registry. The optimizer/batch/seed schedule is
  the declared motion campaign recipe; it is not represented as an exact image
  training recipe.

## Evidence and cost

The default 512-D global vector is accompanied by 16×512 local float32 values
and 16 validity booleans: **34,832 array bytes per sample**, versus 2,048 bytes
for a single float32 512-D vector. This excludes archive-container overhead and
model-wide parameters. Reporting only the nominal 512 dimensions would conceal
DIML's storage cost. Runtime scoring uses double precision and additional
working memory; saved descriptors stay in the encoder output dtype.

Development histories record full descriptor shapes, dtypes, bytes, measured
encoding seconds, and measured scoring seconds. Final structural evaluations
write immutable descriptors, storage metadata, timing/environment metadata,
ranks, and hashes. Report validation rebuilds the scoring head from the selected
checkpoint, reloads all descriptors, reruns scoring, and compares rank evidence.
It also validates the method-specific scoring policy while comparing common
relevance/exclusion/tie policies across methods. Ordinary cosine results retain
the existing format and nonzero-vector requirement.

Component tests cover a closed-form entropic 2×2 example, asymmetric and zero
marginals, nonconvergence, opposite-global correlations, zero-mass behavior,
masked time/anatomy pooling, person invariance, shared projection gradients,
shortlist exclusions, query/pair chunk parity, checkpoint reconstruction,
archive tampering, and rehashed descriptor/rank inconsistencies. CPU synthetic
runner tests exercise training and structural validation. These are local
implementation checks; full MotionBERT parity, SCC profiling, selection, six-seed
training, and novel evaluation remain separate required evidence.
