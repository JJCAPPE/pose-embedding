# DRML-PA motion adapter

Status: callable independent implementation, verified with CPU component and
integration tests. GPU feasibility, tuning, convergence and comparative motion
performance remain unestablished. The complete final-suite seal still applies.

## Paper identity and equations

[Zheng et al., ICCV 2021, §§3–4](https://openaccess.thecvf.com/content/ICCV2021/papers/Zheng_Deep_Relational_Metric_Learning_ICCV_2021_paper.pdf)
defines four 128-dimensional individual FC branches, four reconstruction
decoders, eight 128-dimensional meta-relation FCs, a scalar linear relation
score, and a shared 256-to-128 updater. Updated branches concatenate to 512.

- Equations 2–3: mean unsquared L2 reconstruction error; minimum-error assignment.
  Reconstruction trains only decoders.
- Equations 4 and 10: sum the four assigned-subset metric objectives. These train
  the individual branches and trunk.
- Equations 5–8: directed relation `a_j(y)-b_i(y)`; divide its linear score by
  the incoming-score sum, aggregate source features, then update each node.
- Equation 10: final metric supervision trains only the relation module,
  blocking its gradients through the individual branches and trunk.
- Section 4.2: backbone learning rate `1e-5`, FC rate `1e-4`, reconstruction
  weight `0.1`, final embedding weight `10`.

The screenshot combines different DRML variants: CUB `68.7` and Cars `86.9`
are DRML-PA; SOP `79.9` is DRML-MDW. DRML-PA's SOP R@1 is `71.5`
(Tables 4–6). This configuration explicitly selects **DRML-PA**. It does not
implement DRML-MDW. The [supplement](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Zheng_Deep_Relational_Metric_ICCV_2021_supplemental.pdf)
also reports separate cross-validation experiments.

## Declared motion and numerical choices

Pool MotionBERT final tokens by the mean over people, time and joints, including
exactly tokens with input confidence greater than zero. An entirely invalid
clip produces a zero pooled feature. This global pooling replaces the common
head's retention of joint positions through flattening; its head recipe is
distinct for initialization pairing. The shared MotionBERT weights, paired
physical batches, seeds and split contract remain the benchmark's inputs.

Each individual branch has its own Proxy Anchor class proxies; final embeddings
have another proxy table. All use the pinned PML 2.9.0 PA objective with
`alpha=32`, `margin=0.1` and global class indices. Empty branch subsets skip
their individual/proxy optimizer update, including momentum and weight decay.
Assignment ties choose the lowest branch index. Decoder loss averages over
samples and branches; the individual branch losses sum.

The implementation uses literal linear scores and incoming sums. Negative
weights are permitted; a zero or nonfinite denominator fails the run. No
softmax, absolute-value normalization, epsilon denominator or extra activation
silently replaces Equation 7. Conditioning near zero remains an empirical
feasibility question to report during development.

AdamW, benchmark-configured weight decay, proxy learning rate `1e-4`, default
AdamW epsilon/betas and a constant learning-rate schedule are explicit study
choices where the paper does not supply a complete optimizer recipe. There is
no DRML warmup. The frozen supplementary track freezes only the backbone.
The final concatenated vector is L2-normalized for the benchmark's cosine
retrieval. Graph construction uses only one clip, with no gallery-dependent or
batch-dependent inference context. Decoders/proxies are retained in training
checkpoints but bypassed during retrieval.

## Verification and licensing

Tests cover hand-calculated graph weights/messages, negative weights, zero
denominators, unsquared reconstruction, assignment ties, each objective's
isolated gradient path, masked/empty pooling, assigned-subset PA, exact
inactive-branch skipping, unit-length batch-independent inference, and identical
next updates after restoring the model, criterion and optimizer.

Runner checkpoints bind all branch, decoder, relation and proxy shapes, named
optimizer groups, assignment history and per-branch update counters. Rehashed
corruptions of these records are rejected. Final evaluation reconstructs the
DRML head before any test-opening action.

No source from the official unlicensed DRML repository was copied, adapted or
vendored. Its recorded revision remains reference-only. The implementation was
written from the published mathematics; this document does not grant a new
repository license or authorize novel-test access.
