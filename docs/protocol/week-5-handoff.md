# Week 5 handoff — October 12–18, 2026

Prepared October 8. **Week 4 technical validation passed; Week 5 has not
been executed.** All four Week 5 tasks remain todo and all three gates pending in the
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
final training. All three attempt directories retain 2,859,496,735 logical bytes;
shared caches, external logs and validation receipts are additional storage.

## Four required tasks

1. **Audit nested corruptions and fallback (`w05-task-01`).** On a fixed
   development panel, verify shared jitter fields, nested joint/frame masks,
   severity-zero identity, missingness, boundary/two-person cases, fresh-process
   determinism, fallback frequency and nominal/effective damage, including zero
   damage. Follow the [locked operators](../../plan/research-plan.v3.md#5-nested-corruptions).
   Audit the existing training-only fallback **`0.6601371765136719`**, derived
   from 76,013 development-training rows; do not recompute it from another split.
   Its [preparation evidence](week-3-v3-readiness.md) SHA-256 is
   `06140a298f93f129bbf69b0c17bce8b4d61fac0132e4ea6a7bef4186d5b51438`.
2. **Complete nine development corruption paths (`w05-task-02`).** Retain all
   nine full query paths with exact identities/invariants and deterministic
   outputs. Time maximum severity per family through source/provenance checks,
   preprocessing, encoding, serialization, all three pilot-head projections and
   complete retrieval. Corrupted scores cannot select recipes or settings.
3. **Verify fixed analysis (`w05-task-03`).** Use hand-ranked and unequal-view
   fixtures for query weighting, paired within-action performance-cluster draws,
   all views/multiplicities, 10,000 `PCG64(2026)` replicates and linear percentile
   quantiles. Do not resample seeds/actions. Leave-one-action-out preserves the
   gallery and ranks. Bind the [tested analysis](../../src/pose_embed/evaluation/analysis.py)
   before selection under the [locked rules](../../plan/research-plan.v3.md#6-locked-analysis).
4. **Record October 18 go/no-go (`w05-task-04`).** Combine valid pilots, refreshed
   seals, full pipeline timings and a timing-only segment with all 95,001
   auxiliary feature rows resident, updating only the fixed 80 training actions.
   Add a dated allocation calendar, researcher-confirmed availability and the
   measured remaining-work/storage forecast. Append immutable selection
   authorization against the unchanged protocol digest only after every check
   passes; otherwise stop before the sweep and record a result-blind amendment.

## Three gates and remaining implementation

| Gate | Required result |
| --- | --- |
| `w05-gate-01` | All nine conditions pass nesting, fallback, identity, deterministic-output and full pipeline checks. |
| `w05-gate-02` | Conditional analysis is tested; all three pilots and historical seal audits remain valid under the unchanged digest. |
| `w05-gate-03` | October 18 schedule, storage and availability report passes and authorizes selection; otherwise no sweep starts. |

The [evaluator](../../src/pose_embed/evaluation/runner.py#L78) still rejects
corrupted development scoring: implement/audit the declared v3 engineering mode
while preserving clean-only selection. The [selection authorizer](../../src/pose_embed/protocol_v3_campaign.py#L13)
still fails closed after schema validation: implement/audit complete measured
evidence cross-bindings. These later interfaces are outside the [frozen cache/pilot set](../../src/pose_embed/protocol_v3.py#L143);
preserve its code hashes and all historical artifact checks.

The [capacity rule](../../plan/research-plan.v3.md#8-capacity-gates) requires
`min(filesystem_free, quota_remaining) >= 200*2**30 + 1.25*remaining_peak_bytes`.
Include retained failures/staging without double-counting existing files; apply
at least 25% compute/researcher-work slack plus queue/setup delays. Finish heads
and locks by November 29, novel evaluation by December 6, and preserve December
7–18 for analysis/delivery. Bounded cache checks do not pass this campaign gate.

**Researcher-confirmed future available hours are required before selection.**
Actual Week 4 minutes may remain zero/unreported under the [closure rule](../../apps/tracker/lib/domain.ts#L41).
Neither zero recorded time nor inherited estimates establish future availability.
The three pilots cannot supply the nine corrupted paths, final-size timing,
future allocation calendar or researcher availability; those remain Week 5 work.
