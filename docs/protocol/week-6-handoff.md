# Week 6 handoff: October 19 to 25, 2026

Prepared during Week 5 execution. **Week 5 scientific admission remains pending.**
Read the [Week 5 execution record](week-5-execution.md),
[incoming handoff](week-5-handoff.md), [canonical plan](../../plan/research-plan.v3.md),
[ADR0006](../decisions/0006-v3-execution-completion-amendment.md) and
[SCC runbook](scc-v3-runbook.md). This handoff does not authorize selection.

| Operational handoff field | Current status |
| --- | --- |
| Admitted successor release and protocol/design hashes | Pending final verification and SCC admission |
| Fresh cache/pilot/corruption/geometry/analysis receipts | Follow the Week 5 execution record; admission incomplete |
| Capacity report and immutable selection authorization | Pending |
| SCC jobs, logs and next command | Read `$HOME/pose-embed-scc/WEEK5-STATUS.txt` through `remote`; replace pending fields with verified results before transition |

## Admission before the first selection job

Verify the unchanged design and predecessor binding under
`study-v3/revisions/execution-r1/`, preserving original Week 4 evidence. Require
fresh parity, five clean caches including both complete 95,001-row repeats,
three complete paired pilots and independent validation.
Require the fixed geometry panel, all nine 18,929-query corruption encodings,
27 pilot projections/evaluations, full-query telemetry, and the
[analysis/report rehearsal](v3-software-rehearsal.md), whose synthetic results
do not establish scientific admission.

Bind the current seal audit, exact run matrix, all admission receipts and a
measured capacity decision in immutable selection authorization. Its calendar
must describe remaining windows at authorization time. If a prerequisite fails,
record the blocker in the tracker/repository and keep selection closed.

## Week 6 work and selection rules

Week 6 starts authorized paired runs, records clean endpoints and maintains
attempts/capacity. Week 7, October 26 to November 1, completes the matrix,
reproduces ranking and locks rates. Final training belongs to Weeks 8 and 9.

The matrix has exactly **27 slots**: Contrastive, SupCon and Contextual, each at
`1e-4`, `3e-4` and `1e-3`, each with seeds `7`, `17` and `29`. Freeze all slots
before launch. Use fresh heads, frozen MotionBERT, float32, physical `P=8/K=4`
batches and 20 epochs. Pair initialization/batches across methods and rates
within each seed; preserve all development identities.

Rank each arm's candidates by the unrounded three-seed mean epoch-20 clean
development top-1, then mean MRR, then lower learning rate. A candidate requires
three valid seeds. Retain all nine means or ineligibility reasons, every attempt,
retry lineage, updates, pairing hashes and costs. Exclude pilots, corrupted
scores, partial-seed means and earlier checkpoints. Endpoint winners do not
expand the grid; poor accuracy is valid.

| Failure category | Required treatment |
| --- | --- |
| Infrastructure | Preserve logs/accounting; restart identical inputs from scratch in a new directory. One automatic retry is allowed; further retries require diagnosis, remedy and renewed capacity. |
| Numerical | Preserve the failure and make its candidate ineligible. Repeated launches cannot seek a passing seed. |
| Implementation/provenance | Block the affected stage. Record a result-blind correction, identify every affected comparison and follow release/revalidation requirements. |
| Unresolved | Preserve evidence and block eligibility. Do not relabel an unexplained failure as infrastructure. |

If an arm has no eligible candidate, stop for a documented result-blind amendment.
The ledger validator rejects omitted preserved selection attempts. Lock selected
rates only after the full matrix is accounted for and independently reproduced.

This single-slot template was checked with `train --help`. Resolve variables
from admitted bindings and a new attempt directory; run only in a verified
allocation after admission. Fill the actual release/paths/scheduler command
before handoff.

```bash
.venv/bin/pose-embed train \
  --config "$SELECTION_CONFIG" \
  --protocol-config "$POSE_EMBED_V3_PROTOCOL" \
  --input "$DEVELOPMENT_CACHE" --manifest "$DEVELOPMENT_MANIFEST" \
  --output-dir "$NEW_ATTEMPT" --device cuda --stage development_selection \
  --development-gallery "$DEVELOPMENT_GALLERY" \
  --development-queries "$DEVELOPMENT_QUERIES" \
  --development-gallery-manifest "$DEVELOPMENT_GALLERY_MANIFEST" \
  --development-query-manifest "$DEVELOPMENT_QUERY_MANIFEST"
```

## Capacity, later deadlines and closure

Budget complete command wall time, including CPU hashing, source/cache validation,
checkpoint-to-projection replay, scoring, serialization and report regeneration.
Use the [verified validation call-count audit](week-5-capacity-validation-audit.md)
when forecasting repeated checks and the indivisible report commands; runtime
feasibility still requires measurements.
Include fresh extraction, failed attempts, repeats, queues and review. Use the
slower pilot/full-size estimate per arm with at least 25% compute and researcher
slack. Each unsplit job must fit its usable window and scheduler limit. Start
with one scientific subprocess at a time; preserve the approved budget.

Keep current RAM/VRAM, filesystem and quota measurements with the ledger.
Admission requires
`min(filesystem_free, quota_remaining) >= 200*2**30 + 1.25*remaining_peak_bytes`.
The 120 decimal GB campaign envelope includes originals, successor artifacts and
development projections. Existing artifacts already consume measured free space;
forecast additional peak bytes without double counting. Preserve all evidence.

The researcher confirmed 5 hours weekly normally, up to 10 if necessary. Record
planned contingency weeks explicitly and budget zero guaranteed hours for
November 23 to 29. These are availability bounds, not actual minutes. SCC access
is ordinary queued access without a claimed reservation. Target final lock
review by November 22; November 29 remains the hard deadline. Finish novel
evaluation by December 6 and protect December 7 to 18 for analysis/delivery.

Lock all nine fresh final heads trained on 95,001 auxiliary rows before novel
opening, with complete authorization, independent audit and fresh capacity.
A null or negative result is successful research; keep splits, corruptions,
metrics and claims fixed after opening.

At handoff, reconcile jobs/outcomes, remaining slots and resources; verify the
live tracker and leave `remote` with release/job/log/artifact pointers and the
next command. Record Done, Next and Open issues. Distinguish technical completion
from formal closure and request missing researcher time information.
