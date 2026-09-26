# V2 implementation and release record

Recorded 2026-09-26. The required study is **not complete**: the software supports
all 26 configurations, and no motion retrieval result is established by these
local checks. Their implementation and remaining scientific gates are documented in
[the completion map](remaining-method-adaptations.md).

## Changes delivered

- Preserved the prior verified input contract, 80/20 auxiliary class split,
  official 20 novel classes, Week 3 preprocessing/extraction work, BU confirmation,
  and historical plan/protocol. The original local working tree was preserved.
- Added a separate v2 configuration, registry and artifact namespace. The frozen
  streaming development pilot runs Contrastive then Contextual first. A separate
  configuration enables gradients through MotionBERT for the main study.
- Implemented the standard embedding objectives, shared deterministic physical
  batches, proxy optimization/state, streaming pose training, development-only
  checkpoint selection and paired comparisons. Profile runs execute real backward
  passes but cannot count as scientific runs.
- Added multi-positive retrieval with per-query self/performance exclusions,
  stable ties, Recall@K, mAP, mAP@R and MRR. Full private rank evidence remains
  outside Git; public reports contain aggregate results only.
- Added immutable attempts, failures, initialization/batch/checkpoint provenance
  and verification. Selection/final/opening locks require every declared method
  and six seeds; incomplete coverage cannot authorize the novel test.
- Added the fixed statistical plan and complete-suite report path. Inference is
  conditional on the twenty held-out action classes and eligible gallery, with
  paired training seeds and synchronized-performance cluster resampling.
- Reworked the tracker seed and guarded live migration to put the development
  pair first and retain the entire comparison as required work. No researcher
  hours or weekly closure are inferred. The fourteen weeks remain provisional.

## Local verification

- Python 3.11 locked dependency synchronization, Ruff lint/format, workspace
  verification and scheduler shell syntax passed.
- Full Python suite: **449 passed**; the subsequent cross-version seal change
  passed **32 targeted tests**, including the v2 final evaluator. Legacy training,
  extraction and test-opening commands now also respect a v2 opening ledger.
- Tracker lint, TypeScript, production build and **15 unit tests** passed.
- **20 Playwright desktop/mobile checks** passed.
- Local Supabase: **151 database tests**, the v2 seed import and security advisor
  passed. Production migration dry run identified only the new v2 migration.

These are software checks with synthetic fixtures or metadata. They do not
certify a real MotionBERT backward pass, runtime forecast or retrieval result.

## SCC rollout

The existing checkout at `~/pose-embed-scc/repo` is preserved. A separate release
checkout is prepared at `~/pose-embed-scc/releases/motion-v2`; the locked Linux
CUDA environment is stored on project storage under the artifact root to avoid
exhausting the home quota. Both the adopted data and manifest bundle are reused
only through their verified hashes.

Submit `scripts/benchmark_v2.qsub pilot configs/benchmark.v2.yaml 7` first; it runs
fresh upstream parity, three-step profiles and the paired development experiment.
The fine-tuning configuration gets a separate allocated-GPU profile. Any failed
attempt remains immutable and retries use new directories. Never run model work
on an SCC login node. All broader methods remain behind this first engineering
comparison; novel evaluation remains behind complete final-suite locks.

## Remaining experiments

All 26 adapters, the equal-budget selection campaign, immutable continuation,
supplementary matrices and final evaluation/report paths are implemented and
locally verified. Allocated-GPU validation, full runtime/storage measurements,
campaign declaration, training and scientific results remain outstanding.
No generic loss wrapper, frozen pilot, one seed or image-paper number may fill
these missing motion results. The [storage floor](v2-resource-floor.md) already
exceeds the available project quota; full launch requires additional accessible
storage and a complete measured resource forecast.

## Release observations

PR #22 merged as `b5431f0de0c545a069aa27be8106f73615242ea7` after all three
required CI jobs passed. Hosted migration `20260924223631` was applied. The live
health endpoint confirms that build, Supabase reads, project version 3 and editing
enabled; the public export contains the v2 research question and all fourteen weeks.

Initial SCC jobs `7748336` and `7748337` exited before model/data execution because
Git's directory-only `.venv/` ignore pattern did not cover the external environment
symlink. The pattern is corrected to `.venv`, which covers both forms. The failed
scheduler logs remain under the external artifact root; subsequent submissions
must use new job IDs and output directories. This operational failure provides no
retrieval, timing or memory result.

## First allocated optimizer profiles

All rows below use release `0ef858379c36`, seed 7, three optimizer steps,
physical P=8/K=4, float32, fresh successful MotionBERT parity and development
training inputs. These are capacity measurements, not retrieval comparisons.

| SCC job | Track and method | GPU | Peak allocated bytes | Three-step seconds | Outcome |
| --- | --- | --- | ---: | ---: | --- |
| 7748366 | Frozen Contrastive | L40S | 2,875,836,928 | 3.086 | Passed |
| 7748366 | Frozen Contextual | L40S | 2,875,836,928 | 2.239 | Passed |
| 7748367 | Fine-tuned Contrastive | L40S, 44.42 GiB available capacity | — | — | CUDA out of memory |
| 7748414 | Fine-tuned Contrastive | A100 80 GB PCIe | 62,739,530,240 | 8.604 | Passed |
| 7748414 | Fine-tuned Contextual | A100 80 GB PCIe | 62,739,530,240 | 7.729 | Passed |

Immutable evidence is under the SCC artifact root in
`benchmark-v2/pilots/20260926T202750Z-7748366-0ef858379c36`, the sibling
`7748367` directory, and `20260926T203556Z-7748414-0ef858379c36`.
The unsuccessful fine-tuning attempt is retained; the successful retry changes
only GPU capacity, without reducing the batch or precision. Three steps exclude
setup and do not support a training-time or comparative-speed claim.

Job `7748366` continues the frozen paired development pilot. After the larger
GPU profiles passed, `7748592` was submitted for the fine-tuned paired pilot;
it runs Contrastive and then Contextual on an A100 allocation. No broader
method GPU experiment is submitted before this priority comparison. Novel
classes remain unopened. Running jobs retain their original release checkout
while subsequent adapter implementation proceeds in separate local worktrees.

## Adapter integration checkpoint

The integration branch now includes IBC, ProxyNCA++, HIST, all three Metrix
variants, DRML-PA, R-Margin+S2SD MSDFA and MHGL. Each has a source/variant
record; synthetic implementation evidence is distinct from GPU feasibility
and measured retrieval outcomes. DRML passed 136 integrated checks. The S2SD
component/integration suite passed except four synthetic dimension-fixture
errors, which were corrected; all eight subsequent S2SD runner checks passed,
including optimizer corruption and active delayed-capacity profiling. MHGL
passed 13 component/real-small-DSTformer checks, including frozen/fine-tuned
updates and optimizer tamper rejection; 125 companion integration checks passed.
The original local working tree and running SCC release remain preserved.

## Full adapter integration

All 26 configurations are now callable on the integration branch. DIML passed
164 integrated checks plus the corrected CLI fixture suite (17 checks). AVSL
passed 221 integrated checks and 16 component/optimizer checks, including
licensed source oracles and post-warmup capacity state. DiVA passed 234 integrated
checks and 19 focused checks including actual scaled beta optimizer rates.
These counts overlap and are not a total unique-test count.

The frozen Contrastive seed-7 pilot completed on SCC at
`2026-09-26T21:38:43.766106+00:00` in job `7748366`, release `0ef858379c36`.
Its 1,000 updates used 4,120.33 seconds total, of which summed update timing was
574.00 seconds; validation/input overhead therefore dominates this short pilot.
Peak allocated GPU memory was 2,893,729,792 bytes and its checkpoint was
187,778,419 bytes. Contextual and the fine-tuned pair are still running at this
recording. No paired retrieval result or novel-test outcome is asserted.

## Completed local integration checks

The complete integrated Python suite passed **791 tests** on September 26.
Ruff lint/format (120 Python files), workspace policy, Git diff checks and all
four affected scheduler scripts' Bash syntax passed. The updated tracker passed
lint, TypeScript, **15 unit tests** and a production build. These current checks
supplement the earlier foundation-release database and browser evidence.

Continuation fixtures prove exact split-versus-uninterrupted state for common
training, warmup, Metrix random mixing, delayed S2SD, DiVA memory/EMA, campaign
candidate/final runs and secondary interventions. Audits checked all 26 optimizer
parameter sets, compatible paired initialization, structural descriptor replay,
secondary exclusions and selection/continuation provenance. The exact archived
action-head code bridge is supported by bitwise output, gradient and RNG checks.

The final workload is 468 main development runs, 156 main final runs and 552
secondary training runs. Opening requires all 432 final checkpoints. Separate
main and descriptive secondary reports require their complete declared result
matrices. Full profiles now exercise real post-warmup optimizer paths and a fixed
128-item retrieval prefix; metadata-only verification of the actual development
prefix found 128 items, 10 actions and at least 11 eligible positives per query.
No additional motion inference or retrieval score is implied by that check.

The current priority jobs retain release `0ef858379c36`. Publish subsequent
implementation through a separate release and environment; a full-profile job
must verify their completed fine-tuned comparison before broader GPU work.
