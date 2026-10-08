# Week 4 execution — October 8, 2026

Week 4 is **technically complete and formally closed**. Its October 5–11 scope
is verified: fixed v3 loss/pairing checks, five fresh frozen-feature caches and
three independently validated 20-epoch engineering pilots. The guarded tracker
closure is recorded below. Selection and novel evaluation remain closed.

## Prerequisites and historical-root resolution

The active scientific release remains
`2897f4fe4c1fb1857432a0e92a7391dde68307f5`. The protocol, design and manifest
files were rehashed on SCC and match the Week 3 record:

| Binding | SHA-256 |
| --- | --- |
| Canonical protocol | `52241fefab4d1a5aa0fb313d7af4e37bdc6923e2f8277e01cd179bc27a46beea` |
| Protocol file | `db048df526c360ec3c878edad97b34cab6a5c259c260383945d6ab3cc8601b9e` |
| Design lock | `39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d` |
| Manifest set | `ad815466390e0c52c34913a85bdc190a5fabcc0839f92ecbfc643e579db968ee` |
| Supplemental root-retirement resolution | `85ea2aa45930bb6525b5142b973e6671704a801f2048c42e2a5ae6e14e94e08d` |

The [root-recovery record](week-4-root-recovery.md) documents automatic October 5
worktree cleanup and the researcher's October 8 confirmation of no intervening
runs or novel-test access. The original audit, registry and scientific locks
remain unchanged. The 92 historical local files have not been recovered; empty
replacement roots were not created. An immutable supplemental resolution is
retained under `provenance/local-root-retirement-resolution-20261008.json` at
the canonical SCC artifact root. The initial tracker blocker is retained in
the audit history and superseded by this factual resolution.

## Loss and wiring evidence

Independent numerical fixtures now cover all three locked recipes. The new
tests add standalone contrastive value/backward checks, inactive-hinge zero
gradients, and temperature-0.07 SupCon with three positives per anchor. Existing
contextual fixtures cover the mixed loss, embedding backward, tied STE
comparisons and the non-detached reciprocal denominator. No production loss,
configuration, sampler or frozen code hash changed.

The focused Python suite passed 45 tests with one initially unavailable
MotionBERT source oracle. The pinned Apache-2.0 MotionBERT checkout was then
verified through `fetch_upstreams.py --check`, and that oracle passed separately:
all 46 selected checks are verified. A separately retained pairing fixture
also confirms identical initialization and physical batch-plan hashes across
the three objectives:

| Software pairing fixture | Value |
| --- | --- |
| Head dimensions | 32 → 16, synthetic inputs only |
| Budget | 20 epochs, one physical 8 × 4 batch per epoch |
| Shared initialization | `f5d2d3619a1d0121cbea51afc35375719ccb1701a8c35f7de933018c648da9d2` |
| Shared batch-plan file | `f581a887be8f1e2c01d48980ec0f1b99a6c6317661e9ed68591c499432ccfcac` |

SCC job **7968648** separately ran the constructed 32-row learnable fixture
with the **full 8,704 → 2,048 head**, physical 8 × 4 batches, seed 7 and the
fixed pilot optimizer. Each arm completed exactly 1,000 finite updates and
achieved 100% self-excluded same-label nearest-neighbor retrieval. All three
initialization hashes are
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`.
No licensed source or feature cache was accessed by this job.

| Arm | Fixture wall seconds | Peak allocated CUDA bytes | Result JSON SHA-256 |
| --- | ---: | ---: | --- |
| Contrastive | 23.529607 | 640,254,976 | `a1fd2e6efbfecd3456452e54d87c0a1e2f813b51395bf6c31ae57f62266842f8` |
| Contextual | 6.855546 | 640,257,024 | `12cbd92da254505bbf0bc6c15343cbf195730d5efeeaa98a91fd067e9fff6b08` |
| SupCon | 5.464357 | 640,254,976 | `a734c56e2a899756fbdac98e64b362857e62b17b0eebf5a91ace217efc681063` |

These sequential fixture timings include different warm-up conditions and are
not method speed comparisons or pilot forecasts. The job ran on one
scheduler-visible L40S with four CPU slots and a 32 GiB aggregate memory
request. Accounting reports start/end 18:57:39–18:58:52 UTC, 73 wall seconds,
`failed=0`, `exit_status=0`, and `maxvmem=12.009G` (virtual memory, not RAM).
The outputs and separate immutable outcomes are retained at
`study-v3/fixtures/20261008T185740Z-7968648`; the launch script is retained at
`study-v3/operations/week4-20261008/learnable-fixtures.qsub`, SHA-256
`cddb2131c16ef757d055e77a051c42d02730faa24464969cca7ca966c9d69fd2`.

## Fresh caches and pilots

Cache job **7968689** was submitted using the unchanged
`scripts/study_v3.qsub caches` launcher after the retirement resolution and a
fresh capacity check. It began on an allocated L40S at 19:08:54 UTC. Its output
directory is `study-v3/attempts/20261008T190856Z-7968689`, and its scheduler log
is `logs/pose_v3.o7968689`. It completed at 20:42:58 UTC with all five artifacts
retained.
Scheduler accounting confirms `failed=0`, `exit_status=0` and 5,644 wall seconds
(94 minutes 4 seconds); the retained scheduler-exit record also reports zero.

Fresh parity and independent validation of all five complete caches **passed**.
Every row contains 8,704 frozen features. The two final-training extractions
used distinct sequential processes on the same allocated GPU/environment and
passed exact file, feature, label and sample-order equality. Both repeats are retained.

| Cache | Rows | Artifact bytes | Artifact SHA-256 |
| --- | ---: | ---: | --- |
| Final train, first | 95,001 | 3,315,915,790 | `43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d` |
| Final train, second | 95,001 | 3,315,915,790 | `43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d` |
| Development train | 76,013 | 2,653,158,638 | `954067c0c1a84d448dd9df16176cd28a1231373148264f8db9d62667f5f3b667` |
| Development gallery | 20 | 698,846 | `3fc5bffb6fd72abf7acb4faa0d35727c8c2a9aac0b30244e91ebaf88e6ba86cd` |
| Development queries | 18,929 | 660,698,582 | `9dc4341b5a55a5cb6cd9867635f8c3e1762f56eec4239988f69904de2da45f64` |

| Cache | Extraction wall seconds | Peak CUDA bytes | Peak host bytes |
| --- | ---: | ---: | ---: |
| Final train, first | 1,786.653482 | 3,896,508,416 | 6,915,936,256 |
| Final train, second | 1,787.714046 | 3,896,508,416 | 6,923,649,024 |
| Development train | 1,444.639826 | 3,896,508,416 | 6,087,888,896 |
| Development gallery | 64.978065 | 2,023,751,680 | 3,220,934,656 |
| Development queries | 408.726459 | 3,896,508,416 | 3,629,514,752 |

Wall seconds are rounded to six decimals. Peak CUDA is the larger of allocated
and reserved memory; both final-training repeats separately measured
3,010,839,552 allocated bytes. Host peaks are measured process memory.
The first and second sidecar hashes remain
`4bd3668372b8efadab7a52ed3df2dcb42dae21f79a95995bf9c102da4d87d1a4` and
`55fd1e0b7ec72cf04a40dd3ae28068f7c1975774db307b4cb57de60e989695dd`.
The compact receipt retains all five sidecar, manifest and sample-order hashes.

Independent CPU validation job **7969962** was submitted at 20:48:42 UTC and
ran from 20:52:53 to 20:59:42 UTC. Scheduler accounting reports `failed=0`,
`exit_status=0`, 409 wall seconds and `maxvmem=12.103G` (virtual memory).
The validation routine measured 376.158733 seconds and a peak resident set of
8,509,038,592 bytes. It rechecked the unchanged release/protocol/manifest
bindings, parity, repeatability and all five complete cache artifacts using
the frozen validators and actual manifests.

| Validation evidence | SHA-256 |
| --- | --- |
| Public-safe validation receipt, status passed | `4e87fd994e36f0a5159226138f079a7cf5c68e69aeb03d6a94aed3a4d9288b93` |
| Fresh parity report | `8a9e5fe56744d17f9d67bddfb7730bfd04082f8491aaabc0e1da604746810512` |
| Original repeatability report | `b3f4139f7f9b3ff459d23940799e7db5a55de023d767751b833b1c9236a2af26` |
| Independent repeatability report | `69f35f6978b72127ec1a4605d8fd384aea10e684ba89eb88ceed38957f5d3371` |

All five bounded extraction-resource checks passed again. The conservative
forecast is 2,680.249116 seconds and 4,374,851,077 bytes for 113,945 source rows;
effective free storage was 1,008,480,000,000 bytes, the smaller of project quota
and filesystem availability. This validates the bounded extraction requirement,
not Week 5's full-campaign capacity or allocation gate.

The reviewed one-off validator is staged outside the release under
`study-v3/operations/week4-20261008`.
Its SHA-256 is `485beafe748f0efacac12622a23c6b50baea64278fa25b3dcf7e5ac5bda32d7e`;
it ran inside a scheduler allocation after its inputs completed.
Its four-slot, 32 GiB CPU launcher has SHA-256
`bb6ea403206d93522c956c3c516a2a37bc420592d86d94646f2c34f97e62b1b5`.
The validation log is `logs/pose_w4_verify.o7969962`; both scripts are retained
in the operational artifact directory, leaving the scientific release unchanged.

The pre-pilot check at 21:08:36 UTC confirmed the clean frozen release, unchanged
scientific bindings and no opening records in registered roots. Project quota
had 1,008.48 decimal GB free and the filesystem had 1,189,206,818,816 bytes free.
The scheduler reported 28 available L40S GPUs at that instant; this is not a
future allocation commitment.

The first real-data pilot, **Contrastive job 7970697**, was submitted at
21:12:44 UTC using the unchanged launcher and the newly validated cache attempt.
It started at 21:13:26 UTC on an allocated L40S. The unchanged launcher passed
its release, design and resource checks, and its full-size 1,000-update synthetic
fixture passed at 21:14:43 UTC. The attempt is
`study-v3/attempts/20261008T211328Z-7970697`, with log `logs/pose_v3.o7970697`.
The job completed at 21:21:48 UTC; accounting reports `failed=0`, `exit_status=0`
and 502 wall seconds. Its retained metrics report 20 epochs, 47,520 updates,
21 diagnostic records and all epoch 0/5/10/15/20 records. The measured pilot
wall time is 418.697458 seconds; training/validation/checkpoint stages took
286.739518/4.732477/0.530290 seconds. Peak allocated/reserved GPU bytes are
3,286,354,944/3,420,454,912 and peak host bytes are 4,714,979,328.
The final joint validation below independently passed this complete pilot.

After another clean release, seal and capacity check, **Contextual job 7970756**
was submitted at 21:23:16 UTC and ran from 21:24:33 to 21:33:18 UTC, with attempt
`study-v3/attempts/20261008T212435Z-7970756`. Accounting reports `failed=0`,
`exit_status=0` and 525 wall seconds. Its metrics report 20 epochs, 47,520
updates, 21 diagnostic records and all epoch 0/5/10/15/20 records. Pilot wall
time is 443.507612 seconds; training/validation/checkpoint stages took
323.617977/5.362416/0.525819 seconds. Peak allocated/reserved GPU bytes are
3,286,356,992/3,420,454,912 and peak host bytes are 4,696,555,520.

All three validated pilots share initialization hash
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`
and batch-plan hash
`67128877ad2ac134c5c218ddd6c366903faa6cbfca270036dc2979e30ec859f5`.
All 20 per-epoch batch-plan hashes also match across the three arms.
After the next clean release/seal/resource preflight, **SupCon job 7970877**
ran from 21:36:26 to 21:43:21 UTC per final scheduler accounting, with attempt
`study-v3/attempts/20261008T213627Z-7970877`. Its startup fixture passed at
21:37:10 UTC. Accounting reports `failed=0`, `exit_status=0` and 415 wall
seconds; the initial running-state observation reported a start one second
earlier. The retained metrics report 20 epochs, 47,520 updates, 21 diagnostics
and every required epoch record. Pilot wall time is 364.902558 seconds, with
training/validation/checkpoint stages of 254.941551/4.431795/0.488615 seconds.
Peak allocated/reserved GPU bytes are 3,286,354,944/3,420,454,912 and peak host
bytes are 4,712,165,376. Its reported initialization and batch-plan hashes match
the other two arms, as confirmed by the final joint validation.
All arms retain the fixed physical 8 × 4 batches, seed 7,
learning rate `3e-4` and 20 epochs.

Final CPU validation job **7971490** passed after fresh release, lock, seal
and resource checks. It ran from 21:46:23 to 21:50:47 UTC; accounting reports
264 wall seconds, `failed=0`, `exit_status=0` and `maxvmem=5.531G` (virtual
memory). Its retained scheduler exit is zero. The validation routine took
220.701193 seconds with peak process resident memory of 1,380,646,912 bytes.
Its log is `logs/pose_w4_complete.o7971490`.
This validation retains the original validator and additionally audits all
21 diagnostic records per pilot, timestamps and retained output bytes.
The separate metadata audit is
`study-v3/operations/week4-20261008/audit_pilot_metadata.py`, SHA-256
`b5e4b0ac282e551d14520233ae9f354f41d15ec78b8f7cf5481a5e539520eb16`.
Its pilot-only `validate-week4-complete.qsub` wrapper has SHA-256
`8f64f96464c9b25ef4aaec57fcf050af44acb95dc3d32cd13ee1feadff5c35e0`.
Four constructed metadata checks, lint/formatting, shell syntax and rejection of
cache mode passed. These operational additions leave the frozen release and
the original successful cache-validation scripts unchanged.
Both immutable receipts passed in
`study-v3/validations/20261008T214623Z-7971490-pilots`:

| Receipt | SHA-256 |
| --- | --- |
| `validation.json` | `498116254ff24929183c261c93f0d647b9d97f832d572340068f6a54d3468a9e` |
| `metadata-audit.json` | `e6a9b9a0c46cd1bb3ad43f8fba627ceab3ff5593251b04c0dbb7b5881023102d` |

The unchanged `validate_engineering_pilot` verified the four complete checkpoint
and 18,929-query score records at epochs 5/10/15/20, epoch-zero health, finite
values, non-collapsed embeddings and paired training identities. The additional
audit verified all 21 diagnostic points per arm, including gradient/loss,
variance, hinge, cosine and contextual-neighborhood fields. No recipe was
selected or tuned using development accuracy.

| Arm | Retained run files | Retained run bytes | Checkpoint bytes |
| --- | ---: | ---: | ---: |
| Contrastive | 43 | 953,144,034 | 285,255,316 |
| Contextual | 43 | 953,193,125 | 285,255,828 |
| SupCon | 43 | 953,142,541 | 285,255,316 |

All three complete attempt directories retain **150 files / 2,859,496,735
logical bytes**, including fixtures and scheduler records. This inventory
excludes external scheduler logs, validation receipts and shared caches; it is
not total project storage. At validation startup, node available RAM was
131,567,489,024 bytes, quota free was 1,004.87 decimal GB and filesystem free
was 1,186,346,303,488 bytes. These measured resources met the bounded Week 4
requirement; no allocation or storage commitment for Week 5 is implied.

The initial SCC preflight found no running researcher jobs. At 18:50:52 UTC,
project quota had 1,025.40 decimal GB free and the filesystem had
1,208,391,565,312 bytes free. Immediately before cache submission these were
1,024.44 decimal GB and 1,207,359,766,528 bytes. Both pass the bounded Week 4
requirement of 239,748,364,800 bytes. This supersedes the dated September
capacity shortfall, without reserving shared storage or passing Week 5's
full-workload capacity gate. At 19:53:49 UTC, an immutable resource snapshot
recorded 1,020.41 decimal GB quota free, 1,203,031,244,800 filesystem bytes free,
4,257 MiB used on the allocated GPU and 262,292,209,664 bytes of available
node RAM. Node-wide available RAM is not process peak RAM.
During Contextual training at 21:31:52 UTC, the allocated GPU used 3,837 MiB
of 46,068 MiB, node available RAM was 234,071,187,456 bytes, project quota had
1,006.41 decimal GB free and the filesystem had 1,187,533,291,520 bytes free.
During SupCon training at 21:40:32 UTC, the allocated GPU also used 3,837 MiB
of 46,068 MiB, node available RAM was 261,693,734,912 bytes, project quota had
1,005.52 decimal GB free and the filesystem had 1,187,046,752,256 bytes free.
The completion snapshot at 21:55:06 UTC showed no researcher scheduler jobs,
a clean frozen release, 1,003.80 decimal GB quota free and 1,185,201,258,496
filesystem bytes free. The immutable resource snapshots remain in the
operational artifact directory.

## Verification and handoff

Workspace verification, locked Python synchronization, Ruff lint and formatting
passed. The tracker blocker migration passed 20 local database assertions in a
rolled-back transaction, including optimistic concurrency, audit events,
idempotence and historical-evidence preservation. Its hosted application and
the public Week 4 blocked state were verified before the researcher resolved
the historical interval. The subsequent fixture/resolution migration also
passed its 20 local assertions; hosted migration versions are
`20261008190007` and `20261008191234`. The repeatability milestone migration
`20261008202132` passed 13 additional rollback-only database assertions and
updates only the in-progress cache task and Week 4 reflection (versions 5 → 6).
It does not close a task or gate. At that milestone, live database rows, a fresh
public export and the Week 4 browser page showed **active, two of four tasks done**, with fresh
features in progress. The remaining gate is pending.

Production deployment `dpl_BCzqk1bxhnTqcSak15LLBiHFsbBd` was built successfully,
health-checked and promoted on October 8. The primary public alias resolves
to this READY deployment. Its application source reproduces the preceding
production deployment byte-for-byte, including Journey; only the public
`plan/research-plan.v3.json` content changed. The deployment uploaded 84
public application/plan files (the original `.gitignore` is excluded by the
CLI). No licensed inputs, results, credentials or local redesign changes were
uploaded. Production health reports Supabase-backed data and editing enabled.
The ordinary public export returned Week 4 active/version 5 after promotion;
a prior stale export response was within the existing five-minute cache plus
one-hour stale-while-revalidate window. Tracker tests, lint, typecheck and
production build passed; no tracker runtime logic changed.
The repeatability-only fallback was subsequently published by deployment
`dpl_DUZemD88GqAoi51dw1yXp9hES1fQ`; its fresh export verified Week 4/task 3
version 6 with the passed repeatability hash, while both remained open.
The same production source and Journey preservation checks were repeated.
The cache-generation milestone was then recorded by guarded migration
`20261008205404` (13 rollback-only assertions passed) and published in deployment
`dpl_CaPNAqwhh4v3r6xbEqEPUgYqmnC2`. Week 4 and the cache task advanced to
version 7 while their states stayed active/in progress; no gate or pilot status
was changed. The fresh export verified the successful-generation/pending-validation
distinction before promotion.
After independent validation passed and the first pilot started, migration
`20261008211839` completed the cache task and marked the pilot task in progress.
Its 15 rollback-only database assertions passed. Week 4 remains active at
version 8, with three of four tasks done and the final gate pending; researcher
minutes remain unreported. Deployment `dpl_2ZainyfJ1KxeWcqEZQgbVyCzXuvT` passed
its production build and was promoted after a fresh export verified those
states. The primary alias, ordinary public export and live page were verified.
The same production source preservation checks passed; only the fallback plan
changed. The stale browser expectation for recent completions now follows the
current published seed. Both affected desktop/mobile browser cases, 15 relevant
unit tests, test-file lint and the local production build passed.
All PR checks passed on commit `12d9d6f`, including the full tracker browser
suite, Python/workspace checks and Supabase schema/RLS checks.
The two-completed-pilot milestone was recorded by guarded migration
`20261008214009` after 13 rollback-only database assertions and 15 relevant
tracker unit tests passed. Week 4 advanced to version 9 and the still-open
pilot task to version 7. Production deployment `dpl_J6poQJ4FQrHxNffdp1B4dfFhPu5x`
passed its build, fresh export checks and promotion; the primary alias, ordinary
export and live page confirm the same open states. Application source and Journey
remain unchanged. All PR checks also passed on the preceding documentation
commit `51b5547` and milestone commit `210bbdb`.

After final independent validation passed, guarded migration
`20261008222524_complete_week_four_verified_pilots.sql` completed the pilot task
(version 8), met the final gate (version 4) and formally closed Week 4 (version
10). All four tasks are done and all three gates met. The migration passed
20 rollback-only assertions, including unchanged history/Week 5, concurrent
edits, incomplete prerequisites, exact retries and closed-week protection.
Its SHA-256 is
`20fca95a7257bc7b457f0a904b1630bf177c529a2a8b83b2281d6884b6180d00`.
Hosted rows were verified after application. Actual minutes remain zero as
**unreported**, without inventing researcher time or asserting zero work.
Week 5 remains planned, version 3, with its tasks and gates untouched.
The final fallback snapshot matches the closure; tracker lint, typecheck and
all 22 unit tests passed. The Week 5 browser readiness assertion was updated
for its now-closed prerequisite; both desktop/mobile cases passed, as did the
local production build.

Production deployment `dpl_3u5tMSYf3eeNV8KV7ouVuQJEygGQ` passed its build and
fresh export checks before promotion. Its primary alias, health endpoint,
ordinary public export and live Week 4 page were then verified: **closed,
four of four tasks done, three of three gates met**, with both pilot receipt
hashes present. The public export exactly matches the fallback Week 4 record.
All 84 non-plan source files still match the preserved production source,
including Journey; only the public fallback plan changed.

**Done:** unchanged design bindings rechecked; retired roots factually resolved;
independent numerical checks and full-sized synthetic wiring checks verified;
all five fresh cache files independently validated with passing parity, exact
repeatability, bindings and bounded extraction-resource checks; all three fixed
20-epoch pilots independently validated, with paired hashes, complete snapshots,
diagnostics and measured timing/memory/retained bytes.
**Next:** execute the separately gated Week 5 corruption, analysis and capacity
work using these validated engineering heads.
**Open issues:** no remaining technical Week 4 blocker. Actual researcher
minutes remain unreported; no hours were invented. Future available hours and
a dated allocation calendar remain Week 5 requirements before selection.

Week 5 depends on the three valid pilot heads for nine complete development
corruption paths and measured scoring. It also needs analysis checks, a dated
allocation calendar and researcher-confirmed available hours by October 18.
The [Week 5 handoff](week-5-handoff.md) records those unexecuted requirements
and the remaining implementation prerequisites.
Synthetic timings do not satisfy those requirements. No selection sweep,
final head, novel opening or empirical recipe comparison is claimed here.
