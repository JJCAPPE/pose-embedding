# Week 4 execution — October 8, 2026

Week 4 is **in progress**, not complete. Its October 5–11 scope is the fixed
v3 loss/pairing verification, fresh frozen features and three complete
20-epoch engineering pilots. Selection and novel evaluation remain closed.

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
is `logs/pose_v3.o7968689`. A submission or running state is not completion.
Fresh parity passed. The first 95,001-row extraction completed with cache
SHA-256 `43209789c08e8a5e461f72ec5bbeb9bf986bb862e6b828dc0c0b446ad684ee8d`,
3,315,915,790 bytes and 1,786.653482448 seconds wall time. Its measured peak
allocated/reserved CUDA memory was 3,010,839,552/3,896,508,416 bytes and peak
host memory was 6,915,936,256 bytes. At 19:53 UTC, the second extraction was
running; both-repeat verification and all three development caches still need
completion checks. The three real-data pilots have not started.

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

## Verification and handoff

Workspace verification, locked Python synchronization, Ruff lint and formatting
passed. The tracker blocker migration passed 20 local database assertions in a
rolled-back transaction, including optimistic concurrency, audit events,
idempotence and historical-evidence preservation. Its hosted application and
the public Week 4 blocked state were verified before the researcher resolved
the historical interval. The subsequent fixture/resolution migration also
passed its 20 local assertions; hosted migration versions are
`20261008190007` and `20261008191234`. Live database rows, a fresh public export
and the Week 4 browser page show **active, two of four tasks done**, with fresh
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

**Done:** unchanged design bindings rechecked; retired roots factually resolved;
independent numerical checks and full-sized synthetic wiring checks verified.
**Next:** verify fresh parity and all five caches, then run and validate each
fixed 20-epoch pilot, retaining all attempts and paired hashes.
**Open issues:** real caches and pilots are still pending. Actual researcher
minutes remain unreported; Week 4 must remain open until its evidence is complete.

Week 5 depends on the three valid pilot heads for nine complete development
corruption paths and measured scoring. It also needs analysis checks, a dated
allocation calendar and researcher-confirmed available hours by October 18.
Synthetic timings do not satisfy those requirements. No selection sweep,
final head, novel opening or empirical recipe comparison is claimed here.
