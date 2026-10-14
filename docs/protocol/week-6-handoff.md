# Week 6 handoff: October 19 to 25, 2026

Prepared during Week 5 execution. **Week 5 scientific admission remains held
after the independently reviewed ADR0007 implementation passed separate SCC
installation, allocated software rehearsal and successor preparation. Fresh
scientific regeneration remains pending. No successor is admitted.**
Read the [Week 5 execution record](week-5-execution.md),
[incoming handoff](week-5-handoff.md), [canonical plan](../../plan/research-plan.v3.md),
[ADR0006](../decisions/0006-v3-execution-completion-amendment.md),
[ADR0007](../decisions/0007-safe-validation-reuse-and-stage-capacity.md) and
[SCC runbook](scc-v3-runbook.md). This handoff does not authorize selection.

| Operational handoff field | Current status |
| --- | --- |
| Admitted successor release and protocol/design hashes | Immutable source f101f0e9d9bd64275d2088deab1b0bdcfcc53620 independently reviewed; 1,373 local tests passed, two historical AVSL source-parity skips. Separate SCC installation and independent completion review of CPU rehearsal 8044010 passed (128 checks, nine resource samples, intact seals). Preparation 8045152 passed independent completion review, including all eight original manifest identities and original → r1 → r2 scientific equality. Successor protocol SHA-256 18f7d17fa81e7ae3a6b1e5deddf42d9eda589d96e5a13968188a8ce275bfb95f; scientific admission pending. |
| Fresh cache/pilot/corruption/geometry/analysis receipts | Supplementary 8048540 passed independent completion review October 13 at 20:43:00 UTC: 86 checks, three commands, seven resources, both seals, 108 metadata and 616 source bindings, and both actual metadata tables. Receipt SHA 7703859e50361123de9054fba446c8384d423b8c549b69eab92720314c46c3d2. Geometry and remaining fresh scientific evidence/admission are pending; follow the Week 5 execution record. |
| Capacity report and immutable selection authorization | Prior measured-profile no-go retained; authorized CPU/GPU amendment and fresh capacity evidence pending; selection held |
| SCC jobs, logs and next command | SSH is restored; geometry 8070391 and diagnostic 8072666 remain preserved failures. Corrected diagnostic 8102231 completed October 14 at 20:49:21.682189 UTC: failed=0/exit_status=0, four omp slots, 17 whole-job CPU wall seconds, actual CPU=9.340 seconds. First observation 22:25:31.228546–22:25:43.899681 UTC; independent completion receipt f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36 passed at 22:34:14.167272 UTC, binding 184 metadata/617 external/616 sources, both commands/seals and six resources. The earlier queue-record verifier rejection is retained; the reviewed correction passed 93 checks and preserves numerical/host/resource guards. Native AVX512 matches failed-fresh 4/40/36; DEFAULT matches original four scales, 36/40 tensors and 32/36 rows. The tested recovery hypothesis is unsupported; full cause and compatible permanent profile remain unproven. Diagnose residual jitter differences before a new reviewed allocated confirmation. Next permitted scheduler inspection/preflight October 14 at 7:27 PM EDT (23:27 UTC). Never rerun any executed launcher or observation command. Root remains the sole controller/heartbeat; geometry, every successor, full A and capacity remain held. |

## Admission before the first selection job

Verify the unchanged design and predecessor binding under
`study-v3/revisions/execution-r2/`, preserving original and execution-r1 evidence.
Apply the complete ADR0007 regeneration inventory; retain source/identity/fallback
evidence through validated bindings without adopting old caches or pilots. Require
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
Resident timing 8038355 passed with 95,001 resident rows, 80 optimization
actions and paired fixed update plans. Component measurement 8038699 passed all three unchanged validators and
independent verification: P=778.274100575014 seconds exceeds the measured-profile
necessary bound of 305.840707965 seconds. The largest report's `452P` component
with 25% slack forecasts 122.145796 hours against the shared 48-hour limit.
This is a profile-specific no-go, not a universal hardware bound. The researcher
authorized ADR0007 for bounded numerical validation reuse and separate CPU/GPU
capacity accounting. The implementation passed independent review and the full
local suite. Allocated validation, regeneration, renewed measured capacity and
full admission remain pending. Neither timing nor this
diagnostic authorizes Week 6.
Native initialization replay also requires measured compatible CPU hardware and
runtime. A generic CPU request, or even a requested feature, is not sufficient:
verify actual CPU flags and exact native reproduction of the locked initialization
before the unchanged full validator. Preserve every validation check and failed
attempt; include the narrower compatible CPU queue pool in the forecast. See the
[recorded diagnostic and retry](week-5-execution.md) and
[reviewed allocation procedure](scc-v3-runbook.md). This requirement does not
authorize any future experiment.
Include fresh extraction, failed attempts, repeats, queues and review. Use the
slower pilot/full-size estimate per arm with at least 25% compute and researcher
slack. Each unsplit job must fit its usable window and scheduler limit. Start
with one scientific subprocess at a time; preserve the approved budget.

Keep current RAM/VRAM, filesystem and quota measurements with the ledger.
Admission requires
`min(filesystem_free, quota_remaining) >= 200*2**30 + 1.25*remaining_peak_bytes`.
The October 9 estimate of 120 decimal GB predates execution-r2 regeneration and
does not establish its capacity. Inventory retained evidence and execution-r2
additional peak bytes before admission; no successor numeric envelope is yet
verified. Existing artifacts already consume measured free space; do not count
them again as remaining work. Preserve all evidence.

The researcher confirmed 5 hours weekly normally, up to 10 if necessary. Record
planned contingency weeks explicitly and budget zero guaranteed hours for
November 23 to 29. These are availability bounds, not actual minutes. SCC access
is ordinary queued access without a claimed reservation. Target final lock
review by November 22; November 29 remains the hard deadline. Finish all compute,
including novel evaluation and independent report recertification, by December 6;
protect December 7 to 18 for analysis/delivery.

Lock all nine fresh final heads trained on 95,001 auxiliary rows before novel
opening, with complete authorization, independent audit and fresh capacity.
A null or negative result is successful research; keep splits, corruptions,
metrics and claims fixed after opening.

At handoff, reconcile jobs/outcomes, remaining slots and resources; verify the
live tracker and leave `remote` with release/job/log/artifact pointers and the
next command. Record Done, Next and Open issues. Distinguish technical completion
from formal closure. Preserve actual time as unreported at the researcher's
request; closure depends on required tasks and gates, not fabricated minutes.
