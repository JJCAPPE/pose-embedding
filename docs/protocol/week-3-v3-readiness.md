# Week 3 v3 readiness — September 29, 2026

This record follows the September 29–October 4 implementation row of the
[final v3 plan](../../plan/research-plan.v3.md). Earlier completed Week 3 work
remains [historical evidence](week-3-scc-execution.md); it is not relabeled as
v3 execution.

## Implemented preparation

- Explicit v3 template/resolved validation, all 27 fixed experiment configs,
  immutable design/pilot bindings, and staged evaluation/selection/final
  templates. Modified recipes, seeds, duration, identities or source hashes
  fail validation. Later campaign authorizers remain closed.
- CPU float32 nested corruptions, training-only lower-median torso fallback,
  fixed within-action clustered bootstrap and fixed-gallery sensitivity, with
  independent fixtures including unequal view counts and paired draws.
- A dataset-wide root registry with persistent bindings in every registered
  artifact root, cross-version opening checks, and process locks preventing
  opening during auxiliary access. Unknown roots, unreadable audits, changed
  inventory bindings and dangling opening links fail closed.
- Auxiliary-only packaging and v3-bound manifests with exactly unchanged
  sample identities. Original pickle deserialization is recorded honestly;
  novel annotations do not enter preprocessing, diagnostics or model code.
- The fixed three-arm pilot path with paired initialization/physical batches,
  complete diagnostic score records, immutable checkpoints and failures,
  finite/collapse checks, and runtime/memory evidence. Pilots cannot enter
  selection or the final set.
- Allocated CPU preparation and L40S cache/pilot launchers with clean-release,
  quota, seal and design checks. See the [SCC runbook](scc-v3-runbook.md).

## Verified SCC preparation

SCC job `7790916` completed on `scc-pi2.scc.bu.edu` on
September 29, 2026, from 18:18:52 to 18:25:15 EDT. Scheduler accounting reports
`failed=0`, `exit_status=0`, 383 seconds of wall time and `maxvmem=5.124G`.
The clean scientific release is `2897f4fe4c1fb1857432a0e92a7391dde68307f5`.
The corrected freeze, independent verification process and protocol verification
all passed. The active SCC environment and `current` link select this release
and the prepared v3 manifest bundle; the Week 4 L40S launcher passed the
scheduler's validation-only check.

The auxiliary package from job `7790703` contains 95,001 authorized rows.
All 76,013 fixed development-training samples contributed valid torso scales;
the lower-median fallback is `0.6601371765136719`. No training sample
required fallback. The eight exact identity sets and unchanged manifest bytes
were verified:

| Identity set | Rows |
| --- | ---: |
| Development training | 76,013 |
| Development validation | 18,988 |
| Final training | 95,001 |
| Novel anchors | 20 |
| Primary novel queries | 18,884 |
| Official novel queries | 18,924 |
| Development gallery | 20 |
| Development queries | 18,929 |

The source-bound registry includes both SCC artifact roots and an immutable
external audit of all three local historical artifact roots, found by checking
19 local worktrees. Known opening ledgers and possible opening records were
absent in the audited roots. These are dated seal observations, not future
opening authorization. Novel annotations did not enter preprocessing,
diagnostics or model code. Later selection and final-test authorizers remain
closed.

Job `7790703` initially failed when reloading the JSON protocol, and independent
job `7790712` reproduced the loader error. Job `7790674` had earlier failed on
the system Python version before preparation. Every attempt and failed freeze
is preserved. [Decision 0005](../decisions/0005-v3-json-protocol-recovery.md)
records the JSON parsing correction and result-blind recovery: the resolved
protocol bytes and scientific digest are unchanged; only the corrected loader's
source hash changes in the design lock. Valid auxiliary preparation is reused.

Compact bindings from the successful verification:

| Binding | SHA-256 |
| --- | --- |
| Canonical protocol | `52241fefab4d1a5aa0fb313d7af4e37bdc6923e2f8277e01cd179bc27a46beea` |
| Protocol file | `db048df526c360ec3c878edad97b34cab6a5c259c260383945d6ab3cc8601b9e` |
| Corrected design lock | `39426a3b2ddea74aaa8c1d39737cd9e5fb9c870c21745f5527e4e97b58d14e2d` |
| Artifact-root registry | `88ffa98dcfbec6c544fd6bd790685e165115762a2e3b884e503698c19d3f8eb4` |
| Source inventory | `e0ab842fe2a62b50ff7205d0f8658fad373a03c5b29527c281a2db0225ea0058` |
| Auxiliary container | `0539b60ec4772b6a53afe7ce0f64f4a923c99a31fb06c856b32417fc59ae187a` |
| Fallback evidence | `06140a298f93f129bbf69b0c17bce8b4d61fac0132e4ea6a7bef4186d5b51438` |
| Preparation manifest | `da3afb9b98debcd9168cc392c76e26a9246a76c7279840823b6984bcb6ce0869` |
| Rebound manifest set | `ad815466390e0c52c34913a85bdc190a5fabcc0839f92ecbfc643e579db968ee` |

Full private evidence remains below `POSE_EMBED_ARTIFACT_ROOT`:

- `study-v3/preparation/20260929T214227Z-7790703`: auxiliary package, fallback, identities
  and manifests.
- `study-v3/preparation/20260929T221856Z-7790916-freeze-recovery`: recovery, independent verification,
  protocol verification, cleanup receipts, quota snapshot and scheduler exit.
- `study-v3/locks`: resolved protocol and corrected immutable design lock.
- `provenance`: historical-root audit and dependency-cleanup receipts.

Historical SCC job `7761714` and its two complete auxiliary caches and three
development caches remain preserved. They are historical evidence, not v3
cache results. Fresh v3 parity, cache extraction and three complete pilots are
Week 4 work and have not been launched.

## Cleanup, capacity and tracker handoff

Seven superseded rebuildable dependency environments were removed after
recording their release and lock hashes and checking active jobs. The retired
package-download cache cleanup removed 19,884 files (6.7 GiB). Historical
releases, inputs, scientific caches, checkpoints, run manifests, source
licenses and failure evidence remain available. Active instructions and release
links now select v3; old launchers are explicitly historical reproduction tools.
The 41 superseded local files were hash-verified into a private recoverable
archive and Git stash before clearing the old draft from the active checkout.

The measured usable space after cleanup is **274.72 decimal GB**, taking the
minimum of filesystem free space and project quota. It passes the bounded
Week 4 requirement of **239.7484 GB**. The initial full-campaign requirement is
**314.7484 GB**, leaving a dated **40.0284 GB** gap. Shared quota must be rechecked
before each job; full-campaign storage, measured runtime and researcher
availability remain part of the October 18 go/no-go gate.

All seven Week 3 tasks and gates now have completion evidence. Week 3 is closed
and Week 4 is ready to start. The closure migration updates only the final
preparation task, corresponding gate and open Week 3 record. A separate handoff
migration credits the same freeze in Week 4's duplicate design task/gate, so
the website points to loss/paired-training verification as the next work.
Week 4 stays planned with one of four tasks complete; fresh caches and pilots
remain pending. Both migrations use version/content conflict checks and audit
events. Weeks 1–2 and historical evidence remain unchanged.
Actual researcher time remains unreported and displays as
“No time recorded”; the existing task/gate closure rule does not require
inventing minutes. Additional tasks retain zero estimates as an unestimated
placeholder.

## Release verification

- Full Python suite after the JSON loader correction: **1,015 passed**, no skips,
  including pinned MotionBERT and licensed AVSL oracle fixtures. This is local
  CPU software verification, not a new GPU result.
- Ruff lint, all-file formatting, workspace verification, locked Python
  synchronization and launcher shell syntax checks passed.
- Tracker: 22 tests, lint, TypeScript and production build passed.
- Clean local database reset, 254 database assertions and local security
  advisors passed. The 32 new completion/handoff assertions cover preserved history,
  optimistic concurrency, atomic rollback, idempotence and closed-week rules.
- The historical v1 protocol digest remains
  `c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.

Hosted Auth was rechecked on September 29: public sign-up and anonymous users
are disabled, the Site URL is `https://pose-embed-tracker.vercel.app`, and the
additional redirect allow-list is empty. The completed hosted-access manual
action is removed from the outstanding list.

The hosted security advisor still reports the pre-existing Auth configuration
warnings for leaked-password protection and available MFA methods. This update
changes no Auth, ownership, grant or RLS settings.
