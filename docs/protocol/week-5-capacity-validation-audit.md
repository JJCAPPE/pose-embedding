# Week 5 capacity audit: repeated validation

The frozen implementation repeatedly validates complete evidence when a later
command consumes it. These calls must enter the capacity forecast. **The call
counts below are verified; a capacity failure has not been measured.** No
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
overhead or elapsed allocation time. This is another necessary bound, not a
measured capacity failure; no frozen source has been changed.

Measure complete real admission validation on SCC, including pilot CPU replay,
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
