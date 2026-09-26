# Immutable continuation of long benchmark runs

Long experiments can span several GPU allocations while retaining one
scientific identity, full planned update budget, batch sequence and selection
history. A segment is an operational portion of a run, never an independent
method/seed result. Existing completed runs remain immutable; runs created
before this mechanism cannot acquire missing continuation state retroactively.

## Running on a bounded allocation

For a 12-hour allocation, use a conservative 10-hour soft boundary:

```bash
uv run pose-embed benchmark train \
  --config /absolute/path/to/locked-config.yaml \
  --manifest-set /absolute/path/to/manifest-set.json \
  --parity-evidence /absolute/path/to/parity.json \
  --method contextual --seed 7 --device cuda \
  --output-dir "$POSE_EMBED_ARTIFACT_ROOT/benchmark-v2/experiment" \
  --max-segment-seconds 36000
```

`--segment-steps N` instead stops after N additional updates. The first
reached limit wins when both are supplied. Limits affect operational
boundaries, not the locked training budget or validation schedule. A soft
boundary counts setup/restore work too. It is checked after a complete
optimizer update and any scheduled validation. Leave enough allocation time
for the slowest update, validation, CPU state copies and checkpoint writes;
the two-hour allowance must be checked against measured method costs.

SIGTERM, SIGINT and SIGUSR1 request the same safe stop. They do not interrupt
an update or checkpoint a half-finished queue/EMA operation. SIGKILL, machine
failure or allocation termination during a write cannot be recovered at that
instant: the latest earlier sealed segment remains the valid resume point.
This implementation does not install a scheduler or launch a job.

A partial call returns `status: resumable`, completed/planned step counts,
the sealed manifest path/hash and an exact `next_resume_command`. It emits no
root success outcome or scientific run manifest. Run that command on the
next allocation with the same output directory, effective configuration,
method, seed, code and physical inputs. Validation progress is printed to
stderr as compact JSON without sample IDs; stdout retains the final CLI
response. Capacity profiles cannot be segmented or resumed.

## Append-only evidence

The experiment's original `attempt.json`, `initialization.json` and complete
`batch-plan.json` remain fixed. Each invocation exclusively creates the next
`segments/000NNN/` directory. Its sealed manifest contains the parent path and
SHA-256, start/end steps, complete history/batch-prefix hashes, file hashes,
best-checkpoint reference and resource telemetry. Parent and child steps must
be contiguous. Only the latest sealed segment can be extended.

Each boundary saves the latest model, criterion, optimizer and random state
to a CPU checkpoint. A new selected-best snapshot is written only at a
segment boundary when selection has improved; otherwise the existing best
file is referenced by hash. There is no extra disk checkpoint at every
validation. Best selection still considers every scheduled eligible
validation and retains the earliest maximum exactly as an uninterrupted run.
Secondary study cells retain their fixed inherited final step; intermediate
validation remains descriptive and cannot select an earlier checkpoint.

Failed/unsealed attempts remain in their own directories, including any
failure outcome. A retry appends another directory and uses the latest sealed
parent. Failed attempts must remain visible to campaign audits and operational
review; they cannot be silently dropped from the retry record. No archive is
deleted or overwritten to make space.

At completion, the normal root checkpoint, full history, result, telemetry
and run manifest are published once. `segments.json` binds the final segment
and ancestor chain. The final verifier rechecks every ancestor/checkpoint,
reconstructs the exact history, validates the selected state and compares
cumulative telemetry. Missing, modified, reordered or incomplete chains fail
verification. The required final method/seed matrix counts this as one run.

## State and reproducibility

Boundary state includes all model and criterion buffers/parameters, all Adam
or AdamW moments (including common recipes), stable optimizer parameter
mapping, current phase/step, selected-best state and result, Python random
state including its Gaussian cache, NumPy state/cache, Torch CPU state and
all initialized CUDA generator states. Resume verifies shapes, dtypes,
finite values, optimizer layout and hyperparameters before continuing.

The exact planned batch suffix is regenerated and compared with the original
plan. A new DataLoader iterator consumes a Torch base seed; RNG restoration
therefore happens after constructing that iterator. This preserves dropout
and method random draws across boundaries. The resumed job must match the
numeric runtime, deterministic settings and GPU model. Hostname, GPU UUID and
device ordinal may differ. CPU fixture tests establish exact continuation;
allocated-node GPU evidence remains required before claiming cross-job GPU
parity.

Stateful methods finish their post-optimizer hooks before sealing. S2SD
counters/private sampling state are preserved. DiVA stores queue, queue
indices/labels, EMA model, private RNG and counters; its transient pending
keys/batch indices must be empty. Fresh initialization hashes precede DiVA
bootstrap. Resume restores state and rebinds training labels, and never
bootstraps again. Memory plans/initialization evidence, the effective
campaign configuration and secondary data plan are included in shared segment
bindings when present. Secondary observed labels and source replacements must
regenerate to the identical plan before continuation.

## Resource accounting and storage gate

Segment elapsed time includes input/model setup, training, validation, CPU
snapshot creation and checkpoint writes. Post-seal integrity checks and final
metadata publication are additional overhead. Cumulative time is the sum over
sealed segments; GPU peaks are maxima, not sums. Failed-attempt costs remain
separate audit evidence (elapsed seconds in failure outcomes) and must be
included in campaign resource accounting. Uncatchable termination may have no
failure outcome; scheduler accounting is required for that missing cost.

Receipts report checkpoint size and retained bytes. With an unchanged explicit
step limit, the receipt supplies a storage scenario: for S planned segments
and checkpoint size B, reserve approximately `(2*S + 1)*B` for latest states,
worst-case new best snapshots and the final selected checkpoint. Add histories,
descriptors, failed attempts and filesystem overhead. This is a scenario,
not a measured storage guarantee; method-specific queue/teacher/proxy states
change B. For time-based limits, derive S from measured update plus validation
cost before scheduling. Check available project space against the full
candidate/method/seed campaign; resumability does not authorize deleting old
experiments or changing the scientific budget to fit capacity.
