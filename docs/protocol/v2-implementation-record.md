# V2 implementation and release record

Recorded 2026-09-26. The required study is **not complete**: the software supports
14 of 26 configurations, and no motion retrieval result is established by these
local checks. Twelve full method adaptations remain required in
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

## Outstanding scientific implementation

The required twelve rows need architecture/optimizer/scorer adapters and faithful
component tests, including AVSL's learned scorer. Equal tuning budgets and final
training duration must be declared and measured before selection. Supporting
ablations, training-noise experiments and supplementary motion corruptions also
require their own locked run matrices. No generic loss wrapper, frozen pilot,
one seed or image-paper number may fill these missing motion results.

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
