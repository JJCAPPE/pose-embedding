# 0006: Complete the v3 execution path before selection

Date: 2026-10-09. Status: adopted planning amendment at the researcher's
direction; implementation, revalidation and publication remain pending.

The researcher requested amendments to the upcoming research plan, informed by
the base paper and ML evidence. This decision adopts the execution and reporting
specifications in [the canonical plan](../../plan/research-plan.v3.md), following
the [review](../protocol/upcoming-research-review-2026-10-09.md) and
[primary-source research](../protocol/upcoming-amendment-source-research-2026-10-09.md).
No pilot accuracy values or novel outcomes informed this amendment.

## Decisions and reasons

1. Keep the scientific comparison, recipes, physical P=8/K=4 batches, three
   seeds, finite learning-rate grid, 20 epochs, data identities, fixed fallback,
   corruptions, primary analysis and claim rule. Liao et al.'s Appendix G and
   H.5 support the recipe/margin provenance; MotionBERT Section 4.6/Table 4
   supports frozen-backbone transfer. Neither establishes optimal pose settings
   or a smallest useful effect. Do not add a new arm or search dimension.
2. Complete authorization, final training, novel extraction, evaluation and
   actual v3 report dispatch in one successor release before selection. Current
   guards and fixed lock paths prevent those stages, and affected files are
   frozen. Use `study-v3/revisions/execution-r1/` beneath the existing canonical
   root, with new immutable provenance and a full predecessor/successor binding.
   Preserve the single shared dataset seal. No lock path is created or changed
   by this planning amendment.
3. Revalidate fresh parity, all five clean caches and all three complete pilots
   under the successor release. Preserve original evidence and Week 4 closure.
   This deliberate additional work avoids a cross-release adoption mechanism
   and prevents relabeling artifacts. Reuse original identity/fallback evidence
   only through validated bindings; never select it again from new data.
4. Freeze a deterministic 40–48-row development geometry panel, supplement
   missing edge categories with fixtures, and collect damage/fallback telemetry
   over all development queries. The panel size is an engineering coverage
   choice, not a statistical-power claim. No geometry criterion uses accuracy.
5. Test the complete fixture-to-report path before selection and repeat an
   independent audit before opening. Publish clean/corrupted accuracy, drop,
   Delta/interval and their algebraic consistency together. A zero-crossing
   interval is inconclusive, not equivalence. Report effect magnitude without
   inventing a practical threshold, and retain conditional/full-recipe claims.
6. Freeze objective failure categories, exact attempt/retry lineage and full
   selection tables before ranking. Preserve equal attempted budgets, existing
   tie-breaks and all failed attempts.
7. Reuse each encoder output across heads and run one validated scientific
   subprocess at a time initially. Measure CPU/I/O and all remaining stages
   before changing execution. Keep float32 arithmetic, physical batches and
   integrity checks. The provisional head/revalidation allocation estimate is
   8.69 hours including 25% slack, with extraction/validation/queues and human
   work still additional. Itemize the omitted development projections and
   successor artifacts in a 120 GB campaign-wide envelope. Admission always
   uses current remaining peak bytes and the 200 GiB reserve, not that envelope
   as a new deduction from current free space.

## Binding and chronology

The scientific config/code and real lock files are unchanged by this decision.
The future successor digest will change when revision/provenance bindings do;
compare scientific fields explicitly before admission. Keep original release
`2897f4fe4c1fb1857432a0e92a7391dde68307f5`, locks and receipts unchanged. Within
the admitted successor campaign its digest stays fixed through selection and
opening. A scientific difference requires its own explicit amendment.

Sections 5–10 of the plan, the machine-readable plan and Week 5 handoff now
specify the work. Preserve ADR0004/0005, prior plans, closed weeks, historical
source links, evidence, actual minutes and the final prospectus. No stage is
newly complete; no selection, final training or test opening is authorized by
this document. October 18 remains a measured go/no-go gate. Any live publication
must update the fallback and guarded open-week rows together, preserving the
production source and all unrelated Journey work.

## Repository verification

On October 9, workspace verification, diff checks, tracker lint/typecheck, all
22 tracker tests and the production build passed using Node 24 and existing
dependencies. The bundled public plan matches its Markdown source exactly.
An explicit comparison with the predecessor verified unchanged Weeks 1–4,
existing sources/links, progress, versions, dates and recorded time, and unchanged
scientific source/configuration and dependency locks. Future tasks/gates remain
pending. The system pnpm wrapper attempted an unnecessary dependency refresh;
its noninteractive refusal was avoided by running the existing scripts directly
under Node 24, without installing or changing dependencies.

This verification covers the repository amendment. No live database migration,
deployment, SCC resource measurement, experiment or scientific-lock change was
performed. The source research and engineering estimates are not admission
evidence for the future completion release.
