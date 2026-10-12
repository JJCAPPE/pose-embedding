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

The verified software/metadata milestone (`38b5dc6`) was published through
guarded migration `20261011224523` and deployment
`dpl_6pyeNk2LtqHMjHQo2hmgw66eDMGp`. Live export and health checks at 22:50 UTC
verified Week 5 version 7 active, task 03 version 8 done, task 01 version 5 in
progress, and all three scientific gates pending. All other weeks and existing
source links were unchanged; the private export redirected to sign-in. The
fallback matches the public export, with researcher time still unreported.
Publication passed 16 database tests, 22 tracker unit tests, typecheck, focused
lint, workspace verification and the production build. Live browser checks
rendered the reflection, completed-task evidence and protocol status without
page errors; the preserved Journey returned HTTP 200.

The geometry/cache milestone (`db15cfb`) was published through guarded migration
`20261011225827` and deployment `dpl_Fwyk7yvqPZQmGCPDCMpa348VVrRH`. The live
export and health at 23:02 UTC match Week 5 version 8 active, task 01 version 6 and task 02 version 5
in progress, task 03 version 8 done, and all scientific gates pending. Other
weeks, source links, private-export protection and the production Journey remain
unchanged. Sixteen database checks, 22 tracker unit tests, typecheck, focused
lint, workspace checks and the production build passed. Live browser checks
rendered the reflection, task evidence and protocol without page errors; Journey
returned HTTP 200 and the private export redirected to sign-in.

The cache-controller blocker (`ea69163`) was published through guarded migration
`20261011230509` and deployment `dpl_3yoY1PBA3tAqRVBhVUNBrNEbuuuD`. At 23:09
UTC, live page/export and health verified Week 5 version 9 active, task 02
version 6 blocked, task 03 still done, and all gates pending. All other weeks
and source links were unchanged; the public fallback matched and private export
still redirected to sign-in. Fourteen database checks, 22 tracker unit tests,
typecheck, focused lint, workspace checks and the production build passed. The
browser rendered the failure evidence and protocol status without page errors;
Journey remained available. This is an interim blocker record, not closure.

The verified controller/new-attempt milestone (`34699c7`) was published through
guarded migration `20261011232411` and deployment
`dpl_F89BHGZVWEwXaV7G8Xt9GqfyAfTE`. At 23:28 UTC, live page/export and health
verified Week 5 version 10 active, task 02 version 7 in progress, task 03 still
done, and all scientific gates pending. Actual time stays unreported at the
researcher's explicit request. All other weeks and source links were unchanged;
fallback/protocol data matched, private export redirected to sign-in, and
Journey returned HTTP 200. Fifteen database checks, 22 tracker unit tests,
typecheck, focused lint, workspace checks and the production build passed;
live diagnostic/task evidence rendered without page errors.

The parity/extraction milestone (`b6e22c3`) was published through guarded
migration `20261011233207` and deployment `dpl_3epdmxtE57hmGsjcEST3EBHcws42`.
At **23:36:05 UTC**, live health/export and rendered-page checks verified Week 5
version 11 active, task 02 version 8 in progress, task 03 version 8 done and all
three scientific gates pending. The public fallback and protocol status match;
all other weeks and source links are unchanged. Actual time remains unreported
at the researcher's request. Fifteen database assertions, 22 tracker unit tests,
typecheck, focused lint, production builds, runbook shell checks and workspace
verification passed. The private export redirects to sign-in; browser checks
had no page errors and the preserved Journey returned HTTP 200. PR 33 remains
a draft stacked on PR 31. This is an ongoing handoff: five-cache completion,
independent validation and the remaining Week 5 work are still pending.

The full-size repeatability checkpoint (`aad4449`) was published through guarded
migration `20261012003353` and deployment `dpl_12mfXmcvKYkUDThmyYZoWsopWana`.
At **October 12 00:37:12 UTC**, live health/export and browser checks confirmed
Week 5 version 12 active, task 02 version 9 in progress, task 03 version 8 done,
all three gates pending and actual time unreported. All other weeks and source
links are unchanged; the fallback and protocol match the public export. Fifteen
database assertions, 22 tracker tests, typecheck, focused lint, workspace checks
and local/hosted production builds passed. Private export still redirects to
sign-in; Journey returned HTTP 200 and no browser errors occurred. PR 33 remains
a concise draft stacked on PR 31. Three development caches and independent
five-cache validation remain pending at this checkpoint.

The completed-extraction/validator-launch checkpoint (`cc481c9`) was published
through guarded migration `20261012134927` and deployment
`dpl_FuGpwCEfJaDDHw3fA2FeCGkSsNK8`. At **October 12 13:53:23 UTC**, live
health/export and browser checks verified Week 5 version 13 active, task 02
version 10 in progress, task 03 version 8 done and all gates pending. Actual
time remains unreported. All other weeks and source links are unchanged, and
the fallback and protocol match the public export. Fifteen database assertions,
22 tracker tests, typecheck, focused lint, workspace checks and production builds
passed. Private export redirects to sign-in; Journey returned HTTP 200 and no
browser errors occurred. PR 33 remains a concise draft stacked on PR 31. The
independent cache validator remains pending in this published checkpoint.

The independent-cache-validation/first-pilot checkpoint (`e26f18d`) was published
through guarded migration `20261012140817` and deployment
`dpl_fn4o7PypbskdZ6R1WCykuXPiKAJV`. At **October 12 14:11:55 UTC**, live
health/export and browser checks verified Week 5 version 14 active, task 02
version 11 in progress, task 03 version 8 done and all gates pending. Actual
time remains unreported. All other weeks and source links are unchanged; the
fallback and protocol match the public export. Fifteen database assertions,
22 tracker tests, typecheck, focused lint, workspace checks and production builds
passed. Private export redirects to sign-in; Journey returned HTTP 200 and no
browser errors occurred. PR 33 remains a concise draft stacked on PR 31. The
first Contrastive pilot has a dated queued launch, with no pilot result claimed.

## Researcher availability and schedule

The researcher confirmed up to **5 hours weekly normally, 10 if necessary**, with
limited Thanksgiving-week availability, and reported no SCC access limits.
These are future planning bounds, not hours worked. Budget no guaranteed hours
for November 23–29; identify any weeks that need the authorized contingency.
SCC jobs use ordinary queued access; no reserved GPU time is claimed.
The researcher subsequently requested, **“Leave actual time unreported,”** and
confirmed 5 hours weekly as normal availability. Keep actual minutes at the
existing unreported value; do not convert future availability into hours worked
or repeatedly request actual time.

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
`bujack`, no scheduler jobs at the October 11 21:13 UTC initial observation. At
that checkpoint, the original scientific release was
`2897f4fe4c1fb1857432a0e92a7391dde68307f5` and no Week 5 scientific job had
launched. The later allocated work is recorded below.

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
submitted next at 22:12:18 UTC. Its result was verified at the following
checkpoint; the initial rehearsal milestone did not claim preparation success.

### Verified successor preparation

Preparation job **8028032** completed on `scc-pi8`: scheduler `failed=0`,
`exit_status=0`, 941 seconds wall time. Its immutable operation is
`study-v3/operations/20261011T222327Z-8028032-prepare/` relative to the canonical
artifact root. The successor uses release 731938a and
`study-v3/revisions/execution-r1/locks/` with these bindings:

| Binding | SHA-256 |
| --- | --- |
| Canonical protocol | `cfe70a6520bac36a0466b26709841215ddaa55d61318b5f19173669285729992` |
| Protocol file bytes | `b92b243e81324dfbc83ed612f9d024c74165de807b90985afc3ac418a1df4ae8` |
| Design lock | `5a38707efd2211123a220489da09d96606ccde2c8bb7d9d99780ea0e7d9c89e7` |
| Manifest set | `107d5bfc723ceac06f984eb6429098187109dee7f5e1198fdcf66ecd6c687479` |

All eight manifests are byte-identical to their predecessors. Scientific fields
are unchanged except for the declared successor-relative artifact paths; source
hashes were verified and the shared registry was unchanged.

### Verified supplementary checks and metadata

Supplementary CPU job **8028071**, submitted at 22:36 UTC, completed on
`scc-ne7`: scheduler `failed=0`, `exit_status=0`, 284 seconds wall time. Its
JUnit records **84 passed, zero failures/errors/skips** in 150.93 seconds.
All nine resource samples passed the RAM/storage requirements; the latest
recorded 1,379,651,584 RSS bytes against 32 GiB and 911.93 decimal GB quota free.
The real dataset remained sealed before and after; novel pose data and outcomes
were not loaded.

The operation is
`study-v3/operations/20261011T224100Z-8028071-additional-checks/`. The independent
verification at 22:44:38 UTC and scheduler accounting are in
`study-v3/operations/week5-launches/20261011T224426Z/`, including
`additional-checks-verification.json`. The JUnit SHA-256 is
`1c69f7359c32f603836bb3ef3d95328cab1184cbe42e56f6e0dd1f33147d573e`;
the validation receipt SHA-256 is
`c61337b3190e98b092610bea958b91589dbee08f56fe1d844b8621c1222fa865`.

Actual metadata-dependence tables reside under
`study-v3/revisions/execution-r1/analysis/metadata-dependence/20261011T224100Z-8028071-additional-checks/`:

| Table | Verified query/action counts | SHA-256 |
| --- | --- | --- |
| `development_queries.json` | 18,929 / 20 | `04bad108a88c690e33f50a88ecb1ec654284cb5ed1b2980d7433d5f73a5e296e` |
| `novel_query_primary.json` | 18,884 / 20 | `776bbf1f4a94b1d3c75eb8a8f9eba5a443ed40aec38a5ea9943f23aa18ad0a30` |

Hashes, manifest bindings and counts were independently verified. Task 03's
completion-release, command/report rehearsal, interpretation and actual metadata
requirements are complete. This technical task completion does not pass the
scientific admission gate, which still requires fresh caches, pilots and the
other Week 5 evidence. Geometry job **8028081** was queued at 22:44:39 UTC;
its later outcome is recorded below. All three Week 5 gates remain pending.

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

### Verified geometry and fresh-cache submission

Geometry job **8028081** completed on `scc-ne7`: scheduler `failed=0`,
`exit_status=0`, 614 seconds wall time. Independent verification at 22:57:18 UTC
confirmed 40 base queries, 43 total selected rows, nine conditions and 430
tensors, with exact repeats across two fresh processes. The absent
`invalid_own_scale` and `all_missing` categories have existing executed fixture
coverage. The original training-only fallback was not re-estimated. Both seal
checks and all 14 RAM/storage resource samples passed.

The operation is `study-v3/operations/20261011T224733Z-8028081-geometry/`;
its validation receipt SHA-256 is
`a73168245cce41b9eee1ffbbc0922a80ceb5091a0f3a0a5bb6fd57446f2b9f32`.
The summary is
`study-v3/revisions/execution-r1/locks/geometry/20261011T224733Z-8028081-geometry/summary.json`,
SHA-256 `89a44f1ae55cac79715dcd1e33a545e2f290d17f6e5faa9243d48325bd4fb6c9`.
Accounting and independent geometry verification are under
`study-v3/operations/week5-launches/20261011T225707Z/`.

Fresh five-cache L40S job **8028119** was submitted at 22:57:19 UTC, with its
launch receipt in the same directory. Its cache outcome is not yet verified.
Task 02 is in progress; task 01 remains in progress until all nine full-query
damage summaries pass. All scientific gates remain pending.

The active `finish-pose-embed-week-5` thread heartbeat continues the remaining
Week 5 work every 15 minutes. Allocated jobs retain resource samples every 60
seconds. The persistent SCC handoff remains
`$HOME/pose-embed-scc/WEEK5-STATUS.txt` in `remote`. Continuation covers the
remaining Week 5 evidence and capacity decision only; it does not launch
selection, final training or novel-test work.

Reviewed candidate-assembly helpers, their tests and an explicitly nonauthorizing
planning draft were transferred and byte-verified under
`study-v3/operations/week5-admission-tools/20261011T225931Z/`.
The bound `tools.json` SHA-256 is
`495e5db62e7258f082b6a88f524dc140ebec35ca7605b42817663757a412ab4d`.
The assembler passed 32 local tests and its monitored wrapper passed 19. The
draft leaves measurements null; no candidate or admission job was submitted.
The persistent status link points to this directory's `status.txt`, preserving
the current cache step. At 22:59:31 UTC, cache job 8028119 was still queued;
an actual GPU allocation is not inferred from submission.

### Cache allocation verified; first attempt failed

Scheduler state and parent resource records subsequently verified job **8028119**
running from 22:59:35 UTC on `ece@scc-j08.scc.bu.edu` with four slots. The
operation is `study-v3/operations/20261011T225953Z-8028119-caches/`; scientific
outputs are under
`study-v3/revisions/execution-r1/attempts/20261011T225953Z-8028119-caches/`.
At 23:00:09 UTC the allocated-device check passed: exactly one L40S,
`CUDA_VISIBLE_DEVICES=0`, 47,240,642,560 GPU bytes free of 47,695,921,152 total,
and a 34,359,738,368-byte (32 GiB) host limit. RAM/storage checks passed with
911.76 decimal GB quota free and 1,086,370,873,344 filesystem bytes free.

Workspace, upstream and protocol checks passed. The dated allocation inspection
is retained at `study-v3/operations/week5-inspection/20261011T230031Z/`.
Subsequent verification found job 8028119 ended at 23:00:54 UTC: the outer
operation failed and command 002 exited 2 after 45.0216 seconds with
`CUDA-capable devices busy or unavailable`. No `parity.json` or cache files were
created. The original attempt and release are preserved. No automatic retry or
successful cache result is claimed.
After any corrected attempt completes successfully, continuation must verify
accounting and run the independent cache validator before pilots or admission.

### Verified controller blocker; correction pending

The saved `nvidia-smi.txt` at 23:00:10 UTC and resource record `002-0000` confirm
GPU 0 L40S in `E. Process` (exclusive-process) mode, with sole compute entry
Python PID 81091 (426 MiB). The frozen parent calls
`torch.cuda.mem_get_info` and retains that CUDA context while launching parity.
The child's initial workspace/upstream/protocol checks passed, but parity could
not acquire the exclusive GPU. Source and resource evidence strongly support
this operational failure mechanism; attribution of the listed GPU PID to the
parent remains inferred until the allocated reproduction/remedy check. Diagnosis
and failed accounting are preserved under
`study-v3/operations/week5-cache-failure/20261011T230352Z/`.
Its `accounting.txt` records scheduler `failed=0`, `exit_status=1`, 80 seconds
wall time, from 22:59:35 to 23:00:55 UTC; the child command's exit status was 2.
The scheduler completed the allocation but the scientific command did not pass.

Task 02 is temporarily blocked. An external controller correction is being
prepared with identical scientific commands, a short-lived GPU preflight child
and a CUDA-uninitialized parent. It must pass a small allocated synthetic
reproduction/remedy check before an identical fresh cache retry. No frozen
source, scientific setting, original artifact or approved budget is changed.
There is no running GPU job at this diagnostic checkpoint. Other independent
Week 5 work may continue; all scientific gates remain pending.

The synthetic diagnostic job **8028141** was queued at 23:18:42 UTC. Reviewed
tools were transferred and byte-verified under
`study-v3/operations/week5-gpu-tools/20261011T231839Z/`; the `tools.json` SHA-256
is `9e7aaee8832cb6fa5481f16eb50d44c802f5deff8eb80ccfc9010f3248dd4ad0`.
Diagnostic output is allocated a new immutable directory at
`study-v3/operations/week5-gpu-diagnostic/20261011T231839Z/`. No hardware outcome
is claimed at submission; cache revalidation remains blocked.

The seven operational helpers and four test files are archived separately in
`scripts/operations/` and `tests/unit/`, with transferred source bytes preserved.
All 52 design and five scientific hashes remain unchanged. The local 110-test
operational suite, supplementary geometry self-check, Ruff/format checks and
workspace verification passed. These software checks do not substitute for the
allocated diagnostic. The [runbook](scc-v3-runbook.md#week-5-execution-r1-successor)
routes all four GPU modes through the external controller only after independent
verification of its required diagnostic receipt; CPU validation keeps the
original frozen commands.

### Allocated diagnostic passed; new cache attempt submitted

Diagnostic **8028141** completed on `ece@scc-j04` with four slots: scheduler
`failed=0`, `exit_status=0`, 35 seconds wall time, from 23:20:08 to 23:20:43 UTC.
Independent verification at 23:23:22.796524 UTC checked all 58 evidence hashes,
both dataset seals and all 12 RAM/storage samples. Parent PID 786130 remained
CUDA-uninitialized; holder PID 786171 blocked the held-context probe, then both
sequential probes succeeded. This reproduces the failed controller's mechanism
and verifies the short-lived-context remedy without using scientific data.

The diagnostic summary in the directory above has SHA-256
`b608b95a18ff02ceee2467f3e7025dce8e57f04dcafd65406a2515b156b51395`.
Independent verification and accounting are retained under
`study-v3/operations/week5-launches/20261011T232314Z/`, including
`diagnostic-verification.json`. The reviewed controller SHA-256 is
`cbf13de9bda43b78bef8d3005bf2ccadb225c0daad5bc27b91e9329ee911e7ac`.

New cache job **8028152** was submitted at 23:23:23 UTC using that controller
and exact diagnostic binding; its launch receipt is in the same directory.
At submission it was queued, with no actual allocation or cache result inferred.
Task 02 resumes in progress. Attempt 8028119 remains preserved; all scientific
gates remain pending. The next prerequisite after successful accounting is
independent validation of all five fresh caches before the paired pilots.

The reviewed admission helpers were separately transferred as revision 2 under
`study-v3/operations/week5-admission-tools/20261011T232448Z/`, with `tools.json`
SHA-256 `f71d7efe1634ad8b823be191dca8389c8dee144c5457da0a990d55a63bd33ce5`.
This binds `pose-week5-admission-template-r2.py`,
`pose-week5-run-admission-r2.py`, the unchanged scheduler wrapper, two test files
and five planning drafts with measurements still null. The earlier bundle is
preserved. The 110 new local checks comprise 57 admission and 53 GPU/diagnostic
tests. No candidate or admission job was launched. The persistent status link
now points to this bundle and records cache job 8028152, still queued at the
23:24:48 UTC observation.

### Corrected cache attempt running; parity pending

Job **8028152** was subsequently verified running from 23:25:46 UTC on
`ece@scc-j01` with four slots. Its operation is
`study-v3/operations/20261011T232601Z-8028152-caches/`, and its scientific output
directory is `study-v3/revisions/execution-r1/attempts/20261011T232601Z-8028152-caches/`.
The first short-lived GPU preflight passed at 23:26:18 UTC with
`CUDA_VISIBLE_DEVICES=3`, logical device 0, one L40S, and 47,162,982,400 bytes
free of 47,695,921,152 total. The second preflight also passed before scientific
command 004.

The first command-004 monitor sample recorded 31,182,848 RSS bytes against the
34,359,738,368-byte host allocation, passing RAM/storage checks with 911.74
decimal GB quota free and 1,086,345,707,520 filesystem bytes free. These are
dated samples, not final peaks. Inspection is retained under
`study-v3/operations/week5-inspection/20261011T232632Z/`. Command 004 remains
running at this checkpoint; no parity or cache result has been inferred.

### Parity passed; five-cache extraction running

Independent inspection at **23:30:13 UTC** verified that job **8028152** passed
parity at 23:27:15.814246 UTC with a clean release `731938a`, the exact successor
protocol file and manifest-set bindings. The parity receipt SHA-256 is
`7991c538390e5767a9de1256cf31210cf2ce265510b054cf013a362e891373c7`.
Cache extraction was running on the assigned L40S; five-cache completeness,
accounting, independent cache validation and admission remain unverified.

The resource sample `004-0003.json` at 23:29:27.882052 UTC recorded
2,902,032,384 child RSS bytes against the 32-GiB host allocation and 4,248 MiB of
GPU memory for scientific child PID 2173794. Monitoring parent PID 2118260 was
absent from the GPU process list. Quota free space was 911.74 decimal GB and
filesystem free space 1,086,345,707,520 bytes; RAM/storage checks passed. Its
SHA-256 is `a29549bbe38765c0213bfdb3a816b11d2b98bfc6a882a1f72aae4e1f9435eb0f`.
These are current observations, not final peaks or reserved future capacity.

The compact verification is retained at
`study-v3/operations/week5-inspection/20261011T233012Z/cache-progress-verification.json`,
SHA-256 `5dd0d70236c52a7751bf183bda6c78f1a2888189e07a031866c753fbffbbcdbe`.
The persistent status link now points to that directory's `status.txt`, including
the next verification command and the admission revision-2 helper locations.
Task 02 remains in progress and all scientific gates remain pending. The next
step is successful accounting and complete five-cache validation before pilots;
the Week 5-only heartbeat continues the monitored work.

### Full-size repeated extraction passed; development caches pending

At **October 12 00:33:27.473756 UTC**, independent inspection verified the
sidecar and input bindings for two retained 95,001 × 8,704 float32 extractions
in job **8028152**. The allocated repeatability command reports `status=passed`,
`identical_arrays=true` and `identical_npz=true` across separate processes
2173794 and 3268119. Both archives record SHA-256
`43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d`
and 3,315,915,790 bytes. Independent inspection rehashed the sidecars and
checked the release, protocol, lock, parity, manifest and sample-order bindings;
it did not reread the full archives on the login host. Independent five-cache
validation remains a later allocated command.

The first extraction ended October 11 at 23:57:10 UTC after
1,791.0110672899755 seconds; the second ended October 12 at 00:27:12 UTC after
1,798.3135285119643 seconds. Both recorded peak GPU memory of 3,896,508,416 bytes;
peak host memory was 6,908,186,624 and 6,904,946,688 bytes respectively. All 76
monitor samples passed RAM/storage checks. At 00:32:46.696124 UTC, child RSS was
3,134,291,968 bytes against 34,359,738,368 allocated; quota free space was
905.56 decimal GB and filesystem free space 1,079,706,124,288 bytes.

The repeatability receipt SHA-256 is
`d50dc4ad2a19ff12c12888215ed9ba0cc3c1eea53d96272f1a1681b247d3ab70`.
The sidecar hashes are
`4f647f8f822b01a0f3b8a0c82e9a0c40838d824036c2bbd0c3bac36e0f59c8dc`
and `b45c76a84dafbf42e251147fee957a1252d0edd890b5fac3f46ae150dbf51744`.
The compact verification is retained at
`study-v3/operations/week5-inspection/20261012T003326Z/repeat-progress-verification.json`,
SHA-256 `04e07a8fc983f3158e0e5db792827099bc66f256f4d45047b3ca12011b885c9d`;
the persistent SCC status link points to that checkpoint. The job remained
running with three development caches and independent validation pending.
Task 02 remains in progress, all scientific gates remain pending, and no
scientific admission or weekly closure is claimed.

After successful cache-job accounting, the separate CPU `validate-caches` job
writes `validation.json`, `validation-repeatability.json` and
`validation-quota.txt` under its new
`study-v3/operations/<stamp>-<job>-validate-caches/` directory. Read those
receipts there; the wrapper's scientific-output directory is unused for this
validation step.

### Five-cache extraction completed; independent validator submitted

After the SSH connection was restored, inspection at **October 12 13:48:10 UTC**
reconciled job **8028152** against retained scheduler accounting and operation
receipts. The job ended at **01:00:59.191618 UTC** with `failed=0`,
`exit_status=0` and 5,713 scheduler seconds (5,672.78616988397 command seconds).
All five command outcomes, 105 RAM/storage samples and both dataset seals
passed. The earlier disconnection did not remove the retained job evidence;
this record does not claim active continuation through the connection gap.

All five expected files and sidecar hashes were inspected, including the clean
release, protocol, lock, parity, manifest and sample-order bindings. Recorded
shapes are 95,001 × 8,704 for each full training repeat, 76,013 × 8,704 for
development training, 20 × 8,704 for development gallery, and 18,929 × 8,704 for
development queries. Full independent archive hashing and content validation
had **not** passed at this checkpoint.

The compact verification is retained at
`study-v3/operations/week5-launches/20261012T134755Z/cache-completion-verification.json`,
SHA-256 `5ae2cdb2f82d92801a13732212d4aebd338fc6a03b7fbcc9a65c2447ebc6c486`.
It binds the outcome, attempt, scheduler exit, accounting, parity,
repeatability, sidecar hashes and extraction stage measurements. Scientific
release `731938a` and the successful/failed attempt artifacts remain unchanged.

Independent CPU validator **8034547** was submitted at **13:48:11.405663 UTC**
using the frozen scheduler wrapper and was queued at 13:48:12. Its launch JSON
is retained in the same directory. Prelaunch quota free space was 875.6 decimal
GB and filesystem free space 1,047,535,812,608 bytes, checked with the conservative
84-GB remaining-peak bound. No other jobs were present before submission. The
SCC status record now identifies this validator as pending. Its receipts belong
in its new `study-v3/operations/<stamp>-8034547-validate-caches/` directory;
verify accounting, `validation.json`, `validation-repeatability.json`,
`validation-quota.txt` and seals before launching the paired pilots. Task 02
remains in progress and all scientific gates remain pending.

### Independent five-cache validation passed; Contrastive pilot submitted

Independent CPU validator **8034547** passed on `scc-pi6` with four slots.
Scheduler accounting records `failed=0`, `exit_status=0`, 776 wall seconds and
`maxvmem=16.958G`, from **October 12 13:51:46 to 14:04:42 UTC**. Its operation is
`study-v3/operations/20261012T135208Z-8034547-validate-caches/`. All five full
archive hashes/content checks and exact repeatability passed, as did all three
command outcomes, 18 RAM/storage samples and both dataset seals. The validator
recorded 698.095403 seconds and peak process RSS of 8,711,143,424 bytes; these
are distinct from scheduler virtual-memory accounting.

The independently checked receipt hashes are:

- `validation.json`: `286f5508d1fb1fcb1c917e29a19bdd84fa179912a41d101f63a806adf24aa04c`.
- `validation-repeatability.json`: `cc26902fce1743008776b49e1c803ab96881c96d802020d9c14ec1fba6c85ac4`.
- Accounting: `b56a0ada66e98d6c5cf5f2926e07c2541982f622154c6bbacdbfa16adb77b6ed`.

At **14:07:24.097639 UTC**, the guarded launch check reconciled those receipts
and reverified source release `731938a`, protocol, manifests, locks, dependencies,
seals and resources. The compact receipt is
`study-v3/operations/week5-launches/20261012T140710Z/cache-validation-verification.json`,
SHA-256 `55c68d8b5b68e508038f28d9167539396a92ef35e99eef62d2c6bf0497103adb`.
Full archive checks ran in the CPU allocation; the login-side reconciliation
read their receipts. Scientific admission remains false.

The **Contrastive engineering pilot 8035278** was submitted at
**14:07:25.982651 UTC** and remained queued at the launch checkpoint. The launch
receipt in the same directory has SHA-256
`06d921b20c863f5810571ed4b5eba6d49d4fdf535e5d33a820c932a2dd63fd6f`.
The scheduler request was verified as 12 hours, four slots with 8 GB per slot,
and one L40S with at least 16 GB GPU memory; this is a request, not an observed
allocation. The command uses the reviewed external controller and its exact
passed diagnostic binding with the verified caches. Current quota free space
was 873.72 decimal GB and filesystem free space 1,045,522,546,688 bytes.
The reviewed one-off launch helper is retained under
`study-v3/operations/week5-launch-tools/20261012T140643Z/`; its 17 offline guard
checks passed before launch.
The persistent SCC status points to this launch record. No pilot result is
claimed; task 02 remains in progress and all scientific gates remain pending.

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
with the real dataset seal intact; verified successor preparation job 8028032,
including exact manifest identity and unchanged scientific settings; passed 84
supplementary checks and independently verified the actual dependence tables.
Task 03 is complete. The fixed geometry panel passed independent verification
and exact fresh-process repeats. The allocated controller remedy passed after
the preserved first cache failure; the fresh attempt passed parity and was
independently verified extracting caches on the assigned L40S. Both full-size
extractions are now retained with a passed allocated repeatability receipt and
independently checked sidecar bindings. All five cache commands subsequently
completed successfully with retained accounting, resource and seal evidence;
independent CPU cache validation passed all five archives and repeatability.
The first Contrastive engineering pilot has been submitted.

**Next:** Verify Contrastive engineering pilot 8035278, then the paired
Contextual and SupCon pilots and independent pilot validation. Complete development corruptions,
full-query damage telemetry and timing. Include the
[repeated-validation call-count audit](week-5-capacity-validation-audit.md) in
the measured forecast, including whole-report costs. Use the immutable receipts
for the capacity decision and next-week handoff. Software rehearsal does not
replace fresh scientific admission evidence.

**Open issues:** The three successor pilots and remaining Week 5 admission
evidence are unfinished; the failed first attempt is preserved after its allocated remedy
test passed. Actual researcher minutes remain unreported at the researcher's
explicit request. Technical completion and formal
weekly closure have not been claimed; all selection/final/novel gates remain shut.
