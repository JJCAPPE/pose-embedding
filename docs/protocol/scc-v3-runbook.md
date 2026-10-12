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

Use the frozen successor wrapper for the CPU stages below and the reviewed
external controller for `caches`, `pilot`, `corruptions` and `timing`. The
original GPU invocation failed on an exclusive-process SCC GPU: its persistent
monitoring parent initialized CUDA before the scientific child. Preserve that
failed attempt and release `731938a`; do not use that parent GPU path again.
The external controller keeps its parent CUDA-uninitialized and performs actual
GPU allocation/memory probes in short-lived children that exit before each
scientific stage. It requires a hash-bound, passing allocated diagnostic first.
Allocated diagnostic job 8028141 passed independent verification: a held CUDA
context blocked its probe, then two sequential probes passed with a
CUDA-uninitialized parent. Its evidence permits the corrected cache invocation;
it does not establish cache or scientific admission success.

Both controllers serialize operations using the same advisory lock and start
one scientific subprocess at a time. They write immutable attempts under
`study-v3/operations/` and scientific output under
`study-v3/revisions/execution-r1/attempts/`. Each command, log, status and resource
sample is retained. Every 60 seconds it records system RAM, child-process-group
RSS, `nvidia-smi`, filesystem free bytes and project quota. A failed monitor,
reserve breach, or allocated-RAM breach terminates the child process group and
retains the failure. Scheduler TERM/HUP also cleans up the child group; after
an uncatchable kill, an absent outcome is an incomplete attempt, never success.

The reviewed external GPU tools are retained at
`study-v3/operations/week5-gpu-tools/20261011T231839Z/`, with `tools.json`
SHA-256 `9e7aaee8832cb6fa5481f16eb50d44c802f5deff8eb80ccfc9010f3248dd4ad0`.
Their source is archived in `scripts/operations/`; invoke the verified transferred
copies from the clean frozen checkout, without copying them into that release.
The 52 design and five scientific hashes remain unchanged. Set
`V3_GPU_CONTROLLER` and `V3_GPU_QSUB` to the exact transferred paths verified
against that manifest. After successful diagnostic accounting and independent
receipt verification, set `V3_GPU_DIAGNOSTIC` to its passed summary and
`V3_GPU_DIAGNOSTIC_SHA256` to its reviewed SHA-256. The controller rehashes the
summary and its complete evidence chain before launch; a queued job, synthetic
unit test or unverified file is not a passing receipt. The diagnostic itself is
synthetic, creates no scientific cache and does not authorize selection.

```bash
V3_GPU_TOOLS="$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-gpu-tools/20261011T231839Z"
V3_GPU_CONTROLLER="$V3_GPU_TOOLS/pose-week5-run-gpu.py"
V3_GPU_QSUB="$V3_GPU_TOOLS/pose-week5-gpu.qsub"
V3_GPU_DIAGNOSTIC="$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-gpu-diagnostic/20261011T231839Z/summary.json"
V3_GPU_DIAGNOSTIC_SHA256=b608b95a18ff02ceee2467f3e7025dce8e57f04dcafd65406a2515b156b51395
```

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
: "${V3_GPU_CONTROLLER:?Set the verified transferred controller path}"
: "${V3_GPU_QSUB:?Set the verified transferred scheduler wrapper path}"
: "${V3_GPU_DIAGNOSTIC:?Require the independently verified passed diagnostic}"
: "${V3_GPU_DIAGNOSTIC_SHA256:?Set the reviewed diagnostic summary SHA-256}"
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" "$V3_GPU_QSUB" \
  "$V3_GPU_CONTROLLER" caches \
  --diagnostic-receipt "$V3_GPU_DIAGNOSTIC" \
  --diagnostic-sha256 "$V3_GPU_DIAGNOSTIC_SHA256" \
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
qsub -o "$POSE_EMBED_ARTIFACT_ROOT/logs" "$V3_GPU_QSUB" \
  "$V3_GPU_CONTROLLER" pilot --method contrastive \
  --diagnostic-receipt "$V3_GPU_DIAGNOSTIC" \
  --diagnostic-sha256 "$V3_GPU_DIAGNOSTIC_SHA256" \
  --cache-dir "$V3_CACHES" --remaining-peak-bytes "$V3_REMAINING_PEAK_BYTES" \
  --recorded-by "researcher-authorized Week 5 execution"
```

Set `V3_CONTRASTIVE`, `V3_CONTEXTUAL` and `V3_SUPCON` to the three actual run
directories (the method subdirectory under each new scientific attempt), then
independently validate complete budgets, all snapshot artifacts, fixtures,
input identities and cross-arm pairing:

The unrestricted CPU submission failed in preserved attempt 8035576 because
its native initialization differed from the lock. Synthetic diagnostic 8035737
confirmed the difference on the same Ivy Bridge host without AVX2/FMA, using
three native and three baseline repetitions with identical RNG state. Before
retry, use the reviewed runtime wrapper below: its allocation requests AVX2,
then checks actual CPU flags and exact native locked initialization
`035a3e5e57569c0ae765b797f705b3a9f70353a6832fcb757c7622ebfa9b3284`
before invoking the unchanged full validator. A requested resource or forced
dispatch setting cannot substitute for that native reproduction check. This
preserves source, checks, tolerances, seeds, physical batches and duration.
Include the narrower eligible CPU queue pool in the dated capacity forecast.

The transferred bundle's `tools.json` SHA-256 is
`797e180b1be91171e018961d11238e2468411195fbcaef2520bb0ad46bdf0d9d`;
Python wrapper SHA-256 is
`79acbae9fe8aac4f80149a00cb48029b72370753a9bc85e6fd1edcea87ae603f`
and qsub wrapper SHA-256 is
`786553498785508a1ac59d169b0327c2f5d190bd4556f420849a529f20faefdb`.
Verify these immutable bytes, source/dependencies, seals, capacity and absence
of active or duplicate attempts before a single submission. The reviewed
administrative launcher performs these checks. This direct invocation records
the allocated wrapper interface; do not blindly rerun it after a submission.
Inspect scheduler state and preserved launch intent first.

```bash
qsub -terse -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-cpu-retry-tools/20261012T153900Z/pose-week5-retry-pilot-validation.qsub" \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-cpu-retry-tools/20261012T153900Z/pose-week5-retry-pilot-validation.py" \
  --diagnostic-verification "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-init-verification/20261012T153404Z/verification.json" \
  --diagnostic-verification-sha256 5e5de4bb155e6b22ea486416549d4a080207872e902e1a33ad5173b17ff01cad
```

Retry 8035829 was submitted October 12 at 15:44:10.970322 UTC and its actual
AVX2/FMA flags plus three exact native locked-hash repetitions passed. Its
unchanged full validator subsequently passed and independent completion review
verified all 122 evidence bindings, accounting, native preflight, full numerical
validation, resources and seals. The acceptance receipt is
`study-v3/operations/week5-pilot-validation-verification/20261012T162541Z/verification.json`,
SHA-256 `3716107eecbe3561c29c87d7f547f569816ad8e8a359b4f412434d4a71a25a7d`.
Do not resubmit the command above. Inspect the retained launch intent at
`study-v3/operations/week5-launches/20261012T154408Z/` and existing accounting
first. A passed pilot validator does not establish complete campaign admission.

Use the three validated epoch-20 pilot heads for all nine complete development
conditions. The launcher extracts each 18,929-row corrupted encoder cache once,
then retains 27 query projections and 27 engineering results. Three clean
gallery projections are also retained with scientific sidecars. No scores
select a condition, head, recipe, threshold or retry.

The reviewed corruption launcher was staged before submission under
`study-v3/operations/week5-corruption-launch-tools/20261012T160355Z/`:

- `pose-week5-launch-corruptions.py`: SHA-256
  `a3530454c45e172bd9b8d7e222fa0bc18ba1189d0d162c4251dc51742480c444`;
- `test_pose_week5_launch_corruptions.py`: SHA-256
  `61ce601c8f87596d54b1bf27cf22274bfb0dadb7640ba4b9eafcb6f103e2dd92`;
- `tools.json`: SHA-256
  `c9c28703aa9fc40edc724d1b93e5f03e815906ff2f040657cb36507a5f025a6d`.

Four focused guard tests and independent review passed. The launcher requires
the independently passed **8035829** completion receipt from verifier
`a3a8a73847bf2969eb886d456e68bf657ba27362402a30cd9dc62ca003feb4aa`,
rehashes its metadata evidence, and rechecks the current pilots, caches, geometry,
release, locks, dependencies, GPU diagnostic, seal and resource reserve. Prior
or uncertain corruption submissions block this one-off command. The following
command records the already executed submission; **do not rerun it**.

```bash
cd "$POSE_EMBED_RELEASE"
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python3.11 \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-corruption-launch-tools/20261012T160355Z/pose-week5-launch-corruptions.py" \
  --pilot-validation-verification "${V3_PILOT_VALIDATION_VERIFICATION:?Set the independently passed 8035829 receipt}" \
  --pilot-validation-verification-sha256 "${V3_PILOT_VALIDATION_VERIFICATION_SHA256:?Set its verified SHA-256}"
```

This invokes the unchanged reviewed GPU controller with
`avx2,cpu_arch=sapphirerapids,cpu_type=Gold-6426Y`, matching the recorded pilot
GPU hosts. Later admission recomputes CPU projections with exact array equality;
AVX2 or a matching model name alone does not establish that replay will pass.
Use compatible native CPU/BLAS settings and retain actual runtime evidence.

Job 8035983 was submitted October 12 at 16:27:02.731983 UTC and was queued
at approximately 16:27:50 UTC. Its launch record is
`study-v3/operations/week5-launches/20261012T162658Z/launch.json`
(SHA-256 `530ed00fc8d258d7c3bf4797fe81f4c38690aff988853490f0f70ea37f96470c`).
Do not duplicate that submission; inspect its existing intent and scheduler state.

The corruption completion checker was staged at
`study-v3/operations/week5-corruption-verification-tools/20261012T165607Z/`.
`pose-week5-verify-corruptions.py` has SHA-256
`379bc89bf063f933dd2fde4e078156c603d6eb00210ab8fdee1c1ff361e1345f`;
`test_pose_week5_verify_corruptions.py` has SHA-256
`9452ba1322ebb748a09592d19ef1c9520a8a05169431005669230b8b4f8de806`;
`tools.json` has SHA-256
`2f9cfc2f707c54412c87fe11baee6b6184f898a92b545af798e77084120a3c06`.
Seven focused tests and independent review passed. The checker binds job
8035983 and operation `20261012T162852Z-8035983-corruptions`, checks all 135
commands, 67 GPU preflights, complete output metadata, prerequisite receipts,
resources, seals and accounting, and preserves a fresh verification receipt.
It only reads metadata and checks archive sizes; full admission validation
(full A), including scientific tensor hashes and numerical replay in an
allocation, remains mandatory. The command below subsequently executed after
successful terminal accounting; its passed receipt was written October 12 at
18:31:21.614571 UTC, binding 927 evidence files. The receipt recorded_at marks
review start (18:30:49.548448 UTC), not completion. Its receipt is
`study-v3/operations/week5-corruption-verification/20261012T183049Z/verification.json`,
SHA-256 `4b071bc3a900aa347171998b5dd224885391d019b604763f6d55a5a50af50bd5`.
This is a historical invocation, not a request to rerun it. It clears
`PYTHONOPTIMIZE` so assertions execute and disables bytecode writes:

```bash
cd "$POSE_EMBED_RELEASE"
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python3.11 \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-corruption-verification-tools/20261012T165607Z/pose-week5-verify-corruptions.py" \
  --launch-receipt "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-launches/20261012T162658Z/launch.json" \
  --launch-sha256 530ed00fc8d258d7c3bf4797fe81f4c38690aff988853490f0f70ea37f96470c
```

Before timing, independently review successful corruption accounting, immutable
operation/outcome, all command and GPU-preflight outcomes, resource samples and
both seals. Require nine complete 18,929-row encodings, 27 paired query
projections, three clean gallery projections and 27 engineering results with
the fixed conditions, seed 7, methods and input bindings. Check all nine full-query
geometry summaries and jitter fallback denominators. Scientific archive hashing
and replay stay inside allocations. No accuracy or loss-improvement floor is a
completion criterion. Submit timing only after this review and a fresh
allocation, duplicate-attempt and resource check.

The guarded timing launcher was staged under
`study-v3/operations/week5-timing-launch-tools/20261012T170831Z/`:

- `pose-week5-launch-timing.py`: SHA-256
  `4ce08cfe34bae6ebea2ba7145fe253fdf1b56f8db4231f9ba34f8aa6302ad6c7`;
- `test_pose_week5_launch_timing.py`: SHA-256
  `4bf1a2986568bc93f07a8f94974735b1830c3eb07d28bbac44334e54cf66d785`;
- `tools.json`: SHA-256
  `7b5d934b4c7900242aa393550f8ae1f706c48cfae0a03df561ed89889ea4b726`.

Twelve focused tests and independent review passed. The launcher requires the
actual passed corruption receipt from the checker above and its verified hash,
rehashes retained metadata, checks archive sizes, and rechecks existing pilot,
cache, geometry, source, lock, dependency, diagnostic, seal and storage bindings.
Prior or uncertain timing submissions block it. It requests the unchanged
L40S, four CPU slots, 32 GiB RAM and 12-hour allocation with
`avx2,cpu_arch=sapphirerapids,cpu_type=Gold-6426Y`. The 84 GB remaining-peak bound
is conservative, not a measured campaign forecast. It was executed once with
the passed corruption receipt above and submitted **8038355** at October 12
**18:32:58.249374 UTC**. The job was queued at approximately 18:34 UTC, then started at 18:35:49 UTC
on `ece-long@scc-j01`; eleven initial resource checks passed. Its outcome
remains pending.
**Do not rerun this one-off launcher.** Inspect the existing job and preserved
launch intent first. Full A and measured capacity remain pending.

```bash
cd "$POSE_EMBED_RELEASE"
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python3.11 \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-timing-launch-tools/20261012T170831Z/pose-week5-launch-timing.py" \
  --corruption-verification "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-corruption-verification/20261012T183049Z/verification.json" \
  --corruption-verification-sha256 4b071bc3a900aa347171998b5dd224885391d019b604763f6d55a5a50af50bd5
```

Timing keeps all 95,001
float32 rows resident and maps the locked 76,013 development-training IDs into
that matrix. Only those 80 actions enter optimization; validation and novel
actions are rejected. Each arm uses seed 7, rate `3e-4`, the same initialization
and physical batches, and 20 × 2,969 updates. These additional 178,140 engineering
updates are outside the 39 scientific runs. Batch plans, configuration hashes,
load/validation/train times and memory peaks are retained; no head is saved or
made eligible for selection/final use. Count its actual bytes and time in the
capacity ledger.

The new `study-v3/revisions/execution-r1/attempts/TIMESTAMP-JOB-timing/`
directory must retain `attempt.json`, `timing.json`, `outcome.json` and, for each
method, `timing.json` plus 20 `batch-plan-NNN.json` files. Verify 59,380 updates
per arm, paired initialization and all 20 batch hashes, exact config/input/source
bindings, positive measured loading/validation/training durations and host/GPU
memory peaks. These measurements inform capacity; they do not authorize
selection, final training or novel opening.

The timing completion checker was staged, **not executed**, under
`study-v3/operations/week5-timing-verification-tools/20261012T173820Z/`:

- `pose-week5-verify-timing.py`: SHA-256
  `85af5ae65f64695240255fa686365e4d120be6b594142c18daee8804e567072b`;
- `test_pose_week5_verify_timing.py`: SHA-256
  `379a249ef8e473eb61380d2cf3373018fb2d9d9887badd0bd4063a5280d26ca7`;
- `tools.json`: SHA-256
  `1a11fea592894967c5577eff161e90bfc3d52a562fc2573cef9aa23fe9341240`.

Twelve focused tests and independent review passed. The checker binds the actual
launch to the reviewed launcher, release, controller and corruption receipt;
verifies terminal accounting, commands, resources, seals and allocated GPU
identity; and checks all 60 batch plans and fixed timing records. Sequential
validation, loading and training durations must fit within the recorded internal
wall time. This is metadata verification: archive contents are not read or
hashed on login, and full A remains pending. **Hold the command until the timing
job has completed successfully and its actual launch receipt/hash are verified.**
The actual job is 8038355, with launch receipt
`study-v3/operations/week5-launches/20261012T183252Z/launch.json`, SHA-256
`26761143b4926c7d50d28cc1a2ad4cd1a69b638a3df008d1b5e73eb49cdd49d3`.
These launch bindings do not establish completion.

```bash
cd "$POSE_EMBED_RELEASE"
env -u PYTHONOPTIMIZE PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python3.11 \
  "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-timing-verification-tools/20261012T173820Z/pose-week5-verify-timing.py" \
  --launch-receipt "$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-launches/20261012T183252Z/launch.json" \
  --launch-sha256 26761143b4926c7d50d28cc1a2ad4cd1a69b638a3df008d1b5e73eb49cdd49d3
```

The read-only pilot-validator component diagnostic is staged, **not executed or
submitted**, at `study-v3/operations/week5-p-component-tools/20261012T184957Z/`.
Thirteen focused tests and independent review passed. Retained tool hashes are:

- `tools.json`: `0725e043737a6ceed921c1369c6d053c3acf01f7ef3975b94d9e4d74639233f1`;
- `pose-week5-measure-pilots.py`: `d692f62235aaacc3d210b1530c3239119a7826510b25cca258ccb1465367f0c1`;
- `pose-week5-measure-pilots.qsub`: `95834d5d2879606526bf16a7b9ed2347a25491d4b2de7deaa6be859744c06ebe`;
- `test_pose_week5_measure_pilots.py`: `57d4343e292d11434720a9bcd4580c719ad014ddfba702fc5e876b5bef4338a0`.

**Hold this submission** until the actual passed timing receipt from checker
`85af5ae65f64695240255fa686365e4d120be6b594142c18daee8804e567072b`
and its trusted SHA-256 are available. The root operator must first recheck
source/dependencies, receipt/tool bindings, seals, current storage/reserve,
scheduler state and absence of active, duplicate or uncertain submissions.
Inspect preserved launch intent before any retry. This requests four compatible
CPU slots, 32 GiB and 12 hours without a GPU; actual allocation/native locked
initialization are checked inside the job.

```bash
cd "$POSE_EMBED_RELEASE"
V3_P_COMPONENT_TOOLS="$POSE_EMBED_ARTIFACT_ROOT/study-v3/operations/week5-p-component-tools/20261012T184957Z"
qsub -terse -o "$POSE_EMBED_ARTIFACT_ROOT/logs" \
  "$V3_P_COMPONENT_TOOLS/pose-week5-measure-pilots.qsub" \
  "$V3_P_COMPONENT_TOOLS/pose-week5-measure-pilots.py" \
  --timing-verification "${V3_TIMING_VERIFICATION:?Set the actual independently passed timing receipt}" \
  --timing-verification-sha256 "${V3_TIMING_VERIFICATION_SHA256:?Set its trusted SHA-256}"
```

The fresh immutable operation retains per-method timings, runtime/native CPU
identity, resource samples, both seals and command/outcome evidence. It times
only the unchanged `validate_engineering_pilot` calls in persisted report-path
order **Contextual → Contrastive → SupCon**, separating setup from their sum P.
This measures **P only, not full A**, and makes no controlled cold-cache or
universal hardware-bound claim. Under the measured profile, P must be below
`48*3600/(452*1.25) = 305.84070796` seconds for the larger indivisible report
and coupled GPU-opening limit even to remain feasible; omitted T/V/report costs
make that necessary condition stricter. Passing this component alone does not
establish capacity or scientific admission. Keep full A, dated resources/queues,
remaining-work forecasts and every scientific gate separate.

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
