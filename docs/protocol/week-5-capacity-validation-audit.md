# Week 5 capacity audit: repeated validation

## Historical execution-r1 audit

The execution-r1 implementation repeatedly validates complete evidence when a later
command consumes it. These calls must enter the capacity forecast. **The call
counts below are verified. The October 12 P measurement now rejects the
necessary capacity condition on the measured runtime profile.** No
scientific run, authorization or novel opening follows from this audit.

Audited source: `731938a157be575ee433d6939876f8ca0b95e459`. Source line references
below refer to that release. The audit covers the successful path after Week 5
admission, with all 27 selection slots valid, nine final heads, no retries, one
final-lock verification, one complete report and one independent recertification.
Additional attempts and repeated checks increase the work.

## Validator definitions

| Symbol | Complete call and nested work |
| --- | --- |
| A | [Admission validation](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/protocol_v3_campaign.py#L411): three complete pilot validators, nine corrupted base-cache validators, 27 projected gallery/query pairs, 27 retrieval replays, geometry and receipt checks. |
| T | One successful [selection-run validator](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/training/runner.py#L1028), including its epoch-20 checkpoint, clean source caches, CPU projections and ranks. |
| V | One [final-run validator](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/protocol.py#L1513), including the final-stage validator and complete 95,001-row source/batch/checkpoint evidence. It has no development-score replay. |
| S | [Selected-configuration validation](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/protocol_v3_campaign.py#L839): `A + 27T`. |
| F | [Full final authorization](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/protocol_v3.py#L423): `S + 9V`, hence `A + 27T + 9V`. |

These equations count nested calls; surrounding manifest, hash, registry and
other bookkeeping costs also remain. They are not an instruction to add
overlapping inclusive timings twice. There is no memoization of these complete
validator calls.

The standalone CPU `validate-pilots` duration, D, is not an isolated measurement
of A or F. Its receipt includes the three mandatory pilot-validator calls, P,
plus script setup, design/cache hashing and fixture checks. Command wall time
also includes process overhead; scheduler wall time additionally includes the
native-initialization preflight and environment setup. Therefore D is an
inclusive operational measurement, **not a proven lower bound on A or F**.
Do not subtract guessed overhead or multiply D as though it were P. Measure
complete A later on the intended compatible CPU/BLAS profile; if P is needed
separately, time its three actual validator calls inside an allocation.

## Exact operation counts

| Remaining operation | Heavy validator calls |
| --- | --- |
| 27 selection training commands | `27A` |
| Selected-configuration freeze | `A + 27T` |
| Nine final training commands | `18A + 243T` |
| One final-lock verification | `F` |
| Ten official novel encodings and one gallery encoding | `22F`; first opening also `9V` |
| Ten primary-query subset exports | `40F` |
| 180 query projections and nine gallery projections | `279F` |
| 180 evaluations | `810F + 180V` |
| Complete report build | `451F + 18V` |
| Independent report recertification | `452F + 18V` |

The trainer separately requires admission and selected configurations for each
[final training launch](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/training/runner.py#L228).
A [novel base-cache validation](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/motionbert_features.py#L528)
calls F. A primary cache also recursively validates its official source, so it
costs `2F`; [primary export](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/novel_subset_v3.py#L23)
therefore costs `4F`. Projection validation follows its base-cache lineage.
[Evaluation](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/evaluation/runner.py#L242)
costs `4F + V` for an official query and `5F + V` for a primary query.
[Report provenance](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/report.py#L681)
revalidates every gallery/query pair; failure accounting adds nine V calls.
[Recertification](https://github.com/JJCAPPE/pose-embedding/blob/731938a157be575ee433d6939876f8ca0b95e459/src/pose_embed/report.py#L1495)
also performs its own initial F call.

The table totals `2055F + 46A + 270T + 225V`, expanding to:

- **2,101 A calls**, including 6,303 complete pilot validations;
- **55,755 T calls**;
- **18,720 V calls**.

Each A replays four scored pilot snapshots per arm (epochs 5, 10, 15 and 20),
plus 27 corrupted-query projections: `3*4 + 27 = 39` complete development-query
CPU projections. Each T adds one. Thus this path includes
**`2101*39 + 55755 = 137694` auxiliary query CPU projection replays**, before
the direct novel projection/retrieval work. These are repeated checks of
preserved evidence, not additional trained heads.

Separate post-command validation of all 21 novel base caches and 189 projected
caches would add `310F`; one standalone check per completed training run adds
`27T + 9V`. The table budgets one final-lock verification; any additional lock
assembly/review checks must be added.

## Capacity decision still required

Report build and recertification are currently indivisible commands. For the
larger command, `452F + 18V`, a 12-hour usable allocation with 25% slack requires
the complete runtime of F to be **less than 76.46 seconds**:
`43200 / 1.25 / 452 = 76.46017699`. This is only a necessary condition: the V
calls, report work and other overhead must also fit. Shorter usable windows
make the bound stricter. The call graph alone does not establish actual runtime.

Twelve hours is the runbook's default request, not SCC's maximum. BU documents
up to 720 hours for shared CPU/OMP jobs and 48 hours for GPU jobs in its
[job-submission guidance](https://www.bu.edu/tech/support/research/system-usage/running-jobs/submitting-jobs/).
Most shared buy-in nodes accept only requests of 12 hours or less, so longer
requests reduce the eligible pool; see
[resource selection](https://www.bu.edu/tech/support/research/system-usage/running-jobs/resources-jobs/).
A forecast may use a longer CPU window only with evidence for scheduler access,
the dated window and queue allowance. No future allocation is claimed here.

The current opening preflight also applies the same campaign-wide
`maximum_job_seconds * compute_slack` to the remaining wall time in the
actual L40S allocation. A longer CPU report window alone cannot resolve this
shared limit. Even at BU's 48-hour GPU maximum, the report pair's larger command
requires F below `172800 / 1.25 / 452 = 305.84070796` seconds, before other
overhead or elapsed allocation time. This necessary bound is applied to the measured P component below; no frozen
source has been changed.

Before any eventual admission after the blocker is resolved, measure complete
real admission validation on SCC, including pilot CPU replay,
corruption validation, hashing, archive loading and geometry. Use measured
epoch-20 replay and full-size source validation to forecast T and V conservatively;
label future final/novel estimates as forecasts until those stages can be
measured. Include all nested checks, the report pair, serialization, RAM/VRAM,
storage reserve, queue allowance and slack. Preserve the approved scientific
budget and every safeguard; keep the affected gate closed if the forecast does
not fit.

Pre-opening work is `46A + 270T + F`. Post-opening generation/evaluation is
`1151F + 189V`, and the report pair adds `903F + 36V`. The current capacity
schema admits evaluation compute windows only through December 6; it has no
separate December 7–18 compute bucket. Budget the report pair before December 6
under that schema, while protecting later researcher time for interpretation
and delivery. Do not silently omit report compute or count unavailable windows.

## October 12 measured-profile no-go

Allocated diagnostic **8038699** on Sapphire Rapids Gold-6426Y (`scc-ke2`, four
CPU threads/slots, native PyTorch 2.9.1+cu128, NumPy 2.4.6) passed the three
unchanged pilot validators in persisted report order. The sum was
**P = 778.274100575014 seconds**. Independent completion verification passed
1,276 metadata bindings, 17 resource samples, both seals, accounting and actual
native runtime/call-order checks; the [execution record](week-5-execution.md#verified-component-measurement-and-capacity-no-go--october-12)
retains its exact receipt/hash and chronology. Neither setup nor the synthetic
native preflight is inside P. This is not a controlled cold-cache benchmark.

| Component forecast using this measured profile | Before slack | With 25% slack |
| --- | ---: | ---: |
| Pilot component of largest indivisible report, `452P` | 97.716637 h | **122.145796 h** |
| Pilot component of complete remaining successful path, `2101P` | 454.209413 h | 567.761766 h |

The first row already exceeds the shared **48-hour** GPU-opening maximum by
**2.544704 times**, before other A/T/V/report work. BU's published GPU/OMP limits
were rechecked on October 12; the sources above still specify 48/720 hours.
Because the frozen capacity and opening checks share one maximum-job value,
requesting a longer CPU report job does not resolve the opening constraint.

These are dated measured-profile component forecasts, not measured full A, F,
report durations, a complete feasible calendar, or universal hardware bounds.
They do not establish that every compatible runtime would fail. A replacement
profile would have to improve P by more than 2.544704 times merely to leave room
for omitted costs, and must pass all exact reconstruction checks; no such profile
or allocation is claimed. The 36 configured compatible queue instances are not
reservations. Queue/setup/retries and report completion before December 6 remain
in the eventual complete forecast. Availability remains five researcher hours
weekly normally, ten when needed, and zero guaranteed Thanksgiving hours;
actual time is unreported.

**Historical decision: no-go on the measured profile.** Full A and selection
were held rather than fabricating a passed capacity candidate. The no-go receipt
and the earlier prohibition on memoization remain evidence of execution-r1.

## Authorized successor, October 12

The researcher subsequently authorized
[ADR0007](../decisions/0007-safe-validation-reuse-and-stage-capacity.md) for
command-local numerical proof reuse and separate CPU/GPU capacity accounting.
Implementation and independent review passed before source release
`f101f0e9d9bd64275d2088deab1b0bdcfcc53620` was frozen. Separate SCC installation,
allocated rehearsal and preparation passed independent completion review;
scientific regeneration, admission and a measured feasible calendar remain
pending. The predecessor evidence above is not relabeled.

The amendment retains every complete A, T, V, S and F validator invocation and
all fresh hash, provenance, seal, inventory and authorization checks. Its initial
reuse is limited to successful pilot snapshot numerical replay and trained-feature
projection equality within a command. Thus the historical nested **call counts
remain useful**, but multiplying the old P by those counts does not forecast the
successor: repeated numerical work may be reused while full content rehashing
and other checks still recur. Fresh commands and independent recertification
start with no proofs. Measure both first-use and repeated costs, including the
remaining hashing and whole-command overhead, before making any capacity claim.

Schema-2 receipts classify each complete job as CPU or GPU. CPU report work must
fit dated CPU windows and complete-job limits; all CPU validation/I/O inside a
GPU job stays in that GPU job's wall time. Both classes require nonoverlapping
windows, queue/setup allowance, 25% slack, retained storage/reserve, the original
deadlines and researcher availability. A longer CPU window cannot justify a GPU
job exceeding its own allocation. Ordinary SCC access is not a reservation.

The successor requires its full regeneration inventory, independent checks and
fresh full A before selection authorization. No method, seed, epoch, physical
batch, metric, corruption or opening safeguard is reduced. Actual time remains
unreported; technical completion and weekly closure remain pending.

## October 13: successor geometry failure and runtime probe

Successor geometry 8070391 consumed 229 scheduler wall-clock seconds and failed its
fixed-panel identity wrapper. Keep that whole-job cost and failed attempt;
tracked checker completion does not admit geometry. Metadata comparison found
all 43 clean hashes unchanged but 2,051 candidate scales and 129 jitter hashes
different. CPU dispatch remains an unproven cause.

Diagnostic 8072666 was submitted at 22:49:45 UTC and observed queued at
22:52:26 UTC. It compares native/default dispatch in two fresh CPU workers on
four fixed cases; there is no measured result or capacity evidence yet. The
1-GiB reserve covers 67,480,406 bytes of additional metadata/logs, with no archive
copy; it is not a campaign forecast. Keep complete scheduler wall time, including
setup, hashing and both commands, distinct from command-only timers.

Before a permanent profile choice, require full candidate/panel reproduction
and fresh paired initialization, complete pilot replay and exact projections
under the same eventual full-A profile. Full A runs these validators in one
process. New r2 heads have their own locked initialization evidence; historical
r1 heads cannot be adopted. A successful four-case diagnostic alone cannot
establish compatibility, scientific admission or deadline feasibility.

## October 14: diagnostic wrapper failure

The restored controller observed 8072666 terminal at 19:40 UTC. It consumed
**two whole-job CPU wall-clock seconds** (four slots, CPU=0.098 seconds) and
failed before the parent, workers or resource sampler started. Dependency setup
passed; the wrapper incorrectly searched the scheduler spool directory for its
helper. Independent metadata-only failure receipt SHA
`c9e2d25740334923a537c36c82b0d2574f6b90a74b7d45ebf26ddc0c3aac371d`
confirms zero numerical results. Retain this cost and failed attempt alongside
geometry's 229 seconds. The CPU-dispatch hypothesis, compatible-profile proof
and measured successor capacity remain pending. Any reviewed new diagnostic
remedy retains the original four-slot, 32-GiB, 30-minute and 1-GiB reserve scope.
The reviewed staged remedy input contains 80,064 bytes; its unchanged
source-binding copy contains 73,320 bytes. The metadata/log bound is
67,481,168 bytes before rounding to 1 GiB, with no archive copy. Fresh
quota/filesystem evidence is still required at launch. This is a diagnostic
reserve, not measured campaign capacity. It cannot replace full candidate/panel
or paired-pilot compatibility checks.

Diagnostic remedy 8102231 was submitted October 14 at 20:43:11.969137 UTC after
fresh quota 826,630,000,000 bytes and filesystem free 994,956,017,664 bytes passed
that diagnostic-only reserve. Independent submission receipt SHA
`63aa23c6e514f9cd1757021354fa1262b8f48f89af10e8a8015259e885dbb471`
binds all source/input/command/seal evidence. Whole-job accounting is still
unobserved: submission establishes no runtime measurement, numerical result,
compatible-profile proof or campaign capacity. First job observation is
October 14 at 5:45 PM EDT (21:45 UTC), after the hourly preflight boundary.

### October 14 diagnostic completion accounting

Diagnostic 8102231 completed with four omp slots, no GPU, failed=0/exit_status=0,
17 whole-job CPU wall seconds and actual CPU=9.340 seconds. The entire scheduler
wall time counts, including environment setup, hashing and parent overhead.
Independent receipt `f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36`
binds exact accounting, both commands/seals, six resources and 184 metadata/617
external/616 source records. Its valid negative diagnostic result does not admit
geometry or establish a compatible profile, GPU timing or campaign capacity.
Every failed attempt and the earlier verifier queue-record rejection is retained.
The new verifier changes only exact queue representations; all parity/resource
checks remain fixed. No declared workload or capacity budget is reduced. Next
permitted scheduler inspection/preflight at that checkpoint was October 14 at
7:27 PM EDT (23:27 UTC), now historical.

### October 14 separate libm diagnostic submission

Diagnostic 8104416 was submitted at 23:29:21.658353 UTC. Independent submission
receipt `0b6a6e05b49bd698cc4d0d317d5142d319d3ec6a5677448e0b90803e19938b33`
verified 815 metadata/616 source bindings, exact intent/source/tools/input/command
and both launch seals. Fresh quota 824,700,000,000 bytes and filesystem free
992,888,225,792 bytes passed the 200-GiB plus 1.25-times-remaining-peak reserve.
The diagnostic-only derived additional peak is 67,667,170 bytes, rounded to
1 GiB; the existing 17,675,344-byte archive remains read only, with zero archive
or runtime ELF output copies. This reserve does not certify campaign capacity.

The request is four omp CPU slots, 32 GiB, 30 minutes, no GPU. No actual allocated
runtime/dispatch, resource record, outcome or whole-job accounting has been
observed. Environment setup, archive/runtime-library reads, hashing, both fresh
workers and parent overhead must count in the complete CPU job wall time;
parent/worker timers cannot substitute for qacct. The actual pre-submit qstat
completed at 23:29:20.793929 UTC. First permitted job observation is October 14
at 8:31 PM EDT (October 15, 00:31 UTC), with independent terminal review required.
No capacity_passed, permanent profile, geometry acceptance, residual workload
reduction or CPU/GPU budget relaxation follows from submission or four cases.
Full fresh same-profile scientific regeneration/replay and the measured schema-2
typed CPU/GPU campaign capacity conditions remain pending.

### October 15 libm completion accounting

Job 8104416 completed with failed=0/exit_status=0, four omp slots and no GPU:
**21 whole-job CPU wall seconds**, actual CPU=14.493 seconds, RSS=695,096 KiB,
maxvmem=9.140G. The complete allocation, including setup, archive/runtime reads,
hashing, fresh workers and parent overhead, belongs in the CPU ledger.
Independent receipt
`9f45a91a0ba63431f22bad35b6402fde9faabcde0d8b53682b4c448f9b6b3277`
binds actual accounting, commands, both seals, six resources and
240 metadata/617 external/616 frozen-source records.

The diagnostic is valid but its intervention is inconclusive: no recorded math
implementation offset changed, and both conditions retain the same four tensor
hash and four damage-row differences from the original four-case reference.
This is no compatible-profile proof, scientific admission, GPU measurement or
campaign capacity result. Keep the prior failed attempts and their entire costs;
do not reduce remaining regeneration/replay or any budget. SSH subsequently
disconnected; exact recorded metadata recovery and SCC status refresh await
researcher-restored authentication. Full same-profile scientific reproduction,
fresh pilot/replay evidence and measured schema-2 capacity remain pending.
