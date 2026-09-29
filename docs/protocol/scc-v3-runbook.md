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
data and artifact roots. Continue with the Week 4 commands below. The initial
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
`study-v3/locks/test-opening.v3.json` and `locks/dataset-opening.json`.

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

## Retired workflow and cleanup

The `benchmark_v2*.qsub` and `extract_motionbert_week3.qsub` scripts are
historical reproduction tools. Do not use them as v3 launchers. Their matching
protocols and evidence remain versioned so earlier results can be audited.
Remove superseded active release links and rebuildable dependency environments
only after checking active jobs and retaining the recorded release/lock hashes.
Never remove original inputs, historical caches, checkpoints, run manifests,
failure evidence or opening records to reclaim quota.
