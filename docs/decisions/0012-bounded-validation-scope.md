# 0012 — Minimum validation for the frozen study

Date: 2026-11-11. Status: **researcher-authorized, result-blind engineering amendment.**

The researcher authorized the smallest defensible validation scope and delegated
its design and implementation. This supersedes the earlier, unadopted proposal
for two complete audits of every evidence set. No further scope approval is
required for the bounded implementation and qualification below. Scientific
execution still follows the dependency order and current access/resource gates.

## Problem

The old post-opening call graph performs 2,054 historical admission invocations
inside 392 commands. At C=1372.9295508799842 and R=1190.5385979909915 seconds,
`(392*C + 1662*R)*1.25/3600 = 873.910949` hours. This is projected serial
validation overhead in the November 30–December 6 window, not remaining Week 5
time or training time. The actual measurement job took 66.4 minutes. Its timed
passes were parser-warm; this is a profile-specific forecast, not a universal
runtime bound. Other work was excluded.

Reading authorization repeatedly reran pilots, development evidence, selection
runs, final-head checks and manifest reconstruction. Command-local numerical
caching did not remove those outer audits. The correction separates issuing an
acceptance record from subsequently consuming that record.

## Minimum retained checks

1. **Keep accepted historical evidence.** Preserve its original producer, source,
   runtime, paths and hashes. Do not regenerate caches/pilots or require a new
   artifact-by-artifact adoption campaign merely because the validator or current
   system libraries changed. Never relabel old evidence as new-runtime evidence.
2. **Check new computations once.** Qualify the remaining GPU path with the
   existing fixed 48-sample, all-12-layer parity check. Reuse accepted CPU
   initialization/geometry qualification 8561360. Add one compact development
   projection/retrieval comparison only if accepted evidence does not cover the
   changed path. Do not repeat all five caches, three pilots or nine development
   corruptions to establish the same implementation property.
3. **Keep one complete issuer check.** The existing full admission validator runs
   when issuing selection authorization, and complete selection validation runs
   when locking the selected configurations. These existing checks provide the
   trust anchor without a new certificate system. Remove the separate second
   full Week 5 recertification requirement. All 27 planned selection slots and
   every attempt remain accounted for; failed/ineligible slots follow the
   existing rules, with an eligible three-seed candidate required per method.
4. **Make consumers check their own inputs.** Reuse the existing immutable
   authorization, selected-config, final-run and protocol-lock records. Parse
   them freshly, verify direct bound file contents, canonical paths, protocol,
   source, role and chronology. Selection reads retain the hashed outcome →
   manifest/metrics → epoch record chain, complete attempt/retry inventory,
   pairing and deterministic winner. They do not replay historical numerical
   checks or walk every unused ancestor. Every producer still checks its actual
   input/output bytes, identity/order, configuration, finite values and completion.
5. **Keep initial opening complete.** Before the first novel loader, retain the
   source-manifest audit, all nine head checks, fixed lock cross-bindings, fresh
   capacity, dataset seals and atomic opening record. Later consumers verify
   the existing opening and their actual input bindings. Current permissions,
   resources and applicable timestamps remain fresh; historical evidence grants
   no new permission.
6. **Verify the final scientific answer independently once.** Recompute all 180
   cells' ranks and metrics from retained embeddings, and rederive the report
   and prescribed paired bootstrap in a fresh process. Report construction
   retains provenance/matrix checks but does not perform another retrieval
   replay before that independent check. Saved rank summaries alone are
   insufficient. No final scientific acceptance or publication precedes this
   independent verification.

This explicitly supersedes ADR0007's requirement for fresh whole validators on
consumer reads and full historical transitive rehash on every nested reuse. It
extends ADR0011's metadata-only correction scope and removes its mandatory
whole-history re-adoption and second complete recertification. The existing
numerical proof store may remain command-local; no generic persisted cache,
new certificate format, snapshot service or stage-audit framework is required.

Trust is in records issued by the reviewed write-once functions under controlled
storage. Hashes detect changes against their bound records; they do not
authenticate an actor who can replace every root record and its hashes. Changes
to unused historical ancestors need not be detected on every later read.
Directly consumed evidence, newly issued records and irreversible access retain
the checks above. Changed scientific inputs or algorithms invalidate affected
results; the amendment is not permission to conceal failed comparisons.

## Implementation and qualification

Preserve frozen producer releases and r2 locks. Freeze the corrected validator
separately and extend the reviewed producer/validator binding mechanism to its
changed files. Producer provenance remains checked against the original source;
record current execution identity separately. Preserve historical cache parity
paths rather than substituting a new-runtime report into old sidecars.

Use focused synthetic tests for changed behavior: issuer-versus-consumer calls,
changed direct hashes and bound selection metadata, complete attempts and
eligibility, lock/role/chronology rejection, and pre-loader opening guards.
Keep the independent numerical metric-forgery check. Run required release/CI
checks once after the final code changes; retain historical tests without
repeatedly scheduling unchanged suites in SCC.

Resolve the stopped measurement receipt from existing accounting and metadata;
no repeated measurement is needed for bookkeeping. A terminal metadata-only
acceptance writer may observe unopened seals before and after its work without
holding the scientific dataset lock, provided it reads no scientific arrays,
retains exact bindings, and cannot authorize admission, adoption or opening.
Scientific operations retain the dataset lock unchanged.

Use the existing parity helper's bounded parity-only path and existing runtime
gate for the one remaining GPU qualification. Measure the corrected consumer
path and relevant remaining work in allocations; local tests establish behavior,
not SCC throughput. Reuse the existing capacity model with the corrected call
graph. The former 873.911-hour estimate no longer describes that graph; no new
runtime total is claimed until measured. The earlier 16.8-hour figure was an
engineering target, not an additional gate or a measured forecast.

Retain the full study: three methods, three paired seeds, 20 epochs, 27 planned
selection slots, nine final heads, all query definitions/corruptions and 180
cells. Numerical tolerances, metrics, claim rules, the 200 GiB reserve, 25%
capacity margin and fixed November 29/December 6/December 7–18 deadlines remain.
Selection runs, final training and novel opening are not authorized by this
Week 5 engineering amendment. The legacy Codex automation remains paused;
future authorized jobs use the single completion watcher in the current runbook.

Evidence: [measurement and execution record](../protocol/week-5-execution.md),
[historical call graph](../protocol/week-5-capacity-validation-audit.md),
[ADR0007](0007-safe-validation-reuse-and-stage-capacity.md), and
[ADR0011](0011-validator-runtime-correction.md).
