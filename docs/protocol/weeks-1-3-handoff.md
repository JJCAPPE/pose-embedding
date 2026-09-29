# Weeks 1–3 evidence and handoff

Recorded September 28 and updated September 29, 2026 UTC. This is a status
index for the current [v2 protocol](protocol-v2.md) and
[v2 tracker seed](../../plan/research-plan.v2.json).
It does not change the scientific protocol or authorize novel-test access.

| Week | Verified technical work | Formal state and remaining input |
| --- | --- | --- |
| 1 — protocol and access | All four gates met: adopted hash-bound input contract, verified source inventory, frozen-forward SCC profile, and researcher-confirmed BU determination. See the [remote setup](week-1-remote-setup.md), [input inventory](week-1-input-inventory.md), and [governance record](../compliance/computational-research-scope.md). | Hosted tracker closed September 28 with 0 minutes, although its task note and reflection still say actual time is unreported. Researcher reconciliation is required. |
| 2 — immutable manifests | All four tasks and three gates met: seven hash-bound split manifests, independent byte-identical regeneration, zero forbidden overlaps, and reproducible synchronized-view exclusions. See the [amended manifest audit](ntu-manifest-audit.v2.md). | Hosted tracker closed September 28 with 0 minutes and an empty reflection. Researcher reconciliation is required. |
| 3 — adapter, caches, retrieval | All five tasks and five gates met. SCC job `7761714` passed parity, two byte-identical full final-train extractions, five validated caches, and the 797-test software suite. See the [SCC execution record](week-3-scc-execution.md). | Hosted tracker remains open. Actual researcher minutes are unreported. |

The checked-in seed still shows Weeks 1 and 2 open because it predates those
hosted closures. Its `actualMinutes: 0` represents unreported time; the hosted
zero-minute closures do not establish that zero work occurred. Closed-week edits
require an explicit audited reopen reason, so this handoff records the drift
without rewriting either hosted week. The dataset release agreement is retained
as a [reference copy](../compliance/ntu-rgbd-release-agreement.md);
the acceptance checkbox in [protocol v1](protocol-v1.md) remains unchecked
until the researcher confirms acceptance. BU issuance has already been
researcher-confirmed; the project does not require a public copy of that record.

The guarded September 29 hosted migration updated only Week 3's objective,
deliverable, review prompt, reflection and extraction-gate wording. A read-only
post-migration check confirmed those values and that the hosted Week 1–2 states
and minutes were unchanged.

## What the completed gates establish

The Week 1 A40 physical-batch result is for a **frozen forward pass**. It does
not establish v2 fine-tuning memory. A later priority v2 backward profile
passed on an A100 80 GB and failed with CUDA out of memory on an L40S. The
Week 3 caches and extraction forecast establish the declared Week 3 limits,
not the full 26-configuration training and evaluation budget. The [v2 priority
record](v2-implementation-record.md) and [resource floor](v2-resource-floor.md)
keep these claims separate.

The September 28 Week 3 SCC observation found both novel-test opening ledgers
absent. No Week 1–3 artifact is a final test authorization or a substitute for
the v2 full-roster lock.

## Next decision before the full campaign

Run the already specified complete backward and retrieval capacity profiles
for all 26 configurations, then replace pilot extrapolations with measured
per-method runtime, memory, checkpoint size and an allocation calendar. At the
September 29 02:36 UTC read-only SCC quota check, the shared project area had
293.44 GB free, while even the single-copy encoder-and-optimizer payload for
the planned 1,176 retained runs is 599.27 GB. The [resource calculation](v2-resource-floor.md)
details the larger segmented-run requirement. The complete campaign is a
**storage no-go at that observed quota**. Before launch, document accessible
capacity for the measured forecast plus reserve, or record a result-blind
scientific amendment and revised schedule. Keep existing artifacts and the
novel-test seal intact while making that decision.
