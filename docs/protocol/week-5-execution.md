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
Initial deployment `dpl_96ZkhYkk7TFng7tmyBY2aPFvwv5E` was verified through the
live public export, protocol source, health endpoint and browser. Closed-week
history, private ownership, RLS and the existing production Journey were retained.

The progress milestone (`41fe0a6`) was then published as deployment
`dpl_24eUzUGHsNx8SZSfcaLHgA81Ntk5`: Week 5 version 5 active, task 03 version 6
in progress, all gates pending. Independent public health/export reads confirmed
that state at 21:48 UTC. The private export redirected to login; all other weeks
and existing evidence links were unchanged. Review found stale static protocol
copy still describing Week 3 as pending. Deployment
`dpl_F4ZiW8JNdJA8xtETqu55M4p2axhM` corrected it with stable stage-gate guidance
and a pointer to the live status row; live page/export and Journey checks passed. Local
security advisors passed. Hosted advisors reported existing Auth settings for
leaked-password protection and MFA, with no RLS/table/function findings; those
Auth settings were preserved.

The allocated-rehearsal milestone (`af06ff1`) was published through guarded
migration `20261011221237` and deployment `dpl_FVcgjiXWy6xU8DRnGAm9fx8QYkiy`.
Live page/export and health checks at 22:18 UTC verified Week 5 version 6 active,
task 03 version 7 in progress, all gates pending, unchanged closed history and
existing evidence links, and a private-export redirect to sign-in. The public
fallback matches the live data; no researcher hours or completion were inferred.

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

### Verified SCC software rehearsal

Release [`731938a`](https://github.com/JJCAPPE/pose-embedding/commit/731938a157be575ee433d6939876f8ca0b95e459)
was committed, synchronized and checked against SCC source hash
`d9d683ac8b13f8362c52a435a0604c0ff06f50d5a0a8ffc61e88912e2c722a89`.
Locked dependencies and the pinned MotionBERT upstream were verified. The work
is available in [PR 33](https://github.com/JJCAPPE/pose-embedding/pull/33), stacked
on the Week 4 execution branch.

CPU rehearsal job **8028010**, submitted October 11 at 18:00 New York time,
completed on `scc-pi4`: scheduler `failed=0`, `exit_status=0`, 414 seconds wall
time. JUnit records **41 passed, zero failures/errors/skips** in 390.055 seconds.
The real dataset seal was checked before the rehearsal at 22:02:54.822 UTC and
after it at 22:09:29.945 UTC; both were sealed. Novel data and opening records
used by the tests were isolated fixtures.

Evidence paths relative to the canonical artifact root:

- Launch: `study-v3/operations/week5-launches/20261011T220021Z/`.
- Operation: `study-v3/operations/20261011T220254Z-8028010-rehearsal/`, containing
  the outcome, resource records, `rehearsal.junit.xml`, and
  `fixture-data/test_complete_v3_cli_fixture_r0/fixture-artifacts/software-rehearsal.json`.
- Accounting and resource inspection:
  `study-v3/operations/week5-inspection/20261011T221121Z/`.

The inspection recorded 911.99 decimal GB quota free and 1,086,609,948,672
filesystem bytes free; the rehearsal allocation had 32 GiB host memory. These
are measurements for that checkpoint. The full campaign forecast and GPU
admission evidence remain pending. Successor preparation job **8028032** was
submitted next at 22:12:18 UTC;
its result and metadata-dependence tables were not yet verified at this record.
Task 03 stays in progress and all Week 5 gates stay pending.

### Geometry invocation correction

Review found a destination mismatch in release 731938a's convenience geometry
launcher: it supplies `attempts/`, while the frozen validator requires `locks/`.
The pending-only cancellation guard for preparation job 8028032 declined before
issuing `qdel`, because that job had started at 22:16:44 UTC on `scc-pi8`.
Preparation was not interrupted and no frozen source was changed.

The corrected invocation uses the unchanged geometry CLI under
`locks/geometry/<unique-attempt>`. An independently reviewed operational wrapper
retains the seal, monitoring, immutable commands and output validation. Its
transferred bytes match SHA-256
`14b6799627cd506ae5733c5d84e410b0d8656a3dca6b1d0e05c99e7272ede5cc`;
see the [exact SCC command](scc-v3-runbook.md#week-5-execution-r1-successor).
The path-contract self-check passed locally. This is an invocation correction,
not a scientific amendment or evidence that the actual geometry run passed.

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

Fresh opening capacity evidence is now recorded immediately before the shared
opening event. It verifies the running SCC job, assigned host/slots/GPU, current
RAM/VRAM, quota/free space and remaining dated evaluation/delivery capacity.
Archival reads and crash recovery retain that bound receipt without probing
current hardware. Twelve resource tests and five opening-boundary tests pass.
The successful novel extraction, official-to-primary export and archival
validation path also passed in an isolated, explicitly non-scientific rehearsal;
no real novel input or opening was accessed.

Focused regression tests cover these boundaries. Complete suite, command
rehearsal and SCC validation results will be recorded before software admission;
unit tests alone do not establish a valid scientific release or GPU result.
The complete Python suite passed **1,131 tests** in 234.45 seconds, with two
skipped licensed AVSL source-parity checks for the historical v2 method outside
v3 scope. The pinned MotionBERT source was fetched and checked locally.
Ruff checks/formatting and workspace verification passed. The final isolated
opening check also verifies actual scheduler wall time remaining; 35 targeted
resource/opening/lock/rehearsal tests passed after that final change. Earlier failed development runs were test failures, including a
stale rehearsal assertion and a concurrent test-file import during construction;
no SCC scientific attempt or novel opening resulted.

The tracker milestone passed 14 database tests, 22 unit tests, 22 desktop/mobile
browser tests, lint, typecheck and a production build. Local security advisors
passed; the hosted Auth advisories above remain distinct. The stable static-copy
correction additionally passed four focused protocol/accessibility browser checks.
None of these software checks substitutes for SCC calibration or admission.

## Reflection

**Done:** Reconciled the prior handoff, live closure and authorized amendment;
published the active Week 5 scope; inspected SCC; recorded future availability;
implemented and verified the completion path and review fixes; committed and
synchronized release 731938a; passed the allocated 41-check software rehearsal
with the real dataset seal intact.

**Next:** Verify the prepared successor manifests and metadata-dependence tables,
then complete allocated geometry, fresh caches, pilots, development corruptions
and timing. Use their immutable receipts for the capacity decision and next-week
handoff. Software rehearsal does not replace fresh scientific admission evidence.

**Open issues:** Full Week 5 evidence and selection authorization are unfinished.
Actual researcher minutes remain unreported. Technical completion and formal
weekly closure have not been claimed; all selection/final/novel gates remain shut.
