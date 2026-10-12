# Week 5 capacity audit: repeated validation

The frozen implementation repeatedly validates complete evidence when a later
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

**Decision: no-go on the measured profile.** Hold full A and selection rather
than fabricate a passed capacity candidate. Full A and corrupted-artifact
numerical replay remain mandatory for any future admission, but a full A run
is not needed to establish this conservative rejection. Record a researcher
choice before changing the frozen implementation. Current plan Section 7
explicitly prohibits memoizing validation under the adopted amendment, and
Section 8 requires a result-blind amendment after a failed measured go/no-go.

The recommended next step is a scoped amendment proposal for validation-proof
reuse within a command and per-stage CPU/GPU wall-time accounting, with an
explicit mutation/threat model, fresh independent recertification, complete
checks and all scientific settings/seals preserved. It is not an adopted design
or permission to implement a cache or waive validation. An approved proposal
needs a successor release, affected-evidence regeneration inventory and renewed
measured capacity. Alternatives are a specifically identified compatible faster
runtime with new evidence, or retaining the blocked-study record. All prior
attempts remain preserved; technical completion and weekly closure are not claimed.
