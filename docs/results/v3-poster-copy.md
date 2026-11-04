# Robust human-motion retrieval from noisy pose sequences

Poster text draft, October 28, 2026. Results pending. Methods describe the
declared study; this draft grants no execution authorization.

## Question

Does the full contextual training recipe reduce clean-to-corrupt one-shot
top-1 degradation relative to standard contrastive training? We will compare
complete recipes on unseen actions, with one clean gallery exemplar per action.

## Motivation

Contextual metric learning compares within-batch neighborhoods and combines
contextual, contrastive and regularization terms. Its published image
robustness tests do not answer the pose-query question. MotionBERT supplies
the frozen representation and already uses pose noise/masking in pretraining;
we will measure the additional head-recipe effect.
([Liao et al., 2023](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf);
[Zhu et al., 2023](https://arxiv.org/html/2210.06551))

## Fixed comparison

We use HRNet-derived 2D pose annotations of NTU RGB+D 120. Selection will use
76,013 captures from 80 auxiliary actions and a fixed 20-action development
episode. Nine final heads will train on all 95,001 captures from 100 auxiliary
actions. Novel evaluation will use 20 official anchors and 18,884 primary
queries, excluding synchronized views of anchor performances; 18,924
exact-official queries form the descriptive secondary set.

The frozen MotionBERT encoder will feed identical biased 8,704-to-2,048 linear
heads with L2-normalized outputs. Every run will use 20 epochs, float32 AdamW,
physical batches of eight actions × four examples, and paired seeds 7/17/29.
Initial states and ordered batches will match across recipes within each seed.

| Recipe | Fixed distinction |
| --- | --- |
| Contrastive | Positive/negative cosine margins 0.9/0.6 |
| Full contextual | `0.4 L_context + 0.6 L_contrast + 0.1 L_reg`; margins 0.75/0.6; neighborhood 4; similarity target 0.25 |
| SupCon, descriptive | Single-view supervised contrastive; temperature 0.07 |

The 27 selection runs will test three rates per recipe with all three seeds,
ranking clean epoch-20 development top-1, then MRR, then lower rate. All nine
fresh final heads must be locked before novel opening.

## Query stress

Only queries will change, after preprocessing and before the encoder. Each
family starts clean: shared-field coordinate jitter at 1/2.5/5% torso scale,
nested masks of 3/6/8 joints, or nested masks of 10/25/40 frames. The gallery
stays clean. Sample/family seeds pair corruptions across heads; severities
share randomness. Missing observations, fallback scale and operators follow
the [fixed protocol](../protocol/protocol-v3.md).

## Primary analysis

```text
drop = clean top-1 - corrupted top-1
Delta = mean(contextual drop - contrastive drop)
```

The mean gives equal weight to three seeds and nine corruption cells, with
query weighting within cells. Negative Delta means less contextual degradation.
A paired 10,000-replicate within-action performance-group bootstrap will
support this claim only when its 95% interval's upper bound is below zero.
Seeds, actions, heads and anchors remain fixed. Repeated performances from one
person may remain dependent; the interval is conditional, not population-wide.

## Results and limits

Results are pending: clean accuracy, absolute corrupted accuracy, Delta and its
interval remain empty. All 180 cells, seeds, curves, costs and failures will
be retained. Smaller degradation need not mean higher corrupted accuracy; a
zero-crossing interval will be inconclusive. Complete-recipe differences cannot
isolate neighborhoods, and synthetic tensor stress cannot establish natural
camera robustness. Positive, null and negative results are valid outcomes.
This frozen study does not complete the historical 26-method fine-tuned v2 benchmark.

SCC jobs remain on hold pending additional space. New-kernel validation,
selection, final training and novel opening are incomplete; historical runtime
evidence is not acceptance of the new profile. The
[report draft](v3-report-draft.md) retains the methods, provenance and reporting
requirements.
