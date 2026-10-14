# 0007: Safe validation reuse and separate CPU/GPU capacity

Date: 2026-10-12. Status: researcher-authorized result-blind engineering
amendment. The implementation passed independent review and the stable full local
suite (1,373 passed; two historical AVSL source-parity skips). The separate SCC
installation and allocated rehearsal 8044010 passed independent completion
review (128 checks, no failures or skips). Preparation 8045152 also passed
independent review of its accounting, commands, resources, seals, eight original
manifest identities and original → r1 → r2 scientific equality. Scientific
regeneration and measured admission remain pending. Supplementary checks
8048540 passed independent completion review (86 executed checks, both seals
and reproduced metadata-only dependence tables); this grants no scientific
admission. Geometry job 8070391 passed its tracked checker and exact
within-revision repeats but failed the wrapper fixed-identity check
(229 scheduler seconds; exit_status=1). Its unchanged IDs/manifests and
differing scalar/jitter hashes require a separate diagnostic; CPU dispatch
was an untested recovery hypothesis at that checkpoint. Diagnostic job 8072666 was submitted October 13 at
22:49:45.058490 UTC after 127 local checks passed and initially observed queued
at 22:52:26.185888 UTC. The scheduled 8:00 PM EDT check was not executed after
SSH disconnected. After access was restored, the October 14 inspection at
19:40:13.233256–19:40:25.519918 UTC found wrapper failure before the parent:
neuro-pub@scc-h32, four OMP slots, two scheduler seconds, failed=0/exit_status=1.
Independent metadata-only review verified zero operation/resource/worker outputs;
receipt SHA-256 `c9e2d25740334923a537c36c82b0d2574f6b90a74b7d45ebf26ddc0c3aac371d`.
No CPU capability comparison ran in job 8072666 and the geometry cause remains unproven.
A separate reviewed operational remedy passed 64 focused checks and was staged
at 20:08:33.599282 UTC in new immutable tools, preserving the parent/worker,
source, scientific settings and tolerances. Tools manifest SHA-256
`c6404952ea81aa28b04c2603b6b4b7190cc85c1c759ff08410ee2dd7f63c1d77`; packet SHA-256
`32289c531a0330f93dad42b7974022181eb494d775d6b70825a80a7a1877d716`.
At the staged checkpoint the launcher had not been executed; the earlier
4:41 PM EDT launch/check boundary remains historical. The new guarded launcher
executed once and diagnostic remedy job 8102231 was submitted October 14 at
20:43:11.969137 UTC. Launch SHA-256
`82427510eb77a8bc0875753d343783a1e9a383f05bef736aa2c01654ee4037f2`. Independent submission review
at 20:50:34.444145 UTC verified 763 metadata/616 source bindings, the intent,
packet/command and both launch seals; receipt SHA-256
`63aa23c6e514f9cd1757021354fa1262b8f48f89af10e8a8015259e885dbb471`.
The fresh diagnostic-only quota/free-space reserve passed; this is not campaign
capacity. At the submitted-only checkpoint no post-submission state or result had been
observed; the earlier 5:45 PM EDT first-check boundary is historical.
The October 14 inspection at 22:25:31–22:25:43 UTC found completed job 8102231,
completed at 20:49:21.682189 UTC: neuro-pub@scc-ke1.scc.bu.edu, four OMP slots,
failed=0/exit_status=0, 17 whole-job CPU wall seconds and 9.340 actual CPU seconds.
Independent review at 22:34:10.047781–22:34:14.167272 UTC verified both seals,
worker commands, dispatch, final wrapper marker, six resource records and
184 artifact/617 external/616 source bindings; accepted receipt SHA-256
`f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36`.
The four-case recovery hypothesis is unsupported: native AVX512 matched all
failed-fresh scales/hashes/rows; DEFAULT restored the four original scales but
only 36/40 hashes and 32/36 rows. Four jitter hash/damage-row differences across
two cases remain. This establishes neither the complete cause nor a permanent profile.
The original completion verifier rejected only the scheduler's QUEUE form and
produced no accepted receipt; that failure and source remain preserved.
The independently reviewed replacement accepts bare or exact qualified queue
forms while independently checking the host and retaining every other check;
93 tests, Ruff/format and review passed. Geometry, all dependent stages, full
allocated A/corruption replay, scientific admission and measured CPU/GPU capacity
remain held. At the October 14 completion checkpoint no further profile, helper or job had
been claimed; the earlier 7:27 PM EDT scheduler/preflight boundary is historical.
Separate libm tools were staged at 23:26:33.802337 UTC after 173 checks and
independent review. Tools SHA-256
`90c9336085f01d6b423a04a6087aff381b1527952cc86bea57e67c3cefd43093`; input SHA-256
`1d6ea033970b2b1b49ca6548180e5e6e5f8c097cb722a2466db49b4809d4a4ff`.
The new guarded launcher executed once: job 8104416 was submitted October 14
at 23:29:21.658353 UTC; launch SHA-256
`03fa95ee91fb6c6686b792e111d3033bef8af8e5a12cca740be813023c87caf5`.
Independent submission review at 23:34:29.161902 UTC verified 815 metadata and
616 source bindings, intent/source/tools/input/command and both launch seals;
receipt SHA-256 `0b6a6e05b49bd698cc4d0d317d5142d319d3ec6a5677448e0b90803e19938b33`.
Fresh quota/free reserve passed: 67,667,170 bytes rounded to 1 GiB, with no
archive or runtime ELF output copies; this is not campaign capacity.
The four-case DEFAULT control versus DEFAULT plus version-appropriate libc/libm
FMA-disable request requires allocated runtime/ELF/function-dispatch proof before
interpreting numerical metadata. No permanent profile or full cause is established;
the accepted 8102231 negative result and all failures remain preserved.
Geometry, all dependent scientific/replay/capacity gates and all Week 6 selection,
final training and novel opening remain held. Pre-submit qstat completed at
23:29:20.793929 UTC; no post-submit state or result has been observed.
First permitted observation: October 14 at 8:31 PM EDT (October 15, 00:31 UTC),
under hourly polling. Never rerun any executed launcher.

The researcher explicitly approved a result-blind amendment for safe validation
reuse and separate CPU/GPU time accounting, preserving all scientific checks and
budgets. This decision records that authorization. It follows
[ADR0004](0004-frozen-one-shot-v3.md),
[ADR0006](0006-v3-execution-completion-amendment.md) and the
[measured capacity audit](../protocol/week-5-capacity-validation-audit.md).
It authorizes the bounded engineering work below, not selection, final training,
novel opening or weekly closure. The decision uses execution costs and validation
structure; neither pilot accuracy nor novel outcomes determine the change.

## Evidence and reason

Immutable release `731938a157be575ee433d6939876f8ca0b95e459` repeatedly runs
complete nested validators. On October 12, allocated job 8038699 passed the
three unchanged pilot-validator calls in Contextual, Contrastive, SupCon order:
266.80653271399206, 256.6426796570304 and 254.82488820399158 seconds. Their
sum, **P = 778.274100575014 seconds**, excludes setup and the native-initialization
fixture. Independent completion review verified 1,276 metadata bindings, two
commands, 17 resource samples, both seals, native runtime/call order and successful
836-second scheduler accounting. Its passed receipt was written at
19:32:11.651357 UTC:

- Artifact-relative receipt:
  `study-v3/operations/week5-p-component-verification/20261012T193150Z/verification.json`.
- SHA-256: `cd21652427c8918473b97ec7a58a31db4ebd3e94b5582f6c65f8912f9e898c9b`.

The prior call graph's largest indivisible report contains `452F + 18V`, with
P inside each F. At the measured profile, `452P * 1.25` forecasts 122.145796
hours before other work. The former shared maximum-job check applies that CPU
report requirement to a GPU opening allocation capped at 48 hours. Its necessary
P threshold is 305.8407079646018 seconds. This is a no-go for the measured
profile, not a universal hardware lower bound or a measurement of full A/F.
Preserve the original source, receipts, forecasts, failed attempts and no-go
record unchanged.

## Authorized validation change

A successor may reuse a successful deterministic numerical validation proof only
within one explicitly scoped command. The first encounter still performs the
complete existing validation. Repeated use must establish the exact same
validator, arguments/options, role, protocol/design/source/runtime bindings and
all transitive input content identities. **Rehash the complete bound file
contents on every reuse.** File size, mtime, inode or an unchanged path alone is
not proof. No hash, identity, shape, pairing, numerical tolerance or acceptance
criterion may be omitted or relaxed.

The initial implementation restricts reuse to pilot saved-snapshot numerical
replay and trained-feature projection equality. Whole validators remain fresh.
Recheck committed dependencies before publishing an output and at command exit;
independent commands, processes, threads and asynchronous tasks cannot inherit
proof authority from another execution context.

The implementation must separate this numerical proof from dynamic decisions.
Dataset seal/opening state, authorization and timestamps, attempt/selection
inventory, locks, current allocation/resources and calendar availability are
checked freshly where required. A cached numerical result cannot authorize a
loader, an opening, a state transition, an attempt omission or a resource claim.
Only completed successful checks can enter the command-local store. Exceptions,
partial results and in-progress recursion cannot become successful proofs.
Store only successful numerical proof markers, not mutable result objects.
Caller changes to metadata/options must invalidate reuse. End the store with
its command, including on failure; no disk cache,
cross-command trust, cross-process proof or persisted boolean is authorized.

The mutation model includes changed, replaced, missing or escaping dependencies,
changed metadata/options and content edits that preserve size or mtime. Reuse
must fail closed or perform complete validation when any required identity no
longer matches; it must not return a stale success. Retain the shared access lock,
immutable artifact writers and content/provenance checks. This is an optimization
for controlled immutable inputs, not a substitute for filesystem isolation from
an untrusted writer. Tests must cover transitive dependencies and caller input mutation,
not only direct files. An independent recertification command starts with an
empty store and performs its own complete first validations.

## Authorized capacity change

Use versioned schema-2 capacity evidence with exact CPU/GPU entries for maximum
complete-job duration, remaining pre-opening work and remaining evaluation work.
Every dated allocation window declares its resource class. Reject the old scalar
or unclassified schema as successor admission evidence; do not invent a conversion
or rewrite an old receipt.

Classify the **whole command by its allocation**. CPU hashing, loading, projection,
validation and I/O within a GPU allocation remain part of that GPU job's measured
wall time. Keep CPU-only report and independent-validation jobs in the CPU class.
Do not subtract nested overhead from a GPU job or count it twice in the calendar.
Both classes must fit their complete-job limits and dated windows, with at least
25% compute slack plus queue/setup allowance, global non-overlap and one scientific
subprocess at a time. A future allocation is not a reservation.

At novel opening, compare the fresh allocated GPU job's remaining wall time with
the complete GPU-job requirement, while still requiring sufficient remaining
CPU and GPU evaluation windows and researcher delivery time. Preserve current
RAM/VRAM, storage, source/seal and deadline checks. Final heads/locks remain due
by November 29, compute including report recertification by December 6, with
December 7–18 protected for analysis/delivery. Separate accounting does not move
work outside the calendar or permit overlapping jobs. Five normal researcher
hours weekly, ten when needed and no guaranteed Thanksgiving hours remain
availability bounds; actual time remains unreported by the researcher's request.

## Successor and regeneration inventory

Use `study-v3/revisions/execution-r2/` beneath the existing canonical artifact
root. Bind its predecessor design to execution-r1 and retain the single shared
dataset access lock and opening ledger across all versions. Require a clean
immutable release, locked dependencies, new full source/design/protocol digests,
a reviewed changed-file list and explicit equality of every scientific field.
The original and execution-r1 trees remain intact. No cross-release artifact
adoption, sidecar rewriting or mixed-release campaign is authorized.

| Evidence | Required treatment for execution-r2 |
| --- | --- |
| Licensed sources, verified auxiliary-only container, encoder/upstream pins, source inventory, historical identity and training-only fallback evidence | Retain original bytes and measurements. Revalidate exact hashes and authorized boundaries; bind them explicitly without reselecting IDs or recomputing fallback. |
| Eight role manifests and metadata-dependence tables | Rebind the byte-identical ordered manifests under the successor, compare role/count/order hashes, and reproduce/verify metadata tables against those bindings without novel poses. |
| Original and execution-r1 protocol/design locks, all attempts and no-go evidence | Preserve as historical evidence. Create new immutable successor locks and receipts; none of the old completion labels automatically admits execution-r2. |
| Parity and all five clean caches, including two 95,001-row fresh-process repeats | Regenerate after successor freeze; verify parity, exact repeatability, complete archive contents, bindings, accounting and resource/seal receipts independently. |
| Three engineering pilots and wiring/health evidence | Run all three complete paired 20-epoch, seed-7 pilots with the fixed recipes and full 76,013-row development data; independently revalidate snapshots, numerical replay, exact updates, initialization and ordered batches. Preserve every prior pilot separately. |
| Fixed geometry panel and development corruptions | Retain the pre-score selected panel identity and original fallback. Reproduce its two-process tensors/fixtures under the successor; regenerate all nine full encodings, 27 query projections, three clean gallery projections and 27 results, including full-query damage/fallback telemetry. |
| Software rehearsal, report/analysis and access-boundary evidence | Rerun the complete isolated fixture-to-report path, exact 180-cell checks, tamper/mutation tests, cross-version denial and crash/concurrent opening recovery; verify real opening records remain absent/unchanged. |
| Resident/stage timing, admission and capacity | Measure successor whole commands, residual hashing and numerical reuse, independent recertification, host/GPU peaks and actual bytes. Complete fresh full A and new typed admission/capacity/seal receipts before selection authorization. Old timings remain historical planning inputs. |

The scientific selection matrix remains 27 runs, followed by nine fresh final
heads, all three paired seeds and 20 epochs. Additional engineering regeneration
is retained and counted separately, not substituted for any required run.
The prior 120-decimal-GB planning envelope covered the earlier generations;
prepare a new retained/remaining byte inventory including execution-r2 before
admission. This decision invents no larger numeric envelope or storage pass.
Preserve `available >= 200*2**30 + 1.25*remaining_peak_bytes`, counting existing
artifacts in current free space and only additional peak bytes as remaining work.
Never delete historical evidence to make the successor fit.

## Verification and unchanged scientific safeguards

Before freeze, require cache-disabled versus cache-enabled fixture equivalence,
exact repeated outcomes, fresh independent recertification and rejection of
mutations in every transitive dependency, option, protocol and runtime binding.
Test failed/recursive calls, mutable caller inputs, command teardown and
concurrent/partial opening. Capacity tests must reject missing/misclassified
resource windows, double-counted/overlapping capacity, stale calendars, insufficient
complete-job time, storage/memory failures and unclassified old receipts. Retain
all existing scientific and historical suites; record any justified skip.

SCC execution requires a verified release and scheduler allocation, current
resources/reserve, immutable attempts and periodic resource records. Preserve the
reviewed external GPU controller and measured compatible native CPU checks, or
independently verify their successor before use. Reuse the existing `remote`
session with one operator. The researcher requested
hourly status polling; the in-job periodic resource-recording cadence remains
unchanged.

No recipe, encoder, precision, physical batch, seed, epoch, split, corruption,
metric, bootstrap, claim rule or licensing boundary changes. All nine final
heads must be trained and locked before full novel-opening authorization. A null
or negative result remains valid success. This authorization completes no task
or gate by itself; successor tests, scientific evidence and measured capacity
must pass before the tracker can record completion.
