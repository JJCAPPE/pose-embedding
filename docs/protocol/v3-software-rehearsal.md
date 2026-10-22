# V3 software rehearsal

Run the integrated fixture rehearsal and independent admission/fault checks with:

```bash
uv run pytest tests/unit/test_rehearsal_v3.py tests/unit/test_final_bindings_v3.py tests/unit/test_opening_faults_v3.py tests/unit/test_opening_capacity_v3.py tests/unit/test_test_access.py tests/unit/test_novel_pipeline_v3.py
```

The integrated test invokes the public CLI parser and implementations for fixture
extraction, nine paired 20-epoch heads, all head projections, protocol verification,
the first final evaluation and its atomic opening, the complete 180-cell matrix,
and report generation. It then independently recertifies the saved report, including
every retained rank, provenance input, matrix cell, curve, figure, telemetry record,
and v3 analysis artifact. A schema-valid invented rank must fail recomputation.
In `test_rehearsal_v3.py`, all persistent feature caches, head runs, and attempts retain
`scientific_use_allowed: false`.

The test uses temporary data/artifact roots and an isolated dataset registry. It
does not access licensed annotations, MotionBERT weights, SCC, or project runs.
Its temporary `software-rehearsal.json` lists commands and the following seams:

- A small general-schema evaluation plan replaces real dataset cardinality in
  the command chain. The real v3 plan/manifest/lock validators are independently
  exercised on synthetic metadata with 113,945 source rows, 20 anchors, 18,924
  official queries, and 18,884 primary queries before the command chain starts.
- The fixture head is 32-to-16 dimensions. Only these dimensions are substituted
  when calling the real v3 recipe validator; epochs, seeds, physical batch,
  optimizer, learning rates, losses, margins, and regularization remain checked.
- Test-local admission adapters replace licensed-source and prior-campaign
  authorization. They verify actual fixture bytes, identities, run artifacts,
  training traces, and final lock cross-bindings. Feature validation first runs
  the real fixture hash, lineage, checkpoint, and projection validators, then
  supplies an in-memory source-eligibility value to the final evaluator/report.
  It never changes a persisted eligibility flag or a production validator.
- A hash-bound fixture receipt replaces live SCC resource measurements at the
  opening boundary. Independent resource tests cover allocation, memory, storage
  and dated-window rejection; the fixture does not claim real GPU capacity.

The independent lock tests reject missing or unpaired heads and altered lock,
selection, registry, and chronology bindings. Subprocess fault tests cover
competing openers, crash after shared seal publication, same-authorization
recovery, and refusal of another authorization or protocol after that crash.

Passing these tests is software evidence. It supplies no scientific admission,
MotionBERT parity, real-data result, capacity measurement, or novel-opening
authorization. The measured pilot, geometry, capacity, selection, nine-head lock,
and full final-opening gates still apply to every scientific run.

`test_novel_pipeline_v3.py` separately exercises the positive novel MotionBERT
backend path through the public extraction and primary-export commands. Its
synthetic aggregate covers all 120 actions, including the 20 canonical anchors,
40 official queries and a strict 20-row primary subset. Actual source hashes,
inventory, partition rules, atomic opening, canonical ledger identity,
preprocessing, jitter, pooling, cache provenance and ordered subset validators
run. Primary export must not call the encoder again; it must subset jitter
fallback and geometry records correctly. Archive validation runs with raw pose
loading and encoder loading forbidden. A forged primary feature array with a
consistent artifact hash, shape, labels and IDs must still fail source-row replay.

The positive backend test has explicit test-local adapters for the small physical
source protocol, prior design/campaign and metadata-only head admission, tiny
encoder/assets, fixture parity, clean-checkout status and opening capacity.
The production protocol parser rejects its synthetic source contract. No
production validator changes. Because this path exercises the real backend,
its temporary sidecars carry that backend schema's `scientific_use_allowed: true`;
this flag does not make those test artifacts scientifically admissible. Every
output remains below named `fixture-only-artifacts` / `fixture-only-data` roots,
with a `FIXTURE-ONLY-NOT-SCIENTIFIC.json` marker. On success,
`novel-pipeline-software-rehearsal.json` records `scientific_use_allowed: false`,
commands, adapters, checks, intentionally rejected artifacts and hashes of all
retained files. SCC rehearsal output is preserved within its isolated attempt
directory; none of these files may be promoted into scientific run admission.

Before the successor release is frozen, development-score validation also
replays the recorded epoch checkpoint against both hash-bound clean development
caches. It validates source sidecars, identities, checkpoint configuration,
stage/epoch, float32 projection shape, and retained-array health. Replay runs on
CPU in the same 256-row chunks as scoring. To accommodate CPU/GPU matrix-product
rounding, every component must satisfy `abs(saved - replay) <= 1e-6 +
1e-5 * abs(replay)`, the existing MotionBERT model-layer parity bounds. These
fixed bounds are an engineering consistency check, chosen before successor
measurements; they cannot be widened in response to scores. Retrieval ranks
and clean selection metrics are still recomputed exactly from the retained
arrays, which replay never replaces. A mismatch stops validation. The added
CPU replay and source validation time belongs in the measured capacity forecast.
