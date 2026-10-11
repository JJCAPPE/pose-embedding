# Week 5 execution record

Started October 11, 2026 (America/New_York), before the October 12–18 calendar
week, at the researcher's direction. **Work is active; no Week 5 gate or
scientific admission is complete.** The [incoming handoff](week-5-handoff.md),
[Week 4 record](week-4-execution.md), [current protocol](protocol-v3.md) and
[adopted October 9 amendment](../decisions/0006-v3-execution-completion-amendment.md)
govern this work.

## Starting evidence and scope

The live tracker had closed Weeks 1–4. Week 4's five caches and three complete
20-epoch pilots have independent validation, including job 7971490. Their
original release, protocol, locks and artifacts are retained. The original
local main checkout was behind that work; its unrelated Journey edits were
preserved. Week 5 uses an isolated branch based on the existing Week 4 branch.
The October 9 amendment was already authorized in the preceding research chat.

A closed Week 4 does not admit selection: its frozen implementation disables
later execution stages. Week 5 must complete and verify the successor software,
freeze it, regenerate all required cache/pilot evidence, complete the fixed
geometry/development-corruption work, and pass the measured capacity gate.
None of these requirements can be replaced by publishing the plan.

The live tracker was updated through a guarded, version-checked migration on
October 11: Week 5 active, execution/report task in progress, all gates pending.
Production deployment `dpl_96ZkhYkk7TFng7tmyBY2aPFvwv5E` was verified through the
live public export, protocol source, health endpoint and browser. Closed-week
history, private ownership, RLS and the existing production Journey were retained.

## Researcher availability and schedule

The researcher confirmed up to **5 hours weekly normally, 10 if necessary**, with
limited Thanksgiving-week availability, and reported no SCC access limits.
These are future planning bounds, not hours worked. Budget no guaranteed hours
for November 23–29; identify any weeks that need the authorized contingency.
SCC jobs use ordinary queued access; no reserved GPU time is claimed.

Target the final lock review before Thanksgiving, retaining November 29 as the
hard lock deadline. Novel evaluation must finish by December 6, with December
7–18 protected for analysis and delivery. The 27-slot selection matrix belongs
to Weeks 6–7 and the nine final heads to Weeks 8–9; this task prepares their
interfaces and prerequisites without running those stages early. Complete
heads and final authorization remain mandatory before any novel loading.

The previous 8.69 allocated-GPU-hour estimate includes 25% slack for head work
and clean revalidation only. It excludes development/novel corruption extraction,
CPU validation, projections, reporting, queues, retries and human work. Replace
it with the successor measurements and a dated calendar before admission.
Retained originals and new artifacts count within the 120 decimal GB campaign
envelope. The capacity calculation uses current remaining peak bytes plus the
200 GiB reserve; existing artifacts must not be counted twice.

## SCC operational record

The existing `remote:0.0` SSH pane was inspected and reused. Host `scc1`, user
`bujack`, no scheduler jobs at the October 11 21:13 UTC observation. The original
scientific release remains `2897f4fe4c1fb1857432a0e92a7391dde68307f5`.
No Week 5 scientific job has been launched at this checkpoint.

Canonical roots remain `POSE_EMBED_DATA_ROOT` and `POSE_EMBED_ARTIFACT_ROOT`.
The immutable resource/availability snapshot relative to the artifact root is
`study-v3/operations/week5-20261011/20261011T213837Z/`.
`$HOME/pose-embed-scc/WEEK5-STATUS.txt` points to its status record. The first
status-capture attempt used incompatible system Python 3.6; that empty attempt
was retained, and the retry used the verified release's Python 3.11.15.

Projectnb quota: 18,800 GB limit, 17,873.86 GB used, approximately 926.14 GB
remaining. This is a dated observation, not future capacity or an allocation.
Login-host RAM and the GPU queue inventory are not run memory budgets. Measure
allocated host/GPU memory, filesystem space and quota before each launch and
periodically during work. No historical evidence was deleted.

## Implementation and verification in progress

The successor binds its original design and exact manifest bytes, permits only
coherent `study-v3/revisions/execution-r1/locks/` paths, and compares all remaining
protocol fields for equality. The complete scientific recipe stays unchanged.

Review identified and corrected these implementation problems:

- The opening ledger could be left truncated after a crash. Publication now uses
  the existing atomic immutable JSON writer; the shared dataset seal is retained.
- An engineering evaluation could skip the seal when `--allow-fixture` was used
  with scientific caches. Authorization now follows actual sidecar eligibility.
- A malformed primary-cache reference could recurse into another primary cache.
  It must terminate at a verified official cache before recursive validation.
- A dirty checkout could record an opening before its cleanliness check. The
  check now runs before opening.
- Historical final-head validators imposed loss improvement and changed weights.
  V3 retains finite-value, update-budget, pairing and health checks without a
  real-data improvement requirement; historical v1 behavior is preserved.
- Selection could silently discard a candidate after an implementation/provenance
  failure. That failure now blocks the stage, as the plan requires.
- Capacity could add many short windows although no complete job fit any of
  them. Each job with slack must fit both its usable window and scheduler limit;
  admission cannot count windows already elapsed at authorization time.
- Saved development projections could be replaced while preserving their
  checkpoint binding and recomputing ranks. Validation now replays the recorded
  head against its verified source caches with the existing fixed numerical
  parity bounds; retained-array ranks are still recomputed exactly.
- Initial evaluation timing began before its opening event and could fail later
  report chronology checks. Scientific evaluation timing now begins after opening.

Fresh opening capacity evidence is being integrated immediately before the
shared opening event. Archival reads and recovery must retain the original
bound receipt instead of requiring future hardware to reproduce an old opening.

Focused regression tests cover these boundaries. Complete suite, command
rehearsal and SCC validation results will be recorded before software admission;
unit tests alone do not establish a valid scientific release or GPU result.
The latest broad run recorded 1,070 passing tests, 38 environment-dependent skips
and one stale rehearsal assertion, subsequently corrected. Final verification
remains pending. The tracker milestone passed 14 database tests, 22 unit tests,
22 desktop/mobile browser tests, lint, typecheck, production build and security
advisors; no scientific completion was inferred from those checks.

## Reflection

**Done:** Reconciled the prior handoff, live closure and authorized amendment;
published the active Week 5 scope; inspected SCC; recorded future availability;
implemented and began verifying the completion path and review fixes.

**Next:** Finish independent software/fault verification, commit and synchronize
the clean successor, then execute allocated preparation, geometry, fresh caches,
pilots, development corruptions and timing. Use their immutable receipts for
the capacity decision and next-week handoff.

**Open issues:** Full Week 5 evidence and selection authorization are unfinished.
Actual researcher minutes remain unreported. Technical completion and formal
weekly closure have not been claimed; all selection/final/novel gates remain shut.
