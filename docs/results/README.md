# Result documents

Commit only compact, public-safe summary tables, figures, and final documents
that can be regenerated from an explicit immutable run set. Full checkpoints,
feature caches, predictions, bootstrap samples, and logs belong under
`POSE_EMBED_ARTIFACT_ROOT`, never in Git.

## `pose-embed report build`

The command validates every supplied result schema. For a complete locked
180-row core matrix, it also rehashes the bound scientific inputs, recomputes
retrieval ranks from the immutable feature artifacts, and writes:

- `summary.json` and `summary.md`, containing all method, seed, condition, and
  query-definition rows;
- `primary-analysis.json`, containing the preregistered primary-query Top-1
  degradation effect and the deterministic 10,000-replicate paired percentile
  bootstrap grouped by `(setup, performer, repetition, action)`; and
- `core-metric-curves.json` and six audit-grade SVGs covering Top-1, MRR, and
  R@5 for both primary and exact-official queries, all three corruption
  families, all three core methods, and every paired seed. SVG lines are seed
  means and whiskers span all three observed seeds; no cell is selected.
- `core-error-analysis.json`, containing every method/seed/condition/query/class
  error row and one deterministic example slot per matrix cell. The example is
  the lexicographically first Top-1 error, or `null` when the cell has no error.
- `core-telemetry.json`, containing all 180 evaluation and nine training
  wall-time/peak-memory records plus per-method and overall summaries.
- `core-failures.json`, deterministically derived from immutable final-training
  attempt/outcome pairs, including resolved and unresolved failures.

The bootstrap seed is fixed at `2026`. Synchronized camera observations share
one cluster because camera is deliberately absent from the cluster identity.
The JSON records every seed/corruption cell, the confidence interval, its
direction, and whether the preregistered upper-bound rule is met. A negative
effect means contextual training degraded less; it does not by itself mean
higher clean or overall retrieval.

`summary.json` schema v5 binds every JSON/SVG artifact by SHA-256. The stretch
gate calls `validate_core_report_summary`, which reruns full result provenance
and retrieval checks, recomputes every artifact, and requires byte-identical
JSON and SVG output. These are compact protocol-required audit figures and
tables; poster composition and narrative report layout remain separate Week 10
deliverables.

Telemetry is consumed from the strict `RuntimeTelemetry` object on every
`EvaluationResult` and from the identical top-level `telemetry` object in each
locked training `run-manifest.json`. Its fields are:

- `wall_time_seconds`: finite number greater than or equal to zero;
- `peak_memory_bytes`: integer greater than or equal to zero; and
- `peak_memory_source`: `torch_cuda_max_memory_allocated`, `process_max_rss`, or
  `not_available`.

Training and evaluation validators require wall time to match the corresponding
provenance timestamps. Peak-memory maxima are grouped by source because CUDA
allocator peaks and process RSS are not interchangeable measurements.
