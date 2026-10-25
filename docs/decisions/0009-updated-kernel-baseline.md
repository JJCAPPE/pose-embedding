# 0009: Regenerate Week 5 evidence under the updated kernel

Date: 2026-10-25. Status: **researcher-authorized result-blind amendment;
new runtime acceptance and scientific regeneration remain pending**.

The researcher explicitly authorized the updated-kernel amendment and rerunning
all affected baseline, cache, pilot and admission validations. This follows
[ADR0008](0008-runtime-baseline.md) and the
[verified October 25 failure](../protocol/week-5-execution.md#october-25-targeted-pilot-failure-confirmed-after-access-restoration).
It authorizes prospective baseline verification and the existing Week 5 inventory
after required preflights, not learning-rate selection, final training, novel
opening or Week 5 closure.

## Evidence and bounded change

The accepted baseline records kernel `4.18.0-553.172.1.el8_10.x86_64`. Pilot
attempts **8272259** on `scc-j08` and **8272752** on the requested `scc-j01`
instead observed `4.18.0-553.177.1.el8_10.x86_64`; both failed the unchanged
startup gate before the scientific child. Their complete observed profiles
agree. Apart from the kernel, the only raw difference from the accepted CPU
profile is the already-approved conditional GPU build-report expansion.
The targeted retry used four OMP slots and failed after 29 scheduler seconds.
Its terminal review verified 988 metadata and 616 source bindings and fresh
sealed state, receipt SHA-256
`7df8b7ab15dce8d318f3006eb9708c465e76c55ab023ca1ae7569bb00b8c3163`.

This evidence establishes a runtime availability problem on the observed hosts,
not numerical equivalence between kernels or cluster-wide unavailability.
The decision uses infrastructure and reproducibility evidence, not new pilot
accuracy or novel outcomes. No scientific result is accepted by this amendment.

## Prospective profile and acceptance

1. Record and freeze one complete prospective profile with kernel
   `4.18.0-553.177.1.el8_10.x86_64`, actual Sapphire Rapids **Gold-6426Y**, native
   **AVX512**, **four numerical threads**, and the existing **L40S** GPU target.
   Bind actual hardware/dispatch, interpreter, packages, loaded numerical-library
   hashes and deterministic settings. The sole authorized CPU profile difference
   is the kernel component of `runtime.platform`; every other profile field must
   exactly match the prior accepted baseline
   `d250509286515a1c3e8adaf10d62946c12d58525baa32c75c7adf8998f9d9bc5`.
   Verify the complete profile in every
   allocation, including the existing before/after checks. A scheduler selector
   is not proof of actual hardware. Retain only the previously reviewed exact
   CPU/GPU report-expansion handling; do not normalize away kernel changes,
   broaden an allowlist or treat the old baseline as the new one.
2. Preserve scientific source **f101f0e9d9bd64275d2088deab1b0bdcfcc53620**, the
   existing execution-r2 protocol/design locks, configuration and dependency
   lock. Bind this amendment, the new immutable runtime record and fresh attempts
   through the existing reviewed external operational inputs. Review any
   necessary external correction before use. No new control framework or core
   source/dependency change is authorized; a required core change must use the
   existing separate immutable revision/correction path.
3. Before dependent work, independently accept fresh initialization and geometry
   evidence under the new profile: three fresh initialization processes for each
   seed **7/17/29**, and two complete fixed-panel processes with exact agreement
   across **430 tensors** and damage records. Retain the original **43 panel IDs**,
   ordered manifests and training-only fallback **0.6601371765136719** with its
   original measurement. Do not reselect IDs, recompute the fallback or require
   new runtime-derived values to equal the old baseline. Record differences;
   exact repeatability and paired initialization/batches within the new profile
   remain mandatory.
4. Rerun and independently validate the source-bound synthetic GPU prerequisite,
   parity and **all five clean caches**, including the two fresh-process
   **95,001-row** extractions. Then complete all three paired **20-epoch** pilots,
   their 1,000-update wiring fixtures, epoch-zero diagnostics, epoch 5/10/15/20
   checkpoints/full scores and allocated independent numerical replay. Preserve
   every tolerance, exact update count and physical **P=8/K=4** batch pairing.
5. Regenerate all nine development corruption encodings, 27 query projections,
   three gallery projections and 27 retrieval results with full damage/fallback
   telemetry. Complete affected fixture/report/access-boundary checks, fresh
   resident and whole-job timing, full admission replay, independent
   recertification and measured **schema-2 CPU/GPU/storage/researcher capacity**.
   No prior timing or accepted cache substitutes for new-profile evidence.

Accepted installation, setup and rehearsal remain valid only where their bound
inputs, including applicable runtime inputs, are unchanged. Rerun every affected
check and refresh all required identity, authorization, source, data-seal,
duplicate-job, storage/quota, RAM/GPU and calendar checks before allocations.
Scientific arrays, checkpoint/cache hashing and numerical replay remain
allocation-only. Reuse the existing commands, one SCC controller, common locks
and one scientific subprocess.

## Retention, capacity and unchanged boundaries

Keep the old baseline, its accepted initialization/geometry/GPU/cache evidence,
both failed pilot attempts and every earlier artifact immutable and correctly
labeled. Use new attempt paths and receipts; do not overwrite sidecars, relabel
old caches or mix the two profiles in the admitted campaign. The old five-cache
acceptance remains historical evidence for its original inputs.

Refresh the source-derived retained/remaining storage forecast for the complete
new regeneration. Existing artifacts already reduce free space; count each once
and include all future outputs, failures and temporary peaks. Require
`min(filesystem_free_bytes, quota_remaining_bytes) >= 200*2**30 + 1.25*remaining_peak_bytes`.
Do not reuse a predecessor remaining bound without a new evidence-bound
reconciliation or delete evidence to make space. Renew CPU/GPU/researcher forecasts
with queue/setup, independent recertification and at least 25% slack. Preserve
**November 29** final locks, **December 6** compute and **December 7–18** delivery.
Actual researcher hours and successful capacity are not inferred.

All algorithms, seed derivation, recipes, float32 arithmetic, fixed panel/fallback,
dataset roles, corruption definitions, metrics, bootstrap, claim rule and
licensing/access safeguards remain unchanged. The comparison is the full
contextual recipe versus standard contrastive, with SupCon descriptive. All
nine final heads must eventually be trained and locked before novel opening;
this amendment authorizes none of those later stages.

Historical non-progress diagnostics **8104416/8135335 remain two and stopped**.
The kernel-availability line retains its one unsuccessful but narrowing targeted
retry; this amendment does not erase either history or resume the libm inquiry.
Apply the stopping rule to subsequent blockers. Authorization alone passes no
task, gate or measured admission and does not authorize website closure.
