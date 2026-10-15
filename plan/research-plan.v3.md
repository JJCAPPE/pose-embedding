# Final v3 plan: frozen one-shot pose robustness

Original decision: **2026-09-29**. Execution amendments: **2026-10-09** and
**2026-10-12**. Delivery: **2026-12-18**. Status: **final planning
decision; implementation and measured campaign gates remain to be completed**.
This document replaces the v3 draft. [Decision 0004](../docs/decisions/0004-frozen-one-shot-v3.md)
records the change of direction from v2. It does not constitute a final-test
lock, a completed experiment, or a change to the deployed tracker.

The October 9 researcher-authorized amendment adopts the specifications below
before selection or novel opening. Scientific settings remain fixed; completing
currently disabled stages requires a successor execution release and new
provenance bindings. Preserve the September release, Week 4 closure and all
original evidence. Sections 5–10 govern the remaining work; they do not assert
that the new implementation, capacity checks or deployment have happened.

The October 12 researcher-authorized [ADR0007](../docs/decisions/0007-safe-validation-reuse-and-stage-capacity.md)
permits command-local reuse of successful numerical validation with complete
content rehashing, and separate CPU/GPU capacity accounting. It requires a fresh
`execution-r2` release and regeneration. The independently reviewed implementation
passed the stable full local suite: 1,373 tests with two historical AVSL skips.
Source release `f101f0e9d9bd64275d2088deab1b0bdcfcc53620` is frozen and pushed.
The separate SCC installation and allocated CPU rehearsal 8044010 passed
independent completion review: 128 checks, no failures or skips, successful
194-second accounting, nine resource samples and intact seals. Verification
receipt `week5-r2-rehearsal-verification/20261013T002413Z/verification.json` has
SHA-256 `963babe02eba70d34f3f9c9aa47af21145de387ca4d5a1ad6ccf9c226fb43381`.
This fixture-only evidence does not admit scientific execution. Preparation
8045152 also passed independent completion review: successful 44-second
accounting, three commands, seven resource samples, both seals, all eight
byte-identical manifest identities and original → r1 → r2 scientific equality.
Receipt `week5-r2-preparation-verification/20261013T063819Z/verification.json`
has SHA-256 `0a3823e66a97192c5665185edbb908bf5b44c6dd9b451328d95d96476a84d785`.
The new protocol SHA-256 is
`18f7d17fa81e7ae3a6b1e5deddf42d9eda589d96e5a13968188a8ce275bfb95f`.
Supplementary CPU checks 8048540 completed October 13 at 08:31:43.006302 UTC
on apolkovnikov-pub@scc-h30: 86 checks passed without skips, successful
87-second accounting, three commands, seven resource records and both seals.
Independent review completed at 20:43:00.762966 UTC, verifying 108 metadata
bindings, 616 source bindings and actual locked-ID dependence tables for
18,929 development queries and 18,884 primary novel IDs, each over 20 actions.
Novel poses and outcomes remained unopened. Receipt
`week5-r2-additional-verification/20261013T204221Z/verification.json` has
SHA-256 `7703859e50361123de9054fba446c8384d423b8c549b69eab92720314c46c3d2`.
Geometry job 8070391 was submitted at 20:46:55.956765 UTC and initially
observed queued with four CPU slots at 20:49:22.424937 UTC. Its launch receipt
`week5-r2-launches/20261013T204651Z/launch.json` retains SHA-256
`a8c55f5a6054996d49cb2abab304a8b8925914a4cf0495a2f0368f84e4177452`.
The due inspection at 22:05:07.547370–22:05:19.824007 UTC found terminal
failure: bpnlab-pub@scc-kc1, four OMP slots, 20:51:02–20:54:51 UTC,
229 scheduler seconds, accounting failed=0/exit_status=1. The tracked checker
and exact within-revision repeats passed, but the external wrapper rejected
fixed cross-revision identity. No successor geometry completion is accepted.
Metadata diagnosis found 2,051 candidate own_scale scalars differed; the fixed
43 panel IDs, selection and manifests remained unchanged. All 43 clean tensor
hashes matched. Four selected scales and 129 coordinate-jitter hashes differed
across revisions; all 430 hashes were exact within each revision.
Diagnosis `week5-r2-geometry-diagnosis/20261013T220749Z/diagnosis.json` has
SHA-256 `d9d8b549c159206754d8f8b21eaaac1e6b5f656dee54959c23611717aa70534b`;
discriminator `week5-r2-geometry-diagnosis/20261013T221341Z/clean-tensor-discriminator.json`
has SHA-256 `f0dc0f44ba52c114e76b95ac044dd1ed63fd14fc62c8e1b9efd57c80f886ddcb`.
At that earlier geometry checkpoint, CPU dispatch was an untested recovery hypothesis. Separate native/default diagnostic
job 8072666 was submitted October 13 at 22:49:45.058490 UTC after 127 local
checks passed (60 parent, 27 worker, 40 launcher). Initial inspection at
22:52:26.185888–22:52:38.052404 UTC observed queued (qw), four slots, with
no operation, log or resource records. No numerical diagnostic result was produced.
Launch `week5-r2-launches/20261013T224936Z/launch.json` has SHA-256
`91358af8b0e0f3c04765c7fd9f5d4d5264c32cbb7dbaec2c5a2f7dfa917332a3`.
Its diagnostic-only 1-GiB bound comes from 67,480,406 bytes of metadata/log/source
bindings; the existing 17,675,344-byte archive is read only and never copied.
Fresh quota/filesystem reserve passed; this does not establish campaign capacity.
The October 13 at 8:00 PM EDT check was not executed after SSH disconnected;
no result was inferred during the gap. After access was restored, inspection
on October 14 at 19:40:13.233256–19:40:25.519918 UTC found diagnostic 8072666
failed before its parent started: neuro-pub@scc-h32, four OMP slots,
October 13 at 22:54:00–22:54:02 UTC, two scheduler seconds,
accounting failed=0/exit_status=1. SGE copied the wrapper to its spool directory;
the helper lookup used that directory and failed before either worker ran.
Independent metadata-only review at 19:56:38.194670 UTC verified zero operations,
resource records or worker outputs and 139 artifact/617 external/616 source bindings.
No CPU capability comparison ran in job 8072666; the geometry cause remains unproven.
Failure receipt `week5-r2-geometry-runtime-failure-verification/20261014T195626Z/verification.json`
has SHA-256 `c9e2d25740334923a537c36c82b0d2574f6b90a74b7d45ebf26ddc0c3aac371d`.
A separate reviewed operational remedy derives the unchanged parent helper from
the canonical bound input packet directory. Its 64 focused checks and review
passed; the original parent/worker and scientific settings/tolerances are unchanged.
New immutable tools `study-v3/operations/week5-r2-geometry-runtime-diagnostic-remedy-tools/20261014T200830Z` were staged and verified
October 14 at 20:08:33.599282 UTC. Tools manifest SHA-256
`c6404952ea81aa28b04c2603b6b4b7190cc85c1c759ff08410ee2dd7f63c1d77`; input packet SHA-256
`32289c531a0330f93dad42b7974022181eb494d775d6b70825a80a7a1877d716`; staging verification SHA-256
`ae31768ad55b7107b113c581aa6aff0e8690f7e1b86ecdd575a40bd72dd87316`.
At the staged checkpoint on October 14 at 20:08:33.599282 UTC, the launcher
had not been executed. That checkpoint and the earlier 4:41 PM EDT launch/check
boundary remain historical. The new guarded launcher executed once:
diagnostic remedy job **8102231 was submitted October 14 at 20:43:11.969137 UTC**.
The fresh pre-submit scheduler check completed by 20:43:10.988132 UTC with no
active jobs; it precedes submission and does not establish the new job state.
Launch `week5-r2-launches/20261014T204308Z/launch.json` has SHA-256
`82427510eb77a8bc0875753d343783a1e9a383f05bef736aa2c01654ee4037f2`; submission intent SHA-256
`7c690ce8410753e592a06c555dfb87c4b638ca28e344552a1d246c8c2fdeee6d`.
Independent submission-metadata review at 20:50:34.444145 UTC rehashed 763 metadata
and 616 frozen-source bindings, checked the packet/intent/command and both launch seals.
Receipt `week5-r2-geometry-runtime-remedy-submission-verification/20261014T205034Z/verification.json`
has SHA-256 `63aa23c6e514f9cd1757021354fa1262b8f48f89af10e8a8015259e885dbb471`.
Fresh quota 826,630,000,000 bytes and filesystem free 994,956,017,664 bytes passed
the diagnostic-only reserve. Its 1-GiB bound derives from 67,481,168 bytes of
metadata/log/source/receipt allowances; the existing 17,675,344-byte archive is
read only in allocation, with no copy. This does not establish campaign capacity.
The request remains four OMP CPU slots, 32 GiB, 30 minutes, no GPU and the
reviewed Gold-6426Y/AVX2 selector. At the submitted-only checkpoint, no post-submission state or result had been
observed; the earlier 5:45 PM EDT (21:45 UTC) first-check boundary is historical.
Actual inspection on October 14 at 22:25:31–22:25:43 UTC found completed diagnostic
remedy job **8102231**, completed at **20:49:21.682189 UTC**. Accounting records
neuro-pub@scc-ke1.scc.bu.edu, four OMP slots, failed=0/exit_status=0,
**17 whole-job CPU wall seconds and 9.340 actual CPU seconds**.
Independent completion review at 22:34:10.047781–22:34:14.167272 UTC verified
both seals, two unchanged worker commands, dispatch evidence, the final wrapper
marker, six resource records and 184 artifact/617 external/616 frozen-source bindings.
Receipt `week5-r2-geometry-runtime-remedy-queue-record-verification/20261014T223409Z/verification.json`
has SHA-256 `f077737e6781d002d92458d1a743d83c772f7ef028676ec987ad54455ce34d36`.
The four-case recovery hypothesis is **unsupported**: native AVX512 exactly
matched the failed-fresh four scales, 40 tensor hashes and 36 damage rows.
DEFAULT recovered the original four scales but only **36/40 tensor hashes and
32/36 damage rows**. Clean and all masking records matched the original; four
residual jitter hash/damage-row differences across two cases remain. This does
not establish the complete geometry cause or a permanent CPU profile.
The first completion verifier rejected only the allocation QUEUE representation
and produced no accepted receipt; its source and failure remain preserved.
The reviewed replacement accepts the scheduler's bare queue name with a
separately verified host, or its exact qualified forms. Host, job, PE, slot,
thread, scientific and numerical checks remain unchanged; 93 focused tests,
Ruff/format and independent review passed.
Geometry and every dependent stage, full allocated A/corruption replay,
scientific admission and measured CPU/GPU capacity remain held. At the October 14 completion checkpoint, no further profile, helper or job had
been claimed; the earlier 7:27 PM EDT scheduler/preflight boundary is historical.
Separate libm diagnostic tools were staged and verified at 23:26:33.802337 UTC
after **173 local checks and independent review**. Tools manifest SHA-256
`90c9336085f01d6b423a04a6087aff381b1527952cc86bea57e67c3cefd43093`; input SHA-256
`1d6ea033970b2b1b49ca6548180e5e6e5f8c097cb722a2466db49b4809d4a4ff`.
The new guarded launcher executed once: **libm diagnostic job 8104416 was
submitted October 14 at 23:29:21.658353 UTC**.
Launch `week5-r2-geometry-libm-launches/20261014T232917Z/launch.json` has SHA-256
`03fa95ee91fb6c6686b792e111d3033bef8af8e5a12cca740be813023c87caf5`; intent SHA-256
`574b8f072e3364b6650f01cead24e0bf60fae09eae8cda94bf574e938d3760b9`.
Independent submission review at 23:34:29.161902 UTC rehashed 815 metadata and
616 frozen-source bindings, checked exact intent/source/tools/input/command and
complete before/after launch seals. Receipt
`week5-r2-geometry-libm-submission-verification/20261014T233429Z/verification.json`
has SHA-256 `0b6a6e05b49bd698cc4d0d317d5142d319d3ec6a5677448e0b90803e19938b33`.
Fresh quota 824,700,000,000 bytes and filesystem free 992,888,225,792 bytes passed
the diagnostic-only reserve: 67,667,170 bytes rounded to 1 GiB. The existing
17,675,344-byte archive is read only in allocation, with no archive copy or
runtime ELF output copies. This does not establish campaign capacity.
The request is four OMP CPU slots, 32 GiB, 30 minutes, no GPU and the reviewed
Gold-6426Y/AVX2 selector. The four-case diagnostic pairs fresh DEFAULT control
and DEFAULT plus a version-appropriate libc/libm FMA-disable request; actual
runtime, ELF and selected function implementation must be proven in allocation
before interpreting numerical metadata. No permanent runtime profile or complete
geometry cause is established. The accepted 8102231 negative result and all
earlier failures remain preserved; geometry and every dependent scientific,
replay and capacity gate remain held.
The pre-submit scheduler check ran at 23:29:20.578046–23:29:20.793929 UTC; it
precedes submission and does not establish the new job state. At the submitted-only checkpoint no post-submission state or result had been
observed; the October 15 at 00:31 UTC first-check boundary is historical.
The first observation ran once on **October 15 at 00:32:02.955881–00:32:16.614103 UTC**.
Diagnostic **8104416 completed October 14 at 23:34:33 UTC** on
apolkovnikov-pub@scc-h30.scc.bu.edu: four OMP slots, failed=0/exit_status=0,
**21 whole-job CPU wall seconds and 14.493 actual CPU seconds**, peak RSS 695,096 KiB.
Independent terminal review at **October 15, 02:34:06.243155 UTC** passed
its diagnostic-only accounting/command/seal/final-marker checks, six resources
and 240 artifact metadata/617 external metadata/616 frozen-source bindings.
Receipt `week5-r2-geometry-libm-terminal-verification/20261015T023357Z/verification.json`
has SHA-256 `9f45a91a0ba63431f22bad35b6402fde9faabcde0d8b53682b4c448f9b6b3277`;
retained compact receipt SHA-256
`dc5d3db0011bea0c1f3cae4d814e5d0ec2919588a441afda45d61ccdc2684fd6`.
Classification is **inconclusive-dispatch**: both DEFAULT control and FMA-off
matched the original four scales, **36/40 tensor hashes and 32/36 damage rows**.
Neither required-symbol dispatch nor default math code offsets changed; the
intervention did not establish the intended implementation difference. This
supports neither acceptance nor rejection of the libm cause hypothesis and
selects no permanent profile. The earlier 8102231 unsupported recovery result
and all failed attempts remain preserved.
The next hourly boundary after observation was October 15 at 01:32:16.614103 UTC;
no repeat scheduler query is needed for terminal review. At the later access-blocked checkpoint, SCC access was found disconnected
after an attempted full-receipt export returned no receipt. Only accepted
compact/capture evidence was then retained, with no full local JSON export or
refreshed SCC status claimed; restoration was pending and no new job was claimed.
That checkpoint remains historical. **The researcher restored the existing SCC
connection on October 15.** The full **238,862-byte** verification JSON was
recovered at **15:03:07.054586 UTC** from seven checked metadata chunks, retaining
its exact `9f45a91a0ba63431f22bad35b6402fde9faabcde0d8b53682b4c448f9b6b3277`
identity. Four bound JSONs (child inputs, control runtime, FMA-off runtime and
summary) were recovered and hash-checked against that receipt by
**15:05:07.897329 UTC**. Independent read-only review confirmed exact transport,
the original comparisons and **240 metadata/617 external/616 source** counts.
SCC status was refreshed at **15:13:30.934012 UTC**, SHA-256
`bbf4d01268ac8db236ceba3424aa2167a741caba72c8b930166d57ca0fbd1230`.
Recovery read only metadata: no scheduler query, scientific archive or runtime
binary was read. Last actual scheduler batch remains October 15 at
00:32:05.186540–00:32:16.493406 UTC. The earlier `5644` recovery command stopped
at its export-size guard and remains preserved without rerun; the earlier
`ac786` export remains ambiguous and preserved.

Recovered runtime metadata records glibc **2.28 stable**, baseline
`GLIBC_TUNABLES` unset and candidate `glibc.tune.hwcaps=-FMA_Usable`, with identical
required/default versioned math offsets before/after both conditions.
Classification remains **inconclusive-dispatch**; recovery establishes neither
a libm cause nor a permanent profile. One **data-free resolver sensitivity
design** is selected for local implementation and independent review only:
two serial fresh children, `GLIBC_TUNABLES` unset versus exact
`glibc.cpu.hwcaps=-FMA_Usable`, changing only the namespace from the prior request.
It reads no NPZ, runs no historical worker or numerical experiment, and imports
no Torch in the children; the supervisor imports Torch to retain inherited
safeguards. Actual package/loader provenance and required-version offset
sensitivity must be established in allocation. Producer tools passed **140 local
checks**, Ruff/format/Bash syntax and independent review. Separate metadata-only
submission, observation and terminal controls passed **75 synthetic checks**,
Ruff/format and independent review. Both exact source sets are reviewed and
frozen locally; **nothing is staged or submitted**. No new job, resolver result,
permanent runtime or scientific acceptance is claimed. Geometry, all dependent stages/full allocated replay,
scientific admission, measured CPU/GPU capacity, Week 6 selection, final training
and novel opening remain held. Source, recipes, tolerances, IDs and fallback
remain frozen. Never rerun an executed launcher or observer. Its output can only be diagnostic metadata;
it cannot produce eligible scientific artifacts or pass a gate. Source,
scientific settings and tolerances remain frozen; there is no blind geometry retry.
Fresh successor scientific evidence, full admission and measured CPU/GPU
capacity remain pending. Preserve the measured no-go and all `execution-r1` evidence.

Following the [final prospectus](../docs/proposal/2026/kulis_pose_sequence_retrieval_prospectus.pdf),
the December study asks whether a **full contextual training recipe reduces
one-shot retrieval degradation relative to a standard contrastive recipe**
when only novel pose queries are corrupted. Use one dataset, a frozen generic
MotionBERT encoder, three required objectives, three paired seeds, a fixed
20-epoch budget, and nine synthetic corruption conditions. A null or negative
result completes the scientific objective.

## 1. Final decisions

| Item | Decision |
| --- | --- |
| Required methods | Contrastive, contextual, and single-view supervised contrastive (SupCon) |
| Confirmatory comparison | Full contextual recipe versus standard contrastive recipe |
| Representation | Frozen MotionBERT; biased linear 8,704-to-2,048 head; L2-normalized output |
| Physical batch | Eight classes, four examples per class; 32 examples; no accumulation substitute |
| Paired seeds | 7, 17, 29 |
| Duration | **20 epochs for every pilot, selection run, and final run** |
| Selection | Three learning rates per arm, each evaluated with all three seeds; clean development only |
| Required campaign | Three valid engineering pilots under the completion release + 27 selection runs + nine fresh final heads; retain the three original Week 4 pilots separately |
| Novel evaluation | One clean gallery; clean plus nine corruptions; primary and exact-official queries; 180 result cells |
| Uncertainty | Conditional, within-action performance-cluster bootstrap; fixed seeds/actions/anchors |
| Optional control | **Omitted from this December study**, before any new pilot or selection score |
| Cache policy | Fresh v3-bound caches; historical caches and sidecars remain unchanged |

Fixing 20 epochs removes the draft's adaptive plateau rule, including its
failure to distinguish a plateau from a decline. The pilots measure the whole
declared duration. Their learning curves are reported as fixed-budget
diagnostics; this plan does not claim that 20 epochs establishes convergence.
If the 20-epoch campaign does not fit, stop for a documented, result-blind
amendment before selection. There is no automatic reduction to ten epochs.

The regularizer-only control is omitted to bound implementation, storage, and
researcher work. Its omission is a scope/capacity decision, not a negative
experimental result. Do not add it after viewing scores. The 26-method v2
benchmark, encoder fine-tuning, Multi-Similarity, extra datasets, alternative
batch sizes, and real pose-estimator shifts are future studies. Preserve their
existing code and evidence; do not describe this study as completing v2.

The retained transfer recipe follows the base paper's cross-dataset appendix
rather than a new pose-specific search. Physical batches preserve its within-batch
neighborhood operation. Frozen-backbone transfer also has precedent in
[MotionBERT, Section 4.6/Table 4](https://arxiv.org/html/2210.06551#S4.SS6).
Neither paper establishes optimal pose epochs, seed count or a useful-effect
threshold. Keep the declared budget and report uncertainty instead of inventing
such guarantees. Complete candidate and cost reporting follows
[Dodge et al.](https://aclanthology.org/D19-1224/).

## 2. Evidence and integration base

The local checkout inspected for this plan is `c60c0fe` with existing
uncommitted Week 3 and v3 work. Remote `main`, independently checked on
September 29, is `47ca528a99048278693e28019f52d8e924d7e270`. Implement v3 in a
clean worktree based on that commit or a reviewed successor. Do not reset,
merge over, or copy the dirty local tree wholesale. Reconcile useful local
changes against already committed Week 3 work individually.

The committed [Week 3 execution record](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/week-3-scc-execution.md)
and [compact evidence](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/week-3-scc-evidence.json)
establish two byte-identical 95,001-row clean frozen extractions on an L40S:
1,758.60 and 1,765.83 seconds, 3,315,915,790 bytes each. Development caches
contain 76,013 training rows, 20 gallery rows, and 18,929 primary query rows.
This establishes the clean extraction path, not head-training or corruption
runtime. The v2 fine-tuning forecast is not a v3 runtime estimate.

A fresh, read-only inspection through the authorized `remote` tmux session
observed the following; no GPU job or dataset inference was launched:

| Observation | Evidence at inspection time |
| --- | --- |
| Project quota, 2026-09-29 17:22:14 UTC | `/projectnb/textconv`: 18,527.20 / 18,800 GB used; **272.80 GB free**, conservatively interpreting displayed GB as decimal |
| Filesystem space, 17:26:02 UTC | 399,452,930,048 bytes free; project quota is the tighter limit |
| Required reserve | **200 GiB = 214,748,364,800 bytes** |
| Space above reserve | **58,051,635,200 bytes**, approximately 54.06 GiB |
| Scheduler | No jobs listed for the researcher by `qstat`; this is not a reserved allocation |
| Opening records | No opening ledger found in the active project artifact tree or historical home artifact tree; canonical v1/v2 lock directories absent; bounded release/repository-artifact scan also found none |
| Local records | No opening ledger found in the existing artifact directories of the inspected Git worktrees |

These are time-specific observations. Before pilots, selection, and opening,
repeat the audit against a registered list of every historical local/remote
artifact root and release. An unreadable or unresolved root blocks the seal
gate. Absence in the inspected locations is not proof about an unknown copy.

**Seal terminology:** the current aggregate loader deserializes and validates
all annotations in the shared pickle before selecting auxiliary examples.
Historical evidence therefore supports no novel preprocessing for retrieval,
embedding, visualization, scoring, or tuning access; it cannot establish that
novel pose bytes were never deserialized. Record this packaging fact in the v3
decision. No novel poses or outcomes were read by this planning inspection.
For the new final extraction path, authorization and atomic opening must occur
before the call that deserializes novel inputs. Auxiliary container preparation
must be documented separately and must expose only authorized auxiliary IDs to
preprocessing, diagnostics, or model code. If the historical audit discovers
actual novel representations, scores, or outcome-informed decisions, halt:
a fresh namespace cannot restore a sealed confirmatory test.

October 8 supersedes the initial feasibility uncertainty with verified clean
caches and three valid pilots on release
`2897f4fe4c1fb1857432a0e92a7391dde68307f5`. The dated
[Week 4 record](https://github.com/JJCAPPE/pose-embedding/blob/033e1e3/docs/protocol/week-4-execution.md)
reports successful independent validation and 1,008.48 decimal GB of quota free
at one inspection. These observations are not future reservations. Historical
root retirement was resolved through dated evidence and researcher confirmation;
retain that resolution instead of recreating empty roots. Audit active roots
and the retirement receipts at later gates. Original release evidence does not
authorize a successor release automatically.

## 3. Dataset and fixed episode

Retain the adopted source contract: 113,945 usable HRNet annotations and 535
disjoint official missing-skeleton exclusions reconcile to 114,480 nominal
captures. Bind the exact aggregate, missing list, source inventory, pinned
NTU protocol, checkpoint, and upstream hashes. The original adopted input
protocol hash is
`c8b08b6867bc14dc0a947ebfa94e40b16ea3f0dae38dfa6d86187afecb4fd45f`.
It remains historical provenance, not authorization to execute v3.

- Novel actions: `1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85,
  91, 97, 103, 109, 115`; retain all 20 official exemplars exactly.
- Development-validation actions: `2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62,
  68, 74, 80, 86, 92, 98, 104, 110, 116`.
- Selection training uses the other 80 auxiliary actions. Final training uses
  all 100 auxiliary actions. There is no training-subset contingency.
- Preserve the validated development anchor/query **identities**. Its original
  anchor rule minimizes `SHA256("protocol-v1|dev-anchor-v1|" + sample_id)`
  within each action. Do not change that prefix to obtain new v3 anchors.
  The historical episode hash is
  `88f30f96e35dedfd34b42f8e8ee2b561db44bbaf1f93d82d0522ffe011abba46`.
  Generate v3-bound manifests with the same ordered IDs and exclusion rule;
  retain the original episode and hash as provenance.
- Primary queries exclude the gallery sample and **all synchronized views of
  its underlying performance**, keyed by setup, performer, repetition, action.
  The exact-official secondary set excludes the exemplar itself only.
  Derive and lock both exact lists/counts from metadata before opening.

The [existing manifest audit](https://github.com/JJCAPPE/pose-embedding/blob/47ca528a99048278693e28019f52d8e924d7e270/docs/protocol/ntu-manifest-audit.v2.md)
records 18,944 usable novel rows, **18,924
exact-official queries**, and **18,884 primary queries**. Verify these counts
and exact ordered IDs against the bound manifests; do not reconstruct the
primary set by assuming three views per performance. Keep the gallery order
fixed for deterministic cosine ties.

Use the adopted deterministic `[2 people, 100 frames, 17 H36M joints, 3 channels]`
float32 tensor: camera normalization, tracking, COCO-to-H36M conversion,
uniform temporal sampling, missing-person padding, then spatial normalization.
Derived-joint confidence is the minimum source confidence. Random movement is
off. Preserve the declared local confidence correction; do not claim upstream
confidence preprocessing is byte-identical. Encoder parity uses the same local
input tensor on both paths.

## 4. Fixed model, recipes, and training

The generic pretrained MotionBERT checkpoint remains frozen and in evaluation
mode. Pool its representation over time and people, retaining 17 × 512 =
8,704 pre-head values. Train a biased `Linear(8704, 2048)` followed by L2
normalization: **17,827,840 trainable parameters**. Dropout is zero.

| Parameter | Contrastive | Contextual | SupCon |
| --- | --- | --- | --- |
| Loss | Standard cosine-margin contrastive | `0.4 L_context + 0.6 L_contrast + 0.1 L_reg` | Single-view supervised positive log-softmax |
| Positive / negative margins | 0.9 / 0.6 | 0.75 / 0.6 | Not applicable |
| Context neighborhood / epsilon / STE alpha | Not applicable | 4 / 0.05 / 10 | Not applicable |
| Target mean similarity | Not applicable | 0.25 | Not applicable |
| Temperature | Not applicable | Not applicable | 0.07; no additional temperature multiplier |

These are **fixed transfer recipes**, not starting settings to adjust after
diagnostics. The contextual coefficients and different contrastive-only
positive margin follow [Liao et al., Appendices G and H.5](https://proceedings.mlr.press/v202/liao23b/liao23b.pdf).
Batch 32, dimension 2,048, and 20 epochs are pose-study adaptations. The source
image results do not validate these as pose optima. SupCon's single-view
temperature-0.07 implementation is also an adaptation of the
[original method](https://papers.nips.cc/paper_files/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf).
Neither comparison isolates the contextual term from margins and regularization.

Lock the numerical implementation before pilots:

- Context fits **Equation 5's same-label target `y`**, resolving the conflicting
  printed Algorithm 1. Normalize embeddings; use squared distance
  `max(2 - 2*cosine, 0)` and include self in neighbor selection.
- Retain detached kth-distance thresholds and first-stage neighbor/non-neighbor
  counts, the prescribed constant-alpha comparison backward, reciprocal
  expansion with its **non-detached denominator**, and symmetric output.
  Average the off-diagonal contextual squared error over all `n²` entries.
- Average positive and negative contrastive hinges separately over strictly
  active pairs. Empty active sets contribute zero. The mean-similarity
  regularizer includes the diagonal. Explicitly specify the existing
  denominator clamp to at least one for empty complements as a finite local
  convention, and test degenerate/tied neighborhoods.
- Derive independent hand-calculated labeled forward **and backward** fixtures
  from the paper. Do not use an implementation mirroring production as the
  sole oracle. Ordinary finite-difference checks cannot validate an
  intentionally heuristic discontinuous comparison gradient.
- The unlicensed contextual repository remains reference-only. Do not copy,
  adapt, vendor, or redistribute its code. Preserve permitted MotionBERT
  compatibility-port headers, attribution, and license files.

All arms use float32 features/parameters and constant-rate AdamW:
`betas=(0.9, 0.999)`, `eps=1e-8`, `amsgrad=False`, weight decay `1e-4` on
weight **and bias**; no scheduler, mixed precision, clipping, or augmentation.
Pin the PyTorch implementation/runtime and deterministic settings, including
CUDA configuration before any CUDA initialization. Use PyTorch linear default
initialization under each paired seed and archive its state hash.

Retain the physical `P=8, K=4` sampler. An epoch is `ceil(N/32)` batches;
epoch randomness is derived from seed plus epoch, with class/example queues
shuffled at the epoch start and modular cycling within the epoch. It is a
balanced sampling budget, not a promise that every sample is visited once.
Persist the exact ordered batch plan. Pair it and the initial head state
across arms and learning-rate candidates within a seed.

### Engineering pilots and health criteria

Before fresh parity/cache generation and the first scientific pilot, freeze
the **complete canonical v3 protocol**: recipes, numerical conventions, fixed
duration/grid, exact identities, corruption/analysis semantics, and fallback
value/evidence binding. Calculate that fallback from authorized auxiliary
poses during preparation. Freeze the pilot specification against this same
protocol hash with 20 epochs, seed 7, and learning rate `3e-4`.
Run one pilot for each arm on the full 76,013-row development
training set. Save immutable weight snapshots and complete clean development
scores at epochs **5, 10, 15, 20**, plus epoch-zero diagnostics. Pilots are
explicitly ineligible for learning-rate selection, even where settings match
a candidate. Final selection runs are fresh attempts.

Required wiring checks use a fixed constructed 32-row, eight-label learnable
fixture, paired initialization, and physical batches. In 1,000 updates at the
pilot optimizer settings, each arm must remain finite and reach 100%
self-excluded same-label nearest-neighbor retrieval. This checks memorization
of a deliberately learnable fixture; there is **no required accuracy floor on
real development data**.

On real pilots require finite losses, gradients, and updated parameters at
every step, the exact prescribed update count, and nonzero projected vectors.
At epochs 0/5/10/15/20, require normalized-vector error at most `1e-5` and
`mean_q ||z_q - mean(z)||² > 1e-6` on the complete development query set,
summarized in float64. This screens total numerical collapse; it does not
establish a useful representation or justify tuning. Zero individual
gradients from inactive terms are allowed.

Archive loss-component magnitudes, active positive/negative hinge fractions,
neighborhood and reciprocal counts, empty-complement counts, gradient norms,
embedding variance, cosine quantiles, and actual timing/memory/checkpoint
bytes. Use fixed diagnostic sampling points, including the first batch and
each epoch boundary. Poor accuracy, continued learning, or overfitting curves
are reportable findings, not permission to change recipes or pick an epoch.
A nonfinite/collapse or mathematical failure blocks selection until corrected
under the amendment policy.

### Selection and final training

Run `3 arms × {1e-4, 3e-4, 1e-3} × {7,17,29} = 27` development runs at
20 epochs. Rank candidates separately within each arm by **mean epoch-20
clean development top-1 across all three seeds**; exact ties prefer mean
MRR, then the lower learning rate. Use unrounded metric values for ranking.
There is no best-epoch selection, early stopping, or corrupted-score selection.

A candidate needs three valid seeds. An unresolved numerical failure makes
that candidate ineligible; a two-seed mean cannot compete. Finish the
declared attempt matrix and retain all failures. If an arm has no valid
candidate, stop for a result-blind amendment. Report any unequal number of
eligible candidates; all arms retain the same attempted selection budget.

Lock the three selected configurations, selection evidence, and timestamp.
Train nine **fresh** heads on all 95,001 auxiliary rows, at 20 epochs, with
the selected rates and the three paired seeds. Retain the epoch-20 checkpoint;
do not choose a checkpoint using novel data. Do not reuse a pilot/development
head as a final head.

An infrastructure retry uses the identical configuration, seed, initialization,
and batch plan in a new attempt directory, from scratch. No resumable optimizer
state or v2 segmentation framework is required for v3. Verify complete runs
fit an allocation before selection. Preserve every attempt, including failed
or partial output. A verified implementation defect requires a dated
result-blind correction and rerunning every affected comparison, not only the
unfavorable arm. Parameter changes require a new declared protocol/grid.

Before selection freeze an attempt ledger with exactly 27 matrix slots and
separate attempt IDs. Classify failures using logs and integrity evidence before
ranking scores:

| Reason | Evidence and treatment |
| --- | --- |
| Infrastructure | Scheduler/node termination or verified filesystem/service interruption, with logs/accounting; resolve the cause and restart identical inputs from scratch in a new attempt. One automatic retry is allowed; further retries require a recorded cause/remedy and refreshed capacity, never an accuracy criterion. |
| Numerical | Nonfinite loss/gradient/parameters or the fixed collapse check fails; retain the failure and make the candidate ineligible until a documented correction. Repeated launches cannot shop for a passing seed. |
| Implementation/provenance | Wrong updates, pairing, formula, IDs or hashes; block the affected stage, identify every affected comparison and apply the release/revalidation policy. |
| Unresolved | Preserve evidence and block eligibility; do not relabel an unexplained failure as infrastructure to obtain another draw. |

The selection table contains every slot, attempt/retry lineage, eligibility
reason, updates, initialization/batch hashes, unrounded clean metrics and costs.
Show all nine three-seed candidate means or explicit ineligibility. An endpoint
rate winning means best among the tested rates; it does not expand the grid.
Poor accuracy alone never invalidates a numerically valid run.

## 5. Nested corruptions

Corrupt **only queries**, after the complete deterministic preprocessing above
and before the frozen encoder. Each family starts from the clean tensor;
families are never composed. The gallery stays clean. No deletion of frames,
interpolation, extra normalization, or clipping follows corruption.

Hash UTF-8 `"protocol-v3\0" + sample_id + "\0" + family` with SHA-256.
Let `u` be the unsigned big-endian integer from the first eight digest bytes,
and `seed63 = u & (2**63 - 1)`. Family names are
`coordinate_jitter`, `joint_mask`, `frame_mask`. **Severity is excluded**.
Pin generator/runtime versions and archive corruption-spec and output hashes.

| Family | Exact operator |
| --- | --- |
| Jitter | Draw one CPU float32 Gaussian x/y field per sample with a Torch generator seeded by `seed63`. Multiply the same field by `0.01`, `0.025`, or `0.05` times its clean torso scale. Add only where original confidence is positive; leave confidence and all missing/padded observations unchanged. |
| Joint masks | Shuffle the existing ordered groups `[(11,12,13),(14,15,16),(1,2,3),(4,5,6),(0,7,8,9,10)]` once using pinned Python `random.Random(seed63)`. Concatenate groups, retaining within-group order; take the first 3, 6, or 8 joints. Zero all their x/y/confidence values across people and time. Do not replace already absent joints with visible ones. |
| Frame masks | For length `L` in `{10,25,40}`, set `start = (u * (101-L)) // 2**64`. Zero `[start,start+L)` across people/joints/channels. These intervals are nested and each length has an approximately uniform marginal start position. |

Severity zero returns a byte-identical copy without needing a torso scale.
For jitter use the lower median positive finite distance between shoulder
midpoint (joints 11/14) and hip midpoint (4/1), over clean person/frame
observations whose four confidences are positive. When a sample has no valid
own scale, use one fixed fallback: the lower median of valid **sample-level**
scales from the 80-action clean development-training set. Calculate it once,
record the contributing IDs/count/hash and value, and freeze it before pilots.
Do not recompute it from validation, all-100 final training, or novel queries.
If no positive training fallback exists, the preselection gate fails.

Freeze a development-primary geometry panel before corrupted scoring. For each
of the 20 development actions choose the two smallest
`SHA256("protocol-v3|geometry-panel-v1|" + sample_id)` values, breaking ties by
sample ID: 40 base rows. Add at most eight sentinels from that same query set:
minimum-positive and maximum observed support; minimum-positive and maximum
second-person support; minimum and maximum valid own torso scale; an observed
row with invalid own scale; and an all-missing row. Resolve ties by the same
hash/ID order, deduplicate, and record absent categories without substitution.
Freeze the sorted ID list, selection-code hash and manifest hash outside Git.
This 40–48-row panel is an engineering coverage choice, not a power sample.
Constructed fixtures cover absent categories, boundary frames and degenerate
scales without changing the real-data set.
Verify unchanged shapes, exact mask counts and nesting, one shared jitter
field, severity-zero identity, missingness preservation, boundary frames,
two-person behavior, own-scale failure/fallback, and deterministic repeats in
fresh processes. Record nominal damage and newly masked previously observed
joint-frame/person observations, including zero-effective-damage cases.
Repeat the panel's complete clean-plus-nine-condition tensor generation in
two fresh processes under the pinned environment and require exact array/output
hash agreement, alongside the invariant checks. Retain per-case results and
fail the gate on any violation; do not use a model-accuracy acceptance floor.
During the already-required full 18,929-row passes, record geometry summaries
for every row, not just the panel. Observed support means clean confidence > 0
at a person/frame/joint location. For masks report newly zeroed observed count,
original observed count and their ratio; a zero denominator is recorded as
undefined, not zero. For jitter report per-coordinate RMS displacement
`sqrt(sum_observed(dx**2 + dy**2) / (2 * N_observed)) / scale`, using the actual
own/fallback torso scale and unchanged confidence. No observed locations yields
an undefined value, counted separately.
Summarize min, median, 95th percentile and max over finite per-row values
(using NumPy linear quantiles for median/p95),
undefined counts, zero-damage counts and fallback count/fraction of all queries.
These summaries describe damage, not exclusion or severity-calibration rules.
Never drop a troublesome novel query or redraw its corruption. A nonfinite source/artifact defect stops the relevant gate rather
than silently excluding a sample.

By October 18, run all nine full-size development query corruption paths and
retain their artifacts. Time one full-size pass per family at maximum severity
end to end, including source verification, preprocessing, encoder, serialization,
projection of the three pilot heads, and complete retrieval. The other cells
verify complete identities, invariants, and deterministic outputs. Corrupted
development scores may be logged as evaluator evidence but cannot select
recipes, severities, learning rates, or duration.

These are post-preprocessing tensor stress tests, not actual camera occlusion,
frame recovery, or a new pose estimator. The experiment measures incremental
head-objective effects on an encoder already pretrained with pose masking/noise.

## 6. Locked analysis

Use cosine retrieval and query-weighted top-1, MRR, and R@5, with a fixed
gallery ordering for score ties. With one relevant exemplar, mAP equals MRR;
do not present it as independent evidence. Report every method, seed,
clean/corrupted cell, and both query definitions.

For the primary query set define

```text
drop(m,s,c) = clean_top1(m,s) - corrupt_top1(m,s,c)
Delta = mean over 3 seeds and 9 cells of
        [drop(contextual,s,c) - drop(contrastive,s,c)].
```

Negative Delta means less degradation for the contextual recipe. Queries have
equal weight within each cell; seeds and the nine cells each have equal weight.
The nine-cell mixture is a prespecified synthetic stress mixture, not an
estimate of real-world corruption prevalence.

Freeze the following analysis before selection and rehash it at opening:

1. Compute a per-query effect by averaging the paired correctness-drop
   difference over the fixed three seeds and nine cells.
2. Group queries by `(setup, performer, repetition, action)`. Sort actions,
   group keys, and sample IDs deterministically. In each bootstrap replicate,
   independently within each of the 20 fixed actions, sample its original
   number of groups with replacement. Include every available camera view of
   a sampled group, with multiplicity.
3. Apply that **same draw** to every seed, method, clean/corrupted condition,
   and cell. Divide the summed per-query effects by the sampled number of
   queries. Do not average group means equally: groups can have unequal
   view counts. Do not force equal action weights.
4. Use 10,000 replicates from `numpy.random.Generator(PCG64(2026))` and a
   two-sided 95% percentile interval, quantiles 0.025/0.975 with
   `method="linear"`. **Do not resample seeds or actions.**
5. Also report all three seed effects, all nine cell effects/curves, and all
   20 leave-one-action-out effects. For the last, remove that action's query
   observations only; retain all 20 gallery anchors and the original ranks.
   Report the range and sign changes descriptively, without new tests.

This interval is conditional on the trained heads, three seeds, official
actions/anchors, query definitions, and realized synthetic corruptions. Its
resampling assumption is exchangeability of performance groups within a fixed
action. It does not provide uncertainty over arbitrary seeds, actions,
participants, anchors, or real camera errors; repeated performances from a
person may still be dependent. Ten thousand replicates do not create more
independent training seeds.

Support the one confirmatory statement, **smaller clean-to-corrupt top-1
degradation under the declared mixture**, only if the interval's upper bound
is below zero. Otherwise report a null or contrary result. Always accompany
it with clean accuracy, absolute corrupted accuracy, and the descriptive
contextual-minus-contrastive corrupted accuracy difference. A smaller drop
does not establish better corrupted retrieval. SupCon, exact-official queries,
per-cell differences, seed variation, and sensitivities are descriptive:
no additional superiority tests, cherry-picked winning cells, or causal
attribution uniquely to contextual neighborhoods.

Before selection produce a metadata-only development table, by action, of query
count, performance-group count, views per group, distinct performers and the
largest performer's share of groups. Produce its novel counterpart from the
already-permitted metadata manifests before opening, without loading poses.
This documents residual participant dependence; it does not make groups
independent or replace the declared resampling unit. Keep the conditioning and
exchangeability caveat beside the primary interval, not only in an appendix.
[Benchmark variance research](https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf)
supports disclosing sources of variation; three seeds do not justify population
inference over arbitrary training runs.

Build and test the report template before selection. In percentage points,
show clean accuracy, mean corrupted accuracy, drop, their contextual-minus-
contrastive differences and Delta with its interval in one table. Check the
identity `Delta = clean accuracy gap - mean corrupted accuracy gap`. Report
all cells/seeds separately as already required. Use these fixed interpretations:

| Outcome | Permitted wording |
| --- | --- |
| Upper Delta bound < 0, mean corrupted gap > 0 | Evidence of smaller degradation; higher corrupted accuracy is descriptive. |
| Upper Delta bound < 0, mean corrupted gap <= 0 | Evidence of smaller degradation without higher absolute corrupted accuracy. |
| Interval includes zero | Inconclusive for the declared claim; not evidence of equivalence or no effect. |
| Lower Delta bound > 0 | Results favor greater contextual degradation under this mixture. |

Do not invent a smallest meaningful effect from these papers. Give effect sizes
in percentage points and their descriptive per-1,000-query scale (1 point = 10
correct retrievals per 1,000 under the declared mixture), without a new pass
threshold, equivalence test or deployment recommendation. The complete recipe
comparison cannot isolate contextual neighborhoods from its margins/regularizer.
Synthetic stress does not establish natural-camera robustness; that caution is
consistent with [Taori et al.](https://proceedings.neurips.cc/paper/2020/hash/d8330f857a17c53d217014ee776bfd50-Abstract.html),
whose evidence concerns image benchmarks, not these pose recipes.

## 7. Concrete architecture work

The committed architecture already retains the frozen pipeline next to the
separate v2 benchmark. Extend that path rather than route this study through
v2 fine-tuning. The table below retains the September 29 implementation inventory;
several capabilities are now complete. Its gap descriptions refer to that
original base. The completion-release subsection identifies the remaining work;
do not rewrite verified v3 operators or analysis merely to repeat this table.

| Work package | Existing modules and concrete change | Acceptance check |
| --- | --- | --- |
| A. Version and validate v3 | Add `configs/protocol.v3.yaml`, v3 evaluation/lock/run-set templates, experiment configs, and a v3 tracker plan. Update `config.py`, `protocol.py`, CLI dispatch, `AGENTS.md`, and public protocol bundle using explicit v3 validation. Current v1 literals/shared-margin/six-grid checks cannot accept this plan. Keep v1/v2 scientific settings unchanged. | Valid v3 accepted; changed margins, seeds, duration, grids, IDs, roles, missing locks, and cross-version artifacts rejected; historical suites still pass. |
| B. Authorize the dataset once | Extend shared seal checks across legacy training/extraction, `benchmark/runtime.py`, v2 locks, and v3 entrypoints. Register historical roots. Keep one canonical artifact root; put v3 below `study-v3/`, not in a replacement environment root. Add an immutable dataset-level opening record shared across versions. | Existing v1/v2 opening blocks v3; v3 opening blocks old training/selection commands; unknown roots fail closed; concurrent first opens cannot create inconsistent authorizations. |
| C. Complete pilot/training path | Extend `training/runner.py` with an explicit engineering stage, epoch snapshots, full clean development scoring, deterministic CUDA initialization, health diagnostics, and timing; update strict manifest validators together. Reuse `models/action_head.py` and `training/sampler.py`. | Exact pilot and sweep update counts, paired init/batch hashes, pilot exclusion from selection, finite/overfit checks, and three-seed failure/tie handling. |
| D. Extend frozen extraction | In `motionbert_inputs.py`, `motionbert_features.py`, `features.py`, `artifacts.py`, and CLI, add authorized v3 development-corruption and novel roles/conditions. Separate metadata/hash verification from annotation loading. Add corruption implementation and fallback evidence to cache provenance; current clean-only code digests omit the operator. Reuse pooling/encoder and exact source identities. | Wrong role/condition/split fails; no novel loader call before atomic authorization; all conditions/IDs pair across heads; fixture outputs remain scientifically forbidden. |
| E. Corruption/analysis/report | Version the operators in `corruptions/pose.py`; add fixed fallback evidence. Add a v3 engineering-evaluation mode for declared corrupted development cells, explicitly ineligible for selection; retain the clean-only selection evaluator. Extend `evaluation/analysis.py` from globally pooled groups to within-action resampling. Update runner/report schema and completeness verification for v3. | Hand-ranked fixtures, unequal-view cluster weights, fixed-seed bootstrap, LOAO with fixed gallery, 180 unique authorized rows, and figures reproducing from ranks. |
| F. SCC and tracker | Add a v3 Grid Engine launcher with clean-release checks, external logs, quotas, immutable attempts, and complete measured timing. Add a guarded tracker migration plus matching app fallback/protocol deployment after the scientific bundle is settled. | Job exits/logs bound; no login-node compute; tracker preserves live versions/progress/RLS/ownership; public loaders expose only safe plan/progress fields. |

### Completion release before selection

The following completion-release requirements record the October 9 amendment
for `execution-r1`. The October 12 subsection below defines its authorized
successor; neither changes or relabels the original release.

Adopt one coordinated completion release. The current final-training guard in
`training/runner.py`, novel-role guard in `motionbert_features.py`, final-lock
guard in `protocol.py`, selection authorizer, corrupted-development evaluator
and report dispatch all need completion and testing. The training/extractor
files are already in the design's frozen hash set. Do not add bypass wrappers,
remove validation or edit the original locks to keep old artifacts eligible.

Use the immutable successor prefix `study-v3/revisions/execution-r1/` for its
locks, manifests and attempts, under the same canonical artifact root. Keep
`study-v3/locks/` and all prior attempts unchanged. Bind predecessor protocol
and design hashes, successor full protocol/config hashes, release commit,
changed-file list and regeneration matrix in a dated amendment receipt. Retain
one shared dataset opening ledger and access lock across every revision/version;
a new prefix must not create a new test seal. No mutable current-release alias
or caller-selected ledger may authorize a scientific operation.

The successor full digest may change for provenance/path bindings. A reviewed
field comparison must show identical scientific choices, including IDs/order,
recipes, duration/grid, corruption seed prefix and operators, fallback value,
metrics, bootstrap and claim rule. Preserve original fallback measurement and
identity evidence; regenerate protocol-bound manifests without recomputing or
reselecting them. Any scientific difference requires a separate explicit
amendment before running, not classification as a path-only change.

| Change class | Required evidence before selection |
| --- | --- |
| Documentation, scheduling or report presentation only | Applicable checks and content review; no relabeling or automatic invalidation of scientific artifacts. |
| This completion release: frozen training/extraction/provenance interfaces | Fresh parity, both full 95,001-row repeat extractions, all five bound clean caches and all three complete pilots; independent validation/accounting under the successor bindings. Retain original evidence separately. |
| Corruption/evaluation/analysis implementation | Hand-derived fixtures, nine complete development paths, fresh-process geometry checks and actual v3 report dispatch. Recompute affected downstream artifacts; any bound-code change also follows the preceding row. |
| Later scientific or bound-code correction | New dated release/digest, impact inventory and regeneration of every affected comparison; no mixed-release campaign or silent reuse. |

Before freezing this release, rehearse its real command path on fixture data:
selection authorization and ranking, fresh final training, complete final-run
lock, atomic opening, novel-role extraction, projection, retrieval and v3
report. Synthetic final roles must remain scientifically ineligible. Opening, concurrency
and crash fixtures use a temporary synthetic dataset registry and artifact root,
never production roots or the real opening ledger. Assert that real opening
records remain absent or unchanged after rehearsal. Require
exactly 180 unique cells, missing/duplicate rejection, ordered primary/official
subset equality, unequal-view bootstrap fixtures, the interpretation identity,
tamper/cross-release rejection, authorization before loader invocation,
concurrent/partial-opening recovery and denial of old/new training after
opening. A unit test of an unused analysis function is insufficient: exercise
`report.py` through to the v3 analysis. Retain the independent November audit.

Complete this dependency work first in Week 5, then revalidate caches/pilots,
then run development corruptions and capacity measurements. October 18 remains
a gate, not permission to compress checks if implementation takes longer.

Finish and commit the extractor, preprocessing, corruption operators, config,
dependency, and artifact validation interfaces **before fresh scientific cache
creation**. Current
cache provenance binds those code paths and the dependency lock; a later
correction may require fresh parity/extraction. Do not weaken a digest check
to keep using an invalidated cache. The October 18 gate adds evidence and
selection authorization against the **unchanged successor protocol digest**
after its fresh evidence passes; it does not edit the protocol under existing
pilot artifacts. A correction to that digest
or cache-affecting code requires regenerating affected caches and rerunning
affected pilots before the gate passes. Schedule this work and retain
superseded artifacts in the capacity ledger.

Fresh v3 auxiliary caches are chosen over a cross-protocol adoption wrapper.
Regenerate matching v3-bound manifests without changing sample identities;
run encoder parity and two fresh-process final-training extractions on the
same GPU. Retain both for repeatability, plus development train/gallery/query
caches. Bind the original source/checkpoint hashes in the new sidecars.

For final evaluation, encode the union of eligible novel queries **once per
condition**, then write **two immutable role-specific pre-head cache files**
from those rows: exact-official and primary. The primary file is an exact
ordered subset selected by its locked manifest, with matching feature rows
verified during export. This deliberately retains duplicate rows so existing
head application and role validation need no shared-view abstraction. No
additional encoding is needed to change query definition. All nine heads
reuse these pre-head caches. Apply each checkpoint to
clean gallery and all query conditions, preserving existing byte/provenance
validation and checkpoint-bound normalized embeddings. The 180 result cells
are **not** 180 encoder passes: the semantic encoder workload is one clean
gallery plus ten query conditions, with batching/sharding as recorded.

The current projector and artifact revalidation include CPU projection and
repeated hashing. Include their wall time and temporary memory in measurements;
do not assume the GPU extraction rate predicts end-to-end evaluation. Record
hashing, loading, preprocessing, encoding, projection, artifact revalidation,
retrieval and serialization separately, with host/GPU peaks and saved bytes.

Enforce reuse counts in the campaign manifest: nine development corruption
encodings shared by three pilot heads; one novel gallery plus ten query-condition
encodings; 21 final pre-head files (ten official, ten primary, one gallery);
nine reusable gallery projections and 180 role-specific query projections.
Keep immutable role-specific files and existing validation. The October 9
amendment prohibited memoized validation; that prohibition remains part of the
immutable `731938a`/`execution-r1` evidence. The October 12 exception below
authorizes only bounded numerical proof reuse in a new successor. CPU projection
arithmetic, precision and all content hash checks remain unchanged. Optimize
measured orchestration/I/O reuse first. Start with one scientific subprocess at a time on the validated
L40S. Group fresh subprocess runs only when measured queue/setup savings justify
it and the complete group fits the allocation; preserve independent seeds,
attempts, manifests and failure handling. No unmeasured concurrent GPU jobs.

### October 12 validation and capacity successor

The researcher authorized [ADR0007](../docs/decisions/0007-safe-validation-reuse-and-stage-capacity.md)
after measured P=778.274100575014 seconds made the prior profile's repeated
report component with slack 122.145796 hours against the shared 48-hour opening
limit. Preserve that no-go; it does not prove all hardware infeasible.

Within one guarded command, a new `execution-r2` release may reuse only complete
successful deterministic numerical proofs. Each hit must rehash every transitive
bound file and match validator/options, role, protocol/design/source/runtime
identities. Reuse never substitutes for fresh seal, authorization, timestamp,
attempt inventory, resource or calendar decisions. No stat-only trust, persisted
proof cache, failed/partial result reuse or cross-command reuse is permitted.
Store successful numerical proof markers only, not mutable result objects.
Independent recertification
starts fresh, and changed content/options fail closed or force full validation.

Use the same canonical artifact root and shared seal, new predecessor-bound
locks and explicit scientific-field equality. Follow ADR0007's regeneration
inventory: retain original source/identity/fallback evidence through validated
bindings and byte-identical manifest rebinding; regenerate parity, five caches,
three complete pilots, panel/repeat evidence, nine development paths/projections,
report rehearsal and successor timing/admission receipts. Preserve original and
`execution-r1` artifacts without a cross-release adoption wrapper. Freeze and
verify the complete successor before scientific execution; passing software
checks alone cannot authorize selection or opening.

## 8. Capacity gates

The fixed campaign has the following head-update count under the existing
sampler. Counts are not GPU-hour estimates. The main table counts the accepted
campaign. The original and execution-r1 pilot sets add six retained historical
runs and 285,120 updates. With execution-r2 engineering regeneration, 45 complete
training runs would be retained before other retries/fixtures, totaling
2,245,140 updates across releases. The earlier two-generation estimate was
42 runs and 2,102,580 updates; preserve it as historical planning evidence.

| Stage | Runs | Updates per run | Total updates |
| --- | ---: | ---: | ---: |
| Engineering pilots, 76,013 rows | 3 | 20 × 2,376 = 47,520 | 142,560 |
| Development selection, 76,013 rows | 27 | 47,520 | 1,283,040 |
| Final training, 95,001 rows | 9 | 20 × 2,969 = 59,380 | 534,420 |
| **Required total before retries/fixtures** | **39** | | **1,960,020** |

Target one allocated L40S, the measured extraction hardware; validate the exact
head-training and corruption workload there. A different accelerator requires
repeatability, memory, and runtime checks before inclusion in the paired run
schedule. Keep complete jobs within their approved wall limits. The current
launcher requests four CPU slots and 32 GiB aggregate host memory; confirm
that is sufficient for full arrays, serialization, and projection rather than
assuming from GPU memory alone.

Before selection, create an immutable capacity report that includes:

- All three complete pilot times, checkpoint/validation/I/O time, CPU and GPU
  memory peaks, scheduler queue/setup observations, and actual saved bytes.
- The complete corrupted development passes, projection for all pilot heads,
  source/provenance checking, and one-shot scoring. Measure at least one
  timing segment with all 95,001 auxiliary feature rows resident for
  final-training memory/extrapolation. Update only fixed 80-action training
  batches, keeping held-out labels out of optimization. This is separate
  timing-only engineering outside the 39 scientific runs; record its extra
  steps/bytes, and make its weights ineligible for selection or final results.
  No novel inputs or scores are needed.
- A dated CPU/GPU allocation calendar specifying resource-class windows,
  complete-job limits and queue/setup allowance. Under ADR0007, schema-2 capacity
  evidence separates CPU/GPU maximum-job, remaining pre-opening and remaining
  evaluation time; every window declares its class. CPU/I/O within a GPU job
  stays in that complete GPU wall time. Preserve global non-overlap and one
  scientific subprocess; an empty queue or prior access is not a reservation.
- Researcher-confirmed available hours against the work packages and final
  analysis. The inherited 77 planned hours in Weeks 4–14 and zero recorded
  actual minutes are not evidence of remaining availability or no past work.

Forecast remaining training per arm from its measured update cost and fixed
validation/checkpoint overhead; use the slower pilot/full-size timing for
that arm and include initialization, hashing, scoring, and report regeneration.
Count every fresh extraction, integrity scan, retained attempt, and measured
CPU stage. **Multiply remaining compute/wall-work estimates by at least 1.25**,
then add the allocation calendar's queue/setup delays. Apply the same minimum
25% slack to remaining researcher work. The resulting schedule must finish
final heads and locks by November 29, full novel evaluation by December 6,
and preserve December 7–18 for analysis/delivery. Do not launch overlapping
jobs beyond the demonstrated GPU, host-memory, or storage budget.

At opening, compare actual GPU allocation time remaining with the complete
GPU-job bound, while still requiring sufficient CPU and GPU evaluation windows
and researcher delivery time. Reject scalar/unclassified predecessor receipts
as successor evidence. Independent report/recertification compute remains due
by December 6; separate accounting does not create later compute capacity.

October 8 pilot scheduler seconds were 502/525/415 and training-stage seconds
286.739518/323.617977/254.941551 (Contrastive/Contextual/SupCon). A provisional
head-job estimate is `sum(9*S + 3*(S + T*(59380/47520 - 1)))`, where S is a
pilot's scheduler time and T its training time: 4.987 allocated hours, or
6.23 with 25% slack. Completion-release regeneration adds a measured baseline
of 5,644 cache-job seconds plus 1,442 pilot-job seconds: another 2.46 hours
with slack. The combined **8.69 allocated hours is not a campaign capacity
pass**. CPU validation, nine development corruptions, novel extraction,
projection/report work, queues, retries and software/researcher time are extra.
Replace these estimates with successor measurements and the slower required
full-size timing before authorization. Do not multiply the slack twice.

The Week 5 work ledger must separate implementation/review, release revalidation,
corruption audit, analysis/report verification and resource/availability planning.
Existing tracker minutes are inherited estimates, not measured forecasts or
researcher availability. Re-estimate each package before the go/no-go decision;
retain the deadline only if their dependencies and 25% slack fit. Set scheduler
wall limits from complete measured jobs plus slack and scheduler granularity,
rather than copying the pilot launcher's 12-hour request by default.

Storage uses bytes, not ambiguous GB labels. Let

```text
available = min(filesystem_free_bytes, project_quota_remaining_bytes)
required = 200 * 2**30 + 1.25 * forecast_remaining_peak_bytes
pass iff available >= required.
```

The September 29 planning envelope was **100 GB** incremental including slack.
The October 9 campaign-wide planning envelope was **120 decimal GB including slack**,
while retaining the 200 GiB reserve. It includes retained predecessor evidence
and the planned completion-release regeneration; it is not 120 GB of new work
on top of files already present. It deliberately keeps
the role-specific files expected by the existing architecture. The following
uncompressed payload estimates include float32 features, int64 labels, and
20-character Unicode sample IDs; compression is not credited.

| Retained v3 outputs | Estimated decimal GB |
| --- | ---: |
| Five fresh clean caches, including both final-training repeats | 9.9464 |
| Nine development corruption pre-head caches | 5.9463 |
| Ten exact-official plus ten primary novel pre-head caches and clean gallery | 13.1980 |
| 39 development gallery/query projection pairs: 12 pilot snapshots + 27 selection endpoints | 6.1193 |
| 180 role-specific final query projections and nine reusable clean gallery projections | 28.1768 |
| 48 head checkpoints: 12 pilot snapshots + 27 development + nine final | 3.4229 |
| Conservatively bounded physical batch-plan files | 1.0666 |
| 27 development corruption query projections: three pilot heads × nine conditions | 4.2318 |
| Additional completion-release five clean caches and three pilot directories, approximately | 12.8060 |
| **Planned payload subtotal across both releases** | **84.9141** |
| Metadata, per-query results, retained failures, and temporary-file allowance | **10.0000** |
| Subtotal and allowance multiplied by 1.25 | **118.6426** |
| **Rounded campaign-wide envelope** | **120.0000** |

This table is the pre-`execution-r2` estimate. ADR0007 adds a retained fresh
engineering generation; inventory all actual retained bytes, successor outputs
and remaining temporary peaks before admission. No new numeric envelope or
capacity pass is inferred here. The current-space/reserve equation above remains
mandatory, and no historical evidence may be deleted to fit the plan.

The original roughly 4.14 million development/final per-query result rows,
511,083 development-corruption rows and successor pilot records are covered by
the allowance, not assumed free. Pilot epoch-zero diagnostics do not retain
another full embedding cache; compute their summaries in memory. At epoch 20,
retain one checkpoint artifact per pilot and reference it from both the epoch
record and completion record rather than copying it. The 10 GB allowance is
bounded, not permission for unlimited failed attempts. Replace estimates with
actual bytes at the October gate, including all new artifacts already created.

The September 29 reading failed the original 100 GB envelope by about 41.95 GB;
retain it as historical evidence. The October 8 observation of 1,008.48 GB quota
free is newer but also not a reservation. Remeasure both quota and filesystem
space and apply the remaining-peak formula; request additional authorized
capacity only if that current calculation fails. If a new canonical root is
necessary, register and verify transfers without relabeling or deleting old
evidence. Filesystem space beyond quota is not usable capacity.
The peak forecast includes all yet-to-be-created retained checkpoints,
intermediate pilot weights, batch plans, clean/corrupted pre-head caches,
primary/official duplicates, projected embeddings, ranks, logs, failed attempts,
immutable output staging, and reports. Already present files are reflected in
the current free-space reading, not counted twice. After work begins, use the
remaining measured forecast rather than demanding the 120 GB envelope again.
Retain original v1/v2
artifacts; deleting evidence is not a capacity remedy. Recheck before each
large job and before opening, and stop new work if the reserve would be crossed.
The September 29 observation permits at most **46.44 decimal GB of additional
unmargined peak work** under this formula; it does not reserve that amount.

**October 18 go/no-go:** all three objectives mathematically verified; three
complete, valid 20-epoch pilots; unchanged fixed development episode; nested
corruptions and fallback validated; completion release and end-to-end fixture
rehearsal passed; successor cache/pilot validation complete; full development extraction/projection/scoring verified;
analysis/report template tested; every historical seal audit resolved; and
the complete measured schedule/storage/availability forecast passes. Otherwise
stop before the sweep and record a result-blind amendment. Do not reduce a
single method's budget, discard seeds/cells, or claim a completed comparison.

## 9. Locks, opening, and failures

Keep `POSE_EMBED_DATA_ROOT` for licensed inputs and a stable absolute
`POSE_EMBED_ARTIFACT_ROOT` for all scientific records. Resolve all v3 outputs
under its `study-v3/` namespace and the explicit immutable revision described
in Section 7. Retain predecessor lock paths without overwriting them. The shared
dataset-level opening record remains at the canonical root and binds the
source inventory/physical-source hashes and the historical-root audit. Neither
a caller-selected ledger nor a different study namespace bypasses it.

Use a staged lock sequence to avoid circular prerequisites:

1. **Before fresh parity/caches and pilots:** complete immutable v3 protocol
   and design/pilot specification with fixed recipes, 20 epochs, identities,
   numerical/corruption/analysis conventions, fallback binding, finite LR
   grid, hashes, and the omitted control decision. It authorizes auxiliary
   engineering only. Freeze all cache-affecting code in the release.
2. **By October 18, before selection:** append an immutable selection
   authorization binding the successor protocol digest used by its fresh pilots to corruption/analysis
   verification, pilot records, the complete run matrix/manifests, and the
   capacity decision. Scientific settings are unchanged; the new provenance digest
   is explicit. There are no final checkpoint hashes yet; this is not a test-opening lock.
3. **After selection/final training:** selected configs and timestamps; nine
   final checkpoint/run-manifest hashes, seeds, initializations/batches,
   source/checkpoint/input-contract bindings, code/dependency hashes, exact
   primary/official/gallery IDs, evaluation plan and complete final-run-set.
   Record the researcher-controlled final lock only after its dependencies.
4. **Immediately before opening:** validate the complete cross-binding and
   all prior ledgers, verify no scientific training remains active, recheck
   capacity, and atomically create the immutable dataset opening event and
   its v3 authorization. Coordinate creation so a partial/crashed transaction
   fails closed and can only complete the identical lock, never a new one.
   **Only then** invoke the novel annotation loader/preprocessor/encoder.
5. **After opening:** every extraction shard, head application, evaluation
   cell, and report must match the same source, protocol, run-set, opening,
   cache, code, checkpoint, and corruption bindings. All scientific training
   and selection for this study/source are forbidden across v1/v2/v3 paths.

A crash after the opening event does not reseal the data. Preserve the attempt
and retry only the identical authorized operation and inputs. Missing/malformed
required cells remain visible and prevent a complete report. A scientific or
implementation defect discovered after opening cannot be repaired by silently
changing the confirmatory pipeline: preserve results, explain the limitation,
and label any necessary corrected analysis as a post-opening deviation.

## 10. Execution calendar and verification

| Deadline/window | Required output | Check that closes the stage |
| --- | --- | --- |
| Sep 29–Oct 4 | Clean implementation base; complete v3 protocol/pilot specification, corruption operators/fallback, versioned validators, shared seals, source access separation, pilot instrumentation | Cache-affecting code/config frozen before extraction; historical artifacts untouched; old/v3 protocol and seal tests pass; no novel representation/outcome access |
| Oct 5–11 | Loss value/backward fixtures, paired sampler/init checks, learnable-fixture checks, fresh parity/caches, three full 20-epoch pilots | Every pilot complete with four checkpoint/score records and diagnostic/timing evidence; source/extractor code hashes stable |
| Oct 12–18 | Complete successor interfaces and full fixture/report rehearsal; fresh bound caches/pilots; fixed geometry panel, nine development conditions, dependency and capacity ledger | New release/evidence bindings, analysis/report, allocation, current storage and researcher availability pass before selection; otherwise record blocker/amendment |
| Oct 19–Nov 1 | 27 clean-development selection runs and selected rates | Complete attempt ledger; three valid seeds per selected candidate; exact ranking rule reproduced |
| Nov 2–15 | Nine fresh all-100-action final heads | Paired 20-epoch runs, immutable checkpoints, complete source/config/code provenance |
| Nov 16–29 | Independent repeat of evaluator/run-set/lock audit; audit the report/figure templates already rehearsed before selection | All nine heads locked; exact 180-cell matrix and query lists fixed; current capacity/seal checks pass; Thanksgiving retained for recovery |
| Nov 30–Dec 6 | One authorized novel extraction/evaluation campaign | 180 unique finite provenance-valid cells; per-query ranks reproduce every metric; all operational attempts retained |
| Dec 7–13 | Conditional interval, absolute-score/degradation curves, per-seed/LOAO tables, cost/limitations, report/poster draft | All analysis and figures regenerate from locked records; claims follow the prespecified rule |
| Dec 14–18 | Independent reproduction smoke test, final report/poster and permitted archive; tracker reconciliation | Deliverables complete, limitations explicit, no licensed data/checkpoints/private records in Git |

Test the implementation in layers. Python changes require locked dependency
sync, `python scripts/verify_workspace.py`, Ruff lint/format checks and the
relevant unit/integration suite, followed by the complete Python suite before
the scientific release. Required fixtures cover loss values/backward rules,
sampler pairing, pilot exclusion, failed-candidate selection, corruption nesting,
fallbacks, unequal-view bootstrap weighting, fixed gallery sensitivity,
cross-version seal denial, first-open ordering/concurrency, provenance mutation,
and report matrix completeness. Run scheduler shell syntax checks and GPU
parity/repeatability on the allocated hardware.

For tracker changes run its lint, typecheck, tests, build, local database reset,
database tests and security advisors. Migrate the public v3 plan with expected
row versions, returned-row conflict checks, trigger-managed version increments,
RLS and private ownership preserved. Preserve hosted task evidence and actual
minutes. Closed-week changes require an explicit audited reopen reason;
future-week plan adoption does not silently rewrite closed history. Verify
hosted Auth sign-up/redirect restrictions before enabling editing. Publish the
matching fallback and protocol bundle; do not merely redeploy an older app.

No tracker migration/deployment, experiment, or scientific code modification is
performed by this planning document. The independent-research governance and
recorded BU determination remain in force; no advisor approval is required.
Reconcile dataset-terms acceptance with private evidence, and do not invent
researcher time, approvals, or completed gates.

## 11. Completion criterion

The study is complete when the three selected recipes have nine verified final
heads, all 180 declared result cells reproduce from locked per-query evidence,
the conditional primary analysis and all descriptive tables/curves regenerate,
and the December report/poster explains absolute performance, seed variation,
cost, failures, adaptations, and limits. Deliver permitted code, configs,
manifests, compact summaries, source/license notices, and reproduction
instructions. Keep licensed poses, checkpoints, caches, full artifacts, and
private governance records outside Git.

The final answer can be positive, null, or negative. If a capacity or validity
gate prevents the declared campaign, deliver an honest blocked-study record
and amendment; that is not a completed empirical comparison. This is a final
execution design with explicit go/no-go rules, not evidence that unmeasured
GPU work or researcher availability has already been secured.
