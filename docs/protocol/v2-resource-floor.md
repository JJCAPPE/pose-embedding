# Storage floor before the full campaign

Recorded September 26, 2026. This is a theoretical tensor-payload calculation
from the pinned MotionBERT architecture, not a measured GPU result, filesystem
reservation or complete resource forecast. The priority pilots and all-method
capacity profiles can proceed separately from the full campaign.

## Planned retained runs

| Stage | Completed training runs |
| --- | ---: |
| Main development: 26 methods × 3 candidates × 6 seeds | 468 |
| Main final: 26 methods × 6 seeds | 156 |
| Secondary development | 276 |
| Secondary final | 276 |
| Total, before profiles or failed attempts | **1,176** |

Every completed run retains its own checkpoint. Final scientific checkpoints
must include actual encoder updates after any method warmup. The runner also
retains both Adam/AdamW moment tensors needed for exact continuation.

## Architecture-derived lower bound

CPU construction of the pinned full DSTformer, without poses, checkpoint
loading or a forward pass, gives:

- 42,466,317 float32 encoder state elements: **169,865,268 bytes**.
- 42,464,778 active encoder parameters after excluding the unused 1,539-parameter
  pose-regression head. Two float32 Adam moments: **339,718,224 bytes**.
- Total encoder and moments per completed checkpoint: **509,583,492 bytes**.

The common 512-dimensional action head adds 4,456,960 trainable parameters.
The resulting 46,921,738 trainable parameters match the priority GPU profile's
reported count, providing a consistency check on the architecture calculation.

Even ignoring every embedding head, criterion, proxy, teacher, momentum model,
queue, RNG state, scalar optimizer step, history, descriptor, metric file and
serialization overhead, 1,176 completed checkpoints need:

`1,176 × 509,583,492 = 599,270,186,592 bytes` = **599.27 GB / 558.11 GiB**.

Including only the known common heads (912 runs at 512 dimensions and 24 at
1,536) increases this partial lower bound to **651.90 GB / 607.13 GiB**. It still
excludes all architecture-specific heads and auxiliary state.

## Immutable segments increase retained storage

The default SCC training launcher uses segments. Even a single-segment completed
run retains a latest continuation checkpoint, a selected-best checkpoint and the
root scientific checkpoint. For all 1,176 segmented runs, encoder weights and
moments alone therefore require at least **1.798 TB / 1,674.34 GiB**. Including
only the known common heads raises that partial floor to **1,821.38 GiB**.

For more segments, allow at least one additional encoder-weight snapshot per
additional segment; warmup snapshots may not yet have encoder moments. Include
full moments for every segment after encoder updates, plus any new best-state
snapshots. The measured per-method checkpoint bytes and actual segment count
must replace these lower bounds in the final forecast.

At 2026-09-26 22:28 UTC, `pquota textconv` reported **18,402.00 GB used of
18,800 GB** on the project storage that holds these artifacts: **398.00 GB
remaining**. An earlier observation was approximately 507 GB, illustrating
that other shared usage can change availability. Neither observation covers
the smallest floor. Recheck current project quota and reserve sufficient
accessible storage before launching the full campaign. Capacity profiling
does not reserve that space.
Preserve prior artifacts; silently deleting checkpoints or shortening the
scientific budget is not a storage solution.

At 2026-09-29 02:36 UTC, a fresh read-only `pquota textconv` inspection on
SCC reported **18,506.56 of 18,800 GB used** on `/projectnb/textconv`, leaving
**293.44 GB**. Only **93.44 GB** remains above the Week 3 200 GB reserve. This
shared quota is volatile and cannot hold even the 599.27 GB single-copy tensor
floor for the planned full campaign, let alone the segment floor or input and
evaluation artifacts. The earlier Week 3 extraction pass established that its
five caches fit at the time of that job; it did not establish full-campaign
storage feasibility. Obtain a documented increase in accessible capacity or a
result-blind, scientifically justified amendment before starting the full run
matrix. Preserve the novel-test seal while that decision is made.

The successful A100 priority pair in SCC job 7748592 provides a first timing
scale, not an all-method runtime forecast. Each 1,000-step development pilot
took about 6,500 seconds including ten validations; their update steps alone
took about 2,300 seconds. Multiplying only the observed update time by the
provisional 50,000-update budget gives about **32 GPU-hours per run**. Applying
that rate illustratively to the 468 main selection runs gives about **15,000
GPU-hours** before validation, final training, secondary studies, setup,
queueing or failed attempts. Architecture methods may be faster or slower, so
this is an extrapolation rather than a measured lower bound. The all-method
full-budget profiles and an allocation calendar are required before calling
the 14-week horizon feasible. See `docs/protocol/v2-implementation-record.md`
for the pilot provenance.

The complete feasibility decision must also include validation/scorer runtime,
input setup, integrity-validation I/O, all secondary evaluations, CPU memory,
queue/bootstrap work and failed attempts. Three optimizer steps and a 128-item
retrieval prefix do not establish full-study affordability or completion dates.
