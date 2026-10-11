# V3 report template before selection

This implements the reporting requirements in Section 6 of the canonical
[v3 plan](../../plan/research-plan.v3.md) and
[ADR0006](../decisions/0006-v3-execution-completion-amendment.md). It records no
scientific results or stage authorization. Freeze this document together with
the admitted analysis/report implementation before selection and recheck the
bindings before opening.

The report accepts exactly the 180 authorized final cells: three recipes,
three seeds, ten conditions and two query definitions. It revalidates locks,
input hashes, sample order, paired frozen encoder/cache lineage and every
retained query rank against deterministic retrieval before deriving results.
Development, engineering and partial matrices cannot support the final claim.

The primary aggregate table reports contextual and contrastive clean top-1,
mean corrupted top-1, drop, and contextual-minus-contrastive differences in
percentage points, with the Delta interval beside the drop difference. It
verifies `Delta = clean accuracy gap - mean corrupted accuracy gap`. One
percentage point corresponds to ten correct retrievals per 1,000 queries;
this descriptive scale supplies no practical-effect or equivalence threshold.

| Interval and absolute corrupted difference | Interpretation |
| --- | --- |
| Upper bound below zero; corrupted difference positive | Evidence of smaller degradation; higher corrupted accuracy is descriptive. |
| Upper bound below zero; corrupted difference zero or negative | Evidence of smaller degradation without higher absolute corrupted accuracy. |
| Interval includes zero | Inconclusive for the declared claim; not evidence of equivalence or no effect. |
| Lower bound above zero | Results favor greater contextual degradation under this mixture. |

The interval is conditional on trained heads, seeds, actions, anchors, query
definitions and realized synthetic corruptions. Performance groups are assumed
exchangeable within each fixed action; repeated performances from the same
person can remain dependent. It gives no population uncertainty over arbitrary
seeds, actions, participants, anchors or natural camera errors. Display this
caveat beside the interval. The comparison is between complete recipes and
cannot isolate contextual neighborhoods from margins and regularization.

Retain every cell and all three seed effects. The 20 leave-one-action-out
effects remove query observations only and retain all anchors and original
ranks; their range and sign changes are descriptive. SupCon, official queries,
per-cell differences and sensitivities add no superiority tests.

Before selection, use `metadata_dependence_table_v3` from
`pose_embed.evaluation.analysis` on development query-manifest identifiers.
Before opening, repeat for the permitted novel query metadata. Bind each
immutable output to its manifest hash, query definition and admitted release.
The table contains each action's query count, performance-group count, view-count
distribution, distinct performers and largest performer's share of groups.
This function reads no poses and identifies no individual in its output. The
final report retains the primary table in `primary-analysis.json`; the metadata
summary documents residual dependence without changing the resampling unit.
