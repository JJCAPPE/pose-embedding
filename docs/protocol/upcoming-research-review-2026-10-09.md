# Upcoming research review — October 9, 2026

Review of the frozen v3 plan and implementation at `033e1e3`, using the verified
October 8 engineering evidence. **Recommendations only: no protocol amendment,
tracker change, scientific run or novel access is authorized by this note.**
No pilot accuracy values were used in this review. SCC resources were not
remeasured; dated measurements below are not reservations.

## Assessment

The design is strong for a focused comparison of complete training recipes on
one frozen encoder, one dataset and a fixed synthetic corruption mixture. It
already controls initialization, physical batches, seeds, training duration,
learning-rate search, query identities and final-test access. It accepts null
or negative outcomes and correctly distinguishes smaller degradation from
better absolute corrupted accuracy.

The main risk is execution readiness and the interpretation of a narrow result.
The design does not isolate contextual neighborhoods from margins and
regularization, or establish generalization over new seeds, people, galleries,
datasets or natural camera errors. These are acknowledged scope limits, not
newly discovered omissions. Keep them prominent in the final claims.

## Prioritized improvements

### 1. Resolve future-stage code and freeze compatibility before selection

Verified implementation gaps:

- `training/runner.py:228` unconditionally rejects scientific final training.
- `motionbert_features.py:91` rejects novel extraction; its manifest/loader
  path is currently auxiliary-only.
- Both files are bound by `protocol_v3.py:143`; the design validator rejects
  changes to that file set at line 271.
- `protocol_v3_campaign.py:13` still refuses selection authorization after
  validating the proposed record's schema.
- `evaluation/runner.py:78` refuses corrupted development scoring.
- `report.py:95` calls the legacy primary analysis although the required
  within-action v3 implementation exists in `evaluation/analysis.py:425`.

The [plan already requires these stages](../../plan/research-plan.v3.md#7-concrete-architecture-work),
but the [Week 5 handoff](week-5-handoff.md) names only two of these integration
gaps. Add an explicit implementation/dependency milestone before the sweep:
document which future-stage interfaces can preserve the existing frozen code,
which changes invalidate which artifacts, and the corresponding revalidation
or regeneration cost. Do not remove guards or relax hashes to make a run start.
This does not invalidate the completed Week 4 evidence under its own release.

Rehearse the authorization → extraction → head application → scoring → report
chain on permitted fixtures/development evidence before selection. Acceptance
must cover the v3 analysis dispatch, exact 180-cell structure, missing/duplicate
cells, role/subset identity, clean-only selection, partial opening recovery and
denial of training after opening. Retain the later independent pre-opening audit.

### 2. Specify the Week 5 geometry evidence precisely

The operators, severities, fallback, nesting and zero-damage reporting are
already fixed. What remains unspecified is the geometry panel's exact size,
selection rule/IDs and the denominators of damage summaries.

Freeze a metadata/geometry-selected development panel before corrupted scoring,
covering actions, missingness and two-person examples, plus constructed boundary
fixtures. Record panel IDs, fresh-process output hashes and pass/fail evidence
for each invariant. Report newly masked observations as counts and fractions
of previously observed support, jitter displacement relative to torso scale,
fallback frequency, and damage distributions including zero damage. Do not
redraw corruptions, change severities or exclude difficult queries based on scores.

### 3. Freeze the interpretation and report layout early

The existing rule already requires clean accuracy, absolute corrupted accuracy
and degradation together. Make it a tested report template with the identity:

`Delta = clean contextual-minus-contrastive gap - mean corrupted gap`.

An invented example illustrates the distinction: 60% → 55% loses fewer points
than 80% → 70%, yet has worse corrupted retrieval. Show the estimate and interval
in percentage points beside both absolute accuracies. Reserve the confirmatory
claim for the existing upper-bound-below-zero rule. An interval crossing zero
does not establish equivalence or absence of an effect.

Explain what magnitude would matter scientifically, with a rationale unrelated
to test outcomes. A descriptive magnitude discussion can preserve the current
decision rule; a new equivalence margin, co-primary endpoint or success threshold
would be an analysis amendment, not a reporting clarification.

### 4. Make uncertainty and failure adjudication inspectable

The declared bootstrap handles synchronized views within a performance, while
repeated performances by one person can remain dependent. Before selection,
produce a metadata-only table per action: performance groups, views per group,
distinct performers and concentration of repeated contributions. This makes
the assumption assessable; it does not prove independence.

Keep the interval's conditioning on fixed seeds, actions, gallery and realized
corruptions in the main result caption. Show all three seed effects and the
already-required leave-one-action-out sensitivities. A different resampling
unit or additional inferential test requires a documented amendment.

Specify failure reason codes and retry evidence before ranking: scheduler or
filesystem interruption versus numerical failure versus implementation defect.
Freeze eligibility independently of accuracy. The selection table should show
all 27 attempted settings, actual updates, failed attempts/retry lineage,
three-seed candidate means, exact tie-breaks and cost. An endpoint learning rate
is the best among the tested settings; it does not authorize expanding the grid.

### 5. Replace calendar guesses with a measured execution ledger

The [pilot evidence](week-4-execution.md#fresh-caches-and-pilots) gives scheduler
times of 502/525/415 seconds and training-stage times of
286.739518/323.617977/254.941551 seconds for Contrastive/Contextual/SupCon.
For a provisional estimate, let `S` be scheduler time and `T` training time:

- Selection per arm: `9 * S`.
- Final training per arm: `3 * [S + T * (59380/47520 - 1)]`.

This retains observed non-training overhead rather than claiming savings from
fewer endpoint snapshots. It gives approximately **3.605 allocated hours for
selection + 1.382 for final training = 4.987 hours; 6.233 with 25% slack**.
It is not a passing capacity forecast: full-size resident-array timing, other
seeds/rates, corruption extraction, generic CPU projection/revalidation, report
generation, retries, queues and future allocations remain additional or
unmeasured. Use the slower required full-size measurements when available.

The inference is that raw head training is unlikely to consume the multiweek
calendar by itself; implementation, audit, queue and researcher time need an
explicit critical path. Use measured allocation limits and deterministic job
dependencies. Grouping fresh subprocess runs within an allocation may reduce
queue/setup costs, but must preserve separate immutable attempts, initialization,
batch plans, failure handling and demonstrated resource bounds.

### 6. Implement the already-planned reuse and measure CPU/I/O cost

The plan correctly specifies nine development corruption encodings reused by
three pilot heads, and ten novel query-condition encodings plus one clean
gallery encoding reused by all nine final heads. The 180 result cells are not
180 encoder passes. Verify the covered IDs and reuse explicitly in the campaign
manifest. Keep the required primary/official files and exact ordered subset
checks; changing to shared views is a separate storage design change.

`features.py` performs CPU projection; `artifacts.py:347–409` recursively
revalidates the base cache and recomputes the complete projection with exact
equality. `evaluation/runner.py:330` invokes those checks again before loading
inputs. Time hashing, loading, projection, validation, retrieval and serialization
separately during Week 5. Reuse immutable outputs in orchestration first.
Persistent validation caching, GPU projection, different dtypes or omitted
checks are not free optimizations: they need appropriate equivalence and
provenance verification, including tamper rejection and freeze compatibility.

The storage table does not separately itemize 27 persisted development-corruption
query projections (three heads × nine conditions). Their uncompressed payload
is about **4.232 decimal GB**, plus **511,083 per-query result rows**. Explicitly
allocate these within or beyond the existing 10 GB allowance. Include staging,
validation receipts, retries and any regeneration from item 1. Avoid counting
existing retained files twice. The October 8 observation of roughly 1 TB quota
free supersedes the old shortfall as a dated observation; remeasure instead of
treating either reading as a permanent fact or a future allocation.

## Scope recommendation

Keep the three recipes, paired seeds, fixed 20 epochs, finite learning-rate grid,
corruptions, primary estimand and sealed test intact. Prioritize the execution
and reporting clarifications above. Larger batches, mixed precision, adaptive
epochs, extra seeds, new corruptions and additional inferential tests are not
routine speed improvements under this frozen design.

An optional frozen-encoder/no-trained-head cosine reference could contextualize
what the learned heads add without new training or encoding. It would still
add evaluation scope and change the locked reporting matrix; it requires an
explicit prospective amendment. It is distinct from the deliberately omitted
regularizer-only ablation and is not necessary for the existing recipe claim.
Do not delay the required December study for either extension.

## Primary-source support

- [Bouthillier et al., MLSys 2021](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf):
  data sampling, initialization and hyperparameter search materially affect
  benchmark variance. This motivates keeping the plan's conditional uncertainty
  and complete selection evidence visible; it does not validate this exact
  bootstrap assumption.
- [Taori et al., NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/hash/d8330f857a17c53d217014ee776bfd50-Abstract.html):
  their ImageNet study finds limited transfer from synthetic to natural-shift
  robustness. Applying that caution to pose tensors is an interpretation limit,
  not direct evidence about the performance of these pose recipes.
- [Dodge et al., EMNLP 2019](https://aclanthology.org/D19-1224/):
  model comparisons depend on search budget; disclose development outcomes and
  computational budgets. The existing equal attempted budget is a strength.
- [Hendrycks and Dietterich, ICLR 2019](https://web.engr.oregonstate.edu/~tgd/publications/hendrycks-dietterich-benchmarking-neural-network-robustness-to-common-corruptions-and-perturbations-iclr2019.pdf):
  fixed corruption benchmarks and protection against corruption-specific tuning
  motivate separating geometric verification from model selection.
- [Wang et al., SimpleShot](https://arxiv.org/abs/1911.04623):
  simple nearest-neighbor feature baselines can be informative in few-shot image
  classification. This only motivates considering an optional reference; it
  predicts neither a strong pose baseline nor a contextual improvement.

These recommendations aim for clearer conclusions and less avoidable work.
They do not promise higher model accuracy. This was a document/code review with
independent methodological and compute reviews, not a new scientific benchmark.
