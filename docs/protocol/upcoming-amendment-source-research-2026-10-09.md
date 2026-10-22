# Source research for the upcoming v3 amendment

Date: **2026-10-09**. Prepared for the researcher's request to amend the upcoming
plan using the base paper and machine-learning evidence. These recommendations
use the existing plan and engineering evidence; no pilot accuracy values,
novel poses, embeddings or scores were inspected. This memo does not authorize
a campaign or change a scientific lock. The adopted amendment is recorded
separately.

## Evidence and choice

The recommended scope remains a comparison of **complete recipes** under a
fixed compute budget. Implementation readiness and auditable interpretation
offer more immediate value than expanding the December experiment.

| Primary source and exact location | Evidence relevant to this decision |
| --- | --- |
| [Liao, Tsiligkaridis and Kulis, ICML 2023](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf), Section 3, Equations 5–7; Appendix G; H.5; I.1/Table 6 | Balanced batches use neighborhood size equal to examples per label, at least four. Appendix G supplies the adopted contextual coefficients and margins; H.5 uses the different positive margin for plain contrastive. The regularizer is a distinct component and can improve other losses. Therefore retain the declared complete-recipe comparison, not a claim that neighborhoods alone cause any improvement. |
| Same paper, Sections 4.4 and 5, Appendix G/H.1 | The robustness experiments change training labels/images or withhold classes, not pose queries. Appendix G uses larger image batches, 80 epochs, a schedule and best test checkpoint; H.1 uses mixed precision. These are source settings, not instructions for the sealed pose study. Keeping our fixed endpoint, clean-development selection and float32 avoids changing the already verified experiment. |
| [MotionBERT, Zhu et al., ICCV 2023](https://arxiv.org/html/2210.06551), Sections 3.3 and 4.6, Tables 4–5 | Table 4 directly studies a frozen motion encoder with trained heads. Pretraining includes pose noise and masking. This supports the architecture choice and reusable features, while limiting the claim to an incremental head-recipe effect on an already pretrained encoder. Its published accuracies are not target scores for this study. |
| [Bouthillier et al., MLSys 2021](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf), Sections 2–3 and Appendix C.2 | Data sampling, initialization and hyperparameter search contribute uncertainty; paired comparisons can reduce variance. Keep pairing and disclose fixed sources of variation. Three seeds and one fixed split do not support population-wide algorithm superiority. This source does not validate our exact performance-cluster bootstrap. |
| [Dodge et al., EMNLP 2019](https://aclanthology.org/D19-1224/), Sections 2–4 | Model comparisons depend on search budget; validation outcomes and computation should be reported. Preserve the equal attempted search matrix and expose failures, retries, selection evidence and cost. |

The papers do not establish that our three seeds, three learning rates, 20
epochs, embedding dimension or corruption severities are optimal for poses.
Retain them as declared study choices with a completed engineering basis.
The same applies to any numeric audit-panel size below: it is an explicit
coverage budget, not a statistical power calculation.

## Recommended prospective specifications

### Keep the comparison fixed

Retain all three arms; physical `P=8, K=4`; seeds `7,17,29`; learning rates
`1e-4,3e-4,1e-3`; 20 epochs; fixed endpoint selection; and fresh final heads.
Keep the source-derived method-specific margins and contextual regularizer.
No larger grid, adaptive epoch choice, mixed precision or additional arm is
needed to resolve the identified planning issues. If the winning rate is an
endpoint, report **best among the tested rates**, without claiming a global
optimum or extending the grid automatically.

### Freeze a small, deterministic geometry panel and measure all rows

Use the development-primary query manifest only. Select the two smallest
`SHA256("protocol-v3|geometry-panel-v1|" + sample_id)` values within each of the
20 development actions, breaking digest ties by sample ID: **40 base rows**.
Add at most eight geometry sentinels, using the same hash tie-break:

1. Minimum strictly positive observed-support count.
2. Maximum observed-support count.
3. Maximum observed-support count for the second person.
4. Minimum strictly positive second-person observed-support count.
5. Minimum valid positive own torso scale.
6. Maximum valid own torso scale.
7. First hash among rows with observations but no valid own torso scale.
8. First hash among all-missing rows, if any exist.

An observed element is one person/frame/joint whose clean confidence is
positive. Deduplicate the union, giving **40–48 real rows**. Record unavailable
sentinel categories without substituting arbitrary cases. Freeze ordered IDs,
selection-rule version and hashes before corrupted scoring. Constructed
fixtures separately cover all-missing input, invalid own scale, each mask
boundary, absent/partly observed people and every required operator invariant.
An unavailable real category does not fail the gate if its constructed case
passes; a malformed/nonfinite source remains an artifact failure.

Run invariant checks and independent fresh-process deterministic repeats on
the complete panel for all nine conditions and severity zero. Generate fixed
condition-comparison inspection outputs from this panel; inspection cannot
change the operators or exclude queries.

During the already-required full development extraction, record damage on
**every query**, not just the panel. For masks report newly zeroed clean
observations, divided by clean observed support; an empty denominator is
`not_applicable`, counted separately. Report count, fraction and
minimum/median/p95/maximum, with zero-damage frequency. For jitter report
realized displacement relative to the scale actually used and fallback
frequency. Preserve clean missingness and confidence. None of these geometric
distributions imposes a model-accuracy floor or authorizes severity calibration.

### Make effect interpretation explicit without inventing a success threshold

The primary report should place these quantities together, in percentage
points: mean clean accuracy, mean absolute corrupted accuracy, mean drop, the
contextual-minus-contrastive drop difference `Delta` and its declared interval.
Check the arithmetic identity:

```text
Delta = (clean contextual − clean contrastive)
      − (mean corrupted contextual − mean corrupted contrastive).
```

Retain the existing confirmatory rule: the interval's upper bound must be
below zero. If it includes zero, report uncertainty; do not claim equivalence
or no effect. A supported smaller drop with worse absolute corrupted accuracy
must be described as that tradeoff. Absolute-score differences, individual
cells, SupCon, seed effects and leave-one-action-out results remain descriptive.

Choose **no minimum practically important difference** for this study: neither
the source papers nor an established deployment utility supplies one for this
pose task. Do not invent a 1- or 2-point threshold. Report magnitude, uncertainty
and cost transparently, with no labels such as “practically negligible” that
silently introduce a margin. A deployment claim or formal equivalence test
would need a separate justified prospective decision.

Keep the conditional interval caption prominent. Add a metadata-only summary
of performance groups, views, distinct performers and repeated-performer
concentration by action. This exposes the dependence structure without
pretending that a count table proves exchangeability. Do not silently change
the bootstrap or interpret 10,000 resamples as additional training runs.

### Adjudicate failure before looking at candidate accuracy

Use a small fixed classification with evidence links:

| Classification | Evidence and action |
| --- | --- |
| Infrastructure interruption | Scheduler/node failure, external filesystem error or verified resource interruption. Retain output; retry from scratch only after the cause is resolved, with identical scientific settings, initialization and batch plan in a new attempt. A larger allocation may fix a demonstrated capacity issue; it cannot change scientific settings. |
| Numerical or health failure | Approved inputs/runtime and a recorded nonfinite, zero-vector or existing collapse-check failure, without an identified infrastructure/implementation cause. The affected learning-rate candidate lacks three valid seeds and is ineligible. Do not retry until obtaining a favorable outcome. A pilot-stage health failure still blocks selection under the existing gate. |
| Implementation or provenance defect | Reproducible code/manifest/hash/role error. Stop the affected stage, make a dated correction, identify every affected artifact/comparison and regenerate/revalidate all affected work. |
| Unclassified | Preserve the attempt and hold adjudication. Do not call it an infrastructure failure or rank a partial candidate simply to proceed. |

Choose one automatic fresh retry for a resolved, evidenced infrastructure
incident; a second failure pauses that entry for diagnosis. This is a workload
bound, not a scientific optimum. Later retries need a new recorded cause and
resolution, not a new seed or rate. Failed infrastructure entries stay pending
until resolved; they are not silently converted into inferior candidates.

The final selection ledger must cover all 27 scheduled runs and link every
attempt/retry. Include valid updates, health results, eligibility, runtime,
memory, raw three-seed means, exact tie-breaks and the selected rate. Record
failure adjudication before producing the ranking. Repeat hardware failures
should improve the execution environment, not alter the comparison.

## Limits

These choices improve execution clarity and credibility, not expected
accuracy. No new data access, training, statistical analysis, code changes or
resource measurements were performed for this memo. The geometry rule must be
implemented and its actual IDs/coverage locked before it can pass a gate.
