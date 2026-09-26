# Equal-budget motion selection campaign

Result-blind design recorded September 26, 2026, while the prioritized SCC
Contrastive/Contextual development pilots are running. No novel outcomes have
been opened. This specification fills the selection-grid requirement in
protocol-v2; it does not claim the full campaign has been run or is affordable.

Each of the 26 methods has three candidates: **original, half and double** all
of its declared learning rates together. Method-specific ratios are preserved
(e.g. fast proxies, learned class boundaries and auxiliary graph parameters).
All other recipe, optimizer, warmup, architecture, scorer and data settings stay
fixed at the documented motion adaptation. This is a deliberately narrow tuning
space around each method's published recipe; it does not establish globally
optimal hyperparameters for every algorithm.

Each candidate has six paired seeds, the same physical P×K batches and the same
full update/validation budget. Thus selection requires **468 completed
candidate/seed runs**, followed by **156 selected final runs**. Mean development
Recall@1 across six seeds selects candidate and step per method. Exact candidate
ties prefer original, then half, then double; within a candidate, exact ties
prefer the earliest eligible step after full warmup/delayed components. Selection
never uses novel data. The 512- and 1536-dimensional comparison groups stay separate.

The earlier two-method runs are engineering pilots, disclosed with their original
attempts, failures, outcomes and costs. They are ineligible to choose a final
checkpoint or expand a method's candidate grid. Their role is to verify feasibility
and the paired training/evaluation path. Numerical pilot outcomes must not be used
to change this grid silently. Any further development-driven amendment must be
explicitly versioned, retain the old trial ledger and occur before novel opening.

A campaign declaration must precede every candidate attempt. It binds a fresh
trial directory, complete GPU profiles, all prior engineering trial roots, source
code, configurations and the exact candidate grid. Selection audits every attempt
in that directory, including unsuccessful ones. A retry requires an immutable
operational-failure review; numerical instability cannot be relabeled operational.
No successful candidate run can be omitted, and duplicate successful cells fail
selection. A numerical failure keeps the complete-campaign gate closed pending an
explicitly recorded result-blind treatment, rather than silently benefiting from
extra tuning attempts.

The provisional full budget is 50,000 total updates, including warmup. Actual
profiles must measure every method's complete backward/optimizer path, including
S2SD feature distillation, ProxyNCA++/HIST/AVSL post-warmup encoder gradients,
DiVA memory/EMA and custom descriptor scorers. Update-only forecasts exclude full
validation, input setup and checkpoint work; they cannot establish affordability.
Long jobs require validated continuation across immutable checkpoint segments.
Storage forecasts must include these segments and the selected checkpoints. A full
campaign must not be launched from the earlier three-step pair profiles alone.

## Implemented gate and command flow

Candidate IDs are `baseline`, `half`, and `double`. The original source learning
rates correspond to `baseline`. The machine-readable definition is
`configs/benchmark-campaign.v2.json`; declaration saves its hash and contents.

Every capacity profile now also executes the actual retrieval path on the first
`min(128, available)` records of the development-validation manifest. This common
prefix is fixed in the campaign definition and immutable profile identity. It
uses the method's real encoder, descriptors and scorer, with ordinary performance
exclusions and stable ties. Telemetry saves measured encoding/scoring time,
sample IDs and count, query/gallery/exclusion hashes, scorer policy, and complete
descriptor array bytes. It does **not** save retrieval metrics or ranks. A prefix
without eligible positives fails the check; there is no silent replacement pool.
A short prefix is a bounded capacity check, not an estimate of full nonlinear
retrieval cost. All 26 profiles must include actual GPU allocation and encoder
backward evidence plus this retrieval evidence before declaration succeeds.

```bash
pose-embed benchmark declare-campaign \
  --config configs/benchmark.selection.v2.yaml \
  --run-root "$POSE_EMBED_ARTIFACT_ROOT/benchmark-v2/campaign" \
  --profiles /absolute/profile/directories/... \
  --prior-trial-roots /absolute/engineering/pilot/roots/... \
  --priority-comparison /absolute/completed-finetuned-pair-comparison.json

pose-embed benchmark train \
  --config configs/benchmark.selection.v2.yaml \
  --candidate half --method contextual --seed 7 \
  --manifest-set /absolute/manifest-set.json \
  --parity-evidence /absolute/parity.json \
  --output-dir "$POSE_EMBED_ARTIFACT_ROOT/benchmark-v2/campaign/half/contextual/7"
```

The declared trial root must be empty and disjoint from the prior roots. Prior
inventory binds each attempt/outcome, run manifest, compact result and telemetry
file, and standalone comparison/summary. The completed prioritized fine-tuning
comparison must be revalidated against its original manifests, actual encoder
backward evidence, paired initializations/batches, and original metrics. Old pilot
code may differ from the current campaign code; the original evidence remains
bound and ineligible for selection.

Each candidate run stores an immutable `effective-configuration.json`. Its hash,
recorded optimizer recipe and checkpoint identify the actual learning-rate scale.
The base configuration path is retained separately for reliable resume commands.
Fast run checks validate this binding without reloading all 26 GPU profiles;
complete declaration and selection validation recheck all feasibility evidence.

Selection consumes exactly 468 successful cells and every recorded failed
attempt. It compares initial state, physical batch plan and input provenance
across candidates of each method/seed, as well as the common query/relevance/
exclusion policy across all methods. Method-specific structural scorers retain
separate hash-bound scoring policies. One failed numerical trial prevents the
complete selection gate from passing; it cannot be omitted or reclassified as a
scheduler failure. Operational retries are classified with an appended
`benchmark review-failure --run ... --category ... --reason ...` record.

Final training uses `--phase final` with the base configuration and **without**
`--candidate`. It automatically loads the locked winner and its selected step
budget. The 156-run final lock validates each method's effective configuration,
not one shared learning-rate scale. The evaluation/report configuration still
names the common campaign and its shared scientific conditions.

Local tests use synthetic hashed evidence to exercise the complete 468-cell
selection and 156-cell final gate, missing/duplicate/unpaired attempts,
predeclaration runs, policy changes, operational reviews, immutable effective
configuration output, and actual CPU training/profile paths. They do not certify
GPU feasibility, completed SCC runs, or novel-test results.


The completed priority pair uses an archived release. The campaign retains both
its input fingerprint and the current profiles' fingerprint. One explicit
compatibility declaration in `benchmark-campaign.v2.json` permits the exact old
and new MotionBERT code digests caused by exposing the existing action head's raw
projection; all other input bindings must match. It is directional and does not
permit any other code change. The archival pair remains engineering evidence,
not one of the 468 selection cells.


Integrity validation performs real artifact I/O. Main final collection validates
the complete development matrix once per gate, then each final run; per-run
campaign binding checks are lightweight and do not recursively reopen all 468
development checkpoints. Final evaluation and report commands retain full lock
revalidation, so repeated commands incur additional validation I/O beyond the
bounded inference profile. This cost is not part of the update-only forecast.
