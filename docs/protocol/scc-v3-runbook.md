# SCC execution for the frozen v3 study

The [v3 protocol](protocol-v3.md) and [final plan](../../plan/research-plan.v3.md)
govern these commands. Use a clean committed release, Python 3.11 and the locked
environment. Perform tensor processing only inside Grid Engine allocations.
Historical releases, artifacts and run manifests remain immutable.

## Active SCC installation

The September 29 installation uses the verified release and rebound manifest
bundle recorded in [Week 3 readiness](week-3-v3-readiness.md). Start from:

```bash
source "$HOME/pose-embed-scc/environment.sh"
cd "$POSE_EMBED_RELEASE"
```

`$HOME/pose-embed-scc/current` points to the same committed scientific release.
The environment selects the v3 manifest bundle while retaining the original
data and artifact roots. This is the historical Week 3/4 installation; use the
successor section below for Week 5 after its release is verified. The initial
preparation procedure is retained here for provenance; it is already complete.
The [JSON loader recovery](../decisions/0005-v3-json-protocol-recovery.md) records
the preserved failed freeze and corrected source binding.

## Initial root registration and preparation

Keep the existing `POSE_EMBED_DATA_ROOT` and `POSE_EMBED_ARTIFACT_ROOT` from the
SCC environment. Do not change the artifact environment root to `study-v3`.
Set `POSE_EMBED_MANIFEST_SET` to the adopted historical manifest-set file.

Audit every local and remote historical artifact directory, including retired
release-local artifact directories. An absent known directory, unreadable
directory, dangling opening link or possible opening record needs resolution.
Do not infer absence from a misspelled ledger filename. The known ledger paths
are `locks/test-opening.v1.json`, `benchmark-v2/locks/test-opening.json`,
`study-v3/locks/test-opening.v3.json`,
`study-v3/revisions/execution-r1/locks/test-opening.v3.json` and
`locks/dataset-opening.json`.

For a different host, retain an immutable audit JSON with `schema_version: 1`,
`status: sealed`, the actual `host`, an ISO timestamp with timezone in
`recorded_at`, and the adopted `source_inventory_sha256`. Its `roots` array
must give every absolute `path`, `status: sealed` and `readable: true` based on
an actual audit. A schema-valid assertion without inspection is not evidence.
Copy this compact audit to the canonical artifact tree and pass it with
`--external-audit`. A final audit must be refreshed at the later authorization
stages; a Week 3 snapshot does not establish future absence.

Register all accessible historical roots in one command, repeating `--root`
and `--external-audit` as needed:

```bash
uv run pose-embed study-v3 register-roots \
  --root "$POSE_EMBED_ARTIFACT_ROOT" \
  --root "$HOME/pose-embed-scc/artifacts" \
  --external-audit "$POSE_EMBED_ARTIFACT_ROOT/provenance/local-seal-audit.json"
```

Registration writes an immutable registry under the data root and a binding
at each artifact root. It recursively rejects opening records. Do not remove
these pointers to change roots. An identical retry can finish pointer
publication after an interruption; a changed registry is rejected.

Create the external scheduler-log directory, then submit the CPU preparation:

```bash
mkdir -p "$POSE_EMBED_ARTIFACT_ROOT/logs"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/prepare_v3.qsub
```

This checks quota and seals, packages the auxiliary-only source, computes the
lower-median training-only fallback, verifies the checkpoint/upstreams,
rebinds unchanged manifests and the development episode, and freezes the
resolved protocol/design. The original trusted pickle is necessarily
deserialized for packaging; novel entries are excluded before annotation
inspection, preprocessing or model access. The immutable output directory
and scheduler exit are printed and retained for every attempt.

Successful preparation must produce both
`study-v3/locks/protocol.v3.json` and `study-v3/locks/design-lock.v3.json`.
Inspect the successful job accounting and the bound files before advancing.
The checked-in template alone cannot authorize a scientific run.

## Week 4: fresh caches and complete pilots

The active environment already points `POSE_EMBED_MANIFEST_SET` to the verified
preparation directory's `manifests/manifest-set.json`. Submit:

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3.qsub caches
```

The launcher requests `gpu_type=L40S` and requires one scheduler-visible L40S.
Its resource spelling was verified on September 29. Recheck availability with
`qgpus` on SCC before
submission, as described in the [BU GPU guide](https://www.bu.edu/tech/support/research/software-and-programming/gpu-computing/).
It records fresh parity,
two complete 95,001-row extractions in separate processes, repeatability and
the 76,013/20/18,929-row development caches. It validates all cache bindings.
Retain both repeats and all evidence. Historical caches are never reused as v3.

After that job succeeds, set `POSE_EMBED_V3_CACHES` to its new immutable attempt
directory and submit one complete pilot for each recipe:

```bash
qsub -v POSE_EMBED_V3_CACHES="$POSE_EMBED_V3_CACHES" \
  -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3.qsub pilot contrastive
qsub -v POSE_EMBED_V3_CACHES="$POSE_EMBED_V3_CACHES" \
  -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3.qsub pilot contextual
qsub -v POSE_EMBED_V3_CACHES="$POSE_EMBED_V3_CACHES" \
  -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3.qsub pilot supcon
```

Each pilot runs the 1,000-update synthetic wiring fixture before the real
20-epoch development run, seed 7 and learning rate `3e-4`. Preserve the four
checkpoint/complete-score records, epoch-zero diagnostics, paired hashes,
finite/collapse checks, timings, memory and every failure. These records are
explicitly ineligible for learning-rate selection and final training.

The launcher checks the bounded Week 4 increment plus reserve on every job.
This is separate from the October 18 full-campaign allocation, availability,
storage and measured-time gate. Selection and novel evaluation remain closed.

## Week 5: execution-r1 successor

[Decision 0006](../decisions/0006-v3-execution-completion-amendment.md) requires a
fresh successor release and evidence. It does not authorize selection or opening.
Complete repository tests and the full fixture/report rehearsal before freezing.
Keep release `2897f4fe4c1fb1857432a0e92a7391dde68307f5`, its environment, locks,
five caches, three pilots and all failed attempts. Install a new immutable
checkout at the verified successor commit; never pull or copy files into an
active release. Check its exact Git SHA, clean status, `uv.lock`, pinned upstream
hashes and workspace verification on SCC before each job. A matching filename
or successful upload alone is not synchronization evidence.

Inspect the existing local `remote` tmux session first with `tmux list-panes`
and `tmux capture-pane`. Identify the SCC host and an idle shell before sending
commands. On that shell inspect `hostname`, `pwd`, active processes,
`qstat -u "$USER"`, `qgpus`, `df -B1 "$POSE_EMBED_ARTIFACT_ROOT"` and
`LC_ALL=C pquota textconv`. Do not interrupt another process or infer a GPU
allocation from the login session. Save these observations outside the release.
Retain `$HOME/pose-embed-scc/WEEK5-STATUS.txt` in that session with the current
step, immutable release, job IDs/logs, artifact paths, blockers and next command;
copy each meaningful status into the operation evidence before updating it.

The successor wrapper is CPU-only unless the submission explicitly requests
the L40S resources below. It serializes operations using an advisory lock and
starts one scientific subprocess at a time. It writes immutable attempts under
`study-v3/operations/` and scientific output under
`study-v3/revisions/execution-r1/attempts/`. Each command, log, status and resource
sample is retained. Every 60 seconds it records system RAM, child-process-group
RSS, `nvidia-smi`, filesystem free bytes and project quota. A failed monitor,
reserve breach, or allocated-RAM breach terminates the child process group and
retains the failure. Scheduler TERM/HUP also cleans up the child group; after
an uncatchable kill, an absent outcome is an incomplete attempt, never success.

Before each submission set `V3_REMAINING_PEAK_BYTES` from the current itemized
remaining forecast. It is an upper bound held conservatively during that job;
reduce it only between jobs using verified retained bytes. The 120-decimal-GB
campaign-wide envelope includes predecessor and successor files and slack;
do not subtract the envelope again from current free space. The wrapper checks
`min(filesystem_free, quota_remaining) >= 200*2**30 + 1.25*remaining_peak_bytes`
before launches and during work. Keep all evidence if resources fail; revise
the measured schedule or obtain capacity rather than silently changing recipes.

Run the complete CLI/report and opening-fault rehearsal in a CPU allocation
before preparation. Its child process unsets the real data/artifact-root
environment variables and uses a new fixture directory under its immutable
operation attempt. Preserve all fixture attempts, `software-rehearsal.json`,
JUnit output and command logs there. The parent checks the actual registered
dataset remains sealed before and after the child; fixture opening is not an
opening of licensed data.

```bash
: "${V3_REMAINING_PEAK_BYTES:?Set the measured remaining peak-byte forecast}"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3_execution.qsub rehearsal \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Set `POSE_EMBED_MANIFEST_SET` to the **adopted historical v1 manifest-set** for
the prepare command, not the original v3 rebound bundle. Root registration and
the adopted training-only fallback are reused through verified bindings. No
new source selection or fallback computation occurs:

```bash
: "${V3_REMAINING_PEAK_BYTES:?Set the measured remaining peak-byte forecast}"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" -l h_rt=02:00:00 \
  scripts/study_v3_execution.qsub prepare \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

After successful accounting and independent inspection of predecessor/successor
bindings, select its newly frozen manifest bundle. Preserve the original
environment file; save a separate successor environment and its hash.

```bash
export POSE_EMBED_MANIFEST_SET="$POSE_EMBED_ARTIFACT_ROOT/study-v3/revisions/execution-r1/manifests/manifest-set.json"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  -l gpus=1,gpu_type=L40S,gpu_c=7.0,gpu_memory=16G \
  scripts/study_v3_execution.qsub caches \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

`caches` reuses the existing five-cache recipe with explicit successor protocol
and output paths: fresh parity, two separate full 95,001-row extractions,
repeatability and all three development caches. Set `V3_CACHES` to the new
scientific output path printed in the operation manifest, then run the separate
CPU validator. It rehashes all five files, validates every sidecar/manifest and
reruns repeatability with a fresh quota report.

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3_execution.qsub \
  validate-caches --cache-dir "$V3_CACHES" \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Run the fixed geometry panel before producing corruption scores. Review found
that release `731938a`'s convenience launcher supplies an `attempts/` destination,
while its geometry validator requires the existing `locks/` subtree. Preserve
the frozen release and invoke the unchanged geometry CLI through the reviewed
operational wrapper below. It uses `locks/geometry/<unique-attempt>`, retains the
same operation/seal locks and resource monitoring, and independently validates
the resulting panel. This changes the invocation only, not the scientific code,
panel selection or corruption operators.

The immutable SCC wrapper is
`study-v3/operations/week5-tools/20261011T222146Z/additional-checks.py`, SHA-256
`14b6799627cd506ae5733c5d84e410b0d8656a3dca6b1d0e05c99e7272ede5cc`.
Its companion qsub file records the exact scheduler environment. Verify both
against the adjacent `tools.json` before submitting from the frozen checkout:

```bash
V3_WEEK5_TOOLS="$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-tools/20261011T222146Z"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" "$V3_WEEK5_TOOLS/additional-checks.qsub" \
  --mode geometry --expected-release 731938a157be575ee433d6939876f8ca0b95e459 \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

The same wrapper's `--mode additional-checks` runs supplementary isolated
analysis/failure-path tests and freezes both dependence tables from locked IDs
only. It does not load novel poses. Retain its JUnit, metadata hashes, source
hashes and seal observations alongside the initial software rehearsal.

Run each pilot separately, waiting for accounting and inspecting its preserved
outcome before submitting the next. Repeat this exact command with `contextual`
and `supcon`; do not submit the three jobs concurrently.

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  -l gpus=1,gpu_type=L40S,gpu_c=7.0,gpu_memory=16G \
  scripts/study_v3_execution.qsub pilot --method contrastive \
  --cache-dir "$V3_CACHES" --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Set `V3_CONTRASTIVE`, `V3_CONTEXTUAL` and `V3_SUPCON` to the three actual run
directories (the method subdirectory under each new scientific attempt), then
independently validate complete budgets, all snapshot artifacts, fixtures,
input identities and cross-arm pairing:

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" scripts/study_v3_execution.qsub \
  validate-pilots --cache-dir "$V3_CACHES" \
  --pilot-dirs "$V3_CONTRASTIVE" "$V3_CONTEXTUAL" "$V3_SUPCON" \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Use the three validated epoch-20 pilot heads for all nine complete development
conditions. The launcher extracts each 18,929-row corrupted encoder cache once,
then retains 27 query projections and 27 engineering results. Three clean
gallery projections are also retained with scientific sidecars. No scores
select a condition, head, recipe, threshold or retry.

```bash
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  -l gpus=1,gpu_type=L40S,gpu_c=7.0,gpu_memory=16G \
  scripts/study_v3_execution.qsub corruptions --cache-dir "$V3_CACHES" \
  --pilot-dirs "$V3_CONTRASTIVE" "$V3_CONTEXTUAL" "$V3_SUPCON" \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  -l gpus=1,gpu_type=L40S,gpu_c=7.0,gpu_memory=16G \
  scripts/study_v3_execution.qsub timing --cache-dir "$V3_CACHES" \
  --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Wait for the corruption job before submitting timing. Timing keeps all 95,001
float32 rows resident and maps the locked 76,013 development-training IDs into
that matrix. Only those 80 actions enter optimization; validation and novel
actions are rejected. Each arm uses seed 7, rate `3e-4`, the same initialization
and physical batches, and 20 × 2,969 updates. These additional 178,140 engineering
updates are outside the 39 scientific runs. Batch plans, configuration hashes,
load/validation/train times and memory peaks are retained; no head is saved or
made eligible for selection/final use. Count its actual bytes and time in the
capacity ledger.

The Week 4 cache job took 94 minutes 4 seconds, independent cache validation
about 6 minutes 16 seconds, and each pilot roughly 8–9 scheduler minutes. The
clean query extraction took about 6 minutes 49 seconds, so nine corrupted
extractions alone suggest roughly 61 minutes before added telemetry, validation,
projection and scoring. These are historical planning inputs, not successor
measurements or reservations. Retain `qacct -j JOB_ID` for each new job. Use
extraction sidecar preprocessing/encoding/serialization timings, independent
hash/validation timings, timing-run loading/training measurements and command
wall times for projection/retrieval. Command times include mandatory input
validation; avoid counting nested durations twice in the total forecast.

Construct the measured admission records from the exact typed models in
`protocol_v3_campaign.py`. The corruption receipt binds the verified geometry
summary, nine encodings and 27 results; admission independently replays their
bindings and ranks. Analysis must bind the full fixture/report rehearsal and
independent cache/pilot validators. Capacity needs current filesystem/quota,
all measured stages and memory limits, actual retained bytes, remaining work,
dated queued-access windows and researcher-confirmed availability. Ordinary
queued access is not a reservation. Preserve the confirmed 5 normal/10
contingency hours per week and treat Thanksgiving's unspecified availability
as no guaranteed minimum, never as measured zero work. `authorize-selection`
must validate the full immutable evidence set; these commands never create a
selection authorization, final lock or novel opening implicitly.

At the later authorized novel opening, the opening command automatically records
a fresh allocation, remaining job wall time, L40S VRAM, available/allocated RAM,
filesystem/quota and remaining-calendar check. It uses the bound admission
forecast, including the storage reserve, complete-job slack and confirmed
delivery hours. Run it inside a valid allocation with enough wall time left for
the complete measured job. Every check is retained under the execution revision's
`operations/opening-capacity/`; a failed check leaves the dataset sealed. Verify
SCC `qstat -xml` job start/host/slot fields and `qstat -j` resource requests during
the allocated rehearsal. Existing opening records replay their bound historical
receipt without probing current hardware or changing the original authorization.

## Retired workflow and cleanup

The `benchmark_v2*.qsub` and `extract_motionbert_week3.qsub` scripts are
historical reproduction tools. Do not use them as v3 launchers. Their matching
protocols and evidence remain versioned so earlier results can be audited.
Remove superseded active release links and rebuildable dependency environments
only after checking active jobs and retaining the recorded release/lock hashes.
Never remove original inputs, historical caches, checkpoints, run manifests,
failure evidence or opening records to reclaim quota.
