# Week 5 execution record

Started October 11, 2026 (America/New_York), before the October 12–18 calendar
week, at the researcher's direction. **Week 5 remains open. The measured runtime
profile failed a necessary capacity condition. The reviewed validation/capacity
successor passed installation, rehearsal and preparation; fresh scientific
regeneration and measured admission remain pending. No scientific admission is
complete.** The [incoming handoff](week-5-handoff.md),
[Week 4 record](week-4-execution.md), [current protocol](protocol-v3.md) and
[adopted October 9 amendment](../decisions/0006-v3-execution-completion-amendment.md)
and [October 12 engineering amendment](../decisions/0007-safe-validation-reuse-and-stage-capacity.md)
govern this work.

## Current checkpoint: October 19, 2026

**Week 5 is blocked.** Execution-r2 release
`f101f0e9d9bd64275d2088deab1b0bdcfcc53620` retains accepted
[installation and rehearsal 8044010](#execution-r2-rehearsal-accepted-preparation-submitted),
[preparation 8045152](#successor-preparation-accepted-october-13) and
[supplementary checks 8048540](#transferred-controller-supplementary-checks-accepted-october-13).
Tasks 01 and 03 retain their accepted execution-r1 history; those completions
do not admit execution-r2. Fresh geometry, parity/caches, three pilots,
corruption/replay evidence and measured CPU/GPU capacity remain incomplete.

Resolver job **8135335 failed on October 15 at 1:54:30 PM EDT**, after five
scheduler seconds; the October 19 observation verified the failure. It stopped
at the interpreter ELF build-ID check before either resolver child ran. The
geometry cause and a compatible runtime remain unproven. After inconclusive
job 8104416 and failed job 8135335, the diagnostic stopping count is **two
consecutive allocated attempts without narrowing or unblocking this blocker**.
No further diagnostic jobs or tool-building for this blocker are authorized
under the current stopping rule.

The researcher authorized the [focused runtime review](#october-19-focused-runtime-review-allocations-remain-held)
and explicitly kept new allocations on hold. That review is complete; it
establishes no compatible runtime and does not reset the stopping count.
**Next prerequisite:** resolve the missing interpreter-note and vendor-runtime
identity evidence and obtain a researcher decision before another allocated
comparison. BU Research Computing Services consultation is the recommended
route. The review below specifies the questions and acceptance criteria; no contact or allocation has
been made. Preserve exact equality/identity checks and the original panel/fallback. The October 18
go/no-go did not pass; re-estimate the complete remaining schedule and capacity
before selection. Task 02 and task 04 are blocked, all scientific gates remain
pending, and selection, final training and novel opening remain closed. No job
was active in the October 19 scheduler observation; no new job was submitted.

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

The Contrastive-execution/Contextual-launch checkpoint (`3dbf30d`) was published
through guarded migration `20261012142756` and deployment
`dpl_4P8zAYocHF1hZF1JsA9hejHmRPiT`. The single deployment waited in Vercel's
queue before building; no duplicate deployment or cancellation was used. At
**October 12 14:38:12 UTC**, live health/export and browser checks verified
Week 5 version 15 active, task 02 version 12 in progress, task 03 version 8 done
and all gates pending. Actual time remains unreported. All other weeks and
source links are unchanged; the fallback and protocol match the public export.
Fifteen database assertions, 22 tracker tests, typecheck, focused lint, workspace
checks and production builds passed. Private export redirects to sign-in;
Journey returned HTTP 200 and no browser errors occurred. PR 33 remains a draft
stacked on PR 31; full independent pilot validation remains pending.

The Contextual-execution/SupCon-launch checkpoint (`7267c9b`) was published
through guarded migration `20261012145015` and deployment
`dpl_6vxCMTG9TgxugpPQ6hdzfe9v1kYG`. At **October 12 14:56:10 UTC**, live
health/export and browser checks verified Week 5 version 16 active, task 02
version 13 in progress, task 03 version 8 done and all gates pending. Actual
time remains unreported. All other weeks and source links are unchanged; the
fallback and protocol match the public export. Fifteen database assertions,
22 tracker tests, typecheck, focused lint, workspace checks and production builds
passed. Private export redirects to sign-in; Journey returned HTTP 200 and no
browser errors occurred. PR 33 remains a draft stacked on PR 31. The Week 6
handoff now explicitly preserves unreported time instead of requesting it again.

The SupCon-execution/independent-validator checkpoint (`ece0f1a`) was published
through guarded migration `20261012150708` and deployment
`dpl_BAbHiASDezr2RtkEpoXrqhrXLkxC`. At **October 12 15:10:18 UTC**, live
health/export and browser checks verified Week 5 version 17 active, task 02
version 14 in progress, task 03 version 8 done and all gates pending. Actual
time remains unreported. All other weeks and source links are unchanged; the
fallback and protocol match the public export. Fifteen database assertions,
22 tracker tests, typecheck, focused lint, workspace checks and production builds
passed. Private export redirects to sign-in; Journey returned HTTP 200 and no
browser errors occurred. PR 33 remains a draft stacked on PR 31; no independent
three-pilot validation outcome is claimed at this checkpoint.

The pilot-validation blocker (`ed60772`) was published through guarded
migration `20261012151758` and deployment `dpl_88mYXZxPspai1JMcjZyVFGCNFG2Q`.
At **October 12 15:22:20 UTC**, live health/export and browser checks verified
Week 5 version 18 active, task 02 version 15 blocked, task 03 version 8 done and
all scientific gates pending. Actual time remains unreported. All other weeks
and source links are unchanged; the fallback and protocol match the public
export. Fifteen database assertions, 22 tracker tests, typecheck, focused lint,
workspace checks and production builds passed. The seed-state test was updated
to the verified blocked state. Private export redirects to sign-in; Journey
returned HTTP 200 and no browser errors occurred. PR 33 remains a draft stacked
on PR 31. The initialization cause remains unconfirmed; corruption and timing
work remain held while the preserved failure is diagnosed.

The pre-retry diagnostic/runtime record was committed and pushed as `9333c4a`.
Guarded migration `20261012153919_record_week_five_initialization_diagnostic.sql`
(SHA-256 `ca98fc6c1c606ee51afae7c6faa553fbc9cde1d9f9b775b1c5ff4c5b89099ac5`) applied successfully.
Deployment `dpl_ANXCC3c8j3tpxspxomPg6HHpZ9gQ` was promoted and the live
health/export/page checks passed at **October 12 15:43:31.745 UTC**:
Week 5 v19 remained active, task 02 v16 remained blocked, actual time remained
unreported and all scientific gates remained pending. The fallback and protocol
matched the public export; all 13 other weeks, source links and closed history
were unchanged. The rendered reflection/task/protocol passed, Journey returned
200, no browser errors occurred, and the private export still redirected to
sign-in. Verification passed 15 guarded database assertions, 22 tracker tests,
typecheck, focused lint, local/hosted builds, workspace and runbook shell checks.
The staging inventory preserved all 81 unrelated production files, including
Journey. No scientific source or original attempt was modified.

The compatible-runtime retry checkpoint was committed and pushed as `ecbe3a0`.
Guarded migration `20261012154836_record_week_five_runtime_validation_retry.sql`
(SHA-256 `b7ea3fa5c9039830c265f1b2b0ad82daa3c2c9d7443b25d7157a7dcb2c462f80`) applied successfully.
Deployment `dpl_14spStLnAPhxB2tybVz2f2ohvQkQ` was promoted and the public
health/export/rendered-page checks passed at **October 12 15:52:45.491 UTC**.
Week 5 v20 remained active; task 02 v17 returned to in progress; all gates
remained pending, actual time remained unreported and no full validation pass
was claimed. Fallback/protocol matched the export; all 13 other weeks, links
and closed history were unchanged. Journey returned 200, no browser errors
occurred and private export remained sign-in protected. Verification passed
15 guarded database assertions, 22 tracker tests, typecheck, focused lint,
local/hosted builds, workspace and runbook shell checks. The staged production
inventory preserved all 81 unrelated files. The Week 6 handoff also records
native-runtime compatibility and the narrower CPU queue pool without authorizing
future experiments. Scientific source and preserved attempts remain unchanged.

The accepted-pilot/corruption-submission checkpoint was committed and pushed as
`ff722b5`. Guarded migration
`20261012162733_record_week_five_pilot_acceptance_corruption_launch.sql`
(SHA-256 `486d3ba667510b128b948d66ae50d1a88bb139f239fe1d259c5a3b686dea323e`) applied successfully.
Deployment `dpl_EptFraWeVJBvm9vfYiNsp8w83UX9` was promoted; public
health/export/rendered-page verification passed at **October 12 16:32:05.451 UTC**.
Week 5 v21 remained active, task 02 v18 remained in progress, actual time
remained unreported and all scientific gates stayed pending. Fallback/protocol
matched the export; all 13 other weeks, links and closed history were unchanged.
Journey returned 200, the browser reported no errors and private export remained
sign-in protected. Checks passed 15 guarded database assertions, 22 tracker tests,
typecheck, focused lint, local/hosted builds, workspace and runbook shell checks.
The production inventory preserved all 81 unrelated files.

A later SCC observation confirms job **8035983** started at **16:28:49 UTC** on
`ece@scc-j01`, operation
`study-v3/operations/20261012T162852Z-8035983-corruptions/`.
At **16:31:47 UTC**, 23 resource samples and five allocated-GPU preflights had
passed. The actual L40S used CUDA-visible device 3, with 47,162,982,400 free
bytes out of 47,695,921,152 in the latest probe. Maximum sampled RSS was
351,244,288 bytes; system available RAM was at least 255,471,804,416 bytes,
quota remaining 868.54 decimal GB and filesystem free at least
1,039,952,510,976 bytes. The job had no final outcome. This dated running
observation supplements the earlier queued checkpoint; it does not establish
corruption completion or admission. SCC status and continuation retain the
active job and require verified results before timing.

The geometry/timing milestone was committed as `3edb81c`; its timestamp
correction and active-allocation observation were committed as `69d0abb`.
Both were pushed. Guarded migration
`20261012183312_record_week_five_geometry_completion_timing_launch.sql`
(SHA-256 `f374c2a2162021150a14b2ae10d8eefbdbb3151c7d790bcbd8da3f2782ee1cc4`)
and follow-up `20261012183739_correct_week_five_geometry_receipt_timestamp.sql`
(SHA-256 `833b287551da98fca5b7ec5908339a58530b291f8f0e9fdeeca1dd3693140017`)
applied without rewriting the first migration. Its initial build
`dpl_7C92S9d82FHBnpErYk1ymMkj9b8r` was not promoted.

Corrected deployment `dpl_5wHjdwAK2BThb5USr3MpMYFazUKh` was promoted and
public health/export/rendered-page checks passed at **October 12 18:41:37.265 UTC**.
Week 5 v23 remained active; task 01 v8 was done at the actual receipt-write time
**18:31:21.614571 UTC**, task 02 v20 remained in progress, task 03 remained done,
and every scientific gate remained pending. Actual time remained unreported.
Fallback/protocol matched the public export; all 13 other weeks, source links
and closed history were unchanged. The rendered reflection, both completed-task
evidence sections and active task note passed; Journey returned 200, no browser
errors occurred and private export remained sign-in protected. Each migration
passed 17 guarded database assertions; 22 tracker tests, typecheck, focused lint,
local/hosted builds, workspace and runbook shell checks passed. Seed-progress
expectations now reflect the verified additional task completion. All 81 unrelated
production files were preserved. No frozen scientific source or artifact changed.

The accepted-timing/component-queue checkpoint (`a6ed904`) was published through
migration `20261012190124` and promoted deployment
`dpl_DdBqG5niwEnham7vjwC5QwypnAzY`. Verification at October 12 **19:08:45 UTC**
confirmed Week 5 version 24 active, task 02 version 21 in progress, tasks 01/03
done with their existing completion timestamps, task 04 pending, all three gates
pending and actual time unreported. The [public export](https://pose-embed-tracker.vercel.app/api/export?format=json)
exactly matched the repository fallback and protocol; all 13 other weeks and
source links were unchanged. The page/reflection/evidence and protocol rendered
without browser errors, Journey returned 200, and private export redirected to
sign-in. Fifteen database guards, 22 tracker tests, lint/typecheck, local and
production builds, workspace verification and all 19 runbook shell fences passed.
Production staging preserved all 81 unrelated source files. PR 33 remains a draft;
no component result, full admission, capacity approval or weekly closure is claimed.

The measured-profile no-go checkpoint (`2e6f69a`) was published through guarded
migration `20261012204312` and promoted deployment
`dpl_CjNMpvuZD41kQiSRDBhjJ1oRaBUb`. Live verification at **2026-10-12T20:50:26.908Z**
confirmed Week 5 version 25 active, tasks 01/03 and their completion timestamps
preserved, task 02 version 22 in progress, task 04 version 5 blocked, and all
three gates pending. Gate 03 version 6 contains the verified no-go evidence,
with no waiver or decision timestamp; actual researcher time remains unreported.
The [public export](https://pose-embed-tracker.vercel.app/api/export?format=json)
exactly matched the fallback and protocol, with all 13 other weeks and source
links unchanged. The blocker/reflection/evidence and protocol rendered without
browser errors, Journey returned 200, and private export redirected to sign-in.
Nineteen guarded database tests, 22 tracker tests, lint/typecheck, local and
production builds, workspace checks and all 19 runbook shell fences passed.
Production staging preserved all 81 unrelated source files; PR 33 remains a
draft. The update records an unresolved capacity blocker, not scientific
admission, approval to amend the implementation or formal weekly closure.

The ADR0007 authorization checkpoint was committed and pushed as `05026c0`
before guarded migration `20261012211541` was applied. Deployment
`dpl_EqgPvrFQCKpEKpbRDe1cVDrU5ouW` was promoted and verified at
**2026-10-12T21:22:19.784Z**. The [live export](https://pose-embed-tracker.vercel.app/api/export?format=json)
matched the fallback exactly: Week 5 version 26 active; task 02 version 23 in
progress; task 04 version 6 blocked; all gates pending, including gate 03 version
7 retaining the no-go and adopted authorization. Tasks 01/03, their completion
timestamps, all 13 other weeks, source links and unreported time were preserved.
The live plan source matched canonical Markdown byte-for-byte; the ADR GitHub
evidence link resolved. The page, reflection, evidence and protocol rendered
without errors, Journey returned 200 and private export redirected to sign-in.
Twenty database guard tests, 22 tracker tests, lint/typecheck, local/production
builds and workspace checks passed; 81 unrelated production source files were
preserved. PR 33 remains a draft. This publishes authorization only: successor
implementation verification, freeze, regeneration and measured admission remain
pending.


A follow-up static-plan correction was committed as `1d3e9e2` and deployed as
`dpl_4LrQxr4LVDJEnT4KadM5mnEbDtSg`, with live health verified at
**2026-10-12T21:27:56.749Z**. The manual capacity action now labels 120 decimal GB
as the historical October 9 estimate and requires a fresh execution-r2 inventory;
the schedule action and scope authority describe ADR0007's CPU/GPU accounting
and pending successor work. No database update was needed. The live export
matched the corrected fallback, all progress rows and versions were unchanged,
and the rendered protocol, Week 5 evidence, Journey and private-export boundary
passed verification. All 81 unrelated production source files remained unchanged.

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

### Contrastive execution checked; Contextual pilot submitted

Contrastive engineering pilot **8035278** completed on `scc-j07` from
**October 12 14:12:08 to 14:20:13 UTC**: scheduler `failed=0`, `exit_status=0`,
485 wall seconds. The fixed run records 20 epochs and 47,520 updates. Inspection
at **14:22:15 UTC** checked execution and metadata, including hashes/presence of
21 diagnostic records, five epoch records and required artifacts. The frozen
trainer ran its health guards; this inspection did not independently replay
numerical health checks or verify checkpoint tensor content. The receipt marks
`scientific_use_allowed=false` and full allocated three-pilot validation pending.
No pilot accuracy is used to choose scientific settings.

Operation: `study-v3/operations/20261012T141227Z-8035278-pilot/`.
The run is the `contrastive/` subdirectory of the corresponding revision attempt.
The compact metadata check is retained at
`study-v3/operations/week5-pilot-verification/20261012T142215Z/contrastive-metadata-verification.json`,
SHA-256 `34fab419ae0ed9fa3627eea5c8bef49becc475fa3b8eac1470ce3cfa3035e1ce`.
It binds run manifest `15a733d5aa87d7e4a26cee172586ea6e7e11a9e068cee843bf874e9bab2da9fa`,
metrics `86548e7acfcee76bfae95b0c6cccea589352f4ffe7e0790fffc90081ceb1716b`
and accounting `b2a61a144c9b1c4cc3556f1854bc9a204989efa6bec888482a64e53b9634ccff`.
The reviewed metadata helper passed six offline checks; its exact source hash is
bound in the receipt. Outer command/resource/seal and diagnostic-binding checks
passed separately through the existing reviewed operation validator.
Nineteen resource files passed. Run telemetry records 386.14067 seconds
(440.8384832230222 seconds for the complete scientific command), peak host
memory 4,711,288,832 bytes, peak GPU allocation 3,286,354,944 bytes and reserved
GPU memory 3,420,454,912 bytes. Retained checkpoints total 285,255,316 bytes.

**Contextual engineering pilot 8035452** was submitted at
**14:27:05.178539 UTC** and was queued with four slots at launch. It preserves
seed 7, 20 epochs, physical P=8/K=4, the verified caches, external controller and
exact passed diagnostic binding. Prelaunch checks reverified clean release
`731938a`, the 52 bound source files, locked dependencies, protocol/manifests,
cache validation, Contrastive accounting/metadata, seals, no running jobs and
absence of a duplicate Contextual attempt. Quota free space was 872.83 decimal
GB and filesystem free space 1,044,566,245,376 bytes; the conservative 84-GB
remaining-peak bound passed the required reserve check.

The launch is retained at
`study-v3/operations/week5-launches/20261012T142651Z/launch.json`.
Its SHA-256 is `ae858b487789ffadb79401440df3e59ffa534a9e2bd2fe2e84bda011ed5d9235`.
The reviewed one-off helper is preserved at
`study-v3/operations/week5-launch-tools/20261012T142648Z/launch-contextual.py`,
SHA-256 `b351836631c0c5167341070d385804423a9c9cf42e4dead69da3942279fd71fd`;
four offline duplicate-guard checks and peer review passed before launch.
No Contextual outcome is claimed. Task 02 remains in progress, all scientific
gates remain pending and full independent three-pilot validation is still required.

### Contextual execution and pairing checked; SupCon submitted

Contextual pilot **8035452** completed on `scc-j01`, starting October 12 at
14:31:22 UTC and ending at **14:40:50.527599 UTC**. Scheduler accounting records
`failed=0`, `exit_status=0` and 568 wall seconds. Execution/metadata checks record
20 epochs, 47,520 updates, five epoch records, 21 diagnostics, 20 passing resource
checks and seals. Initialization, batch plan and all 20 epoch-plan hashes match
Contrastive. Full checkpoint tensor and numerical validation remains pending
in the separate allocated three-pilot validator.

The compact receipt is retained at
`study-v3/operations/week5-pilot-verification/20261012T144700Z/contextual-metadata-verification.json`,
SHA-256 `3e4ca8d5cafdf11397fa2c832a65105019b2443a3a1c1656c8f6beda350a9f35`.
Run time was 469.532168 seconds, including 343.053875 training, 5.085005
validation and 0.52249 checkpoint seconds. Peak host memory was 4,700,549,120
bytes; GPU allocated/reserved peaks were 3,286,354,944 and 3,420,454,912 bytes.
Retained checkpoints total 285,255,828 bytes. These measurements do not establish
full scientific admission.

**SupCon pilot 8035533** was submitted at **14:49:36.052186 UTC** and was queued
at launch. Frozen source/locks, dependencies, all 58 diagnostic bindings, cache
validation, prior Contextual accounting/metadata, seals, no running jobs and
duplicate-attempt guards passed. Quota free space was 871,930,000,000 bytes and
filesystem free space 1,043,601,555,456 bytes; the conservative 84-GB
remaining-peak bound passed the reserve check. The scheduler request was
verified as four 8-GB slots, one L40S and 12 hours; no allocation is inferred.

Launch: `study-v3/operations/week5-launches/20261012T144920Z/launch.json`,
SHA-256 `bf2014596e0f121336b2d41c531163ebacb697beafcd3c667c06fdbb1094d3ee`.
The reviewed helper is preserved at
`study-v3/operations/week5-launch-tools/20261012T144902Z/pose-week5-launch-supcon.py`,
SHA-256 `b072e5df19f59b027895247b375b1acec6ecd568c046d2056bf2e8ffd3e3ca83`.
No SupCon outcome is claimed. Task 02 remains in progress, all gates remain
pending, and independent three-pilot validation is required before corruption work.

SupCon job 8035533 subsequently started at **14:52:42 UTC** on `ece@scc-j08`
with four slots, 32 GiB host memory and one L40S (`CUDA_VISIBLE_DEVICES=0`).
Its operation is `study-v3/operations/20261012T145244Z-8035533-pilot/`; the run
is `supcon/` in the corresponding revision attempt. The allocated GPU preflight
passed at 14:52:58 UTC with 47,163,047,936 bytes free of 47,695,921,152 total.
The 14:53 UTC resource observation passed RAM/storage checks. This is a dated
allocation observation; no SupCon completion or pilot admission is inferred.

### SupCon execution checked; independent three-pilot validator submitted

SupCon engineering pilot **8035533** completed on `scc-j08` from
**October 12 14:52:42 to 15:00:01.270723 UTC**. Scheduler accounting records
`failed=0`, `exit_status=0` and 439 wall seconds. Execution/metadata checks
record 20 epochs, 47,520 updates, five snapshots, 21 diagnostics, 18 passing
resource files and both seals. Initialization, batch plan and all 20 epoch-plan
hashes match Contextual and therefore all three pilots. Full checkpoint tensor
and numerical validation remains pending in the separate allocated validator.

The compact receipt is retained at
`study-v3/operations/week5-pilot-verification/20261012T150130Z/supcon-metadata-verification.json`,
SHA-256 `c0b3ef082032f4183c8649dbceff8fa9fd937b27691d08cea8eb0f04f3a4c0d7`.
Run time was 368.018387 seconds, including 254.76661 training, 5.299794
validation and 0.493757 checkpoint seconds. Peak host memory was 4,711,464,960
bytes; GPU allocated/reserved peaks were 3,286,354,944 and 3,420,454,912 bytes.
Retained checkpoints total 285,255,316 bytes.

**Independent CPU pilot-validator 8035576** was submitted at
**15:06:35.682596 UTC** and queued at launch. The frozen wrapper requests four
8-GB slots and 12 hours, with no GPU, for the exact Contrastive, Contextual and
SupCon runs. Source, dependencies, locks/manifests, cache validation, all three
metadata/accounting/pairing receipts, seals, no running jobs and duplicate
guards passed prelaunch verification. Quota free space was 871,040,000,000 bytes
and filesystem free space 1,042,645,254,144 bytes; the conservative 84-GB
remaining-peak bound passed the required reserve check.

Launch: `study-v3/operations/week5-launches/20261012T150600Z/launch.json`.
The launch SHA-256, verified at 15:08:09 UTC, is
`386ad185a04f22d217f6ec9d6a09c87feb4a75afe765efbaa47b55f316d81791`.
The reviewed one-off CPU launcher is retained under
`study-v3/operations/week5-launch-tools/20261012T150400Z/`, source SHA-256
`337f2f598fdb86f58d9d3cfabb70729fa21e445f6d3b94407b8e3cef03b32800`;
14 offline checks and independent review passed. No validator result is claimed.
Task 02 remains in progress and all scientific gates remain pending. Verify the
allocated outcome, accounting, complete three-pilot receipt, resources and seals
before corruption work; retain all original pilot attempts.

### Independent pilot validation failed; initialization mismatch unresolved

Independent pilot-validator **8035576** failed at **October 12
15:11:23.328668 UTC**. Command 002 exited 1 with
`ValueError: locked initialization hash cannot be reproduced`.
Scheduler accounting records `failed=0`, `exit_status=1` and 113 wall seconds.
The failed validation took 67.278541 seconds with peak RSS 996,483,072 bytes;
all eight resource files passed RAM/storage checks. No active jobs remained
when the failure was inspected. The three pilot execution/metadata receipts
remain valid records, but full independent three-pilot validation has failed.

The failed operation is
`study-v3/operations/20261012T150934Z-8035576-validate-pilots/`.
Its `validation.json` SHA-256 is
`c30e021a6d2f5de0c55fa36d410cd2e726fb006b0ec936a06d32bab6bb7dc96e`.
The original operation has **no seal-after receipt**. A separately retained
post-failure seal check passed, SHA-256
`34295455fded9b7bbcee92a57d1d4571e51d37c4f4e4606421b372b0839c905d`;
the original attempt was not backfilled or rewritten. The independent failure
audit is retained at
`study-v3/operations/week5-pilot-validation-failure/20261012T151648Z/failure-audit.json`,
SHA-256 `abcb612681e6ef18b22ca9f62b97a8011a69492a44d6ae4e68d27e580290b23d`.

The cause remains unconfirmed. CPU arithmetic dispatch is under investigation;
source inspection confirms that both the originally generated and rebuilt heads
are initialized on CPU. Week 4's validator lacked this new initialization
reproduction check, so its previous pass does not validate the new check.
The next step is an isolated synthetic initialization diagnostic on the failing
host with reviewed source/platform evidence. Preserve all attempts and require
valid independent verification before advancing. Task 02 is blocked, all gates
remain pending, and corruption/timing continuation is held. No research recipe,
seed, batch, metric or scientific claim has been changed in response.

### Synthetic initialization diagnostic and pre-retry runtime requirement

Synthetic-only job **8035737** completed successfully in **17 scheduler wall
seconds** on the same failing `scc-pi4` host. Its Intel E5-2650 v2 (Ivy Bridge)
CPU lacks AVX2/FMA. Three native `DEFAULT` and three explicit baseline `DEFAULT`
initializations all produced SHA-256
`d09429fb578c782281dc032258ba707213494ec78f2f704aba28097fdcd40d69`,
instead of the locked
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`.
RNG state was identical. The diagnostic used a synthetic full-size head only:
no dataset tensors, saved heads or GPU were used. This confirms a runtime
initialization difference on that CPU. A local arithmetic diagnostic supports
CPU-dispatch/FMA rounding as an explanation; compatible full pilot validation
has not yet passed.

Independent verification bound all **27 evidence files**, five passing resource
records, both dataset seals and successful accounting. The verification is
`study-v3/operations/week5-init-verification/20261012T153404Z/verification.json`,
SHA-256 `5e5de4bb155e6b22ea486416549d4a080207872e902e1a33ad5173b17ff01cad`;
its verifier SHA-256 is
`f02bc38a76f674c6bf55136e84c0df60a5eff0cc4fc8c0b646224e4a6d4dc94b`.
The diagnostic summary SHA-256 is
`9d480bc546a4983d42bf8eadde080452a7309e8dccdda2e583e0e651b4786072`.
The original failed validator and separate post-failure seal remain unchanged.

Before the affected retry, the [SCC runbook](scc-v3-runbook.md) now requires the
reviewed allocation wrapper: request AVX2, inspect actual CPU flags, and verify
the exact locked initialization with native CPU dispatch before invoking the
unchanged full validator. The transferred wrapper bundle is
`study-v3/operations/week5-cpu-retry-tools/20261012T153900Z/`, with `tools.json`
SHA-256 `797e180b1be91171e018961d11238e2468411195fbcaef2520bb0ad46bdf0d9d`.
Eleven guard tests and independent review passed. No retry submission is claimed
at this checkpoint. This is an allocation/runtime requirement, with **no change
to frozen scientific source, checks, tolerances, seeds, physical batches or
20-epoch duration**. The narrower eligible CPU queue pool must enter the dated
capacity forecast; no future allocation or feasibility is inferred. Task 02
remains blocked, all scientific gates remain pending, and corruption/timing
work remains held until full independent pilot validation passes.

### Compatible-runtime preflight passed; full pilot validation retry running

Retry **8035829** was submitted at **October 12 15:44:10.970322 UTC** and
started at **15:46:06 UTC** on `w@scc-wg4`, with four CPU slots, 32 GiB,
12 hours and no GPU. The allocated CPU has actual AVX2/FMA flags and its native
AVX2 runtime reproduced the exact locked initialization
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`
in all three full-size repetitions. Independent verification passed the
preflight command, three resource files and both seals. The preflight operation
is `study-v3/operations/20261012T154626Z-8035829-pilot-validation-preflight/`;
its native receipt SHA-256 is
`ac7d383de62bbf778708312966c9bff8ba97d807e62f9b0cb17d070981874422`.

The independent preflight metadata receipt is
`study-v3/operations/week5-runtime-verification/20261012T154801Z/verification.json`,
SHA-256 `29a26154ed7309be908007fa6cc382f0773eda63764d23deb0aff06182625b5d`.
Launch evidence is
`study-v3/operations/week5-launches/20261012T154408Z/launch.json`, SHA-256
`7a7f9c2a1cf58bcf4178ff8befb8430418dba1669542711fd48d8f19b1e7bf5f`.
The reviewed administrative launcher was used once; inspect its preserved intent
and the existing job before considering any later action. Do not resubmit it.
The current full-validation resource preflight passed with 244,574,945,280 bytes
host memory available, 868,540,000,000 bytes quota remaining and
1,039,960,899,584 bytes filesystem free. The assigned job budget remains 32 GiB.

The **unchanged full validator is running**, at
`study-v3/operations/20261012T154645Z-8035829-validate-pilots/`.
Its final accounting, tensor/numerical validation, resources and seals have not
yet been accepted. Task 02 returns to in progress, preserving failed attempt
8035576 and its separately recorded post-failure seal. Corruption/timing work
remains held until full validation passes; all scientific gates stay pending.
No frozen source, checks, tolerances, seeds, physical batches or duration changed.
The narrower eligible CPU queue pool remains a capacity-planning requirement.

### Independent three-pilot validation accepted

Allocated retry **8035829** completed successfully: scheduler accounting records
`failed=0`, `exit_status=0`, **2,007 wall seconds**, start October 12
15:46:07 UTC and end 16:19:34 UTC on `scc-wg4`. The full validator completed at
16:19:33.493679 UTC. All three arms passed their fixed **20 epochs / 47,520
updates**, complete saved snapshots, numerical projection/health/rank replays
and cross-arm pairing. The compatible Broadwell runtime reproduced locked
initialization without changing scientific source, validation checks,
tolerances, seeds, batches or duration. Failed attempt 8035576 remains preserved.

The allocated `validation.json` SHA-256 is
`c576f7840438c50486615635fe0583d99ddc2d851a56a86b200ad24d7b0e4dcb`.
Its complete validation telemetry is **1,935.639018 seconds**, with command wall
1,940.4239999730198 seconds and peak process RSS **4,667,924,480 bytes**.
These inclusive measurements include standalone setup and checks; they are not
an isolated lower bound on repeated admission or final-authorization calls.

The independent completion review at **16:25:41.428722 UTC** checked all **122
bound evidence files**, scheduler accounting, 39 full-validation resource
samples, three native-preflight resource samples and both seals for each phase.
Its receipt is
`study-v3/operations/week5-pilot-validation-verification/20261012T162541Z/verification.json`,
SHA-256 `3716107eecbe3561c29c87d7f547f569816ad8e8a359b4f412434d4a71a25a7d`;
verifier SHA-256 is
`a3a8a73847bf2969eb886d456e68bf657ba27362402a30cd9dc62ca003feb4aa`.
Tensor and numerical checks ran in the allocated job; the login-node review
verified their preserved receipts and bindings rather than rereading tensors.
This accepts independent pilot validation, **not campaign admission**. Further
corruption, full-query telemetry, resident timing and capacity evidence remain
required. Task 02 remains in progress and all scientific gates remain pending.

### Corruption job submitted; results pending

Corruption job **8035983** was submitted at **October 12 16:27:02.731983 UTC**
and remained queued at approximately **16:27:50 UTC**; no allocation, scientific
operation or result was present at that observation. Its reviewed launcher bound
the accepted pilot receipt, original release 731938a, all 52 source hashes,
locks/manifests/dependencies, cache validation, fixed geometry and the 58-file
GPU diagnostic. Dataset seals, absence of active/duplicate jobs and the storage
reserve passed before submission. The request is four CPU slots, 32 GiB,
12 hours and one L40S, with compatible AVX2/Sapphire Rapids/Gold 6426Y CPU
requirements. Requested resources are not evidence of an actual allocation.

Launch evidence is
`study-v3/operations/week5-launches/20261012T162658Z/launch.json`, SHA-256
`530ed00fc8d258d7c3bf4797fe81f4c38690aff988853490f0f70ea37f96470c`.
Prelaunch quota remaining was **868,540,000,000 bytes** and filesystem free space
was **1,039,960,899,584 bytes**; the conservative 84-GB additional-peak estimate
and 200-GiB reserve passed. The fixed work is all nine development corruption
conditions, 27 query projections and 27 engineering results. No result may
select a head, condition, recipe, threshold or retry. Inspect this job and its
preserved launch intent; do not duplicate the submission. Task 02 remains in
progress, all gates remain pending and no campaign admission is authorized.

### Corruption execution accepted; full-query geometry task complete

Corruption job **8035983** completed at **October 12 18:28:39.920098 UTC**;
terminal accounting records `failed=0`, `exit_status=0`, **7,190 wall seconds**
and end time 18:28:40 UTC on `scc-j01`. The passed independent completion receipt was written at
**18:31:21.614571 UTC**, after review started at
**18:30:49.548448 UTC**. The review passed **927 evidence bindings**, all **135 commands**,
**67 GPU preflights**, **358 RAM/storage samples** and both dataset seals.
Nine 18,929-row encodings, 27 query projections, three clean gallery projections
and 27 engineering results are retained: **39 archives / 9,833,359,944 bytes**.
The receipt is
`study-v3/operations/week5-corruption-verification/20261012T183049Z/verification.json`,
SHA-256 `4b071bc3a900aa347171998b5dd224885391d019b604763f6d55a5a50af50bd5`.
Checker SHA-256 is
`379bc89bf063f933dd2fde4e078156c603d6eb00210ab8fdee1c1ff361e1345f`.
This is an execution/metadata completion review: full scientific archive hashing
and numerical admission replay remain required in an allocation. No tensor
hashing or numerical replay was performed on the login node.

Task 01 is complete on this verified evidence. The previously verified fixed
40-base/43-total panel, two-process exact repeats and absent-category fixtures
are now joined by all nine complete, ordered full-query damage records and
independently recomputed summaries. Every condition has **18,929 finite rows,
zero undefined rows and zero zero-damage rows**, with **38,605,963 originally
observed joint-frame/person locations**. Each jitter condition used fallback
**0 / 18,929 = 0**. The frozen training-only value **0.6601371765136719** and
original evidence binding remain unchanged; zero observed use is not permission
to remove the fallback or its fixture coverage.

The damage quantiles below are rounded for display; exact per-row values and
NumPy-linear summaries remain in the bound sidecars. These describe synthetic
damage, not accuracy, exclusion rules or calibrated real-world prevalence.

| Condition | Minimum | Median | P95 | Maximum | Newly masked observed locations |
| --- | ---: | ---: | ---: | ---: | ---: |
| coordinate_jitter:0.01 | 0.00952559998 | 0.00999750451 | 0.0101852938 | 0.0104900056 | 0 |
| coordinate_jitter:0.025 | 0.0238140002 | 0.024993762 | 0.0254632356 | 0.0262250163 | 0 |
| coordinate_jitter:0.05 | 0.0476280007 | 0.0499875245 | 0.0509264712 | 0.0524500322 | 0 |
| frame_mask:10 | 0.0552486188 | 0.1 | 0.1 | 0.134228188 | 3,861,686 |
| frame_mask:25 | 0.158227848 | 0.25 | 0.25 | 0.32885906 | 9,654,334 |
| frame_mask:40 | 0.278481013 | 0.4 | 0.4 | 0.510067114 | 15,446,557 |
| joint_mask:3 | 0.176470588 | 0.176470588 | 0.176470588 | 0.176470588 | 6,812,817 |
| joint_mask:6 | 0.352941176 | 0.352941176 | 0.352941176 | 0.352941176 | 13,625,634 |
| joint_mask:8 | 0.470588235 | 0.470588235 | 0.470588235 | 0.470588235 | 18,167,512 |

The maximum sampled process-group RSS was 3,288,424,448 bytes; accounting peak
RSS was 3,635,044,352 bytes. Recorded minima were 254,516,006,912 bytes system
available RAM, 855,980,000,000 bytes quota remaining and 1,026,178,416,640 bytes
filesystem free. All recorded resource checks passed. Task 02 stays in progress;
resident timing, allocated full admission replay and measured capacity remain
pending, and all scientific gates remain pending. No selection/final/novel stage
is authorized by this engineering completion.

A separate periodic-GPU metadata audit rechecked all 358 original resource
records against the accepted corruption receipt. Allocated device 3 peaked at
**4,257 MiB / 46,068 MiB reported total**; every `nvidia-smi` status was zero and
usage stayed within the reported total. The unchanged resource files are bound
by `study-v3/operations/week5-corruption-gpu-verification/20261012T183538Z/verification.json`,
SHA-256 `28260ab09bf83d602a2deb7ee6af350a3886b9ce600235ce2cd37bcff8083d6e`.
This adds resource evidence without changing gate status.

### Resident timing submitted; no timing outcome yet

Guarded timing launcher `4ce08cfe34bae6ebea2ba7145fe253fdf1b56f8db4231f9ba34f8aa6302ad6c7`
ran once with the passed corruption receipt and submitted **8038355** at
**October 12 18:32:58.249374 UTC**. The job was **queued at approximately
18:34 UTC**, with no allocation or completion claimed. Its launch record is
`study-v3/operations/week5-launches/20261012T183252Z/launch.json`, SHA-256
`26761143b4926c7d50d28cc1a2ad4cd1a69b638a3df008d1b5e73eb49cdd49d3`.
The unchanged request is four CPU slots, 32 GiB, 12 hours and one L40S with
AVX2/Sapphire Rapids/Gold 6426Y CPU constraints. Prelaunch quota remaining was
**855,690,000,000 bytes**, filesystem free **1,026,165,833,728 bytes**; the
84-GB additional-peak bound and reserve passed. No future allocation is inferred.

Timing retains all 95,001 source rows resident while optimizing only the locked
80 development-training actions. The approved three methods, paired seed/batches
and 20-epoch duration remain fixed; no final head is produced or admitted.
Inspect existing job/launch intent instead of resubmitting. Hold the staged
`85af5ae65f64695240255fa686365e4d120be6b594142c18daee8804e567072b`
completion checker until this actual job finishes successfully and terminal
accounting is available. Full admission replay and the capacity decision remain
separate requirements, with every scientific gate still pending.

A later allocation observation confirms timing job **8038355** started at
**18:35:49 UTC** on `ece-long@scc-j01`, operation
`study-v3/operations/20261012T183551Z-8038355-timing/`. Its actual L40S used
CUDA-visible device 3; eleven initial resource checks and all corresponding
`nvidia-smi` exit statuses passed at approximately 18:36 UTC. No final outcome
was present. This supplements the earlier dated queued observation.

The first tracker milestone used the corruption receipt's `recorded_at` as
completion time. Inspection confirmed that field marks review start; the passed
immutable receipt was written at **18:31:21.614571 UTC**. A separate guarded
correction updates task 01 to this actual receipt-write timestamp, preserving
the original applied migration and its audit trail. The verified geometry
result and pending admission gates are unchanged.

## Accepted resident timing and queued component measurement — October 12

Timing job **8038355** completed at 18:54:55.877214 UTC; terminal accounting
reported success and 1,147 seconds. Independent checker `85af5ae6…` wrote its
passed receipt at **18:59:21.217675 UTC** (its `recorded_at` is the review start):
`study-v3/operations/week5-timing-verification/20261012T185854Z/verification.json`,
SHA-256 `29974c7287b0f36e75dd92c78e6099e16ce7bc652fc631fe021d95061b04ad0c`.
It verified 138 metadata bindings, five commands, two allocated GPU preflights,
29 resource records, both seals and all 60 paired batch plans. Each arm retained
95,001 resident rows while optimizing 76,013 rows from 80 actions for 59,380
updates. No head was saved or made eligible for selection/final use.

Internal wall time was 1,122.070329 seconds; the complete command took
1,124.818611962 seconds. Training took 346.0708438 seconds for Contrastive,
406.2501320 for Contextual and 319.7583118 for SupCon; loading took 2.0954758
and artifact validation 26.7996596 seconds. Peak host RSS was 5,076,500,480
bytes, allocated GPU memory 3,947,458,048 bytes and reserved GPU memory
4,078,960,640 bytes. Separate review of all 29 periodic GPU samples passed,
with peak usage 4,465 of 46,068 MiB:
`study-v3/operations/week5-timing-gpu-verification/20261012T190036Z/verification.json`,
SHA-256 `b36d5406ce0671481e003a47ef781e409fe8d50d3ed32863fb94ab5287f74e0b`.
These are retained engineering measurements, not full scientific admission.

The guarded administrative launcher `983b3e3d…` then submitted read-only
component-measurement job **8038699** at **19:01:02.227712 UTC**, observed queued
at 19:01:56.931301 UTC with four CPU slots and no operation yet. Its immutable
launch is `study-v3/operations/week5-launches/20261012T190054Z/launch.json`,
SHA-256 `134c93fa90316d483a22580e04d698ff5506ed904db082e3bb23e7a941315261`.
Fresh quota remaining was 854,970,000,000 bytes and filesystem free space
1,025,398,276,096 bytes. The launcher has run once; do not resubmit it.
The [runbook](scc-v3-runbook.md) retains the held completion-verifier command
bound to this launch. Its 22 focused and 23 reused tests and independent review
passed; this does not establish the pending job's result.

This diagnostic isolates only the three unchanged pilot-validator calls in
Contextual → Contrastive → SupCon report order. Its measured P is separate
from full A and is not a universal hardware lower bound. Full allocated
admission hashing/numerical replay and the measured capacity decision remain
pending. Tasks 01 and 03 remain complete, task 02 remains in progress and every
scientific gate remains pending; actual researcher time remains unreported.

## Verified component measurement and capacity no-go — October 12

Job **8038699** ran from 19:08:04 to 19:22:00 UTC on `neuro-pub@scc-ke2`
(Sapphire Rapids, Gold-6426Y), with four CPU slots, 32 GiB and no GPU.
Accounting passed (`failed=0`, `exit_status=0`, 836 seconds). The unchanged
validator passed all three complete calls in persisted report order:

| Call | Measured seconds |
| --- | ---: |
| Contextual | 266.806532714 |
| Contrastive | 256.642679657 |
| SupCon | 254.824888204 |
| **P: sum of all three calls** | **778.274100575** |

Independent checker `7f1609d3…` passed **1,276 metadata bindings**, two monitored
commands, 17 resource samples, both seals, exact accounting, native initialization
and runtime/call-order checks. Its receipt is
`study-v3/operations/week5-p-component-verification/20261012T193150Z/verification.json`,
SHA-256 `cd21652427c8918473b97ec7a58a31db4ebd3e94b5582f6c65f8912f9e898c9b`.
Review began at 19:31:50.483463 UTC; the passed receipt was written at
**19:32:11.651357 UTC**. Peak scheduler RSS was **4,601,929,728 bytes**;
periodic samples observed up to 2,300,039,168 bytes. All three validators ran
inside the allocation; no scientific tensor/checkpoint hashing or replay ran
on login. No new head or selection authorization was produced.

The [capacity audit](week-5-capacity-validation-audit.md) derives the required
necessary condition: P must be below **305.840707965 seconds** to leave any
room for the other work within the shared 48-hour maximum, with 25% slack.
Measured-profile scaling of the largest report's pilot component alone is
`452 × P × 1.25 = 122.145796 hours`, **2.544704 times** that maximum. The remaining
successful path's `2101P` component forecasts 454.209413 hours before slack,
or 567.761766 hours with slack. These are component forecasts on this measured
runtime profile, not measured complete report/A/F durations or universal
hardware lower bounds. Other validation, report work, queue/setup and retries
are additional. The prior inclusive validator duration was not substituted for P.

The immutable no-go record is
`study-v3/operations/week5-capacity-blocker/20261012T204735Z/no-go.json`,
SHA-256 `bf813d94f1c19ae66ed84e74dcffff10e3d96730dd8e4717e9cf877806475a4a`.
At **20:47:35 UTC**, the administrative recorder rechecked the clean frozen
source, current SCC registered-root seals and unchanged bound historical
external audit records; this is not a new local-machine seal observation.
No user jobs remained. Fresh quota remaining was **853,660,000,000 bytes** and
filesystem free space **1,023,988,989,952 bytes**. The existing conservative
84 GB operational bound plus reserve still fits; that does not establish a
complete campaign storage forecast. The separate seal receipt SHA-256 is
`302073fa4814d8911d207c13b08bede062de2398c95ac93ae2a8e960750835fb`.
The reviewed metadata-only recorder is preserved under
`week5-capacity-blocker-tools/20261012T204720Z/`, source SHA-256
`96c8f31576c562719522ad5e19367a0f7f2ac81667abce2ac7bc5178964120d2`.
No scientific arrays were read and no further job was submitted.

This is a **measured-profile no-go**, not a failure of the three pilot checks.
Full scientific admission A, corrupted-artifact numerical replay and the complete
capacity ledger remain unfinished and are held. No optimistic capacity receipt
was created to reach an A timer. At this no-go checkpoint, the then-current plan forbade validation memoization
under ADR0006 and required a result-blind amendment after a failed
go/no-go. A longer CPU allocation alone cannot repair the shared opening-GPU
maximum-job constraint.

Before the later ADR0007 authorization recorded below, the consequential choice
was to authorize a narrowly scoped implementation
amendment proposal, retain release `731938a` and identify a demonstrably faster
compatible runtime for renewed measurement, or retain the blocked study.
The recommended proposal would examine safe reuse of complete validation proofs
within one unchanged command input snapshot and job limits appropriate to CPU
and GPU stages. It was **not yet adopted or implemented at this checkpoint**. The proposal had
to retain exact
numerical/provenance checks, tamper invalidation, fresh independent recertification,
the shared seal and full opening authorization; all recipes, epochs, physical
batches, paired seeds, 27 selection slots, nine final heads and 180 cells stay
fixed. Any approved change needs its own successor release, impact/regeneration
inventory, tests and renewed measured admission. No code, artifact, lock or
scientific budget has been changed by recording this blocker.

## Authorized result-blind engineering amendment: October 12

The researcher explicitly approved safe validation reuse and separate CPU/GPU
time accounting while preserving every scientific check and budget.
[ADR0007](../decisions/0007-safe-validation-reuse-and-stage-capacity.md) records
that authorization, its mutation model and the required regeneration inventory.
The decision follows the verified runtime no-go above; it uses no novel outcome
or pilot accuracy criterion. The no-go and all `731938a` evidence remain intact.

The authorized successor is `study-v3/revisions/execution-r2/`. It may reuse only
successful deterministic numerical proof markers inside one guarded command,
rehashing full transitive contents on every hit and keeping dynamic decisions
fresh. Separate CPU/GPU capacity evidence must count each whole command in its
allocation class, including CPU/I/O overhead inside a GPU job. No capacity gain
or implementation pass is asserted by this authorization.

Implementation/review, a new immutable freeze, full fixture/report rehearsal,
fresh parity/five caches/three pilots, geometry/corruption evidence, successor
timing, full A and a new measured capacity decision remain required. Original
source/identity/fallback evidence and byte-identical manifests may be retained
only through validated bindings; old caches, pilots and sidecars remain original
evidence and cannot be relabeled. The former 120 GB planning estimate must be
replaced by an actual retained/remaining inventory including the extra generation;
the 200 GiB reserve and 25% remaining-work slack remain mandatory.

Tasks 01 and 03 retain their verified execution-r1 history. Task 02 remains in
progress, task 04 remains blocked by incomplete measured capacity, and all gates
remain pending. Actual time remains unreported. The researcher requested hourly
status polling; in-job resource recording remains unchanged. No selection,
final training or novel opening is authorized by this engineering decision.

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

## ADR0007 implementation verification — October 12

The successor implements command-local success markers only for pilot numerical
snapshot replay and trained-feature projection equality. Each reuse hashes all
bound content again; design/source/lock, metadata/options and native runtime
commitments are included. Live authorization, dataset state, inventory and
resource checks remain fresh. Publication and command-exit checks reject changed
inputs; independent recertification starts empty. No numerical algorithm,
tolerance, RNG initialization, recipe, seed, batch, epoch or scientific budget
changed. Explicit frozen hashes take precedence over observed/provenance hashes,
and conflicting path aliases are rejected.

Schema-2 capacity receipts and dated allocation windows account separately for
complete CPU and GPU jobs. CPU overhead inside a GPU allocation remains GPU job
wall time. Both resource classes, non-overlap, slack, remaining dates, memory,
storage and opening safeguards remain mandatory. The exact original → r1 → r2
predecessor chain and shared opening/operation locks preserve historical evidence.
New source-bound GPU diagnostics, complete regeneration and fresh measured A are
required; old receipts cannot admit the new release.

Independent implementation and operational-adapter reviews passed. The final
stable local suite passed **1,373 tests**, with only two skipped licensed AVSL
source-parity checks for the historical v2 method. Forty focused proof/replay
checks, Ruff, formatting, workspace verification and all 19 runbook shell fences
passed. An earlier development suite found the new module missing from the shared
scientific hash inventory; that entry was added. A second test saw source changes
during the earlier run; both failed tests passed in the isolated 22-test protocol
suite and the final stable full suite. No SCC computation resulted from those
local failures. The dependency locks remain unchanged.

The first successor operation is an isolated allocated CPU rehearsal, followed
by verified preparation and the full ADR0007 regeneration inventory. Installation
and submission receipts must identify the actual immutable commit, separate
locked environment and current resource/seal observations before any success is
claimed. Full A, capacity, selection authorization and weekly closure remain
unresolved. The live publication still records authorization with all gates
pending and actual time unreported.

## Execution-r2 release and installation handoff

Release `f101f0e9d9bd64275d2088deab1b0bdcfcc53620` was committed, pushed and
matched against the remote branch after the stable checks above. Its local full
suite log SHA-256 is
`6aedc075b09fd6ff0eb2ffe9f298e187e675296668b8377216e0aadfb53b8f72`.
At October 12 21:42:51 UTC, the reviewed metadata-only installer started through
the existing `remote:0.0` SSH connection. It creates
`$HOME/pose-embed-scc/releases/week5-execution-r2-f101f0e9d9bd` with its own locked
environment under the canonical artifact root. The original release/environment
remain intact. Setup tools are retained under
`study-v3/operations/week5-r2-setup-tools/20261012T214251Z/`:
installer SHA `bbc8e66f1838d7b4a34ed65d4cdea16cb904062a311f0dce1fea47a698409e78`;
held rehearsal launcher SHA
`113780e87b0934d0b7cad4810127f67206020e77b7ba5a0c15f079bd851f983e`.
Both passed independent review, compile checks and four fail-closed guards.

The installation record under `week5-r2-installation/` must show successful
source/dependency/upstream/workspace checks and both seal observations before
using its digest-bound rehearsal launcher. Installation is not a scientific job.
The held first job requests no GPU, four compatible CPU slots, 32 GiB and 12 hours;
its wrapper retains 60-second resource monitoring. Check actual installation,
launch intent, scheduler state, logs and outcome before proceeding; never blindly
rerun either one-off tool. No rehearsal submission is claimed in this checkpoint.

The 24 GiB additional setup/rehearsal reserve is a scoped conservative bound,
not campaign admission: the measured old environment was 7,259,285,367 bytes,
old fixture tree 702,476,060 bytes and upstream checkout 433,152 bytes. Twice
the environment, four times the fixture tree and 2 GiB overhead fit below this
bound. Current quota/filesystem reserve is checked before setup and submission.
A fresh full retained/additional-peak inventory is still required for admission.
Automatic chat checks are at most hourly; do not leave a turn waiting on a healthy
process. Keep in-job monitoring intact and provide an exact EDT check-back time.

## Verified installation and queued rehearsal — 21:49 UTC

Separate installation completed at **21:45:32.590026 UTC**. Root checked all eight
successful command outcomes, clean exact release, Python 3.11.15, 47 compatible
installed packages, package import origin, the separate environment, pinned
MotionBERT and workspace result. The installation receipt is
`study-v3/operations/week5-r2-installation/20261012T214306Z/installation.json`,
SHA `4e4f556773c9b6d7ab7dc9a56a589794e6b6a1d36c400a6e60f2f62fece4f96d`.

The reviewed one-off launcher then submitted **8044010** at
**21:47:02.502287 UTC**. Its launch receipt is
`study-v3/operations/week5-r2-launches/20261012T214658Z/launch.json`, SHA
`64c6c26a07f6b1bd5399b1cb46f7c1431b66521556bbcaec0c85cfc2da3c8618`.
At **21:49:08.807964 UTC**, exact scheduler state was **qw**: queued, four slots,
with no operation/resource samples yet. The scoped reserve passed with
841,160,000,000 quota bytes and 1,008,855,941,120 filesystem bytes free.
Both the installer and launcher have now run; inspect their immutable receipts
and intent before any action, never blindly resubmit. No completed rehearsal,
successor preparation or scientific admission is claimed.

The current SCC pointer resolves to
`study-v3/operations/week5-status/20261012T214908Z/status.txt`, SHA
`6b387795746014ef33e14590c8cd23efdc58c3f1d4a958ff9b839688a10e8cb3`.
It preserves the old status and records the actual scheduler observation and
next gate. Verify job 8044010 accounting, command outcomes, full JUnit, source
bindings, periodic resources and both seals before advancing to preparation.
Next recommended check: **October 12 at 6:55 PM EDT (22:55 UTC)**. Automatic
checks remain hourly; the remote session and in-job monitoring are preserved.

The reviewed-source milestone is live through guarded migration
`20261012214324` (SHA
`88aa03183c09e8de2092e0fad9498e692cc6d826bcfd5f8424a7e51fc3493616`) and deployment
`dpl_Gnx3BMDHTrdETKYvX84YdfVM2vMr`, verified at **21:47:04.730 UTC**.
Its installation-pending wording explicitly describes the earlier 21:42
checkpoint; the accepted installation and queued submission above are later
operational observations. Week 5 v27 remains active, task 02 v24 in progress,
task 04 v7 blocked, gate 03 v8 pending, all gates pending and actual time
unreported. Root independently matched the complete public export/fallback,
including manual actions and protocol, at **21:49:20.309720 UTC**; export SHA
`f6593b2bfb8f4b48cce3e15cd3b8af4b2276446d5814ddaf7479821b7506e25c`.
All 13 other weeks and links, completed-task timestamps, private ownership/RLS,
closed history and unrelated Journey were preserved. Twenty-one database guard
tests, 22 tracker tests, lint/typecheck, production build and live page/privacy
checks passed. The publication commit is `5f55bb7`; source release remains
`f101f0e`. No completion or capacity waiver was published.

## Execution-r2 rehearsal accepted; preparation submitted

The hourly inspection at **2026-10-12 23:53:05.648857 UTC** found rehearsal
8044010 complete. It ran on `neuro-pub@scc-ke1` from 21:50:49 to 21:54:03 UTC,
with exact-job accounting `failed=0`, `exit_status=0` and **194 seconds**.
The isolated operation is `study-v3/operations/20261012T215109Z-8044010-rehearsal`.
All **128 checks passed, with no failures, errors or skips**. They exercise the
amended validation and complete fixture report; they do not admit scientific
artifacts.

Independent completion review passed at **2026-10-13 00:24:45.238807 UTC**:
`study-v3/operations/week5-r2-rehearsal-verification/20261013T002413Z/verification.json`,
SHA `963babe02eba70d34f3f9c9aa47af21145de387ca4d5a1ad6ccf9c226fb43381`.
It checked **32 metadata bindings and 616 tracked source bindings**, all three
commands, nine resource samples, exact accounting, operation and fresh review
seals, and the fixture-only 180-cell report with nine trained fixture heads.
Scientific arrays/checkpoints were not read or hashed by this login-node review.
Verifier SHA `b2d7e5d3978d7fe1faa49d324014168d89101827a38170e5e4fa96188026922c`
passed eight focused tests and independent/root reviews.

Preparation **8045152** was submitted at **2026-10-13 00:25:38.993553 UTC**.
Launch receipt `study-v3/operations/week5-r2-launches/20261013T002535Z/launch.json`
has SHA `18955c81a3585af137ffeb21cca334cb6c99e5f3930f36e5f8abf63f73d79d85`.
It requests four CPU slots, 32 GiB, two hours, no GPU, and the matching
AVX2/Sapphire Rapids/Gold-6426Y profile. It uses immutable `f101f0e`, its separate
locked environment, `prepare --revision execution-r2` and the original adopted
`manifests/ntu-input-v2-7721684/manifest-set.json`; the frozen command checks the
original → r1 → r2 design chain inside the allocation.

The preparation-only additional bound is **1 GiB**: twice 58,822,903 bytes of
retained predecessor manifest/lock metadata, plus 64 MiB for logs/metadata,
rounded up. Current quota free **837,890,000,000 bytes** and filesystem free
**1,007,052,390,400 bytes** passed `200 GiB + 1.25 * remaining_peak_bytes`.
This is neither a measured campaign forecast nor reuse of the prior 24-GiB
installation/rehearsal allowance. The launcher rechecked the accepted receipt,
sources, dependencies, input metadata, seals, reserve, absent successor output
and duplicate/uncertain submission intents. Its SHA is
`1236411097728a2fd1a0f10a0818099dc37362aa996cb97a39998447923a9d11`;
28 focused tests and independent/root reviews passed. Both tools are preserved
under `study-v3/operations/week5-r2-transition-tools/20261013T002400Z`, tools.json
SHA `2d070401b5855022b4d5d59dbc63158d05ad76123a11ecc21e0127c6c95f81a7`.
They have now run; never blindly repeat their invocation.

The one initial scheduler observation at **00:26:31.182636 UTC** found 8045152
**queued (`qw`)**, four slots, with no operation or resource samples yet.
The observation is retained under `study-v3/operations/week5-status/20261013T002630Z`.
No preparation completion, regenerated scientific evidence or admission is claimed.
Do not poll again automatically before **01:26:31 UTC**; recommended check-back:
**October 12, 2026 at 9:30 PM EDT (October 13 01:30 UTC)**. Preserve the existing
remote session and the allocation's 60-second resource monitoring.

### Publication and hourly handoff, October 13 00:33 UTC

Commit `452b3409cd88f008130d94e2d4b3cf3c79affbd0` published the accepted
rehearsal and dated preparation submission. Guarded migration `20261013002548`
(SHA `e5927d5c8aab95fc21fe172773876033d782ab41db9d517b3bd839bcb7ae9f80`)
and promoted deployment `dpl_5UNdWC4A14gxqeZMntYcEZTHcTbK` passed live health
verification at **00:30:45.224 UTC**. Week 5 is v28 active, task 02 v25 in
progress, task 04 v8 blocked and gate 03 v9 pending. All scientific gates
remain pending and actual researcher time remains explicitly unreported.

Root independently matched the complete public content to the repository
fallback at **00:33:21.691433 UTC**, including manual actions and protocol,
after normalizing equivalent UTC timestamps and source/link ordering. Runtime
export timestamps and the Supabase data-source envelope were checked separately.
The retained formatted export SHA is
`2ad86485487a4adf31be52833306d207f19bf461f2e89411b17d49d62937e689`.
All 13 other weeks, links, historical task 01/03 timestamps, private ownership,
RLS and unrelated Journey content were preserved. The 22 database guards,
22 tracker tests, lint, typecheck, build, workspace and 19 runbook shell fences
passed.

The SCC pointer now resolves to
`study-v3/operations/week5-status/20261013T002630Z/status.txt`, SHA
`5badc56457760828536722b8020fabc36cf65a2fe436a2516b5460a9473928dc`.
Its guarded update preserved the previous status and recorded the next command.
The last scheduler inspection remains **00:26:31.182636 UTC**; no additional
poll was made for this publication. Check back **October 12 at 9:30 PM EDT**
(October 13 01:30 UTC), then inspect preparation 8045152 without resubmitting.
The scientific source remains `f101f0e9d9bd64275d2088deab1b0bdcfcc53620`;
preparation completion, regenerated evidence, full A and capacity remain pending.

### Successor preparation accepted, October 13

Preparation **8045152** completed on `neuro-pub@scc-ke1` at
**00:31:55.111517 UTC**. Exact accounting records `failed=0`, `exit_status=0`,
four CPU slots and **44 scheduler seconds**. Operation
`study-v3/operations/20261013T003113Z-8045152-prepare` retained three successful
commands, seven passing resource samples and both dataset seals. The hourly
inspection at 02:02:09 UTC found the job terminal; the later acceptance review
did not rerun preparation or scientific data processing.

Independent metadata verification passed with receipt
`study-v3/operations/week5-r2-preparation-verification/20261013T063819Z/verification.json`,
SHA `0a3823e66a97192c5665185edbb908bf5b44c6dd9b451328d95d96476a84d785`.
Written at **06:39:11.971297 UTC**, it checked 73 metadata bindings, exact
accounting, commands, resource arithmetic, seals, all 616
tracked source bindings, eight ordered manifest identities and the complete
original → execution-r1 → execution-r2 predecessor/scientific-equality chain.
The successor protocol digest is
`18f7d17fa81e7ae3a6b1e5deddf42d9eda589d96e5a13968188a8ce275bfb95f`.
Scientific binary hashing remained inside the completed preparation allocation;
the independent login review read metadata and source only.

Reviewed administrative tools are preserved under
`study-v3/operations/week5-r2-preparation-tools/20261013T063754Z`; tools.json
SHA `905eead907bca0428860ed3061b372524935573b644d17ceb7c5a03f89a4ccd0`.
The executed verifier SHA is
`2e77fdd376fe50843fdd04bfd6a8a3f179e7e0019d8fc947cd26410e58a651d9`;
11 focused and ten existing revision tests passed, with independent/root review.
The supplementary launcher SHA is
`e2037e2eaa64ff07230a0bdb2a757de29aa93192fb406265f5036f0952ae1a81`
and its thin CPU wrapper SHA is
`b7d037082d244142df27f66e1b6059d0e3cbdc23189418e0076d55f1dce10384`;
17 focused tests, shell syntax and independent/root review passed. The wrapper
invokes the unchanged tracked supplementary checker from source `f101f0e` with
explicit full release/revision bindings and the new manifest bundle. Preparation
acceptance grants no cache/pilot/corruption completion, capacity or selection
authorization. Every predecessor artifact remains unchanged.

Supplementary CPU job **8048540** was submitted at **07:58:52.315989 UTC**:
`study-v3/operations/week5-r2-launches/20261013T075848Z/launch.json`, SHA
`0e77ecb106c977dd9922f473b80f29fd7475d8b4f5b243d9db9b34cc92368fd8`.
It requests four slots, 32 GiB, two hours, no GPU and the compatible
AVX2/Sapphire Rapids/Gold-6426Y profile. Log:
`logs/pose_w5_r2_additional.o8048540`. The reviewed launcher has now run;
preserve its intent and never resubmit it blindly.

The separate **1-GiB supplementary-only bound** uses four times 140,510,037
retained fixture bytes, twice 58,782,800 successor metadata bytes and 64 MiB
for logs/tables, rounded up. This stat-only inventory read no scientific arrays.
Quota free **835,100,000,000 bytes** and filesystem free
**1,003,713,724,416 bytes** passed `200 GiB + 1.25 * remaining_peak_bytes`;
this does not establish campaign capacity. The initial observation at
**08:17:32.236172 UTC** found job 8048540 queued (`qw`), four slots, with no
operation or resource samples yet. It is retained under
`study-v3/operations/week5-status/20261013T081732Z`.
Do not automatically check again before **09:17:32 UTC**. Recommended
check-back: **October 13, 2026 at 5:20 AM EDT (09:20 UTC)**. No supplementary
completion or successor scientific admission is claimed.

### Publication verified; SSH reconnection required

Commit `ae31c8074fa3d968b5669f4eed703d2e0541903c` is pushed. Migration
`20261013081701` (SHA
`833fb79979266b8c37bbb6300842bee8e92deff41ec5801f5b8c4663dbe22e1c`)
applied with exact after-row verification. Deployment
`dpl_AiYz64avKSNuoCJdxm8vDaqc5dJ5` was promoted and verified at
**October 13 10:18:59.728 UTC**. Root independently matched complete public
content to the fallback at **11:01:10.052112 UTC**, including protocol/manual
fields, equivalent UTC/source-order normalization and separate runtime-envelope
checks. Retained formatted export SHA:
`3716306546f1ea02bfb3cc9497689c6102af14237503e23da825800ff5beb95e`.
Week 5 is v29, task 02 v26 in progress, task 04 v9 blocked and gate 03 v10
pending. All scientific gates and unreported time remain unchanged. The 23
database guards, 22 tracker tests, lint/typecheck/build/workspace and 19 runbook
shell fences passed; other weeks/history, RLS/private ownership and Journey
were preserved.

The last confirmed SCC status is
`study-v3/operations/week5-status/20261013T101918Z/status.txt`, SHA
`d5f49bb5ef2c646de157ab1cba05cede6c0c7285fd137b884e79a14b4fad01ac`.
It records accepted preparation and the dated queued supplementary observation,
but its publication-pending paragraph is superseded by the verified result above.
The existing SSH connection then closed with `Broken pipe`. A subsequent
publication-status update was attempted but its remote outcome is unconfirmed;
inspect the pointer and any new status directory after reconnecting before
writing again. No new job was submitted and no active job was interrupted.
The local command is `/tmp/pose-week5-r2-published-status-command.txt`; do not
blindly resend it, particularly at the local shell prompt.

Last scheduler inspection remains **08:17:32.236172 UTC**. Reconnect SSH in
`tmux remote:0.0` before the next check, **October 13, 2026 at 9:00 AM EDT
(13:00 UTC)**. Inspect actual job 8048540 without resubmitting. Supplementary
completion, geometry, regenerated scientific evidence, full A and capacity
remain unverified. The chat ends rather than waiting for the queued process.

### Transferred controller; supplementary checks accepted, October 13

The authorized controller transfer paused `finish-pose-embed-week-5` through
the automation tool, preserving its prompt and configuration. The previous
chat was idle. The researcher had completed the existing SSH connection;
`remote:0.0` was an authenticated idle SCC shell. No second monitor was created.
The metadata read at **20:27:54 UTC** confirmed the old status pointer and SHA
`d5f49bb5ef2c646de157ab1cba05cede6c0c7285fd137b884e79a14b4fad01ac`.
No later publication-status directory existed; the publication outcome recorded
above supersedes that pointer's pending paragraph.

The permitted inspection at **20:30:20.881094 UTC**, completed at
**20:30:32.587786 UTC**, found job **8048540** terminal. Exact accounting gives
`failed=0`, `exit_status=0`, four `omp` slots and **87 scheduler seconds** on
`apolkovnikov-pub@scc-h30`. Its operation completed at
**08:31:43.006302 UTC**, not during this later inspection. The retained observation
is `study-v3/operations/week5-status/20261013T203020Z/observation.json`, SHA
`85a5d061bda8bdee3d9f3e0346883b85c54af6fa60055266775b738946f47de3`.
No job was resubmitted or progress inferred during the connection gap.

Independent metadata review ran from **20:42:57.604956 UTC** and wrote the passed
receipt at **20:43:00.762966 UTC**:
`study-v3/operations/week5-r2-additional-verification/20261013T204221Z/verification.json`,
SHA `7703859e50361123de9054fba446c8384d423b8c549b69eab92720314c46c3d2`.
It accepted **108 metadata bindings, 616 source bindings, three monitored
commands, seven resource records, both operation seals and fresh review seals**.
All **86 JUnit checks executed and passed**, with no failures, errors or skips;
unique case identities cover the frozen source test functions. Source, locked
environment, protocol/design/manifests, accounting chronology, resource arithmetic
and every bound content hash passed. The two actual tables were reconstructed
from locked metadata IDs: **18,929 development queries and 18,884 novel-primary
queries**, each across the fixed 20 actions. Their SHA-256 values remain
`04bad108a88c690e33f50a88ecb1ec654284cb5ed1b2980d7433d5f73a5e296e` and
`776bbf1f4a94b1d3c75eb8a8f9eba5a443ed40aec38a5ea9943f23aa18ad0a30`.
No novel poses/outcomes or scientific binaries were read by this login review.

Reviewed administrative tools are retained at
`study-v3/operations/week5-r2-supplementary-tools/20261013T204116Z`, tools manifest
SHA `f467643196ce4f3e44e0ae99b002175b91d160fe15c4424588308c716b794286`.
The verifier SHA is
`5bbe204ce03412bfe85e0f1a582224e71f1669b3f572661af0aad34912f59791`;
its fixed preparation-helper SHA remains
`2e77fdd376fe50843fdd04bfd6a8a3f179e7e0019d8fc947cd26410e58a651d9`.
All 33 focused failure-case tests, Ruff/format and independent review passed.
The two staging errors occurred before directory creation: tmux's direct-input
limit and the older login Python. The verified transfer used a paste buffer and
the separate Python 3.11 environment; every staged hash matched. No scientific
attempt, source change or credential entry resulted from those staging errors.

### Fixed-panel geometry submitted; initial queued observation

After supplementary acceptance, reviewed geometry tooling was staged at
`study-v3/operations/week5-r2-geometry-tools/20261013T204527Z`, tools manifest
SHA `f478f4fa591d3188826767632d083a3524d25f46af23bc2e1082015bcf0e72b9`.
All 71 focused tests, Ruff/format, shell syntax and independent review passed.
Launcher SHA `842df907bc04f2d186cb9c89cf040013af841b31ae35fd20033c517320f18293`;
wrapper SHA `d33c65c58e3b5ca5bfd4da0b738fc6c284c7fd3b59a36601edbaf65ef6707f6b`.
The fixed sibling helper remains
`e2037e2eaa64ff07230a0bdb2a757de29aa93192fb406265f5036f0952ae1a81`.

The new launcher requires both accepted preparation and supplementary receipts,
fresh source/dependency/seal/quota checks, no duplicate intent/job and the common
`execution-r1.operation.lock`. Its allocated path runs the unchanged tracked
geometry checker with the full release and `--revision execution-r2`. Admission
still requires that checker's `validation.json`. The additional identity receipt
requires exact agreement with the retained **40-base/43-total panel**, all 18,929
candidate metadata rows, sentinels, absent categories, selection code, manifest
and original fallback evidence/value. Only the declared protocol/manifest/source
provenance bindings may change. The original panel SHA remains
`bbe8f3dcc839a3f178f8a66a2cddf946b38b4f1d21c1d04d12a7f31523f1fc11`;
no new panel identity or fallback estimate is accepted. All scientific hashing
and tensor validation stay inside the allocation.

Geometry job **8070391** was submitted at **20:46:55.956765 UTC**. Launch:
`study-v3/operations/week5-r2-launches/20261013T204651Z/launch.json`, SHA
`a8c55f5a6054996d49cb2abab304a8b8925914a4cf0495a2f0368f84e4177452`.
Request: four CPU slots, 32 GiB, two hours, no GPU and the compatible
AVX2/Sapphire Rapids/Gold-6426Y profile. Log:
`logs/pose_w5_r2_geometry.o8070391`. The launcher has run; preserve its intent
and do not resubmit it.

The geometry-only remaining peak is **1 GiB**: 35,088,000 uncompressed tensor
bytes, 3,522,560 archive/header bytes, two copies of 3,042,766-byte panel metadata
and 64 MiB for logs/verification, totaling 111,804,956 bytes before GiB rounding.
Fresh quota remainder **833,220,000,000 bytes** and filesystem free
**1,002,027,614,208 bytes** passed `200 GiB + 1.25 * remaining_peak_bytes`.
This stage bound does not establish campaign capacity.

The one initial inspection at **20:49:22.424937 UTC**, completed
**20:49:34.991908 UTC**, found job 8070391 queued (`qw`), four slots, with no
operation, log or resource samples yet. Retained observation:
`study-v3/operations/week5-status/20261013T204922Z/observation.json`, SHA
`d126dd55daf56df4c71237e8a470ea73708fb011860ab4c056861d819d53fc2a`.
No geometry completion is claimed. Next check: **October 13, 2026 at 5:55 PM EDT
(21:55 UTC)**; no automatic scheduler inspection before 21:49:35 UTC. Scheduler
resource sampling remains 60 seconds. End the chat turn while queued or healthy.
Supplementary acceptance and geometry submission grant no scientific admission;
fresh GPU diagnostic/caches/pilots/corruptions/timing, full allocated A and
measured typed CPU/GPU capacity remain required. All gates and unreported time
remain unchanged.

### October 13: supplementary milestone published

The guarded publication updated only Week 5 reflection, task 02/task 04 notes
and gate 03 evidence. Migration `20261013204121_record_week_five_successor_supplementary.sql`
has SHA `cad80feb4fd8e3a47fdf5797e532fb0298add4e89bd67b035e29874403992fe2`.
The transaction checked expected versions, omitted version payloads and verified
returned rows: Week 5 **29→30**, task 02 **26→27**, task 04 **9→10**, gate 03
**10→11**. States, historical task 01/03 completion timestamps, researcher time,
all 13 other weeks, source links, ownership/RLS and remote migration history
were preserved. A separate controller read verified the exact resulting rows.

Production deployment `dpl_GQBWbraowYxxVBcwfS6d5j87uufP` was promoted to
<https://pose-embed-tracker.vercel.app>. The publication receipt, recorded at
**21:18:01.289325 UTC**, has SHA
`b204e87026158dd0842c6c253edbf307feebfe85dde1e6452547ad3792751a8d`.
Independent controller verification completed at **21:23:31.859947 UTC**:
the complete canonical export matches the repository fallback after equivalent
UTC/source-order normalization, with runtime envelope checked separately.
Export SHA: `3fedf6dc33bdd88a9e81e7cb890ac38321538374cfa7aef31c542793fd429051`.
Rendered accepted/queued/check-back text, historical task completion fields and
protocol content passed browser verification with no page errors. Journey returned
200; anonymous private export returned 307 to `/login?reason=sign-in` with an
empty body; health reported Supabase `ok`. Unrelated Journey source was preserved.

Verification passed 33 supplementary-verifier tests, 71 geometry-launcher tests,
27 database guards, 22 maintained tracker tests, three Journey tests, lint,
typecheck, default production build, workspace checks and runbook shell syntax.
Five historical assertions in the separate website staging directory fail
identically before and after this publication; they were preserved and are not
counted as passed. Two pre-existing hosted Auth advisor warnings also remain
unchanged. Scientific source/configuration/dependency locks remain frozen at
`f101f0e9d9bd64275d2088deab1b0bdcfcc53620`; no scientific result or admission
is inferred from publication. Geometry's latest scheduler evidence remains the
20:49 UTC queued observation above. The next check remains October 13, 2026 at
**5:55 PM EDT (21:55 UTC)**, with the previous heartbeat paused.

### October 13: geometry failed; bounded runtime diagnostic submitted

The next permitted inspection ran from **22:05:07.547370** to
**22:05:19.824007 UTC**. Geometry **8070391** was terminal: scheduler failed=0,
exit_status=1, four `omp` slots and **229 seconds** on `bpnlab-pub@scc-kc1`.
Accounting start/end were 20:51:02/20:54:51 UTC. The tracked checker completed,
but the external wrapper rejected fixed-panel identity. Preserve the entire
failed attempt; its tracked completion does not establish geometry acceptance.
Observation `week5-status/20261013T220507Z/observation.json` has SHA
`ba56692352707522a21ceed0f31075b3297f61660e4ad1209dc4207ad3064cb6`;
retained exact accounting SHA is
`62f684cac707ebf57ac2e00201d95b7351f5d4bf9fd05d93621cacf038c0638c`.

Metadata-only diagnosis found **2,051 of 18,929 candidate torso scales** differ
by small float32 rounding steps. Fixed IDs, base IDs, sentinels, absent
categories, selection code and manifest identities match. All **43 clean tensor
hashes** match across revisions; four selected scales and all **129 jitter
tensor hashes** differ. Mask tensors match, and each revision's two fresh-process
repeats remain exact. These comparisons read/hash JSON receipts only; no
scientific archive was read or hashed on login. Diagnosis
`week5-r2-geometry-diagnosis/20261013T220749Z/diagnosis.json` has SHA
`d9d8b549c159206754d8f8b21eaaac1e6b5f656dee54959c23611717aa70534b`;
the clean-tensor discriminator at `20261013T221341Z/clean-tensor-discriminator.json`
has SHA `f0dc0f44ba52c114e76b95ac044dd1ed63fd14fc62c8e1b9efd57c80f886ddcb`.
The original node `scc-ne7` is configured as Ivy Bridge without AVX2; the
successor node is Sapphire Rapids/Gold-6426Y. CPU dispatch is a hypothesis,
not a verified cause or permission to relax comparisons.

Reviewed external diagnostic tools were staged at
`week5-r2-geometry-runtime-diagnostic-tools/20261013T224338Z`, tools SHA
`b782d1823ae4d43d209f42d0b3893a7c28ec5caac1bbe0f88806c098a91b171c`.
Worker SHA `6e2ca3e4dc21f987245f66c3882c46ae9e5a225feb30374a54b672a4d403328b`,
parent SHA `d68157b44bdff49fc637408a22ca35a1ceb768b0acbbcf19cbd9e8717cd086fc`,
launcher SHA `c5c12102f05a533817c03cf7ed69eae8b9c675bb4128c588eaf40b30869f8d92`
and wrapper SHA `487c56d7d8bd892541ed9e0e7cc9229c916364734cc79a6439fa8f258470ad07`
passed independent review, **127 focused tests** (27 worker, 60 parent, 40
launcher), Ruff/format and shell syntax. Pre-submission review checked the actual
diagnosis schema and metadata-only boundary. Historical
staged-not-executed labels must not be used to rerun executed tools.

Diagnostic **8072666** was submitted at **22:49:45.058490 UTC**. Launch
`week5-r2-launches/20261013T224936Z/launch.json` has SHA
`91358af8b0e0f3c04765c7fd9f5d4d5264c32cbb7dbaec2c5a2f7dfa917332a3`;
immutable input SHA is
`1b24d390cf1ec2ad8829e00b3d01c0d5fc4acc15c656a50badf3ee30369e9ce6`.
Log: `logs/pose_w5_geometry_runtime.o8072666`. Request: four CPU slots,
32 GiB, 30 minutes, no GPU, compatible Gold-6426Y/AVX2. It reads the failed
archive only inside the allocation and both leases, runs native/default CPU
dispatch in separate fresh processes on four fixed cases, and compares all
four scales, 40 tensor hashes and 36 damage rows exactly. The failed archive is
diagnosis input only; neither worker nor parent can produce eligible geometry.
An unsupported hypothesis is a valid completed diagnostic.

Additional peak is **1 GiB**, rounded from **67,480,406 bytes** for metadata/logs,
two input/source-binding copies and receipts. The existing 17,675,344-byte archive
is read-only and not copied. Fresh quota **833,030,000,000 bytes** and filesystem
free **1,001,834,676,224 bytes** passed the reserve. This is not campaign capacity.
One initial inspection at **22:52:26.185888 UTC**, completed **22:52:38.052404 UTC**,
found the diagnostic queued (`qw`), four slots, no operation/log/resources and
no accounting yet. Observation `week5-status/20261013T225226Z/observation.json`
has SHA `6c7d3d7d3dfd2005eea7dec86adb81b38792b17746a299bdbac746c5e47ab670`.
No diagnostic result or subsequent scheduler state is claimed. Next check:
**October 13, 2026 at 8:00 PM EDT (October 14, 00:00 UTC)**; no automatic
inspection before 23:52:39 UTC.

The researcher explicitly approved resuming the existing hourly heartbeat in
this chat. Its ID/name/schedule and original configuration were preserved; only
the target, current prompt and active status changed. No second monitor exists.
Root alone controls SCC. Before a new geometry attempt, require a reviewed
compatibility preflight and full candidate/panel reproduction. Before a permanent
runtime choice or full-A admission, require fresh paired initialization, complete
pilot replay and exact projections under the eventual full-A profile. Full A
validates geometry, pilots and projections in one process; it cannot combine
proof authority from different profiles. Fresh r2 heads must be regenerated,
not adopted from r1. All scientific gates remain held and time remains unreported.

### Verified milestone publication and controller transfer

Guarded linked-database publication advanced only evidence versions:
Week 5 **30 → 31**, task 02 **27 → 28**, task 04 **10 → 11**, gate 03
**11 → 12**. Root independently compared the resulting public-row projection
with the prior rows and current fallback. Task/gate states, completed-history
fields, researcher time, all other weeks, sources and links remain unchanged.
Migration `20261013223908_record_week_five_geometry_failure_and_runtime_probe.sql`
SHA `2aaaf34235c3f8d1dab76b45ed65611c42ba2b09d39c80437e982fd467309564`
and its exact history entry were verified; prior remote history was preserved.

Production deployment **dpl_ADArATdHU2DCqdiXv1ZYCUHkA3PU** was staged, verified
and promoted to <https://pose-embed-tracker.vercel.app>. Publication receipt,
recorded **2026-10-13 at 23:05:01.746898 UTC**, has SHA
`3da5a84ec051e121d01d714686f01ad7efb86e176bb98c7f2006695615d9154e`.
Root's separate complete canonical export/envelope/health/private-redirect/Journey
check at **23:06:30.487018 UTC** passed; receipt SHA
`eeb46c6356fa5228547bdb749c99e4919529536cc901167ed6f54aabdb13c2f7`.
Its export SHA is
`17d49f36619d832947d02e373cba12bd4caee695762b1040ac308f3e67642647`.
Both staged and canonical browser checks confirmed the failed geometry, dated
queued diagnostic, next check, existing completed-task history and protocol.
Journey remained available; anonymous private export redirected with an empty
body; no page errors were observed. The existing 79 staging app-source files,
including Journey, were preserved apart from the requested protocol bundle.

All **30 pgTAP guards**, **22 maintained tracker tests**, **three Journey tests**,
lint/typecheck, default Node 24 builds, local database security/workspace checks,
independent review and **19 runbook shell syntax checks** passed. The full
historical staging suite retains the same five assertions failing before/after;
its 20 other checks pass. Two inherited hosted Auth warnings are unchanged.
No scientific source/configuration/dependency lock or primary-checkout change
was made. Publication and heartbeat resumption grant no scientific acceptance
or measured campaign capacity. Latest diagnostic observation remains the dated
22:52 UTC queued snapshot; publication made no later scheduler query.

### October 14: SSH visibility lost; completion review prepared

The transferred SCC connection closed with `Broken pipe`; the pane returned
to a local shell before the next diagnostic observation could execute. Root
requested that the researcher restore authentication in the existing pane.
No scheduler query, new submission, diagnostic result or remote status update
was made during this visibility gap. The latest actual diagnostic observation
remains **October 13 at 22:52:26–22:52:38 UTC**, queued `qw`. Diagnostic 8072666
and failed geometry 8070391 must not be resubmitted.

Local independent completion tools are prepared, reviewed and preserved.
The metadata-only diagnostic verifier has SHA
`c02d66d5b069f9987f51f1cccd0277f7ca366057cff92600743c3d9195e8e871`;
**85 checks** passed (57 author tests and 28 independent edge cases), with
Ruff/format and independent review. The guarded observation tool passed
**nine checks** and independent review. It rejects execution before the saved
time, optimized Python, unsafe paths and unbounded metadata; partial records
from a healthy job are preserved without a completion claim.

Completion verification requires exact immutable observation/accounting hashes,
whole-job accounting, both commands, all resource/seal/source/input/runtime
bindings and independent reconstruction of the scalar/hash/damage-row comparisons.
A positive summary cannot override a later parent/postcheck or scheduler failure.
The verifier checks every build/runtime field exactly, normalizing only Torch's
single CPU-capability report line after checking it against that worker's declared
mode. Numerical comparisons and tolerances are unchanged. Scientific archives
receive stat/binding checks only on login; their complete hashes remain allocated
worker claims. A valid unsupported hypothesis is diagnostic completion, not
scientific acceptance. No real diagnostic completion was verified locally.

Resume only after observing an authenticated idle SCC prompt and reviewing the
latest private controller handoff and retained remote status pointer. Preserve
every prior record and use the prepared metadata-only observer/verifier; never
rerun an executed launcher or infer progress during disconnection. Source remains
frozen at f101; geometry, dependent stages, full A and measured capacity stay held.

### October 14: restored access and verified wrapper failure

The researcher restored the existing SSH connection. Root verified an
authenticated idle SCC prompt at **19:37:51 UTC**, read the retained status
pointer, then inspected diagnostic 8072666 once at
**19:40:13.233256–19:40:25.519918 UTC**. The earlier visibility gap is historical;
no scheduler progress was inferred from it.

The diagnostic failed before its parent or workers started: failed=0/exit=1,
four `omp` slots, **two whole-job CPU wall-clock seconds**, CPU=0.098 seconds,
`neuro-pub@scc-h32`. It ran October 13 at 22:54:00–22:54:02 UTC. Dependency setup
passed, then the wrapper looked for its helper beside the scheduler's copied
script under `/var/spool/sge/`, where that helper did not exist. There are zero
parent operations, resource samples or numerical outputs. The CPU-dispatch
hypothesis remains untested. Preserve the original job, launch, intent and tools;
its executed launcher must never run again.

Observation `week5-status/20261014T194013Z/observation.json` has SHA
`c40240ac655192b2ab2ed525dd09a54bb1b4c7a76ecc90d68b9ee2999bd52208`;
accounting SHA `170e02451bfccfe53ce4f8e30752aec7242338df5aa335c16ea19c3b76dc142d`;
log SHA `01358f1b1d4f22753ec447a1b5b08cf121605c5fc19b4f26735d92c80cbb8cf2`.
Independent metadata-only failure verification completed at **19:56:38.194670 UTC**:
`week5-r2-geometry-runtime-failure-verification/20261014T195626Z/verification.json`,
SHA `c9e2d25740334923a537c36c82b0d2574f6b90a74b7d45ebf26ddc0c3aac371d`.
It binds 139 metadata records, 617 external metadata/source records and all
616 scientific source files. Its verifier passed 19 local checks and independent
review; it reads no scientific binary. A passed failure-verification receipt
confirms the failure and grants no diagnostic completion or scientific acceptance.

The reviewed administrative remedy was staged at **20:08:33.599282 UTC** under
`week5-r2-geometry-runtime-diagnostic-remedy-tools/20261014T200830Z`.
Tools SHA `c6404952ea81aa28b04c2603b6b4b7190cc85c1c759ff08410ee2dd7f63c1d77`;
input SHA `32289c531a0330f93dad42b7974022181eb494d775d6b70825a80a7a1877d716`;
staging receipt SHA `ae31768ad55b7107b113c581aa6aff0e8690f7e1b86ecdd575a40bd72dd87316`.
Staging rechecked 757 metadata/source bindings. The new launcher remains
**unexecuted**; there is no new job or scheduler result. The old failed job is
not resubmitted. The new wrapper resolves its canonical tools beside the
hash-bound input file and checks the failure receipt before and after the
unchanged parent. All original input fields remain equal except the explicit
administrative remedy. Parent, worker, scientific source and resource budgets
are unchanged. The new launcher/wrapper passed 64 tests, including actual
scheduler-spool-copy regression and receipt/path/hash failure tests, plus
independent review, Ruff/format and Bash syntax.

At **October 14, 2026 at 4:41 PM EDT (20:41 UTC)**, root may read the latest
status pointer and execute this new launcher once after its fresh duplicate,
source, seal, lock, runtime and quota/reserve guards pass. No routine scheduler
query is permitted before 20:40:26 UTC. No scheduler polling loop is used.

The new metadata observer and independent completion verifier were separately
reviewed and staged at **20:27:34.800332 UTC** under
`week5-r2-geometry-runtime-remedy-control-tools/20261014T202734Z`, tools SHA
`650418b03e6600d65decc6e1acfb0dd59fe0ad1dd152650b6537e9f4c1c9aaaa`.
Observer SHA `18c30ef7722fd84482d786980dd1df0cdcd70d0410e2bc1dd76d853e68f6eeab`;
verifier SHA `6001322b261f3229e1bbb2e75054b79180c9408b93dbb897338e5d6781390798`.
All **106 checks** passed (29 observer, 77 verifier), including the actual
staged metadata schema, with Ruff/format and independent review. These tools
remain unexecuted on SCC. No job descriptor exists yet: root must create it
only after actual submission, binding the real job/launch, current status,
input/tools/failure receipts and exact permitted observation time. The observer
rechecks the current pointer before querying. Completion still requires the
unchanged full comparison/accounting/resource/seal/runtime evidence and the
new wrapper's final marker; a valid negative diagnostic grants no scientific
acceptance. The original c02/f23 tools and every original attempt remain intact.

### Verified failure/staging publication

Guarded migration `20261014195000_record_week_five_runtime_wrapper_failure_and_remedy.sql`,
SHA `a4e0f3b2360a81189918f1e51afc361924bc9ac730a8d297e4899604a899d8da`,
advanced only evidence/version fields: Week 5 **31 → 32**, task 02 **28 → 29**,
task 04 **11 → 12**, gate 03 **12 → 13**. Root's separate database check at
**20:21:30.919483 UTC** verified every complete public row, all prior history
and the new migration statement/source hash. Independent DB receipt SHA
`06e1d4e01907ecef10f033c4948c589df87f6d67f3be876c1dec87587ebb48aa`.
States, completed-task history,
researcher time, 13 other weeks, sources and links remain unchanged.

Deployment **dpl_AHXW34C6wTpPiQ4WLdVMvvQcVRDw** passed staged checks and was
promoted to <https://pose-embed-tracker.vercel.app>. Publication receipt at
**20:27:44.360419 UTC** has SHA
`fa17dc34075f2c7148a58af19d91eadbd88be5b5f48afe8e60af5f21c3a9bcfe`.
Root's independent complete canonical check at **20:28:27.858713 UTC** passed,
receipt SHA `d739e3d462080701b8f682cd5d145a899d92e05e3f2e32340954a3a72eb46907`;
export SHA `7a9f619dbb8edc0e62f9de82dd588d8472513297896ccdb092730f5fb146f6ac`.
Page/export/fallback/protocol/health match. Staged and canonical browser checks
rendered the verified failure, unexecuted staged remedy, next check and retained
task 01/03 history without page errors. The private export redirected with an
empty body; Journey returned 200. Deployed functions use Node 24; the existing
79 staging app-source files were preserved except the requested protocol bundle.

All **31 database guards**, **22 maintained tracker tests**, **three Journey
tests**, lint/typecheck, default Node 24 builds, local security/workspace checks
and independent review passed. The same five inherited staging assertions fail
before/after, with 20 other checks passing; two pre-existing hosted Auth warnings
remain unchanged. Scientific source/configuration/dependency locks and the
primary checkout are unchanged. Publication records staging, without claiming
a new job, a numerical result, scientific admission or measured capacity.

### New remedy submitted; first observation deferred

The permitted boundary arrived during final handoff. Root read the verified
20:37 status, executed the guarded **new** launcher once and submitted diagnostic
**8102231 at 20:43:11.969137 UTC**. Launch
`week5-r2-launches/20261014T204308Z/launch.json` has SHA
`82427510eb77a8bc0875753d343783a1e9a383f05bef736aa2c01654ee4037f2`;
intent SHA `7c690ce8410753e592a06c555dfb87c4b638ca28e344552a1d246c8c2fdeee6d`.
Every staged/unexecuted claim above is a dated checkpoint. The actual launch
supersedes those operational labels; neither this launcher nor its guarded
command may execute again. The old failed diagnostic is preserved separately.

Independent submission-metadata verification at **20:50:34.444145 UTC** rehashed
763 metadata and 616 source bindings and checked the exact intent, packet,
six wrapper arguments and both launch seals. Receipt
`week5-r2-geometry-runtime-remedy-submission-verification/20261014T205034Z/verification.json`
has SHA `63aa23c6e514f9cd1757021354fa1262b8f48f89af10e8a8015259e885dbb471`.
Fresh quota **826,630,000,000 bytes** and filesystem free **994,956,017,664 bytes**
passed the unchanged diagnostic reserve: 1 GiB from 67,481,168 additional
metadata/log/source/receipt bytes, no archive copy. Resources remain four `omp`
slots, 32 GiB, 30 minutes, no GPU, Gold-6426Y/AVX2. No actual allocated runtime
or numerical outcome is accepted from submission alone.

The empty pre-submit duplicate-job check completed by **20:43:10.988132 UTC**.
To preserve the hourly inspection limit, the **first actual job observation is
deferred to October 14, 2026 at 5:45 PM EDT (21:45 UTC)**. No post-submit query,
operation, log, resource sample or outcome has been inspected; no queued,
running or completion state is inferred. No waiting/polling loop is used.
Source, inputs, comparisons and every held scientific gate remain unchanged.

The large bulk metadata export exceeded terminal scrollback and its partial
capture was retained. A compact metadata-verification attempt also stopped
before producing a receipt because its local 1-MiB limit excluded large panel
JSON. The corrected version uses the already reviewed 64-MiB metadata limit
and preserves the scientific-binary denylist; that version produced the receipt
above. Neither issue altered or resubmitted the job. Original commands/captures
are preserved privately; no scientific comparison or tolerance was changed.

### Verified submitted-only milestone publication

The submitted-only milestone advanced the guarded evidence versions to Week 5
33, task 02 30, task 04 13 and gate 03 14. Full public rows and prior migration
history were independently checked at 21:00:27.615952 UTC on October 14;
root receipt SHA is
`01bf019aef7095f54e13428d61f59de03b47414394ab67c998a1565ed5e0233b`.
Migration `20261014204512` has exact source/statement SHA
`a6b1b980daeaddda87f35840b2be0994542c4f506515a8dae84f8d189ea021d4`.
Task/gate states, task 01/03 history, actual time, the other 13 weeks, source
links, ownership and RLS remain unchanged.

Deployment `dpl_4NaBAGp9XYxFaqiC948oEhsud5SU` passed staged checks and was
promoted to <https://pose-embed-tracker.vercel.app> with Node 24. Publication
receipt SHA `d9b26e6002c7365678684b7024052a7b2dca94d9d14fb26886f72db24865db6a`
was recorded at 21:12:09.523251 UTC. Root independently checked the canonical
export, envelope, protocol, health, private login redirect and Journey at
21:12:58.610318 UTC; receipt SHA
`b43d74bd2ffc5a8bba1517a09d6952c3953d55fbb15cfbc8f41d334dfb05bbd9`
and exact export SHA
`af6d1dc303f35102308dee293c5a693c42f41b88e9d9b9800ddf7d72eb733ce3`
bind the published submission facts. No job query or scientific acceptance is
inferred from this publication.

The 32 pgTAP guards, 22 maintained tracker tests, three Journey tests, lint,
typecheck, Node 24 builds, workspace verification and independent review passed.
The same five inherited staging assertions and two hosted Auth warnings remain
unchanged. Scientific source, configurations and dependency locks remain frozen
at `f101f0e9d9bd64275d2088deab1b0bdcfcc53620`. First diagnostic observation
remains October 14 at 5:45 PM EDT (21:45 UTC).

### Corrected diagnostic completed; tested recovery remains incomplete

Root's first post-submission observation ran October 14 from
22:25:31.228546 to 22:25:43.899681 UTC. Diagnostic **8102231** completed on
`neuro-pub@scc-ke1.scc.bu.edu`: four `omp` slots, failed=0, exit_status=0,
**17 whole-job CPU wall seconds**, actual CPU=9.340 seconds. Submission/start/end
accounting is retained, including setup and parent overhead. Observation SHA
`1173326cdf23c740b8c041bf22b18c677efd9ae7b1227b8dfc426c2659dc111b`
and accounting SHA
`29a6e9af415ec18fcd553d6ae818826218ba328b283c284f7884f499f1b317e5`
bind the actual operation
`study-v3/operations/20261014T204914Z-8102231-geometry-runtime-diagnostic`.
No launcher or job was resubmitted.

The first metadata completion verifier stopped because it expected a combined
queue/host string, while the actual allocation records `QUEUE=neuro-pub` and
`HOSTNAME=scc-ke1.scc.bu.edu` separately. Preserve that failed verifier attempt
and original source. A new reviewed verifier accepts the exact bare queue,
full qualified queue or SCC short-host qualified queue, with all separate
job/host/PE/slot/thread, source, numerical, seal, resource and accounting checks
unchanged. Actual allocation SHA is
`b68f110b3662b8e1e7e9f90ea721d54370f4e7d7211b1988dacb2b81dfcd7957`.
The new verifier SHA is
`9b2908891555f7636f138a72fa183961a2b545866f336480c7f67bf6d956fcce`;
93 checks, Ruff/format and independent review passed. Its new immutable tools
manifest has SHA
`522a10317ead8150e8f4506538c4e959e75c5a596529973104563e443bffbb55`.
No scientific artifact or sidecar was changed.

Actual completion verification passed from 22:34:10.047781 to
22:34:14.167272 UTC. Receipt
`study-v3/operations/week5-r2-geometry-runtime-remedy-queue-record-verification/20261014T223409Z/verification.json`,
SHA `f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36`,
binds 184 metadata, 617 external metadata and 616 source records, both seals,
both fresh-process commands, six resource samples, dispatch identity, final
parent/wrapper markers and complete scheduler accounting. The completion
verifier reads metadata only; the scientific archive hashing occurred in the
allocated parent/workers.

The result is **hypothesis-unsupported**, a valid completed diagnostic. Native
AVX512 reproduced the failed-fresh reference exactly: four scales, 40 tensor
hashes and 36 damage rows. Explicit `DEFAULT` reproduced the original four
scales, **36 of 40 tensor hashes and 32 of 36 rows**. All four clean tensors
and 24 mask tensors/rows match; four jitter tensors and their damage values
remain different, confined to two cases. This establishes that the tested
`DEFAULT` setting is insufficient; it does not establish a complete cause,
compatible permanent profile or scientific acceptance. Geometry 8070391 and
both earlier failure attempts remain preserved; every dependent stage, full A
and capacity remain held. Scientific source stays frozen at
`f101f0e9d9bd64275d2088deab1b0bdcfcc53620` with unchanged comparisons,
original fallback and fixed panel IDs.

At the completed-diagnostic checkpoint, the saved scheduler inspection or launch
preflight boundary was **October 14, 2026 at 7:27 PM EDT (23:27 UTC)**. The
separate later submission is recorded below. Diagnose the runtime difference before
preparing a new allocated confirmation; never rerun either executed launcher.
Any later profile still requires full ordered 18,929-candidate and fixed
43-clean/430-tensor/387-row confirmation, then fresh paired r2 initialization,
full pilot/projection replay and full A under the same eventual profile before
permanent runtime or admission. That checkpoint claimed no new profile, job or
admission.

### Verified completion milestone publication

The guarded completion milestone advanced only evidence versions to Week 5
34, task 02 31, task 04 14 and gate 03 15. Independent root full-row/history
verification at 22:49:54.406199 UTC has receipt SHA
`b0378a3afe949f408f7a6a716a054455871ebee2c0f6716abe04d1e6c1493e54`;
exact migration `20261014223712` source/statement SHA is
`fee92654b61de4fe592c68e0c280cdaf941bdb24c1d9564d09f41cee56dfc640`.
Task/gate states, task 01/03 history, all prior migrations, actual time, the
other 13 weeks, source links and privacy remain unchanged.

Node 24 deployment `dpl_7KL74p4iwKbPQig5yAPECUg3NU9A` passed staged checks
and was promoted. Publication receipt, recorded at 22:51:56.908206 UTC, has SHA
`2af4a3e17952c17bf97e151440c9a271f5a25f8ad96d780fc18770bb61c448e3`.
Root independently checked the complete canonical export/envelope, health,
private login redirect and Journey at 22:53:01.500432 UTC: receipt SHA
`99f43f021ecda863ea8c11fc6d68e49c884efcbe5e5172a02710eb6104d7bf9d`,
export SHA
`db21f8abecaf556670981b341fc029933e9a99aa71c9f7347b830ef6a1b83b04`.
Plan source, rendered completion/history and protocol checks also passed.
The 34 pgTAP guards, 22 maintained tracker tests, three Journey tests, lint,
typecheck, Node 24 builds, workspace and independent review passed. The same
five inherited staging assertions and two hosted Auth warnings remain unchanged.
Publication establishes no new job, compatible profile, geometry acceptance or
scientific/capacity gate. The previous submitted-only milestone remains retained.

### Separately reviewed libm diagnostic submitted; outcome unobserved

At the October 14 completion checkpoint, no further profile, helper or job had
been claimed; the earlier 7:27 PM EDT scheduler/preflight boundary is historical.
Separate libm diagnostic tools were staged and verified at 23:26:33.802337 UTC
after **173 local checks and independent review**. Tools manifest SHA-256
`90c9336085f01d6b423a04a6087aff381b1527952cc86bea57e67c3cefd43093`; input SHA-256
`1d6ea033970b2b1b49ca6548180e5e6e5f8c097cb722a2466db49b4809d4a4ff`.
The new guarded launcher executed once: **libm diagnostic job 8104416 was
submitted October 14 at 23:29:21.658353 UTC**.
Launch `week5-r2-geometry-libm-launches/20261014T232917Z/launch.json` has SHA-256
`03fa95ee91fb6c6686b792e111d3033bef8af8e5a12cca740be813023c87caf5`; intent SHA-256
`574b8f072e3364b6650f01cead24e0bf60fae09eae8cda94bf574e938d3760b9`.
Independent submission review at 23:34:29.161902 UTC rehashed 815 metadata and
616 frozen-source bindings, checked exact intent/source/tools/input/command and
complete before/after launch seals. Receipt
`week5-r2-geometry-libm-submission-verification/20261014T233429Z/verification.json`
has SHA-256 `0b6a6e05b49bd698cc4d0d317d5142d319d3ec6a5677448e0b90803e19938b33`.
Fresh quota 824,700,000,000 bytes and filesystem free 992,888,225,792 bytes passed
the diagnostic-only reserve: 67,667,170 bytes rounded to 1 GiB. The existing
17,675,344-byte archive is read only in allocation, with no archive copy or
runtime ELF output copies. This does not establish campaign capacity.
The request is four OMP CPU slots, 32 GiB, 30 minutes, no GPU and the reviewed
Gold-6426Y/AVX2 selector. The four-case diagnostic pairs fresh DEFAULT control
and DEFAULT plus a version-appropriate libc/libm FMA-disable request; actual
runtime, ELF and selected function implementation must be proven in allocation
before interpreting numerical metadata. No permanent runtime profile or complete
geometry cause is established. The accepted 8102231 negative result and all
earlier failures remain preserved; geometry and every dependent scientific,
replay and capacity gate remain held.
The pre-submit scheduler check ran at 23:29:20.578046–23:29:20.793929 UTC; it
precedes submission and does not establish the new job state. No post-submission
scheduler observation or numerical result is claimed; no queued, running or
completed state is inferred. First permitted observation:
**October 14, 2026 at 8:31 PM EDT (October 15, 00:31 UTC)**, under the hourly limit.
Never rerun any executed launcher.

The same root controller retains the common operation and dataset-access locks,
opening ledger, scheduler-side 60-second resource sampling, every attempt and
all seals/manifests. The launch request does not establish actual allocated
runtime, memory, dispatch or whole-job accounting. Those require the first
observation and independent terminal review. Source/input/tool/status guards
and a fresh sealed descriptor must pass before that observation; a newer status
pointer requires review. This diagnostic cannot admit geometry or replace full
ordered candidate/panel reproduction and same-profile fresh initialization,
full paired pilot/projection replay and full A.

### Verified libm submitted-only milestone publication

Only evidence versions advanced to Week 5 35, task 02 32, task 04 15 and gate 03
16. Migration `20261014233121` source/statement SHA is
`5f9d69c3955e37d9079509c5b878677bd80b1f832ddb073e3dfccff34a230822`;
actual database trigger timestamp is 23:44:04.942481 UTC. Root independently
verified every before/after public row and all prior migration statements,
project/source links, other 13 weeks, task 01/03 history, actual time and pending
scientific gates: receipt SHA
`b5dc7732f5f945cd70a9f3ce7a03cbca12a7d866e89fbca6a6fd87f7d3396380`.

Node 24 deployment `dpl_CNQgfiTqYuGN6oMJZr3cQ1jJ3iSa` was inspected, promoted
and verified. Actual publication receipt at 23:47:12.831163 UTC has SHA
`195b1df4f41789691337e22be0aa66b0f5c197d0e69de56a6fbcc938becfb223`.
Root independently verified the complete canonical export/envelope, history,
health, private redirect with empty response and Journey at
23:48:23.697795 UTC: receipt SHA
`08f07c32a513a14e5e6d3563658bf7fa4ea012e76be32d1fb943ae3e120a1a9a`,
export SHA `4617e9166d38dcc40e7197ae59f658272e7eb476262f800ff14575986b85c167`.
Canonical plan/protocol sources and rendered submission/negative history passed.
The 36 pgTAP guards, 22 maintained tracker tests, Node 24 lint/typecheck/builds,
workspace and independent reviews passed. The same five inherited staging
assertions and two hosted Auth warnings remain unchanged. The narrow verifier
passed all eight changed public fields/four evidence rows and the complete live
export. No post-submission job state/result, geometry acceptance, profile choice
or scientific/capacity gate follows from this publication.

### October 15: libm diagnostic verified, intervention inconclusive

The first observer executed once at 00:32:02.955881 UTC; its scheduler batch
ran at 00:32:05.186540–00:32:16.493406 UTC and inspection completed at
00:32:16.614103 UTC. Observation SHA
`4197d2bf4784b91b6947447477767303b442775e8e04d6824e549eecfa81ca61`
and accounting SHA
`e095946f5d0b0fe07985d6666bc6328baf1b6732c239590845e607faa035f04e`
bind the actual operation `20261014T233420Z-8104416-geometry-libm-diagnostic`.
Job 8104416 completed October 14 at 23:34:33 UTC on
`apolkovnikov-pub@scc-h30.scc.bu.edu`: failed=0/exit_status=0, four omp slots,
**21 whole-job CPU wall seconds**, actual CPU=14.493 seconds,
RSS=695,096 KiB and maxvmem=9.140G. Keep setup, hashing and parent overhead in
the whole-job ledger; command timers do not replace scheduler accounting.

The new metadata-only observer/verifier passed 110 local checks, Ruff, format,
root review and independent peer review before immutable staging. Corrected
observer source SHA is
`07ae5a3b8611fb3f943810eca6a883236f9fcc54cd89e5bb1a6391f26d253c3d`;
terminal verifier SHA is
`15c5b78c9ecf27ecca0477fcad32f9054796504543b728b33c60011601309c1d`.
Both mains have now executed once. The preserved earlier staging guard failure
occurred before directory creation or scheduler queries; the reviewed correction
adds bounded reads for sealed JSONL/XML metadata. It changes no scientific code.

Independent terminal receipt
`week5-r2-geometry-libm-terminal-verification/20261015T023357Z/verification.json`,
SHA `9f45a91a0ba63431f22bad35b6402fde9faabcde0d8b53682b4c448f9b6b3277`,
was recorded at 02:34:06.243155 UTC. It passed 240 metadata, 617 external and
616 frozen-source bindings, six resources, commands, both seals, final marker,
accounting and recorded runtime/comparison checks. No scientific archive or
runtime library was rehashed on login. Its four-case-only result is
**inconclusive-dispatch**: the FMA-off request changed neither required-version
nor default math-symbol implementation offsets. Both conditions match all four
original scales, 36/40 tensor hashes and 32/36 damage rows; against failed-fresh
evidence both match 0/4 scales, 28/40 hashes and 24/36 rows. An intervention
without a measured dispatch change cannot reject the libm hypothesis or prove
the cause. No compatible permanent profile or geometry admission follows.

SSH subsequently closed with connection reset/Broken pipe. At that checkpoint
the pane was a local shell and restoration had been requested. Root
stopped remote commands. An attempted full-receipt metadata export returned no
receipt; preserve the ambiguous attempt without claiming an export or its
execution timing. The exact compact completion receipt and completed capture are retained
and independently reviewed. The SCC status pointer was last verified at the
dated pre-observation status; refresh it only after authentication, following the
newer observation and completion receipts. Never rerun an executed launcher,
observer or terminal-verifier main. Recover already-recorded metadata without
scientific binary reads or a redundant scheduler query. All dependent stages,
full A, capacity, selection, final training and novel opening remain held.
Actual researcher time remains unreported.

### Verified inconclusive-diagnostic milestone publication

Only four evidence records advanced to Week 5 36, task 02 33, task 04 16 and
gate 03 17. Migration `20261015052051` has source/statement SHA
`7101a72ffa9612520894f4af6656495093d236f6146692a4e5c99861241f4f72`;
the actual database timestamp is October 15 at 10:06:28.172255 UTC.
Independent full-row/history review receipt SHA
`524c4b20e56dac501b87ca4dba8257a8d42a64868042c55029b6df7ba68da052`
confirms that only the four evidence payloads and their trigger-maintained
versions/timestamps changed. Other weeks, states, sources, links and actual
researcher time are preserved.

Node 24 deployment `dpl_68t2AbGm6SLREsp8WTVQpkUPxanw` was promoted.
Independent canonical verification at 10:27:19.307379 UTC passed the complete
export/fallback, history, health, private redirect with empty body and Journey:
receipt SHA `5430680454a2ec84fe9b102091bb54461eafe0deb0360ad73a83bd09e16cbfe3`,
export SHA `278e35692ce77da56566ebafabeb7e2799516dfbe3ff4ede5d31c4bd1df3d989`.
The 38 pgTAP guards, 22 maintained tracker tests, lint/typecheck/Node 24 builds,
workspace, narrow scope and independent reviews passed. The same five inherited
staging assertions and two hosted Auth warnings remain unchanged. This records
the valid inconclusive diagnostic; it adds no scientific/profile/capacity gate
or SSH restoration. At that published checkpoint, remote metadata recovery and
SCC status refresh remained blocked by the disconnected session.

### October 15: access restored and exact runtime metadata recovered

The researcher restored the existing connection. Root verified the authenticated
idle SCC pane before each metadata command, without entering credentials or
creating a connection. No scheduler query was needed or performed: the last
actual batch remains October 15 at 00:32:05.186540–00:32:16.493406 UTC.

The complete **238,862-byte** terminal receipt was recovered at 15:03:07 UTC,
with exact SHA `9f45a91a0ba63431f22bad35b6402fde9faabcde0d8b53682b4c448f9b6b3277`.
Its compressed representation required seven bounded pieces, independently
reassembled and checked against the recorded hash. The preceding recovery
command stopped at its 60,000-character export guard; the 101,196-character
encoding, failed attempt and all distinct subsequent commands are preserved.
Never rerun those commands or infer execution of the earlier ambiguous export.

Four JSON files from the actual `20261014T233420Z-8104416-geometry-libm-diagnostic`
operation were then exported separately at 15:05:07 UTC. Independent review
confirmed their exact raw bytes against the terminal receipt:

| Recorded metadata | SHA-256 |
| --- | --- |
| `child-inputs.json` | `f282baa5b5cbdc257932cf34ca538af01a8c34123e4da864b7e6223e8dd9fd3a` |
| `control-runtime.json` | `fa6c5c72536fa89cbe34730104455dbcebbf644de5660529df3fd575a4a8856d` |
| `fma-off-runtime.json` | `b976f865f42599aa4b94846028b889f27a6836f3c30083c5b4ed0ac0199fa898` |
| `summary.json` | `74c5ba083235766f0532b7bc5eb8c3e0c2edac8b62b9558539cd3bdd4fd46f0c` |

These are recovered records, not a new numerical validation. The actual records
show glibc 2.28, an unset baseline `GLIBC_TUNABLES`, candidate
`glibc.tune.hwcaps=-FMA_Usable`, and ATEN `default`. Binary identities, imported
symbol versions/providers and required/default code offsets agree before and
after both conditions. In particular, the recorded `logf` import is
`GLIBC_2.27`; an unversioned or legacy-wrapper explanation is not established by
these records. The result remains inconclusive, with no cause or permanent
profile selected. No runtime ELF or scientific binary was read on login.

The SCC status was refreshed once at 15:13:30.934012 UTC:
`week5-status/20261015T151330Z/status.txt`, SHA
`bbf4d01268ac8db236ceba3424aa2167a741caba72c8b930166d57ca0fbd1230`;
manifest SHA `effbe46b62b85e908e082d2f93468c94ac5ba4ee47d32cb9f1599e0d17614c52`.
The previous pointer/hash was checked before publication and the new pointer/hash
was verified afterward. Three local boundary checks and independent source review
passed. The earlier status and executed descriptor remain immutable history.

The next diagnostic is prepared and independently reviewed locally: one data-free CPU
allocation with two serial fresh resolver processes, `GLIBC_TUNABLES` unset
versus `glibc.cpu.hwcaps=-FMA_Usable`. It changes only the namespace from the
previous request. Actual package/loader provenance, unchanged binary/import
identity, exact control offsets and a measured required-version dispatch contrast
must be checked in allocation. Resolver children must not import Torch, run the
scientific worker, read licensed inputs or evaluate tensors/math functions. The
supervisor may import Torch for inherited locks/resource checks; its entire cost
stays in CPU allocation time. No tools are staged or job submitted at this
checkpoint. A changed resolver would establish sensitivity only; no change would
remain inconclusive. Neither result admits geometry, a permanent profile or any
dependent scientific/capacity stage. All 140 producer checks and 75 independent
controller checks passed, including separate hashes for the `readelf` executable
and its recorded output. Ruff/format, wrapper syntax and independent source
reviews passed. These are software checks, not an allocated runtime result.
The next permitted SCC prelaunch check is October 15 at 12:14 PM EDT
(16:14 UTC); the exact future command and current-pointer guards remain in the
private handoff.

### October 19: resolver failure verified; diagnostic stopping rule reached

The existing observer ran once on October 19. Its scheduler queries ran from
15:38:32.013261 to 15:38:43.208815 UTC: the user queue was empty, job 8135335
was absent from `qstat`, and `qacct` recorded its October 15 terminal failure.
Observation `week5-status/20261019T153819Z/observation.json` has SHA-256
`04f51f12fed2eea628c45e6cccb4f837f45bf039b0be02a28655cbaedcc7342b`;
the adjacent `qacct.txt` has SHA-256
`017c4798794d41006009dd861ff79d46f5e6ad5bee95b1a5ec43a64d803e51c1`.
Paths here are relative to `study-v3/operations/` under the canonical artifact
root. No resubmission or scientific job followed this observation.

Job 8135335 ran on `apolkovnikov-pub@scc-h30.scc.bu.edu`, four OMP slots,
from October 15 at 17:54:25 to 17:54:30 UTC. Accounting reports `failed=0`,
`exit_status=1`, **five whole-job CPU wall seconds**, 3.260 actual CPU seconds
and peak RSS 676,296 KiB. The parent recorded 0.40552129491697997 seconds;
that internal timer does not replace whole-job accounting. Operation
`20261015T175429Z-8135335-resolver-sensitivity/outcome.json`, SHA-256
`85f4c15f995d6c3a0362213f00a0e2bd3ba851ed9ad14a1cf6673380e070b234`,
records `AssertionError: Missing/ambiguous ELF build ID`. The traceback stops
at `shim.binary(Path(sys.executable).resolve())`, before resolver children;
the operation contains no child runtime or comparison-summary output. The
retained scheduler log has SHA-256
`367747b49e8584fd38429510bd45b76714cf985515d5f2ba19de2de747c26d84`.
Recorded before/after seals remain `sealed`, and the outcome records no novel
pose/outcome access or eligible scientific output. This is an operational
provenance-check failure, not evidence against the scientific hypothesis.

The prior 8102231 diagnostic narrowed the issue to residual jitter differences;
8104416 then established no dispatch intervention, and 8135335 produced no
resolver comparison. Carrying that history forward gives **two consecutive
allocated attempts without narrowing or unblocking the geometry blocker**.
Stop further diagnostic allocations and tool-building for it. Retain every
attempt and request the researcher decision in the current checkpoint; do not
weaken the ELF, geometry or identity checks. October 18 passed without admission.
Fresh scientific regeneration, complete validation/recertification, remaining
storage and both resource calendars still require evidence, including all
diagnostic costs, queue/setup and 25% slack. Final locks remain due November 29,
all compute December 6, with December 7–18 protected. No capacity pass, selection
authorization or Week 5 closure is claimed.

Independent read-only review verified the retained failure bundle, all seven
embedded file hashes, accounting, source ordering and the two seal snapshots.
Review receipt SHA-256:
`76330be5e043db9ea33879bd2544e4ffa275424680feba36d97bd0e55895c459`.
This accepts the terminal failure record, not a completed runtime diagnostic.

The guarded status update changed only Week 5 and task 02/task 04/gate 03 to
versions **38/35/18/19**. Task 02 is now blocked; no gate passed. Rollback,
idempotence and stale-version rejection checks passed, and a complete before/after
row comparison confirmed all other tracker rows unchanged. The CLI's bulk
migration push found three pre-existing timestamp aliases; those were left
unchanged. Only migration `20261019154211` was applied through the linked SQL
command and registered after verification. The public export at
15:48:46.331265 UTC matched the checked-in status after equivalent timestamp
normalization, preserving all other weeks and source links; export SHA-256
`da36400d04cf63178c02e7369afcef1ad769fe2a55326cc79fb502af338047b1`.
The existing data tag and CDN cache were refreshed without a deployment.
Workspace verification, whitespace checks and the 22 tracker tests, typecheck
and lint under Node 24 passed. Scientific code and frozen tools were unchanged;
no GPU, pilot or full scientific validation was run.

### October 19: focused runtime review; allocations remain held

The researcher instructed: **“Proceed with the focused runtime review; keep new
allocations on hold.”** Root reviewed retained metadata and upstream sources;
two bounded, independent local reviews examined provenance enforcement and the
runtime evidence separately. Neither reviewer controlled SCC. This review
changes no frozen source, helper, scientific setting or acceptance threshold.

The review acceptance checklist is complete: identify the failed guard and its
protected requirement; distinguish demonstrated numerical results from untested
runtime explanations; specify the smallest justified next approach. No new
scientific evidence has been accepted. The stopping count remains **two**.

**Interpreter identity failure.** The resolver parent newly passes the Python
executable to the frozen `binary()` helper, previously used for libc, libm and
libtorch. Its `readelf --notes` parser requires exactly one build-ID match and
fails before storing the executable SHA-256. The retained evidence
contains neither those raw notes nor the interpreter identity record. Therefore
8135335 proves only that the parsed count was not one: absence, duplicate output
and parsing mismatch remain unresolved. Mock fixtures with a fabricated build
ID did not establish compatibility with the real executable.

The canonical plan requires pinned runtime identity. The resolver runbook also
requires package/loader identity and unchanged recorded libraries/imports;
neither requires exactly one GNU build-ID for every executable. GNU ld permits
disabling the build-ID note and states that it is not a file-content checksum.
Thus the failed cardinality assertion is a tool representation constraint, not
itself failed scientific evidence. This does **not** establish that Python has
no build ID or authorize removing the guard. See the
[GNU ld build-ID documentation](https://sourceware.org/binutils/docs/ld/Options.html#index-_002d_002dbuild_002did).

If a correction is later authorized, preserve the frozen helper and attempt;
retain the resolved executable path, full SHA-256, size and bounded raw ELF-note
evidence before deciding how to represent the observed case. An interpreter-only
representation correction must reach parent capture, child validation,
independent verification and fixtures together. Preserve the strict existing
library identities, before/after and cross-process bindings, and every numerical
comparison. This is a correction design, not implemented or accepted code.

**Runtime compatibility evidence.** Each row describes its own retained result;
hardware-family labels do not establish exact library or dispatch identity.

| Evidence | Established runtime distinction | Accepted result or remaining limitation |
| --- | --- | --- |
| Original geometry 8028081 | `scc-ne7`, r1; documented Ivy Bridge without AVX2, but original math-library identities/dispatch are absent from the inspected receipt | Original 43-row panel, 430 tensors and fresh-process repeats accepted for r1 |
| Initialization 8035737 | Ivy Bridge; native and explicit DEFAULT | Same RNG state, wrong locked initialization hash; DEFAULT cannot simply be adopted for the whole pipeline |
| Initialization/pilot replay 8035829 | Broadwell with actual AVX2/FMA flags; native AVX2 | Three exact initialization repeats and unchanged full three-pilot validator passed; geometry was not checked on this profile |
| Geometry comparison 8102231 | r2, Python 3.11.15, Torch 2.9.1+cu128, NumPy 2.4.6; native AVX512 versus DEFAULT, Torch threads 4/inter-op 32 | Native reproduces failed r2 on the four tested cases (4 scales, 40 hashes, 36 rows); DEFAULT restores 4/4 original scales, but only 36/40 output hashes and 32/36 damage rows |
| Libm comparison 8104416 | DEFAULT in both; unset tunables versus `glibc.tune.hwcaps=-FMA_Usable`; exact library identities retained | No measured dispatch change; both conditions retain the same four residual jitter mismatches |
| Resolver 8135335 | Parent interpreter-note guard failed before children | No package/loader or resolver comparison; no numerical result |

The four DEFAULT mismatches are jitter 0.025/0.05 in case 2 and 0.01/0.05 in
case 4; clean and mask outputs agree. The evidence does not distinguish Gaussian
generation from later float32 arithmetic or libm dispatch. Pinned PyTorch source
uses separate scalar and AVX2 normal-generation paths; this supplies a plausible
mechanism, not proof of the residual cause in the loaded binary. See
[PyTorch 2.9.1 DistributionTemplates.h](https://raw.githubusercontent.com/pytorch/pytorch/v2.9.1/aten/src/ATen/native/cpu/DistributionTemplates.h).

For 8104416 the imported `logf@GLIBC_2.27`, `sinf@GLIBC_2.2.5`,
`cosf@GLIBC_2.2.5` and `sincosf@GLIBC_2.2.5` resolved to offsets 551968,
553168, 554624 and 556160 respectively. Required-version and default-symbol
offsets stayed identical before/after and across both conditions. A requested
environment setting is therefore not evidence that an intervention occurred.

The retained glibc version string **2.28** does not identify vendor backports.
Upstream 2.28 uses `glibc.tune`, whereas 2.29 uses `glibc.cpu`; the namespace
rename also exists in the CentOS downstream patch archive. Both inspected
upstream parsers recognize `FMA_Usable`, while the 2.28 FMA selector checks both
FMA and AVX2 usability. These sources cannot identify SCC's installed package or
prove that changing the namespace alone will change the imported implementations.
Sources: [2.28 parser](https://raw.githubusercontent.com/bminor/glibc/glibc-2.28/sysdeps/x86/cpu-tunables.c),
[2.29 parser](https://raw.githubusercontent.com/bminor/glibc/glibc-2.29/sysdeps/x86/cpu-tunables.c),
[2.28 selector](https://raw.githubusercontent.com/bminor/glibc/glibc-2.28/sysdeps/x86_64/fpu/multiarch/ifunc-fma.h),
[downstream rename patch](https://gitlab.com/CentOS/archives/git.centos.org/rpms/glibc/-/raw/b61eb49f301ad1e476c2ab99445fa0e6c7287f2e/SOURCES/glibc-rh1817513-2.patch).
GNU also documents that tunables vary by release/distribution; modern
`--list-tunables` support must not be assumed for this unverified loader.
See [GNU tunables documentation](https://sourceware.org/glibc/manual/latest/html_node/Tunables.html).

**Recommended next approach: BU RCS compatibility consultation, before another
allocation.** Use the existing four-case reproducer, retained library hashes and
this review to resolve two questions: which exact installed package/loader build
and tunable semantics correspond to the recorded libc/libm identities; and how
the locked Python executable's actual ELF notes should be represented without
losing identity evidence. No consultation message has been sent. Runtime binary
inspection stays allocation-only and requires renewed researcher authorization;
missing metadata must not be collected on the login node to evade the hold.

After those questions and any necessary correction review are resolved, the
smallest useful common-profile comparison would run the existing four-case
geometry probe and full-size initialization preflight serially under the **same
recorded native AVX2 profile** already known to reproduce initialization. This
is a proposed future comparison, not a selected or authorized runtime. Require
4/4 original scales, 40/40 output hashes, 36/36 damage rows and three exact
initialization repeats matching
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`.
Passing would nominate a candidate for full original-panel reproduction and
same-profile pilot/projection replay; failure would rule out that profile before
expensive regeneration. Switching dispatch between checks would not establish
a common profile. Any proposed libm intervention must first demonstrate a change
in the actually imported symbol implementations with other bindings unchanged.

This review consumed **no allocated CPU/GPU time** and started no monitor or job.
It provides no capacity estimate. The October 18 gate remains missed; full fresh
scientific evidence, independent validation and schema-2 capacity are still
required before selection. All attempts, seals, the original panel/fallback and
November 29/December 6 deadlines remain preserved. Next check is on a researcher
decision or new supplied runtime evidence; there is no scheduled SCC poll.

Two independent local reviews checked the evidence and acceptance limits; their
wording findings were corrected: the native comparison covers only four cases, the failure packet
includes logs/accounting outside the operation directory, and RCS consultation
is a recommendation rather than a new protocol requirement. Workspace and
whitespace checks and 22 tracker tests under Node 24 passed. The existing guarded
migration body passed rollback/idempotence and stale-version checks; the applied
`20261019161401` update changed exactly four status texts and their versions,
with every task/gate state and all other rows unchanged. Live versions are
**39/36/19/20** for Week 5/task 02/task 04/gate 03. Public export verification at
16:16:18.858474 UTC matched the plan after normalizing equivalent timestamps,
ID-keyed row order and response-only metadata; export SHA-256
`fe5149ebd3aa1528ad5d70fe31800e04681ed0a0792c7cb2fee690fd60c74c31`.
Other weeks and sources were unchanged. Cache refresh required no deployment.
The guarded SCC status pointer now targets
`week5-status/20261019T161457Z/status.txt`, SHA-256
`8ab60816bc48f4545d21b94b942ebb7041563fa289e5881cc31d76ceaa38db19`;
this metadata update performed no scheduler query or allocation.

## Reflection

**Done:** Reconciled the prior handoff, live closure and authorized amendment;
published the active Week 5 scope; inspected SCC; recorded future availability;
implemented and verified the completion path and review fixes; committed and
synchronized release 731938a; passed the allocated 41-check software rehearsal
with the real dataset seal intact; verified successor preparation job 8028032,
including exact manifest identity and unchanged scientific settings; passed 84
supplementary checks and independently verified the actual dependence tables.
Task 03 is complete. Task 01 is now complete after full-query geometry
summary/fallback verification; the fixed panel passed independent verification
and exact fresh-process repeats. The allocated controller remedy passed after
the preserved first cache failure; the fresh attempt passed parity and was
independently verified extracting caches on the assigned L40S. Both full-size
extractions are now retained with a passed allocated repeatability receipt and
independently checked sidecar bindings. All five cache commands subsequently
completed successfully with retained accounting, resource and seal evidence;
independent CPU cache validation passed all five archives and repeatability.
The Contrastive engineering pilot completed its fixed run and passed
execution/metadata checks. Contextual completed with matching initialization
and batch-plan metadata. SupCon also completed with matching metadata, and
independent CPU validation of the three-pilot set failed at initialization
reproduction. The failure and a separate post-failure seal check are preserved.
Synthetic diagnostic 8035737 confirmed the failing CPU runtime produces a
different native initialization hash with identical RNG state; all evidence,
resource, seal and accounting checks passed. Retry 8035829 subsequently passed
its allocated AVX2/FMA and three exact native initialization checks; the unchanged
full validator passed all three fixed pilots, numerical replays and pairing.
Independent completion review accepted all 122 evidence bindings, accounting,
resource records and seals. Corruption job 8035983 completed all nine encodings,
27 query projections, three clean galleries and 27 engineering results; its
execution/metadata review accepted all 927 evidence bindings and full-query
geometry summaries. Resident timing 8038355 passed independent completion
review, fixed resident/optimization counts and paired update plans. Full
scientific admission replay remains pending. The three-call P diagnostic then
passed independent verification and established the measured-profile capacity
no-go described above. The researcher then authorized ADR0007. Its implementation
passed independent review and the stable full local suite: 1,373 passed and two
historical AVSL source-parity skips. The clean successor release is
`f101f0e9d9bd64275d2088deab1b0bdcfcc53620`. Separate installation and
independent review of the 128-check allocated rehearsal passed. Preparation
8045152 subsequently passed independent completion verification, including all
eight manifest identities and predecessor/scientific equality. Supplementary
8048540 then passed independent review of 86 checks, three commands, seven
resource records, both seals, 108 metadata and 616 source bindings, and both
actual metadata-dependence tables. Scientific regeneration and admission remain
pending.

**Next:** Follow the [October 19 checkpoint](#current-checkpoint-october-19-2026):
the authorized runtime review is complete, with BU RCS compatibility consultation
recommended before choosing another comparison. New allocations remain explicitly
held. Do not rerun executed launchers/observers or continue diagnostic tool-building
after the two-attempt stopping threshold.

**Open issues:** Tasks 02 and 04 are blocked; all scientific gates remain
pending. Accepted predecessor evidence and the measured-profile capacity no-go
are preserved. Execution-r2 geometry and a compatible runtime remain unproven
after resolver job 8135335 failed before its comparison. Fresh scientific
regeneration, full admission validation and renewed CPU/GPU capacity remain
required. Actual researcher minutes remain unreported by explicit request.
Week 5 cannot close while these gates remain unresolved; selection, final
training and novel opening remain closed.
