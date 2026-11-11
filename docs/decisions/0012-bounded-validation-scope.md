# 0012 — Bounded validation scope

Date: 2026-11-11. Status: **proposed for researcher approval; not implemented or adopted.**

## Decision requested

Replace recursive historical revalidation with two complete acceptance passes
per evidence set: its initial validation and one fresh independent verification.
Later consumers check the resulting immutable certificates, their actual inputs
and outputs, and current permissions. Rehash the complete dependency inventory
at bounded stage entry and before stage acceptance. Keep the full scientific
study. This changes validation scope and frequency, not scientific predicates.

This explicitly amends ADR0007's prohibition on persisted/cross-command proof
authority and its full transitive rehash on every nested reuse. It extends
ADR0011's finite-artifact validator exception beyond parser and episode reuse.
Until approved, those existing restrictions remain in force. Approval would
authorize reviewed implementation and allocated qualification within Week 5;
it would not authorize selection runs, final training, novel opening or closure.

## Why 873.911 hours appeared

This is a forecast of serial validation wall time in the future November 30–
December 6 campaign, including 25% margin. It is not remaining Week 5 time,
training time, researcher time or CPU-slot-hours. Job 8565319 itself took
3,982 scheduler seconds (66.4 minutes); its final guarded acceptance remains
unverified. Its retained metadata passed local independent review.

The unchanged call graph predicts the following repeated Week 5 audits:

| Operation | Commands | Historical admission calls | Forecast hours with margin |
| --- | ---: | ---: | ---: |
| Novel encodings | 11 | 22 | 9.791 |
| Primary-query exports | 10 | 40 | 17.169 |
| Head projections | 189 | 279 | 127.303 |
| Retrieval evaluations | 180 | 810 | 346.238 |
| Report construction | 1 | 451 | 186.498 |
| Independent report verification | 1 | 452 | 186.912 |
| Total | 392 | 2,054 | 873.911 |

With first/fresh-proof cost C=1372.9295508799842 seconds and reuse cost
R=1190.5385979909915 seconds, `(392*C + 1662*R)*1.25/3600 = 873.910949` hours.
All timed passes started with a warm parser in one process. The figure is a
profile-specific estimate, not a guaranteed runtime or universal lower bound;
it omits other validation, science, setup and queue costs.

The trigger is `_validate_authorization()` in `protocol_v3_campaign.py`:
reading selection authorization reruns the three pilots, geometry, nine
development encodings, 27 development evaluations and dependence tables.
Final authorization additionally revisits the complete 27-slot selection ledger
and its successful runs, plus nine final heads. Cache, projection, evaluation and report validators call this chain
repeatedly. Final-head validation checks initialization, batches, checkpoint
and run evidence; it does not retrain the model for 20 epochs.

The reuse measurement spent 110.497 of 1190.539 seconds inside proof-store
rehashing, with zero numerical proof execution. Removing that timer alone
cannot solve the remaining cost. The outer historical validators must stop
reconstructing the same evidence for every consumer.

## Required scope

| Evidence | Initial complete check | Fresh independent check | Later consumption |
| --- | --- | --- | --- |
| Week 5 finite retained inventory | Complete candidate replay/adoption and admission | One complete independent recertification | Accepted certificates and integrity/authority checks; no repeated pilot/development replay |
| Each successful run among 27 planned selection slots | Existing checkpoint/projection/retrieval and attempt checks | Verify the complete slot/attempt ledger and locked selection once | Selected-config certificate; fresh complete attempt inventory where required |
| Each of nine final heads | Existing initialization, physical batch plan, checkpoint and run checks | Verify all nine and the final lock once | Head/final-lock certificate, checkpoint identity and live opening guards |
| Each of 21 novel pre-head files and 189 projections | Existing role, order, numerical/provenance checks when produced | Once per artifact in its stage verification | Full consumed-file hashes, role and certificate checks |
| All 180 result cells and final report | Compute/validate each result and construct the report once | Independently recompute every cell's required metrics/ranks and verify the complete report once | Verified report and immutable result identities |

Each row retains every current numerical predicate and tolerance. Producer
generation is not its independent verification. Existing accepted evidence is
reused only within its recorded producer/runtime scope. In particular, the
changed libc/libm candidate still needs GPU/parity qualification and the
ADR0011 artifact-specific replay/adoption receipts. A certificate cannot turn
old-runtime acceptance into new-runtime acceptance.

The 27 slots need not all succeed. Preserve the existing failed/ineligible-run
rules and complete attempt ledger; each method still needs an eligible
three-seed candidate. This proposal creates no new success requirement.

Do not repeat accepted CPU qualification, regenerate unchanged caches, retrain
pilots or rerun historical fixture suites merely because a later command reads
their evidence. Revalidate affected dependencies when inputs, source, options,
runtime or protocol change. Preserve all failed attempts and original artifacts.

## Integrity and authority boundaries

Use the existing proof engine, immutable receipts, dataset-access lock and
operation wrappers. Do not introduce a new orchestration or snapshot system.
A stage is a finite, reviewed command/input/output inventory within one
allocation. If work spans allocations, each allocation gets fresh boundaries.
Examples are retained-evidence validation, pre-head extraction/export,
projection, retrieval, report generation and separate report verification.

1. At stage entry, fully hash the unique transitive dependency inventory and
   validate its certificates. Bind original producer/source/runtime, current
   validator/source/runtime, protocol/design, options, ordered identities,
   roles, canonical paths, checked predicates and exact successful outcomes.
   No stat-only trust, fabricated pass, missing ancestor or unlisted artifact.
2. Before each command reads an input, hash all its bytes and validate its
   role/path and certificate. Recheck consumed inputs before completing that
   command. Parse reports freshly; do not share mutable result objects.
3. Keep permissions, seal/opening state, chronology, complete attempt inventory,
   locks, source/runtime identity, resources, calendar and deadlines fresh at
   their existing required boundaries. A numerical certificate grants none of
   these permissions. Before irreversible access, including novel opening,
   freshly validate the complete relevant dependency closure and live guards.
4. Before stage acceptance, rehash the full transitive inventory and outputs.
   Independently verify new scientific artifacts as specified above. Until
   this succeeds, outputs are provisional: they may be retained and consumed
   within this bounded stage, but cannot pass a gate, authorize opening or be
   accepted by a subsequent stage. A mismatch blocks every affected descendant.

This deliberately changes mutation-detection cadence. A persistent change to
an unread ancestor is caught at the next boundary, rather than at every nested
call. Entry/exit hashes cannot guarantee detection of a change that is restored
between checks. Retain the controlled-storage and cooperative-lock assumptions;
do not claim filesystem immutability. Directly consumed files and irreversible
access retain fresh checks. If these assumptions cannot be established for an
allocation, use the original complete checks rather than trusting certificates.

## Small verification and rollout scope

Before adoption, independently review the changed call graph and exact impact
inventory. Keep original producer locks and evidence; freeze the corrected
validator separately. Use synthetic fixtures locally for these checks:

- Original versus scoped validator: identical complete 180-cell report,
  ordered roles, metrics/ties, selection decision and rejection behavior.
- Changed bytes, ancestors, source/runtime/options/protocol/roles and receipt
  identities: invalidation or rejection; no passed descendant after mismatch.
- Failed/partial/forged certificates, caller mutation, command/process
  separation, crash/publication and missing/duplicate inventory rejection.
- Fresh authority/seal/resource checks even with a valid certificate; opening
  remains blocked before loader access. Independent verification uses a fresh
  process and recomputes the required numerical checks, without inheriting the
  producer's numerical proof results.
- Invocation counters: one complete initial and one independent audit per
  unchanged evidence set; no historical admission replay in each result cell.

Run affected tests during implementation and the required complete release
checks once before freeze. Retain existing tests; do not repeatedly allocate
unchanged historical test suites. Required CI still applies to repository work.

Reconcile the stopped 8565319 acceptance process/receipts before any retry; do
not repeat that measurement just to recover paperwork. After local equivalence
and required runtime qualification, use one bounded allocated measurement of
the corrected path, including a fresh command, complete hashing, actual retained
evidence and the largest report-verification workload on permitted evidence.
Combine this with required finite-inventory replay where possible; do not create
another sequence of component-only diagnostics. No novel arrays are opened.
The order is bounded measurement and finite-inventory verification while
admission remains blocked, then measured capacity, then full admission and
fresh independent recertification, then selection authorization. Preserve the
existing expected pending-capacity rejection during measurement; never invent
a passed capacity receipt to reach the timing code.

Target total post-opening validation at **16.8 wall-hours including 25% margin**
(10% of the 168-hour window), with each indivisible validation command fitting
the normal 12-hour request. These are engineering targets, not measured results
or new scientific acceptance gates. The complete measured CPU/GPU/storage/
calendar/researcher forecast must still pass, including all remaining science,
setup, queue and the existing 200 GiB reserve. If the target is missed, report
the measured dominant work; do not waive a check or silently reduce the study.

Two complete historical-prefix checks at the observed C would be about 46
minutes, or 57 minutes with margin. This illustrates only the repeated component
being removed; it is not a prediction of total Week 5 or campaign duration.

All methods, three paired seeds, 20 epochs, 27 selection runs, nine final heads,
queries, nine corruptions, 180 cells, metrics, tolerances and claim rules remain.
November 29 locks, December 6 compute and December 7–18 delivery remain fixed.
The legacy Codex automation stays paused. Future authorized jobs use the single
completion watcher under the current SCC runbook; this proposal arms no job.

Evidence: [November 11 measurement](../protocol/week-5-execution.md#november-11-whole-prefix-review-and-scc-access-blocker),
[call-graph audit](../protocol/week-5-capacity-validation-audit.md),
[ADR0007](0007-safe-validation-reuse-and-stage-capacity.md), and
[ADR0011](0011-validator-runtime-correction.md).
