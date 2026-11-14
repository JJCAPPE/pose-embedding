# 0013 — Qualify the Week 5 runtime on SCC kernel 553.184.2

Date: 2026-11-14. Status: **researcher-authorized, result-blind runtime amendment.**

The researcher approved bounded qualification of kernel
`4.18.0-553.184.2.el8_10.x86_64` for the current Week 5 work. This changes only
`profile.runtime.platform` in the complete accepted CPU 8561360 profile, from
`Linux-4.18.0-553.182.1.el8_10.x86_64-x86_64-with-glibc2.28` to
`Linux-4.18.0-553.184.2.el8_10.x86_64-x86_64-with-glibc2.28`. Every other profile
field must match. This is an exact candidate, not a kernel allowlist or a claim
of numerical equivalence.

Job 8616892 stopped at the startup runtime gate before its admission controller
ran. The corrected `CUBLAS_WORKSPACE_CONFIG=:4096:8` setting matched the accepted
profile; independent review found only the kernel difference. No measurement
operation or admission timing was produced. The retained startup record,
`study-v3/operations/week5-runtime-minimal-admission/20261114T124944Z/runtime.json`,
has SHA-256 `4dd9e9ed3610b83db35f674af8b15f4bff7ab8cf59ce19a3bbde726d97149302`.
Terminal accounting has SHA-256
`a23371ecb20b79d290c6704938811c49165d5af041bf5f3b3994700309606ce4`.
The independent review accepts the failure diagnosis only; its SHA-256 is
`0f4da44d5ef390754287df51c5da8934cb4d7c858355fd572a308e3a66300873`.

Derive a new immutable candidate from accepted CPU 8561360's full profile record,
`study-v3/operations/week5-r2-launches/20261110T185424Z/runtime-profile-8561360.json`,
SHA-256 `a2d8eac846e712081eed731c9898c88e33f121398965e24924e1379d80ca197e`.
Preserve that accepted record. Freeze and independently review the complete new
profile and amendment bindings through the existing external correction path
before numerical comparisons. Require the full profile before and after each
affected allocation; the previously approved GPU-only build-report expansion is
not broadened.

Qualification proceeds in dependency order:

1. In an allocation, run three fresh CPU initializations for each seed 7/17/29
   and two complete geometry processes on the original 43 panel IDs, retaining
   all 430 tensor-comparison requirements. Keep the original fallback, identities,
   ordered manifests, algorithms, existing historical scientific-equality checks
   and numerical tolerances. Preserve exact fresh-process repeatability and
   initialization/batch pairing; a mismatch blocks qualification.
2. Independently accept the CPU accounting, exact commands, fresh-process results,
   complete runtime/source/input bindings, resource records and before/after
   seals before relying on this profile. Scheduler exit alone is insufficient.
3. Retain the required GPU qualification. Repeat only the existing fixed
   48-sample, all-12-layer parity check if the actual changed runtime or computation
   path lacks accepted coverage. Record that coverage decision and its bindings;
   do not claim an old profile's result as a new-profile result.
4. After accepted qualification, continue the existing single corrected
   admission-prefix measurement. Use its independently accepted timing in the
   existing complete capacity model before genuine admission issuance. Do not
   repeat the old three-pass campaign or invent downstream records for timing.

[ADR0012](0012-bounded-validation-scope.md) remains the controlling validation
policy. Preserve accepted historical caches, pilots, development evidence,
timing and their original producer/source/runtime provenance. This amendment
does not require their regeneration, a whole-history adoption campaign or a
second full Week 5 recertification. Keep the complete issuer checks, initial
opening safeguards and one independent final verification of all 180 cells and
the report/bootstrap. A failed comparison blocks the affected qualification;
it never silently becomes a new expected result.

Preserve frozen source `f101f0e9d9bd64275d2088deab1b0bdcfcc53620`, the separately
reviewed validator, r2 protocol
`18f7d17fa81e7ae3a6b1e5deddf42d9eda589d96e5a13968188a8ce275bfb95f` and design
`7750452c1110412dc0ccb5fb147018310f056b58d403f7267a7d9fe64bc64744`.
Dependencies, actual Gold-6426Y/Sapphire Rapids CPU, native AVX512, four numerical
threads and the L40S target remain fixed. Refresh required source, identity,
authorization, seals, duplicate-attempt, storage, memory and calendar checks
before allocation. Preserve every attempt and manifest, the 200 GiB reserve,
25% capacity margin and researcher-confirmed availability; actual hours remain
unreported.

All three recipes, three paired seeds, physical P=8/K=4 batches, 20 epochs,
27 selection slots, nine final heads, corruptions, metrics and claim rules remain
fixed. November 29 final locks, December 6 compute and December 7–18 delivery
remain binding. This authorizes bounded runtime qualification and subsequent
already-authorized prerequisites only. It grants no runtime acceptance, capacity
pass, selection runs, final training, novel opening or Week 5 closure. The two
historical non-progressing libm diagnostics remain stopped. Use one SCC controller
and the existing completion watcher for any authorized submitted job; keep the
legacy automation paused.

Evidence and governing records: [Week 5 execution](../protocol/week-5-execution.md),
[ADR0010](0010-kernel-182-baseline.md),
[ADR0011](0011-validator-runtime-correction.md),
[ADR0012](0012-bounded-validation-scope.md), and the
[canonical plan](../../plan/research-plan.v3.md).

