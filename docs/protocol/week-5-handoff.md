# Week 5 handoff — October 12–18, 2026

Incoming handoff prepared October 8; amended October 9 under [decision 0006](../decisions/0006-v3-execution-completion-amendment.md). **At handoff, Week 4 technical validation had passed and Week 5 had not
been executed.** Current work and live status are recorded in the
[Week 5 execution record](week-5-execution.md). The original handoff began with
all four Week 5 tasks todo and all three gates pending in the
[canonical plan](../../plan/research-plan.v3.json). Selection and novel access
remain closed. This handoff does not authorize either.

The [Week 4 execution record](week-4-execution.md) retains the verified cache
evidence, frozen release/protocol bindings and current pilot status. Known
artifact locations below are relative to the canonical SCC artifact root:

| Evidence | Retained location and status |
| --- | --- |
| Five clean caches | `study-v3/attempts/20261008T190856Z-7968689`; independent validation passed |
| Contrastive attempt | `study-v3/attempts/20261008T211328Z-7970697`; independent validation passed |
| Contextual attempt | `study-v3/attempts/20261008T212435Z-7970756`; independent validation passed |
| SupCon attempt | `study-v3/attempts/20261008T213627Z-7970877`; independent validation passed |

Final validation job **7971490** passed both receipts and scheduler accounting
(`failed=0`, `exit_status=0`). Its immutable receipt directory is
`study-v3/validations/20261008T214623Z-7971490-pilots`:
`validation.json` SHA-256
`498116254ff24929183c261c93f0d647b9d97f832d572340068f6a54d3468a9e`, and
`metadata-audit.json` SHA-256
`e6a9b9a0c46cd1bb3ad43f8fba627ceab3ff5593251b04c0dbb7b5881023102d`.
Each pilot completed 47,520 updates, four full checkpoint/score records,
epoch-zero health and 21 diagnostic points with identical initialization and
batch-plan hashes. Carry the execution record's timing/memory/byte evidence
into Week 5; pilot heads remain ineligible for learning-rate selection and
final training. This evidence remains valid for its original release; the
completion release requires fresh admission evidence without reopening Week 4. All three attempt directories retain 2,859,496,735 logical bytes;
shared caches, external logs and validation receipts are additional storage.

## Four required tasks, in dependency order

1. **Complete and rehearse the execution/report path (`w05-task-03`) first.**
   Implement selection/final authorization, final training, novel-role extraction,
   corrupted-development scoring and actual v3 report dispatch. The existing
   `training/runner.py`, `motionbert_features.py` and related validators are
   hash-bound and still disable later stages; fixed lock paths also prevent
   in-place replacement. Use the coordinated successor release specified in
   [plan Section 7](../../plan/research-plan.v3.md#7-concrete-architecture-work),
   under `study-v3/revisions/execution-r1/`, keeping original locks and the
   canonical dataset seal intact. Record predecessor/successor provenance and
   verify scientific fields are identical. Rehearse actual commands on fixtures
   through final lock, atomic opening, extraction, projection, scoring and the
   v3 report. Use a temporary synthetic dataset registry/root for opening fixtures,
   never the real ledger; verify real opening records remain absent/unchanged.
   Require 180-cell completeness, ordered subset equality, correct
   bootstrap/report dispatch, tamper/revision rejection, pre-loader authorization,
   concurrent/crashed opening recovery and cross-version training denial. Freeze
   the report interpretation template and metadata-dependence table now; retain
   the independent November audit.
2. **Audit the fixed geometry panel and fallback (`w05-task-01`).** Freeze the
   exact panel before corrupted scoring: two hash-selected primary development
   queries per action plus at most eight support/second-person/scale/fallback/
   all-missing sentinels. The [plan](../../plan/research-plan.v3.md#5-nested-corruptions)
   fixes selection, tie-breaking, absent-category handling and denominators.
   Store IDs/hashes outside Git. Constructed fixtures cover absent/boundary cases;
   two fresh processes must reproduce every panel condition exactly. Bind the
   original training-only fallback **`0.6601371765136719`** from 76,013 training
   rows, with preparation evidence SHA-256
   `06140a298f93f129bbf69b0c17bce8b4d61fac0132e4ea6a7bef4186d5b51438`.
   Do not recompute or select a new fallback. No real-data accuracy floor applies.
3. **Revalidate the release and development paths (`w05-task-02`).** After the
   coordinated freeze, generate fresh parity, both full 95,001-row repeats and
   all five bound caches, then all three complete 20-epoch pilots. Obtain
   independent validation/accounting under successor bindings. Retain original
   artifacts separately. Then complete all nine 18,929-query corruption paths,
   with full-query damage/fallback telemetry and three pilot-head projections
   per condition. Reuse encodings across heads. Time maximum severity per family
   through hashing/loading, preprocessing, encoding, projection/revalidation,
   retrieval and serialization; retain host/GPU peaks and bytes. Corrupted
   scores remain ineligible for selection.
4. **Record October 18 go/no-go (`w05-task-04`).** Combine all successor receipts,
   fixed analysis/report tests, resolved seals and full pipeline measurements.
   Include the all-95,001-row resident timing segment updating only the fixed
   80 training actions. Re-estimate implementation/review, revalidation,
   corruptions, reporting and resource-planning work separately; inherited
   tracker estimates do not establish feasibility. Require a dated allocation
   calendar, researcher-confirmed available hours and the current remaining-peak
   storage calculation. Append immutable selection authorization only against
   the admitted successor digest, which then remains unchanged throughout the
   campaign. If evidence or schedule fails, stop before selection.

## Three gates

| Gate | Required result |
| --- | --- |
| `w05-gate-01` | Fixed panel and all nine full conditions pass exact geometry/repeatability and identity checks; full-query damage telemetry and reusable projections are complete. |
| `w05-gate-02` | Completion-release scientific equality, full command/report rehearsal, fresh caches/pilots and independent validation, analysis/interpretation fixtures and shared seal audits pass. |
| `w05-gate-03` | Measured dependency/schedule/storage/availability report passes before successor selection authorization. |

Original Week 4 closure remains unchanged. Fresh successor pilots are additional
Week 5 admission work and cannot be substituted with relabeled original runs.
This document specifies work; it does not implement the new paths or pass gates.

## Capacity and execution choices

Pilot-based estimates are **6.23 allocated GPU hours** for remaining selection
and final head jobs plus **2.46 hours** for cache/pilot revalidation, both already
including 25% slack. The combined 8.69 hours excludes CPU validation, development
and novel extraction, projection/report stages, queues, retries and human work.
Replace it with successor/full-size measurements before the gate. Start with one
scientific subprocess at a time on the validated L40S; preserve float32 arithmetic,
physical batches and integrity checks. Set wall limits from measured jobs.

The amended **120 decimal GB campaign-wide envelope** includes retained originals,
successor clean caches/pilots and 27 development-corruption projections. It is not
a fresh 120 GB subtraction from remaining space. Admission still requires:

`min(filesystem_free, quota_remaining) >= 200*2**30 + 1.25*remaining_peak_bytes`.

Remeasure current quota/filesystem space; do not carry forward the September
shortfall or October free-space observation as current capacity. Existing files
already consume measured free space and must not count twice. Retain historical
root retirement receipts; do not recreate empty roots or re-ask resolved history.

Freeze infrastructure/numerical/implementation/unresolved failure categories and
the 27-slot selection ledger before ranking. One automatic identical infrastructure
retry needs evidence; further retries require diagnosis/remedy and current capacity.
No accuracy-driven reruns, extra rates, new arms or skipped seeds are adopted.

**Researcher-confirmed future available hours are required before selection.**
Actual Week 4 minutes remain zero/unreported under the existing closure rule.
No researcher time or resource commitment is inferred from automation speed.
Finish final heads/locks by November 29 and novel evaluation by December 6;
preserve December 7–18 for analysis/delivery. Calendar dates do not waive gates.
