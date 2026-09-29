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

## Measured SCC state and remaining work

The September 29 remote tmux audit reconfirmed historical SCC job `7761714`
finished with `failed=0`, `exit_status=0`. Its two complete auxiliary caches
and three development caches remain preserved. The repeatability report hash
was `7cfdc738ccded6a371ab3739e9941b90359c0127bb1dd6a1e8a4a5dbb78cd214` and
parity report hash was
`837aa87f25e50347c027ae32b66cedaf28d14378a4d3324fd8eed46c74c0214a`.
The correct v1/v2 opening ledgers were absent in the canonical and historical
home artifact roots at 17:41 UTC. This observation is not a complete v3
historical-root registration or a later opening authorization.

The remote connection then ended. V3 root registration, real auxiliary
packaging/fallback measurement and the resolved design freeze have **not**
run on SCC. They must succeed before Week 4 cache extraction. No v3 GPU
result, parity result, cache or pilot is claimed in this record.

The last project-quota snapshot had 271.50 GB free, versus a 314.7484 GB
initial full-campaign gate: a 43.2484 GB shortfall. This is a changing shared
quota and needs a fresh reading. The bounded Week 4 jobs enforce their own
smaller increment plus the fixed reserve; passing that check does not pass
the October full-campaign gate.

Actual researcher time and the weekly availability calendar remain unreported.
Do not invent minutes or close the week on the strength of historical gates.
Weeks 1–2 remain unchanged; their recorded zero-minute closures are not proof
that no work occurred.

## Cleanup and handoff

The active README and launch instructions now point to v3. Obsolete v2 campaign
directions have been removed from the current runbook. Historical protocols,
code, evidence, source licenses and hash-bound configurations remain available
for reproducibility and shared seal enforcement. All 41 superseded local files
were hash-verified into a private recoverable archive and Git stash before
clearing the old draft/work-in-progress from the active checkout. The local
main checkout was then advanced from `c60c0fe` to the published v3 plan.

The public tracker must retain historical completed tasks while distinguishing
verified v3 software from pending SCC preparation. Formal Week 3 completion
requires the pending preparation evidence and actual time record.
The additional tasks use zero estimate minutes as an unestimated placeholder,
not a claim that the work takes no time.

## Release verification

- Full Python suite: **1,012 passed**, no skips, in 137.72 seconds, including
  the pinned MotionBERT and licensed AVSL oracle fixtures. This is local CPU
  software verification, not a new SCC or GPU result.
- Ruff lint and all-file format checks; workspace verification; locked Python
  environment synchronization; both launcher shell syntax checks passed.
- Tracker: 21 tests, lint, TypeScript and production build passed.
- Clean local database reset, all 222 database assertions, and local security
  advisors passed. The new migration's 28 assertions cover unchanged history,
  ownership, concurrency conflicts, idempotence and closed-week protection.
- The historical v1 protocol digest remains
  `c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.

The hosted security advisor still reports the pre-existing Auth configuration
warnings for leaked-password protection and available MFA methods. The readiness
update changes no Auth, ownership, grant or RLS settings.
